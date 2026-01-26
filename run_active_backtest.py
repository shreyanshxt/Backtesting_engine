#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RUN BACKTEST WITH ACTIVE STRATEGY
This will generate MANY more fills than Buy & Hold!
"""

from complete_backtest_system import *
from active_strategies import MovingAverageCrossStrategy
import datetime

if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════════════╗
║          ACTIVE STRATEGY BACKTEST - MORE FILLS!                    ║
╚════════════════════════════════════════════════════════════════════╝

Using Moving Average Crossover Strategy:
- SHORT MA: 50 days
- LONG MA: 200 days
- Generates BUY signal when 50 MA crosses above 200 MA
- Generates SELL signal when 50 MA crosses below 200 MA

This will create MANY more fills than Buy & Hold!
    """)
    
    # Configuration
    csv_dir = '/Users/shreyanshsingh/mp_env/data'
    symbol_list = ['NVDA']  # Your NVDA data
    initial_capital = 600000.0
    heartbeat = 0.0
    start_date = datetime.datetime(2020, 1, 1, 0, 0, 0)
    
    # Create backtest with ACTIVE STRATEGY
    backtest = Backtest(
        csv_dir=csv_dir,
        symbol_list=symbol_list,
        initial_capital=initial_capital,
        heartbeat=heartbeat,
        start_date=start_date,
        data_handler=HistoricCSVDataHandler,
        execution_handler=SimulatedExecutionHandler,
        portfolio=Portfolio,
        strategy=MovingAverageCrossStrategy  # ← ACTIVE STRATEGY (more trades!)
    )
    
    # Run backtest
    backtest.simulate_trading()
    
    print("""
╔════════════════════════════════════════════════════════════════════╗
║                     WANT EVEN MORE FILLS?                          ║
╚════════════════════════════════════════════════════════════════════╝

Try these strategies (in active_strategies.py):

1. MeanReversionStrategy - Bollinger Bands (very active!)
2. MomentumStrategy - Rate of change (high frequency)
3. RSIStrategy - Oversold/Overbought (frequent trades)
4. RebalancingStrategy - Trade every N days (guaranteed fills)

Example:
    from active_strategies import RSIStrategy
    
    backtest = Backtest(
        ...
        strategy=RSIStrategy  # Very active in ranging markets
    )
    """)
