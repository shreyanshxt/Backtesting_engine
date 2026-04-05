from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
from io import BytesIO
import os
import datetime
import yfinance as yf
from complete_backtest_system import (
    Backtest, HistoricCSVDataHandler, SimulatedExecutionHandler, 
    Portfolio, MultiStrategyRunner, RegimeDetector
)
from active_strategies import (
    MomentumStrategy, MeanReversionStrategy, RSIStrategy,
    MovingAverageCrossStrategy, RebalancingStrategy, MLStrategy
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"status": "online", "engine": "NexusQuant Backtesting v2.0"}

@app.post("/backtest")
async def run_backtest(
    strategy: str = Form("momentum"),
    symbol: str = Form("NVDA"),
    customCode: str = Form(None),
    startDate: str = Form("2023-01-01"),
    endDate: str = Form("2024-12-31"),
    leverage: float = Form(1.0),
    stopLoss: float = Form(5.0),
    takeProfit: float = Form(15.0),
    posSize: float = Form(10.0),
    commission: float = Form(0.05)
):
    # Setup paths
    csv_dir = os.path.join(os.getcwd(), 'data')
    if not os.path.exists(csv_dir):
        os.makedirs(csv_dir)

    symbol_list = [symbol]
    
    # Check if data exists, if not, download it
    file_path = os.path.join(csv_dir, f"{symbol}.csv")
    if not os.path.exists(file_path):
        try:
            print(f"Downloading data for {symbol}...")
            # Use a wider range to ensure we have enough data for Indicators
            df = yf.download(symbol, start="2020-01-01", end=endDate)
            if not df.empty:
                # Yahoo Finance returns: Date, Open, High, Low, Close, Adj Close, Volume
                # Our system expects: datetime, open, high, low, close, volume (matching DataHandler)
                # Ensure the columns are in the right order and named correctly
                df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
                df.columns = ['open', 'high', 'low', 'close', 'volume']
                df.index.name = 'datetime'
                df.to_csv(file_path)
            else:
                return {"error": f"No data found for symbol: {symbol}"}
        except Exception as e:
            return {"error": f"Failed to download data for {symbol}: {str(e)}"}

    initial_capital = 1000000.0
    
    try:
        start_date = datetime.datetime.strptime(startDate, "%Y-%m-%d")
    except Exception:
        start_date = datetime.datetime(2023, 1, 1)

    try:
        end_date = datetime.datetime.strptime(endDate, "%Y-%m-%d")
    except Exception:
        end_date = datetime.datetime(2024, 12, 31)

    # Configuration
    execution_kwargs = {
        'commission_pct': commission / 100.0,
        'slippage_pct': 0.0005,
        'use_regime_detection': True,
        'risk_kwargs': {
            'pos_size_pct': posSize / 100.0,
            'max_drawdown': 0.20,
            'max_exposure_pct': leverage,
            'stop_loss_pct': stopLoss / 100.0,
            'take_profit_pct': takeProfit / 100.0
        }
    }

    strategy_map = {
        "momentum": MomentumStrategy,
        "mean_reversion": MeanReversionStrategy,
        "rsi": RSIStrategy,
        "mac": MovingAverageCrossStrategy,
        "rebalance": RebalancingStrategy,
        "ml": MLStrategy,
        "multi": MultiStrategyRunner
    }

    if strategy == "custom":
        if not customCode:
            return {"error": "No custom code provided."}
        
        namespace = {}
        exec_globals = {
            "pd": pd,
            "np": np,
            "Strategy": __import__("complete_backtest_system").Strategy,
            "MarketEvent": __import__("complete_backtest_system").MarketEvent,
            "SignalEvent": __import__("complete_backtest_system").SignalEvent
        }

        
        try:
            exec(customCode, exec_globals, namespace)
            chosen_strategy = namespace.get("CustomStrategy")
            if not chosen_strategy:
                return {"error": "Your code must define a class named 'CustomStrategy'."}
        except Exception as e:
            import traceback
            return {"error": str(e), "traceback": traceback.format_exc()}
    else:
        chosen_strategy = strategy_map.get(strategy, MomentumStrategy)

    # Create and run backtest
    backtest = Backtest(
        csv_dir=csv_dir,
        symbol_list=symbol_list,
        initial_capital=initial_capital,
        heartbeat=0.0,
        start_date=start_date,
        data_handler=HistoricCSVDataHandler,
        execution_handler=SimulatedExecutionHandler,
        portfolio=Portfolio,
        strategy=chosen_strategy,
        execution_kwargs=execution_kwargs
    )

    # Special handling for MultiStrategy
    if strategy == "multi":
        detector = RegimeDetector(backtest.data_handler)
        backtest.strategy.regime_detector = detector
        backtest.strategy.add_strategy(MomentumStrategy(backtest.data_handler, backtest.events), regimes=['TRENDING', 'HIGH_VOL'])
        backtest.strategy.add_strategy(MeanReversionStrategy(backtest.data_handler, backtest.events), regimes=['RANGING', 'HIGH_VOL'])

    backtest.simulate_trading()
    
    # Return JSON summary for the dashboard
    return backtest.get_summary_json()