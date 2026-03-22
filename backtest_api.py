from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
from io import BytesIO
import os
import datetime
from complete_backtest_system import (
    Backtest, HistoricCSVDataHandler, SimulatedExecutionHandler, 
    Portfolio, MultiStrategyRunner, RegimeDetector
)
from active_strategies import (
    MomentumStrategy, MeanReversionStrategy, RSIStrategy,
    MovingAverageCrossStrategy, RebalancingStrategy
)

app = FastAPI()

# Enable CORS for the Vite dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": "online", "engine": "Antigravity Backtesting v2.0"}

@app.post("/backtest")
async def run_backtest(
    strategy: str = Form("momentum"),
    symbol: str = Form("NVDA"),
    customCode: str = Form(None)
):
    # Setup paths
    csv_dir = os.getcwd() + '/data'
    symbol_list = [symbol]
    initial_capital = 1000000.0
    start_date = datetime.datetime(2023, 1, 1)

    # Configuration
    execution_kwargs = {
        'commission_pct': 0.0002,
        'slippage_pct': 0.0005,
        'use_regime_detection': True
    }

    # Map strategy strings to classes
    strategy_map = {
        "momentum": MomentumStrategy,
        "mean_reversion": MeanReversionStrategy,
        "rsi": RSIStrategy,
        "mac": MovingAverageCrossStrategy,
        "rebalance": RebalancingStrategy,
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
            "MarketEvent": __import__("complete_backtest_system").MarketEvent
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
        backtest.strategy.add_strategy(MomentumStrategy(backtest.data_handler, backtest.events), regimes=['TRENDING'])
        backtest.strategy.add_strategy(MeanReversionStrategy(backtest.data_handler, backtest.events), regimes=['RANGING'])

    backtest.simulate_trading()
    
    # Return JSON summary for the dashboard
    return backtest.get_summary_json()