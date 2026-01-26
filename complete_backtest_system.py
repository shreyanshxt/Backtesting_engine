"""
Complete Event-Driven Backtesting System
All components in one file for easy understanding
"""

# ============================================================================
# IMPORTS
# ============================================================================

from abc import ABCMeta, abstractmethod
import datetime
import os
import os.path
import pandas as pd
import numpy as np
from active_strategies import *
try:
    import Queue as queue
except ImportError:
    import queue
import time


# ============================================================================
# EVENT CLASSES
# ============================================================================

class Event(object):
    """Base class for events."""
    pass


class MarketEvent(Event):
    """Handles the tick event."""
    def __init__(self):
        """Initialize the market event."""
        self.type = 'MARKET'


class SignalEvent(Event):
    """Handles the signal event."""
    def __init__(self, strategy_id, symbol, datetime, signal_type, strength):
        self.type = 'SIGNAL'
        self.strategy_id = strategy_id
        self.symbol = symbol
        self.datetime = datetime
        self.signal_type = signal_type
        self.strength = strength


class OrderEvent(Event):
    """Handles the order event."""
    def __init__(self, symbol, order_type, quantity, direction):
        self.type = 'ORDER'
        self.symbol = symbol
        self.order_type = order_type
        self.quantity = quantity
        self.direction = direction
    
    def print_order(self):
        print("Order: Symbol = %s, Type = %s, Quantity = %s, Direction = %s" % 
              (self.symbol, self.order_type, self.quantity, self.direction))


class FillEvent(Event):
    """Handles the fill event."""
    def __init__(self, symbol, timeindex, exchange, quantity, direction, fill_cost, commission=None):
        self.type = 'FILL'
        self.timeindex = timeindex
        self.symbol = symbol
        self.exchange = exchange
        self.quantity = quantity
        self.direction = direction
        self.fill_cost = fill_cost
        
        # Calculate commission
        if commission is None:
            self.commission = self.calculate_ib_commission()
        else:
            self.commission = commission
    
    def calculate_indian_commission(self):
        """
        Indian equity delivery transaction cost model.
        Approximation:
        - Buy  : 0.15%
        - Sell : 0.15%
        """
        trade_value = self.quantity * self.fill_cost

        if self.direction == 'BUY':
            return trade_value * 0.0015
        elif self.direction == 'SELL':
            return trade_value * 0.0015
        else:
            return 0.0

# ============================================================================
# DATA HANDLER
# ============================================================================

class DataHandler(object):
    """Abstract base class for data handlers."""
    __metaclass__ = ABCMeta
    
    @abstractmethod
    def get_latest_bar(self, symbol):
        """Returns the last bar updated"""
        raise NotImplementedError("Should implement get_latest_bar")
    
    @abstractmethod
    def get_latest_bars(self, symbol, N=1):
        """Returns the last N bars updated"""
        raise NotImplementedError("Should implement get_latest_bars")
    
    @abstractmethod
    def get_latest_bar_datetime(self, symbol):
        """Returns the last bar datetime"""
        raise NotImplementedError("Should implement get_latest_bar_datetime")
    
    @abstractmethod
    def get_latest_bar_value(self, symbol, val_type):
        """Returns the last bar value"""
        raise NotImplementedError("Should implement get_latest_bar_value")
    
    @abstractmethod
    def get_latest_bar_values(self, symbol, val_type, N=1):
        """Returns the last N bar values"""
        raise NotImplementedError("Should implement get_latest_bar_values")
    
    @abstractmethod
    def update_bars(self):
        """Updates the bars"""
        raise NotImplementedError("Should implement update_bars()")


