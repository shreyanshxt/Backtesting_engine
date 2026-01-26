#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AGGRESSIVE REBALANCING STRATEGY - GUARANTEED FILLS!
Trades every N days - you control exactly how many fills you want
"""

from complete_backtest_system import *
from active_strategies import RebalancingStrategy
import datetime

if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════════════╗
║       AGGRESSIVE STRATEGY - MANY FILLS GUARANTEED!                 ║
╚════════════════════════════════════════════════════════════════════╝

Using Rebalancing Strategy:
- Trades every 30 days (adjustable)
- GUARANTEED fills!
- For 3 years of data: ~36 fills minimum

Want MORE fills? Change rebalance_days:
- rebalance_days=7  → ~156 fills/year (weekly)
- rebalance_days=1  → ~252 fills/year (daily)
    """)
    
    # Configuration
    csv_dir = '/Users/shreyanshsingh/mp_env/data'
    symbol_list = ['NVDA']
    initial_capital = 600000.0
    heartbeat = 0.0
    start_date = datetime.datetime(2023, 1, 26)  # Match your NVDA data start
    
    # Create backtest with REBALANCING STRATEGY
    # This will generate MANY fills!
    backtest = Backtest(
        csv_dir=csv_dir,
        symbol_list=symbol_list,
        initial_capital=initial_capital,
        heartbeat=heartbeat,
        start_date=start_date,
        data_handler=HistoricCSVDataHandler,
        execution_handler=SimulatedExecutionHandler,
        portfolio=Portfolio,
        strategy=lambda bars, events: RebalancingStrategy(
            bars, events, rebalance_days=30  # ← Change this! Try 7, 14, 30
        )
    )
    
    # Run backtest
    backtest.simulate_trading()
    
    print(f"""
╔════════════════════════════════════════════════════════════════════╗
║                   ACTUAL FILLS ACHIEVED                            ║
╚════════════════════════════════════════════════════════════════════╝

Signals: {backtest.signals}
Orders: {backtest.orders}
Fills: {backtest.fills}

THIS IS {backtest.fills}X MORE THAN BUY & HOLD!

Want EVEN MORE fills?
Edit this file and change: rebalance_days=30
Try: rebalance_days=7 (weekly) or rebalance_days=1 (daily)
    """)
