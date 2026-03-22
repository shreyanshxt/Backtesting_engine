#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
COMPREHENSIVE BACKTEST EVALUATION SUITE
Tests all available strategies and prints detailed KPI metrics.
"""

from complete_backtest_system import *
from active_strategies import (
    MovingAverageCrossStrategy,
    MeanReversionStrategy,
    MomentumStrategy,
    RSIStrategy,
    RebalancingStrategy
)
from riskstats import PerformanceStats
import datetime
import os
import io
import contextlib

if __name__ == "__main__":
    print("================================================================================")
    print("COMPREHENSIVE BACKTEST EVALUATION SUITE")
    print("Evaluating all active strategies on NVDA (2023-2026)")
    print("================================================================================")
    
    csv_dir = os.path.join(os.getcwd(), 'data')
    symbol_list = ['NVDA']
    initial_capital = 1000000.0
    heartbeat = 0.0
    start_date = datetime.datetime(2023, 1, 1)
    
    execution_kwargs = {
        'commission_pct': 0.0002,
        'slippage_pct': 0.0005,
        'benchmark_symbol': 'SPY' if not os.path.exists(os.path.join(csv_dir, 'HDFCBANK.NS.csv')) else 'HDFCBANK.NS'
    }

    strategies_to_test = [
        ("Moving Average Crossover", MovingAverageCrossStrategy, {}),
        ("Mean Reversion (Bollinger Bands)", MeanReversionStrategy, {'period': 20, 'num_std': 2.0}),
        ("Momentum (RoC)", MomentumStrategy, {'lookback': 14, 'threshold': 0.01}),
        ("RSI Oversold/Overbought", RSIStrategy, {'period': 14, 'oversold': 30, 'overbought': 70}),
        ("Monthly Rebalancing", RebalancingStrategy, {'rebalance_days': 21})
    ]

    for name, strategy_cls, params in strategies_to_test:
        print(f"\n▶ Evaluating: {name}...")
        
        # Suppress the heavy engine logging during the simulation
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            # Wrapper to pass custom parameters through the generic Strategy initialization
            class WrappedStrategy(strategy_cls):
                def __init__(self, bars, events, regime_detector=None, **kwargs):
                    super().__init__(bars, events, **params)
            
            backtest = Backtest(
                csv_dir=csv_dir,
                symbol_list=symbol_list,
                initial_capital=initial_capital,
                heartbeat=heartbeat,
                start_date=start_date,
                data_handler=HistoricCSVDataHandler,
                execution_handler=SimulatedExecutionHandler,
                portfolio=Portfolio,
                strategy=WrappedStrategy,
                execution_kwargs=execution_kwargs
            )
            backtest.simulate_trading()
            
            equity_df = backtest.portfolio.equity_curve
            
            if equity_df is not None and not equity_df.empty:
                adv_stats = PerformanceStats(
                    equity_df=equity_df,
                    cash_flows=backtest.portfolio.cash_flows,
                    closed_trades=backtest.portfolio.closed_trades
                )
                results_dict = adv_stats.summary()
                results_dict["Peak Unrealized PnL"] = round(equity_df['unrealized_pnl'].max(), 2)
            else:
                results_dict = {"Error": "No simulation data"}

        # Print the extracted metrics directly
        print("-" * 50)
        for k, v in results_dict.items():
            print(f"  {k}: {v}")
        print("-" * 50)
        
        # Format and Print Trades Table
        closed_trades = backtest.portfolio.closed_trades
        if closed_trades:
            import pandas as pd
            print("\n  [Recent Closed Trades (Last 10)]")
            trades_df = pd.DataFrame(closed_trades)
            # Select relevant columns for clear display
            cols = ['symbol', 'entry_time', 'exit_time', 'side', 'entry_price', 'exit_price', 'pnl', 'pnl_pct']
            display_cols = [c for c in cols if c in trades_df.columns]
            print(trades_df[display_cols].tail(10).to_string(index=False))
        else:
            print("\n  [No closed trades recorded]")
            
        # Print Equity Curve Tails
        if equity_df is not None and not equity_df.empty:
            print("\n  [Equity Curve (Last 5 Bars)]")
            print(equity_df[['total', 'cash', 'realized_pnl', 'unrealized_pnl']].tail(5).to_string())
            
        print("=" * 80)

    print("\n✅ Evaluation Suite Complete.")