class HistoricCSVDataHandler(DataHandler):
    """Handles historical data from CSV files."""
    
    def __init__(self, events, csv_dir, symbol_list):
        self.events = events
        self.csv_dir = csv_dir
        self.symbol_list = symbol_list
        self.symbol_data = {}
        self.latest_symbol_data = {}
        self.continue_backtest = True
        self._open_convert_csv_files()
    
    def _open_convert_csv_files(self):
        """Open CSV files and create generators."""
        comb_index = None
        for s in self.symbol_list:
            self.symbol_data[s] = pd.read_csv(
                os.path.join(self.csv_dir, '%s.csv' % s),
                header=0,
                index_col=0,
                parse_dates=True,
                names=["datetime", "open", "high", "low", "close", "volume"]
            ).sort_index()
            
            if comb_index is None:
                comb_index = self.symbol_data[s].index
            else:
                comb_index = comb_index.union(self.symbol_data[s].index)
            
            self.latest_symbol_data[s] = []
        
        for s in self.symbol_list:
            self.symbol_data[s] = self.symbol_data[s].reindex(
                index=comb_index, method='pad'
            ).iterrows()
    
    def _get_new_bar(self, symbol):
        """Returns the latest bar from the data feed."""
        for b in self.symbol_data[symbol]:
            yield b
    
    def get_latest_bar(self, symbol):
        """Returns the last bar from the latest_symbol list."""
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("Symbol %s is not available in the historical data set." % symbol)
            raise
        else:
            return bars_list[-1]
    
    def get_latest_bars(self, symbol, N=1):
        """Returns the last N bars from the latest_symbol list."""
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("Symbol %s is not available in the historical data set." % symbol)
            raise
        else:
            return bars_list[-N:]
    
    def get_latest_bar_datetime(self, symbol):
        """Returns a Python datetime object for the last bar."""
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("Symbol %s is not available in the historical data set." % symbol)
            raise
        else:
            return bars_list[-1][0]
    
    def get_latest_bar_value(self, symbol, val_type):
        """Returns one of the Open, High, Low, Close, Volume or OI values."""
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("Symbol %s is not available in the historical data set." % symbol)
            raise
        else:
            return getattr(bars_list[-1][1], val_type)
    
    def get_latest_bar_values(self, symbol, val_type, N=1):
        """Returns the last N bar values from the latest_symbol list."""
        try:
            bars_list = self.get_latest_bars(symbol, N)
        except KeyError:
            print("Symbol %s is not available in the historical data set." % symbol)
            raise
        else:
            return np.array([getattr(b[1], val_type) for b in bars_list])
    
    def update_bars(self):
        """Pushes the latest bar to the latest_symbol_data structure."""
        for s in self.symbol_list:
            try:
                bar = next(self._get_new_bar(s))
            except StopIteration:
                self.continue_backtest = False
            else:
                if bar is not None:
                    self.latest_symbol_data[s].append(bar)
        
        self.events.put(MarketEvent())


# ============================================================================
# STRATEGY
# ============================================================================

class Strategy(object):
    """Abstract base class for strategy."""
    __metaclass__ = ABCMeta
    
    @abstractmethod
    def calculate_signals(self, event):
        """Calculate signals based on market data."""
        raise NotImplementedError("Should implement calculate_signals()")


class BuyAndHoldStrategy(Strategy):
    """Simple buy and hold strategy for testing."""
    
    def __init__(self, bars, events):
        self.bars = bars
        self.symbol_list = self.bars.symbol_list
        self.events = events
        self.bought = self._calculate_initial_bought()
    
    def _calculate_initial_bought(self):
        """Adds keys to the bought dictionary for all symbols."""
        bought = {}
        for s in self.symbol_list:
            bought[s] = False
        return bought
    
    def calculate_signals(self, event):
        """For Buy and Hold, generate Signal to buy once for each symbol."""
        if event.type == 'MARKET':
            for s in self.symbol_list:
                bars = self.bars.get_latest_bars(s, N=1)
                if bars is not None and bars != []:
                    if self.bought[s] == False:
                        # (Long only) Send the signal
                        signal = SignalEvent(1, s, bars[0][0], 'LONG', 1.0)
                        self.events.put(signal)
                        self.bought[s] = True


# ============================================================================
# PORTFOLIO
# ============================================================================

