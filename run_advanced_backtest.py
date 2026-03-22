#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ADVANCED BACKTEST DEMONSTRATION
This script showcases Regime-Aware Multi-Strategy Execution.
It uses:
1. RegimeDetector (ADX/ATR based)
2. MultiStrategyRunner (Gated execution)
3. Combinations of Momentum and Mean Reversion strategies.
"""

from complete_backtest_system import *
from active_strategies import (
    MomentumStrategy, 
    MeanReversionStrategy, 
    MultiStrategyRunner
)
from riskstats import PerformanceStats, PerformanceVisuals
import datetime
import os

if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════════════╗
║          ADVANCED REGIME-AWARE BACKTEST ENGINE                     ║
╚════════════════════════════════════════════════════════════════════╝

Architecture:
1. Regime Detector: Monitors market volatility and trend strength.
2. Strategy Gating: 
   - [TRENDING] -> Momentum Strategy active
   - [RANGING]  -> Mean Reversion Strategy active
   - [HIGH_VOL] -> All entry signals silenced (Capital Preservation)
    """)
    
    # Configuration
    csv_dir = os.getcwd() + '/data'
    symbol_list = ['NVDA'] 
    initial_capital = 1000000.0
    heartbeat = 0.0
    start_date = datetime.datetime(2020, 1, 1)
    
    # Execution parameters for Indian/International markets
    execution_kwargs = {
        'commission_pct': 0.0002,      # 0.02% commission
        'slippage_pct': 0.0005,        # 0.05% slippage
        'benchmark_symbol': 'SPY' if not os.path.exists(os.path.join(csv_dir, 'HDFCBANK.NS.csv')) else 'HDFCBANK.NS'
    }

    # 1. Initialize the Base Engine Components
    # We use a dummy Strategy class because MultiStrategyRunner will manage sub-strategies
    
    backtest = Backtest(
        csv_dir=csv_dir,
        symbol_list=symbol_list,
        initial_capital=initial_capital,
        heartbeat=heartbeat,
        start_date=start_date,
        data_handler=HistoricCSVDataHandler,
        execution_handler=SimulatedExecutionHandler,
        portfolio=Portfolio,
        strategy=MultiStrategyRunner,  # <--- Our coordinator
        execution_kwargs=execution_kwargs
    )

    # 2. Configure the MultiStrategyRunner
    # Access the already initialized runner from the backtest instance
    runner = backtest.strategy
    
    # Initialize the RegimeDetector
    detector = RegimeDetector(backtest.data_handler, vol_threshold=0.05)
    runner.regime_detector = detector

    # Add sub-strategies with specific regime gates
    # We pass the same bars and events queue to sub-strategies
    momentum = MomentumStrategy(backtest.data_handler, backtest.events, lookback=14, threshold=0.01)
    mean_rev = MeanReversionStrategy(backtest.data_handler, backtest.events, period=20, num_std=1.5)

    runner.add_strategy(momentum, regimes=['TRENDING'])
    runner.add_strategy(mean_rev, regimes=['RANGING'])

    print(f"Engine initialized with {len(runner.strategies)} gated strategies.")
    
    # 3. Run Simulation
    backtest.simulate_trading()
    
    # 4. Output Results
    print("\n" + "="*50)
    print("ANALYSIS SUMMARY")
    print("="*50)
    
    stats = backtest.portfolio.output_summary_stats()
    for s in stats:
        print(f"{s[0]}: {s[1]}")
        
    # Export for the dashboard
    import json
    summary = backtest.get_summary_json()
    with open("advanced_backtest_results.json", "w") as f:
        json.dump(summary, f, indent=4)
        
    print("\nAdvanced results exported to 'advanced_backtest_results.json'")
    print("="*50 + "\n")

    # 5. Advanced Performance Stats & Visuals
    print("\n" + "="*50)
    print("ADVANCED PERFORMANCE STATS & VISUALS")
    print("="*50)
    
    equity_df = backtest.portfolio.equity_curve
    if equity_df is not None and not equity_df.empty:
        adv_stats = PerformanceStats(
            equity_df=equity_df,
            cash_flows=backtest.portfolio.cash_flows,
            closed_trades=backtest.portfolio.closed_trades
        )
        adv_results = adv_stats.summary()
        for k, v in adv_results.items():
            print(f"{k}: {v}")
            
        print("\nLogging trades to CSV...")
        logger = TradeLogger("advanced_trades_log.csv")
        logger.log_trades(backtest.portfolio.closed_trades)
        
        print("\nGenerating Performance Visuals (Close window to continue)...")
        visuals = PerformanceVisuals(equity_df)
        visuals.plot_all()
    else:
        print("No trades to visualize.")

    # 6. Walk-Forward Demonstration
    print("\n" + "="*50)
    print("DEMONSTRATING WALK-FORWARD ANALYSIS")
    print("="*50)
    
    # Define Walk-Forward windows
    wf_windows = [
        (None, None, datetime.datetime(2024, 1, 1), datetime.datetime(2024, 12, 31)),
        (None, None, datetime.datetime(2025, 1, 1), datetime.datetime(2025, 12, 31)),
        (None, None, datetime.datetime(2026, 1, 1), datetime.datetime(2026, 12, 31))
    ]
    
    # The Strategy class used in Walk-Forward is typically a single strategy.
    # To use MultiStrategyRunner in WalkForward, we can pass it, but it requires
    # setup (adding sub-strategies and detector). The WalkForward orchestrator
    # instantiates the strategy internally. For a simple demonstration, we will
    # pass MomentumStrategy.
    wf = WalkForwardBacktest(
        csv_dir, symbol_list, initial_capital, start_date,
        HistoricCSVDataHandler, SimulatedExecutionHandler, Portfolio, MomentumStrategy,
        wf_windows, execution_kwargs
    )
    wf.run() # Run full Walk-Forward
    print(f"Walk-Forward Engine initialized with {len(wf_windows)} windows.")
    print("="*50 + "\n")

    # 7. Cost Sensitivity Demonstration
    print("\n" + "="*50)
    print("DEMONSTRATING COST SENSITIVITY ANALYSIS")
    print("="*50)
    
    config = {
        'csv_dir': csv_dir, 'symbol_list': symbol_list, 'initial_capital': initial_capital,
        'heartbeat': 0.0, 'start_date': datetime.datetime(2023, 1, 1), 'end_date': datetime.datetime(2025,12,31),
        'data_handler': HistoricCSVDataHandler, 'execution_handler': SimulatedExecutionHandler,
        'portfolio': Portfolio, 'strategy': MomentumStrategy,
        'execution_kwargs': execution_kwargs.copy()
    }
    
    analyzer = CostSensitivityAnalyzer(config, [0.0, 0.001], [0.0005, 0.002])
    analyzer.run_analysis() # Run full sensitivity report
    print("Cost Sensitivity Analyzer initialized for 4 scenarios.")
    print("="*50 + "\n")
