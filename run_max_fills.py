#!/usr/bin/env python
"""
MAXIMUM FILLS - Daily Rebalancing
This will generate the MOST fills possible!
"""

from complete_backtest_system import *
from active_strategies import RebalancingStrategy
import datetime

if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════════════╗
║             MAXIMUM FILLS - DAILY REBALANCING!                     ║
╚════════════════════════════════════════════════════════════════════╝

Trades EVERY DAY!
Expected fills: ~750 (one for each trading day in your data)
    """)
    
    backtest = Backtest(
        csv_dir='/Users/shreyanshsingh/mp_env/data',
        symbol_list=['NVDA'],
        initial_capital=600000.0,
        heartbeat=0.0,
        start_date=datetime.datetime(2023, 1, 26),
        data_handler=HistoricCSVDataHandler,
        execution_handler=SimulatedExecutionHandler,
        portfolio=Portfolio,
        strategy=lambda bars, events: RebalancingStrategy(
            bars, events, rebalance_days=1  # ← DAILY! Maximum fills!
        )
    )
    
    backtest.simulate_trading()
    
    print(f"""
╔══════════════════════════════════════════════════════════════════╗
║                   RESULTS - MAXIMUM FILLS!                       ║
╚══════════════════════════════════════════════════════════════════╝

Fills: {backtest.fills} 

THIS IS {backtest.fills}X MORE THAN BUY & HOLD!

You now have HUNDREDS of fills for analysis!
    """)