class Portfolio(object):
    """Handles positions and market value of all instruments."""
    
    def __init__(self, bars, events, start_date, initial_capital=100000.0):
        self.bars = bars
        self.events = events
        self.symbol_list = self.bars.symbol_list
        self.start_date = start_date
        self.initial_capital = initial_capital
        
        self.all_positions = self.construct_all_positions()
        self.current_positions = dict((k, v) for k, v in [(s, 0) for s in self.symbol_list])
        
        self.all_holdings = self.construct_all_holdings()    # list of dicts per timestep
        self.cash_flows = [(self.start_date, -self.initial_capital)]      # for XIRR
        self.current_holdings = self.construct_current_holdings()
    
    def construct_all_positions(self):
        """Constructs the positions list using the start_date."""
        d = dict((k, v) for k, v in [(s, 0) for s in self.symbol_list])
        d['datetime'] = self.start_date
        return [d]
    
    def construct_all_holdings(self):
        """Constructs the holdings list using the start_date."""
        d = dict((k, v) for k, v in [(s, 0.0) for s in self.symbol_list])
        d['datetime'] = self.start_date
        d['cash'] = self.initial_capital
        d['commission'] = 0.0
        d['total'] = self.initial_capital
        return [d]
    
    def construct_current_holdings(self):
        """Constructs the current holdings."""
        d = dict((k, v) for k, v in [(s, 0.0) for s in self.symbol_list])
        d['cash'] = self.initial_capital
        d['commission'] = 0.0
        d['total'] = self.initial_capital
        return d
    
    def update_timeindex(self, event):
        """Updates positions and holdings at each bar."""
        latest_datetime = self.bars.get_latest_bar_datetime(self.symbol_list[0])
        
        # Update positions
        dp = dict((k, v) for k, v in [(s, 0) for s in self.symbol_list])
        dp['datetime'] = latest_datetime
        
        for s in self.symbol_list:
            dp[s] = self.current_positions[s]
        
        self.all_positions.append(dp)
        
        # Update holdings
        dh = dict((k, v) for k, v in [(s, 0) for s in self.symbol_list])
        dh['datetime'] = latest_datetime
        dh['cash'] = self.current_holdings['cash']
        dh['commission'] = self.current_holdings['commission']
        dh['total'] = self.current_holdings['cash']
        
        for s in self.symbol_list:
            market_value = self.current_positions[s] * self.bars.get_latest_bar_value(s, 'close')
            dh[s] = market_value
            dh['total'] += market_value
        
        self.all_holdings.append(dh)
    
    def update_positions_from_fill(self, fill):
        """Updates positions based on a fill."""
        fill_dir = 0
        if fill.direction == 'BUY':
            fill_dir = 1
        elif fill.direction == 'SELL':
            fill_dir = -1
        
        self.current_positions[fill.symbol] += fill_dir * fill.quantity
    def update_from_cash_event(self, event):
        self.cash += event.amount
        self.cash_flows.append((event.timestamp, -event.amount))
        return self.cash_flows

    def update_holdings_from_fill(self, fill):
        """Updates holdings based on a fill."""
        fill_dir = 0
        if fill.direction == 'BUY':
            fill_dir = 1
        elif fill.direction == 'SELL':
            fill_dir = -1
        
        fill_cost = self.bars.get_latest_bar_value(fill.symbol, 'close')
        cost = fill_dir * fill_cost * fill.quantity
        
        self.current_holdings[fill.symbol] += cost
        self.current_holdings['commission'] += fill.commission
        self.current_holdings['cash'] -= (cost + fill.commission)
        self.current_holdings['total'] -= (cost + fill.commission)
    
    def update_fill(self, event):
        """Updates the portfolio based on a fill."""
        if event.type == 'FILL':
            self.update_positions_from_fill(event)
            self.update_holdings_from_fill(event)
    
    def generate_naive_order(self, signal):
        """Generates a simple order (100 shares)."""
        order = None
        
        symbol = signal.symbol
        direction = signal.signal_type
        strength = signal.strength
        
        mkt_quantity = 200
        cur_quantity = self.current_positions[symbol]
        order_type = 'MKT'
        
        if direction == 'LONG' and cur_quantity == 0:
            order = OrderEvent(symbol, order_type, mkt_quantity, 'BUY')
        if direction == 'SHORT' and cur_quantity == 0:
            order = OrderEvent(symbol, order_type, mkt_quantity, 'SELL')
        if direction == 'EXIT' and cur_quantity > 0:
            order = OrderEvent(symbol, order_type, abs(cur_quantity), 'SELL')
        if direction == 'EXIT' and cur_quantity < 0:
            order = OrderEvent(symbol, order_type, abs(cur_quantity), 'BUY')
        
        return order
    
    def update_signal(self, event):
        """Acts on a SignalEvent to generate new orders."""
        if event.type == 'SIGNAL':
            order_event = self.generate_naive_order(event)
            self.events.put(order_event)
    
    def create_equity_curve_dataframe(self):
        """Creates a pandas DataFrame from the all_holdings list."""
        curve = pd.DataFrame(self.all_holdings)
        curve.set_index('datetime', inplace=True)
        curve['returns'] = curve['total'].pct_change()
        curve['equity_curve'] = (1.0 + curve['returns']).cumprod()
        self.equity_curve = curve
        return curve
    
    def output_summary_stats(self):
        """Creates summary statistics from the equity curve."""
        total_return = self.equity_curve['equity_curve'].iloc[-1]
        returns = self.equity_curve['returns']
        pnl = self.equity_curve['equity_curve']
        
        sharpe_ratio = self.create_sharpe_ratio(returns)
        drawdown, max_dd, dd_duration = self.create_drawdowns(pnl)
        
        self.equity_curve['drawdown'] = drawdown
        
        stats = [("Total Return", "%0.2f%%" % ((total_return - 1.0) * 100.0)),
                 ("Sharpe Ratio", "%0.2f" % sharpe_ratio),
                 ("Max Drawdown", "%0.2f%%" % (max_dd * 100.0)),
                 ("Drawdown Duration", "%d" % dd_duration)]
        
        return stats
    
    def create_sharpe_ratio(self, returns, periods=252):
        """Calculates the Sharpe ratio."""
        return np.sqrt(periods) * (np.mean(returns)) / np.std(returns)
    
    def create_drawdowns(self, equity):
        """
        equity: pandas Series of total portfolio value
        """

        running_max = equity.cummax()
        drawdown = (equity / running_max) - 1.0

        max_drawdown = drawdown.min()

        duration = (drawdown < 0).astype(int)
        duration = duration.groupby((duration == 0).cumsum()).cumcount()
        max_duration = duration.max()

        return drawdown, max_drawdown, max_duration



