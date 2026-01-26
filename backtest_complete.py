#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Complete Event-Driven Backtesting System
This file contains a complete Backtest class that can use either 
SimulatedExecutionHandler (for backtesting) or IBExecutionHandler (for live trading)
"""

try:
    import Queue as queue
except ImportError:
    import queue

import time
import datetime


class Backtest(object):
    """
    Encapsulates the settings and components for carrying out
    an event-driven backtest.
    """
    
    def __init__(
        self, 
        csv_dir, 
        symbol_list, 
        initial_capital,
        heartbeat, 
        start_date,
        data_handler,
        execution_handler,
        portfolio,
        strategy
    ):
        """
        Initializes the backtest.
        
        Parameters:
        csv_dir - The hard root to the CSV data directory.
        symbol_list - The list of symbol strings.
        initial_capital - The starting capital for the portfolio.
        heartbeat - Backtest "heartbeat" in seconds
        start_date - The start datetime of the strategy.
        data_handler - (Class) Handles the market data feed.
        execution_handler - (Class) Handles the orders/fills for trades.
        portfolio - (Class) Keeps track of portfolio current and prior positions.
        strategy - (Class) Generates signals based on market data.
        """
        self.csv_dir = csv_dir
        self.symbol_list = symbol_list
        self.initial_capital = initial_capital
        self.heartbeat = heartbeat
        self.start_date = start_date
        
        self.data_handler_cls = data_handler
        self.execution_handler_cls = execution_handler
        self.portfolio_cls = portfolio
        self.strategy_cls = strategy
        
        self.events = queue.Queue()
        
        self.signals = 0
        self.orders = 0
        self.fills = 0
        self.num_strats = 1
        
        self._generate_trading_instances()

    def _generate_trading_instances(self):
        """
        Generates the trading instance objects from 
        their class types.
        """
        print("Creating DataHandler, Strategy, Portfolio and ExecutionHandler")
        self.data_handler = self.data_handler_cls(self.events, self.csv_dir, self.symbol_list)
        self.strategy = self.strategy_cls(self.data_handler, self.events)
        self.portfolio = self.portfolio_cls(self.data_handler, self.events, self.start_date, 
                                            self.initial_capital)
        self.execution_handler = self.execution_handler_cls(self.events)

    def _run_backtest(self):
        """
        Executes the backtest.
        """
        i = 0
        while True:
            i += 1
            print("Iteration:", i)
            
            # Update the market bars
            if self.data_handler.continue_backtest == True:
                self.data_handler.update_bars()
            else:
                break
            
            # Handle the events
            while True:
                try:
                    event = self.events.get(False)
                except queue.Empty:
                    break
                else:
                    if event is not None:
                        if event.type == 'MARKET':
                            self.strategy.calculate_signals(event)
                            self.portfolio.update_timeindex(event)
                            
                        elif event.type == 'SIGNAL':
                            self.signals += 1
                            self.portfolio.update_signal(event)
                            
                        elif event.type == 'ORDER':
                            self.orders += 1
                            self.execution_handler.execute_order(event)
                            
                        elif event.type == 'FILL':
                            self.fills += 1
                            self.portfolio.update_fill(event)
            
            time.sleep(self.heartbeat)

    def _output_performance(self):
        """
        Outputs the strategy performance from the backtest.
        """
        self.portfolio.create_equity_curve_dataframe()
        
        print("Creating summary stats...")
        stats = self.portfolio.output_summary_stats()
        
        print("Creating equity curve...")
        print(self.portfolio.equity_curve.tail(10))
        pprint.pprint(stats)

        print("Signals: %s" % self.signals)
        print("Orders: %s" % self.orders)
        print("Fills: %s" % self.fills)

    def simulate_trading(self):
        """
        Simulates the backtest and outputs portfolio performance.
        """
        self._run_backtest()
        self._output_performance()


# Example usage for BACKTESTING (with SimulatedExecutionHandler)
if __name__ == "__main__":
    """
    Example of how to use the Backtest class with SimulatedExecutionHandler
    """
    # Import all necessary classes (assumed to be defined elsewhere)
    # from events import MarketEvent, SignalEvent, OrderEvent, FillEvent
    # from data import HistoricCSVDataHandler
    # from execution import SimulatedExecutionHandler
    # from portfolio import Portfolio
    # from strategy import BuyAndHoldStrategy  # or your custom strategy
    
    csv_dir = '/path/to/your/data'
    symbol_list = ['AAPL']
    initial_capital = 100000.0
    heartbeat = 0.0  # Speed for backtest
    start_date = datetime.datetime(2010, 1, 1, 0, 0, 0)
    
    # For BACKTESTING - use SimulatedExecutionHandler
    backtest = Backtest(
        csv_dir, 
        symbol_list, 
        initial_capital,
        heartbeat, 
        start_date,
        HistoricCSVDataHandler,
        SimulatedExecutionHandler,  # <- Use this for backtesting
        Portfolio,
        BuyAndHoldStrategy
    )
    
    backtest.simulate_trading()
    
    
    # For LIVE TRADING - use IBExecutionHandler
    # backtest_live = Backtest(
    #     csv_dir, 
    #     symbol_list, 
    #     initial_capital,
    #     heartbeat, 
    #     start_date,
    #     HistoricCSVDataHandler,  # or LiveDataHandler for IB
    #     IBExecutionHandler,      # <- Use this for live trading
    #     Portfolio,
    #     YourStrategy
    # )
    # backtest_live.simulate_trading()