# ============================================================================
# EXECUTION HANDLERS
# ============================================================================

class ExecutionHandler(object):
    """Abstract base class for execution handlers."""
    __metaclass__ = ABCMeta
    
    @abstractmethod
    def execute_order(self, event):
        """Execute an order."""
        raise NotImplementedError("Should implement execute_order()")


class SimulatedExecutionHandler(ExecutionHandler):
    """
    Simulates order execution - NO REAL TRADING
    Use this for BACKTESTING
    """
    def __init__(self, events):
        self.events = events
    
    def execute_order(self, event):
        """Simulates executing an order."""
        if event.type == 'ORDER':
            fill_event = FillEvent(
                symbol=event.symbol,
                timeindex=datetime.datetime.utcnow(),
                exchange='SIMULATED',
                quantity=event.quantity,
                direction=event.direction,
                fill_cost=None,  # Will use current market price
                commission=True  # Will be calculated
            )
            self.events.put(fill_event)


# ============================================================================
# BACKTEST ENGINE
# ============================================================================

class Backtest(object):
    """
    Encapsulates the event-driven backtesting system.
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
        Initialize the backtest.
        
        Parameters:
        -----------
        csv_dir : str
            Path to CSV data directory
        symbol_list : list
            List of symbol strings
        initial_capital : float
            Starting capital
        heartbeat : float
            Backtest heartbeat in seconds (0.0 for max speed)
        start_date : datetime
            Start date of strategy
        data_handler : class
            DataHandler class (not instance)
        execution_handler : class
            ExecutionHandler class (not instance)
        portfolio : class
            Portfolio class (not instance)
        strategy : class
            Strategy class (not instance)
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
        
        self._generate_trading_instances()
    
    def _generate_trading_instances(self):
        """Generate trading instance objects from classes."""
        print("Creating DataHandler, Strategy, Portfolio and ExecutionHandler")
        
        self.data_handler = self.data_handler_cls(
            self.events, self.csv_dir, self.symbol_list
        )
        
        self.strategy = self.strategy_cls(
            self.data_handler, self.events
        )
        
        self.portfolio = self.portfolio_cls(
            self.data_handler, self.events,
            self.start_date, self.initial_capital
        )
        
        self.execution_handler = self.execution_handler_cls(
            self.events
        )
    
    def _run_backtest(self):
        """Execute the backtest."""
        i = 0
        while True:
            i += 1
            if i % 1000 == 0:
                print("Processing bar %d" % i)
            
            # Update the market bars
            if self.data_handler.continue_backtest:
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
        """Output the strategy performance."""
        self.portfolio.create_equity_curve_dataframe()
        
        print("Creating summary stats...")
        stats = self.portfolio.output_summary_stats()
        
        print("\n=== BACKTEST RESULTS ===")
        print("Signals: %s" % self.signals)
        print("Orders: %s" % self.orders)
        print("Fills: %s" % self.fills)
        print("\n=== PERFORMANCE STATS ===")
        for stat in stats:
            print("%s: %s" % (stat[0], stat[1]))
        
        print("\n=== EQUITY CURVE (last 100 bars) ===")
        print(self.portfolio.equity_curve[['total', 'returns', 'equity_curve']].tail(100))
    
    def simulate_trading(self):
        """Run the backtest and output performance."""
        print("\n" + "="*50)
        print("STARTING BACKTEST")
        print("="*50)
        self._run_backtest()
        self._output_performance()
        print("="*50)
        print("BACKTEST COMPLETE")
        print("="*50 + "\n")
        print("Backtest created successfully :",backtest.strategy)
        print("commission:",backtest.portfolio.current_holdings['commission'])
# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║        EVENT-DRIVEN BACKTESTING SYSTEM                       ║
    ║                                                              ║
    ║  This is a complete backtesting framework that uses:        ║
    ║  • SimulatedExecutionHandler (for backtesting)              ║
    ║  • NOT IBExecutionHandler (that's for live trading)         ║
    ║                                                              ║
    ║  To run this example:                                       ║
    ║  1. Create a 'data' folder in this directory                ║
    ║  2. Add CSV files with OHLCV data (e.g., AAPL.csv)          ║
    ║  3. Update the csv_dir and symbol_list below                ║
    ║  4. Run this script                                         ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Configuration
    csv_dir = '/Users/shreyanshsingh/mp_env/data'  # UPDATE THIS PATH
    symbol_list = ['RELIANCE.NS']  # UPDATE THIS LIST
    initial_capital = 50000.0
    heartbeat = 0.0  # 0 for max speed
    start_date = datetime.datetime(2020,1,1 , 0, 0, 0)
    end_date = datetime.datetime(2023,12,29, 0, 0, 0)
    
    # Create backtest with SIMULATED execution (not IB!)
    backtest = Backtest(
        csv_dir=csv_dir,
        symbol_list=symbol_list,
        initial_capital=initial_capital,
        heartbeat=heartbeat,
        start_date=start_date,
        data_handler=HistoricCSVDataHandler,
        execution_handler=SimulatedExecutionHandler,  # ← SIMULATED for backtest
        portfolio=Portfolio,
        strategy=MomentumStrategy
    )
    
    from riskstats import PerformanceStats
    from riskstats import PerformanceVisuals

    
    # Run the backtest
    backtest.simulate_trading()
    
    from riskstats import PerformanceStats

    # Access the portfolio from the backtest instance
    portfolio = backtest.portfolio
    
    equity_df = portfolio.equity_curve
    
    # Check if we have data
    if equity_df is not None and not equity_df.empty:
        stats = PerformanceStats(
            equity_df=equity_df,
            cash_flows=portfolio.cash_flows
        )
        results = stats.summary()
        print("\n=== PERFORMANCE STATS ===")
        for k, v in results.items():
            print(f"{k}: {v}")
        print("\n=== PERFORMANCE CURVE ===")
        visuals = PerformanceVisuals(equity_df)
        visuals.plot_all()
    else:
        print("No trades generated or backtest failed.")

    
