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
import json
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
    def __init__(self, symbol, timeindex, exchange, quantity, direction, fill_cost, commission=0.0):
        self.type = 'FILL'
        self.timeindex = timeindex
        self.symbol = symbol
        self.exchange = exchange
        self.quantity = quantity
        self.direction = direction
        self.fill_cost = fill_cost
        self.commission = commission

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
    
    def __init__(self, events, csv_dir, symbol_list, **kwargs):
        self.events = events
        self.csv_dir = csv_dir
        self.symbol_list = symbol_list
        self.symbol_data = {}
        self.latest_symbol_data = {}
        self.continue_backtest = True
        self.benchmark_symbol = kwargs.get('benchmark_symbol', None)
        self._open_convert_csv_files()
    
    def _open_convert_csv_files(self):
        """Open CSV files and create generators."""
        comb_index = None
        
        # Merge symbol_list and benchmark_symbol for data loading
        load_list = list(self.symbol_list)
        if self.benchmark_symbol and self.benchmark_symbol not in load_list:
            load_list.append(self.benchmark_symbol)

        for s in load_list:
            file_path = os.path.join(self.csv_dir, '%s.csv' % s)
            self.symbol_data[s] = pd.read_csv(
                file_path, header=0, index_col=0, parse_dates=True,
                names=["datetime", "open", "high", "low", "close", "volume"]
            ).sort_index()
            
            if comb_index is None:
                comb_index = self.symbol_data[s].index
            else:
                comb_index = comb_index.union(self.symbol_data[s].index)
            
            self.latest_symbol_data[s] = []
        
        # Synchronize all dataframes to the same date index
        for s in load_list:
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
        # Update all symbols including benchmark
        for s in self.symbol_data.keys():
            try:
                bar = next(self.symbol_data[s])
            except StopIteration:
                self.continue_backtest = False
            else:
                if bar is not None:
                    self.latest_symbol_data[s].append(bar)
        
        self.events.put(MarketEvent())


# ============================================================================
# YFINANCE DATA HANDLER (API-based, no CSV files needed)
# ============================================================================

class YFinanceDataHandler(DataHandler):
    """
    Fetches historical OHLCV data from Yahoo Finance at startup (in-memory).
    This is a drop-in replacement for HistoricCSVDataHandler — no CSV files needed.

    Usage:
        backtest = Backtest(
            ...
            data_handler=YFinanceDataHandler,   # <-- Only change needed
            execution_kwargs={
                'start_date': datetime.datetime(2022, 1, 1),
                'end_date':   datetime.datetime(2024, 1, 1),
            }
        )
    """

    def __init__(self, events, csv_dir, symbol_list, **kwargs):
        try:
            import yfinance as yf
        except ImportError:
            raise ImportError(
                "yfinance is required for YFinanceDataHandler. "
                "Install it with: pip install yfinance"
            )
        
        self.events = events
        self.symbol_list = symbol_list
        self.symbol_data = {}
        self.latest_symbol_data = {}
        self.continue_backtest = True
        self.benchmark_symbol = kwargs.get('benchmark_symbol', None)
        
        # Date range for the API download
        start_date = kwargs.get('start_date', None)
        end_date = kwargs.get('end_date', None)
        
        if start_date is None:
            raise ValueError("YFinanceDataHandler requires 'start_date' in execution_kwargs.")
        
        # Build the full list of symbols to fetch (strategy + benchmark)
        load_list = list(self.symbol_list)
        if self.benchmark_symbol and self.benchmark_symbol not in load_list:
            load_list.append(self.benchmark_symbol)
        
        print(f"[YFinanceDataHandler] Fetching {load_list} from Yahoo Finance...")
        
        # Download all symbols in one bulk call (much faster)
        raw = yf.download(
            tickers=load_list,
            start=start_date,
            end=end_date,
            auto_adjust=True,
            progress=False,
            group_by='ticker'
        )
        
        comb_index = None
        
        for s in load_list:
            # Handle both single and multi-ticker download formats
            if len(load_list) == 1:
                df = raw[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
            else:
                df = raw[s][['Open', 'High', 'Low', 'Close', 'Volume']].copy()
            
            df.columns = ['open', 'high', 'low', 'close', 'volume']
            df.dropna(subset=['close'], inplace=True)
            df.index = pd.to_datetime(df.index)
            df.sort_index(inplace=True)
            
            if df.empty:
                print(f"[YFinanceDataHandler] WARNING: No data for {s}. Skipping.")
                continue
            
            self.symbol_data[s] = df
            self.latest_symbol_data[s] = []
            
            if comb_index is None:
                comb_index = df.index
            else:
                comb_index = comb_index.union(df.index)
        
        # Synchronize all dataframes to the unified date index (forward-fill gaps)
        for s in list(self.symbol_data.keys()):
            self.symbol_data[s] = self.symbol_data[s].reindex(
                index=comb_index, method='pad'
            ).iterrows()
        
        print(f"[YFinanceDataHandler] Loaded {len(self.symbol_data)} symbols "
              f"({comb_index[0].date()} to {comb_index[-1].date()}).")

    # ---- Shared interface methods (identical to HistoricCSVDataHandler) ----

    def get_latest_bar(self, symbol):
        try:
            return self.latest_symbol_data[symbol][-1]
        except (KeyError, IndexError):
            raise IndexError(f"No data yet for {symbol}.")

    def get_latest_bars(self, symbol, N=1):
        try:
            return self.latest_symbol_data[symbol][-N:]
        except KeyError:
            raise KeyError(f"Symbol {symbol} not found in data handler.")

    def get_latest_bar_datetime(self, symbol):
        return self.latest_symbol_data[symbol][-1][0]

    def get_latest_bar_value(self, symbol, val_type):
        return getattr(self.latest_symbol_data[symbol][-1][1], val_type)

    def get_latest_bar_values(self, symbol, val_type, N=1):
        bars = self.get_latest_bars(symbol, N)
        return np.array([getattr(b[1], val_type) for b in bars])

    def update_bars(self):
        for s in self.symbol_data.keys():
            try:
                bar = next(self.symbol_data[s])
            except StopIteration:
                self.continue_backtest = False
            else:
                if bar is not None:
                    self.latest_symbol_data[s].append(bar)
        
        self.events.put(MarketEvent())



# ============================================================================
# REGIME DETECTOR
# ============================================================================

class RegimeDetector:
    """
    Detects the current market regime using ADX and ATR.
    
    Regime Labels:
    - 'TRENDING'  : ADX > adx_trend_threshold (strong directional move)
    - 'HIGH_VOL'  : ADX < threshold AND ATR/Price > vol_threshold (choppy + volatile)
    - 'RANGING'   : ADX < threshold AND ATR/Price <= vol_threshold (quiet, mean-reverting)
    
    Usage:
        detector = RegimeDetector(data_handler, adx_period=14)
        regime = detector.detect('RELIANCE.NS')  # -> 'TRENDING', 'RANGING', 'HIGH_VOL'
    """

    def __init__(self, bars, adx_period=14, adx_trend_threshold=25, vol_threshold=0.02):
        self.bars = bars
        self.adx_period = adx_period
        self.adx_trend_threshold = adx_trend_threshold
        self.vol_threshold = vol_threshold  # ATR/Price ratio

    def _atr(self, bars_list):
        """Average True Range over the bar list."""
        trs = []
        for i in range(1, len(bars_list)):
            high  = bars_list[i][1].high
            low   = bars_list[i][1].low
            close_prev = bars_list[i-1][1].close
            tr = max(high - low, abs(high - close_prev), abs(low - close_prev))
            trs.append(tr)
        return np.mean(trs) if trs else 0.0

    def _adx(self, bars_list):
        """
        Wilder's ADX approximation.
        Returns ADX value (0-100). Higher = stronger trend.
        """
        period = self.adx_period
        if len(bars_list) < period * 2 + 1:
            return 0.0

        plus_dm_list, minus_dm_list, tr_list = [], [], []

        for i in range(1, len(bars_list)):
            h  = bars_list[i][1].high
            l  = bars_list[i][1].low
            ph = bars_list[i-1][1].high
            pl = bars_list[i-1][1].low
            pc = bars_list[i-1][1].close

            up_move   = h - ph
            down_move = pl - l

            plus_dm  = up_move   if (up_move > down_move and up_move > 0)   else 0.0
            minus_dm = down_move if (down_move > up_move and down_move > 0) else 0.0
            tr = max(h - l, abs(h - pc), abs(l - pc))

            plus_dm_list.append(plus_dm)
            minus_dm_list.append(minus_dm)
            tr_list.append(tr)

        def wilder_smooth(data, n):
            result = [sum(data[:n])]
            for v in data[n:]:
                result.append(result[-1] - result[-1] / n + v)
            return result

        smooth_tr   = wilder_smooth(tr_list,   period)
        smooth_pdm  = wilder_smooth(plus_dm_list,  period)
        smooth_ndm  = wilder_smooth(minus_dm_list, period)

        dx_list = []
        for i in range(len(smooth_tr)):
            if smooth_tr[i] == 0:
                dx_list.append(0.0)
                continue
            pdi = 100 * smooth_pdm[i] / smooth_tr[i]
            ndi = 100 * smooth_ndm[i] / smooth_tr[i]
            denom = pdi + ndi
            dx_list.append(100 * abs(pdi - ndi) / denom if denom != 0 else 0.0)

        # ADX = smoothed DX
        if len(dx_list) < period:
            return 0.0
        adx = np.mean(dx_list[-period:])
        return adx

    def detect(self, symbol):
        """
        Returns the current market regime for the given symbol.
        Call this once per bar — it reads from the DataHandler's latest bars.
        """
        needed = self.adx_period * 2 + 2
        bars_list = self.bars.get_latest_bars(symbol, N=needed)

        if bars_list is None or len(bars_list) < needed:
            return 'RANGING'  # Default until we have enough data

        adx = self._adx(bars_list)
        atr = self._atr(bars_list[-self.adx_period:])
        current_price = bars_list[-1][1].close

        # High volatility override (regardless of trend strength)
        vol_ratio = atr / current_price if current_price > 0 else 0
        if vol_ratio > self.vol_threshold:
            return 'HIGH_VOL'

        if adx > self.adx_trend_threshold:
            return 'TRENDING'

        return 'RANGING'

        if adx > self.adx_trend_threshold:
            return 'TRENDING'
        return 'RANGING'


# ============================================================================
# ALPHA MODELS
# ============================================================================

class AlphaModel(object):
    """
    AlphaModel base class for generating raw signals/insights.
    Separates the 'signal' from the 'trading logic' (Strategy).
    """
    __metaclass__ = ABCMeta

    def __init__(self, bars):
        self.bars = bars

    @abstractmethod
    def generate_alpha(self, symbol):
        """Produce an alpha value (e.g. 1.0 for bullish, -1.0 for bearish)."""
        raise NotImplementedError("Should implement generate_alpha()")



# ============================================================================
# STRATEGY
# ============================================================================

class Strategy(object):
    """
    Strategy base class. Reacts to MARKET events and generates SignalEvents.
    Can optionally use an AlphaModel.
    """
    __metaclass__ = ABCMeta

    def __init__(self, bars, events, alpha_model=None, **kwargs):
        self.bars = bars
        self.symbol_list = self.bars.symbol_list
        self.events = events
        self.alpha_model = alpha_model
        # Store extra kwargs (like regime_detector) if provided
        for key, value in kwargs.items():
            setattr(self, key, value)

    @abstractmethod
    def calculate_signals(self, event):
        """Calculates the signals of a strategy."""
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
# LOGGING
# ============================================================================

class TradeLogger(object):
    """
    Handles logging of closed trades to CSV/JSON files.
    """
    def __init__(self, output_path="trades_log.csv"):
        self.output_path = output_path
    
    def log_trades(self, trades):
        """Exports the list of trade dicts to a CSV file."""
        if not trades:
            print("TradeLogger: No trades to log.")
            return
        
        df = pd.DataFrame(trades)
        # Ensure times are nicely formatted
        df['entry_time'] = df['entry_time'].dt.strftime('%Y-%m-%d %H:%M:%S')
        df['exit_time'] = df['exit_time'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        df.to_csv(self.output_path, index=False)
        print("TradeLogger: Logged %d trades to %s" % (len(trades), self.output_path))


# ============================================================================
# PORTFOLIO
# ============================================================================

class Portfolio(object):
    """Handles positions and market value of all instruments."""
    
    def __init__(self, bars, events, start_date, initial_capital=100000.0, **kwargs):
        self.bars = bars
        self.events = events
        self.symbol_list = self.bars.symbol_list
        self.start_date = start_date
        self.initial_capital = initial_capital
        
        # Risk Management
        self.risk_manager = RiskManager(**(kwargs.get('risk_kwargs', {})))
        self.running_max_equity = initial_capital

        # Benchmark Tracking
        self.benchmark_symbol = kwargs.get('benchmark_symbol', None)
        self.initial_benchmark_val = None

        # Trade Tracking
        self.open_trades = dict((k, []) for k in self.symbol_list)
        self.closed_trades = []
        
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
        d['realized_pnl'] = 0.0
        d['unrealized_pnl'] = 0.0
        d['total'] = self.initial_capital
        
        if self.benchmark_symbol:
            d['benchmark'] = self.initial_capital
            
        return [d]
    
    def construct_current_holdings(self):
        """Constructs the current holdings."""
        d = dict((k, v) for k, v in [(s, 0.0) for s in self.symbol_list])
        d['cash'] = self.initial_capital
        d['commission'] = 0.0
        d['realized_pnl'] = 0.0
        d['unrealized_pnl'] = 0.0
        d['total'] = self.initial_capital
        
        if self.benchmark_symbol:
            d['benchmark'] = self.initial_capital
        
        # Track cost basis (Average Cost)
        self.avg_cost = dict((k, v) for k, v in [(s, 0.0) for s in self.symbol_list])
        return d
    
    def update_timeindex(self, event):
        """Updates positions and holdings at each bar."""
        latest_datetime = self.bars.get_latest_bar_datetime(self.symbol_list[0])
        
        # Update positions
        dp = dict((k, v) for k, v in [(s, 0) for s in self.symbol_list])
        dp['datetime'] = latest_datetime
        
        for s in self.symbol_list:
            dp[s] = self.current_positions[s]
        
        # Update running max for drawdown calculation
        if self.current_holdings['total'] > self.running_max_equity:
            self.running_max_equity = self.current_holdings['total']
        self.current_holdings['running_max'] = self.running_max_equity

        self.all_positions.append(dp)
        
        # Update holdings
        dh = dict((k, v) for k, v in [(s, 0) for s in self.symbol_list])
        dh['datetime'] = latest_datetime
        dh['cash'] = self.current_holdings['cash']
        dh['commission'] = self.current_holdings['commission']
        dh['realized_pnl'] = self.current_holdings['realized_pnl']
        
        total_market_value = 0.0
        total_unrealized_pnl = 0.0
        
        for s in self.symbol_list:
            # Mark-to-Market (MTM)
            qty = self.current_positions[s]
            close_price = self.bars.get_latest_bar_value(s, 'close')
            market_value = qty * close_price
            
            # Unrealized PnL = (Current Price - Avg Cost) * Quantity
            unrealized = 0.0
            if qty != 0:
                unrealized = (close_price - self.avg_cost[s]) * qty
                
            dh[s] = market_value
            total_market_value += market_value
            total_unrealized_pnl += unrealized
        
        dh['unrealized_pnl'] = total_unrealized_pnl
        dh['total'] = dh['cash'] + total_market_value
        
        # Update Benchmark
        if self.benchmark_symbol:
            try:
                bench_bar = self.bars.get_latest_bar(self.benchmark_symbol)
            except (IndexError, KeyError):
                bench_bar = None

            if bench_bar is not None:
                bench_price = bench_bar[1].close
                if self.initial_benchmark_val is None:
                    self.initial_benchmark_val = bench_price
                
                # Normalize benchmark to initial capital
                bench_equity = (bench_price / self.initial_benchmark_val) * self.initial_capital
                dh['benchmark'] = bench_equity
            else:
                dh['benchmark'] = self.initial_capital # Fallback if no data yet

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
        
        # Current status before this fill
        old_qty = self.current_positions[fill.symbol] - (fill_dir * fill.quantity)
        fill_cost = fill.fill_cost
        trade_value = fill_dir * fill_cost * fill.quantity
        
        # Calculate Realized PnL and Update Average Cost
        if fill.direction == 'BUY':
            if old_qty >= 0: # Adding to long or opening long
                new_qty = old_qty + fill.quantity
                self.avg_cost[fill.symbol] = ((old_qty * self.avg_cost[fill.symbol]) + (fill.quantity * fill_cost)) / new_qty
                
                # Track entry for new long
                self.open_trades[fill.symbol].append({
                    'entry_time': fill.timeindex,
                    'entry_price': fill_cost,
                    'quantity': fill.quantity
                })
            else: # Covering short
                # Realized PnL on short cover = (Entry Price - Exit Price) * Quantity
                realized = (self.avg_cost[fill.symbol] - fill_cost) * min(fill.quantity, abs(old_qty))
                self.current_holdings['realized_pnl'] += realized
                
                # Close out tracked short trades
                self._record_closed_trade(fill.symbol, fill.timeindex, fill_cost, fill.quantity, 'SHORT')
                
                if fill.quantity > abs(old_qty): # Short covered and went long
                    self.avg_cost[fill.symbol] = fill_cost
                    self.open_trades[fill.symbol].append({
                        'entry_time': fill.timeindex,
                        'entry_price': fill_cost,
                        'quantity': fill.quantity - abs(old_qty)
                    })
        
        elif fill.direction == 'SELL':
            if old_qty <= 0: # Adding to short or opening short
                new_qty = abs(old_qty) + fill.quantity
                self.avg_cost[fill.symbol] = ((abs(old_qty) * self.avg_cost[fill.symbol]) + (fill.quantity * fill_cost)) / new_qty
                
                # Track entry for new short
                self.open_trades[fill.symbol].append({
                    'entry_time': fill.timeindex,
                    'entry_price': fill_cost,
                    'quantity': fill.quantity
                })
            else: # Reducing long
                realized = (fill_cost - self.avg_cost[fill.symbol]) * min(fill.quantity, old_qty)
                self.current_holdings['realized_pnl'] += realized
                
                # Close out tracked long trades
                self._record_closed_trade(fill.symbol, fill.timeindex, fill_cost, fill.quantity, 'LONG')
                
                if fill.quantity > old_qty: # Long closed and went short
                    self.avg_cost[fill.symbol] = fill_cost
                    self.open_trades[fill.symbol].append({
                        'entry_time': fill.timeindex,
                        'entry_price': fill_cost,
                        'quantity': fill.quantity - old_qty
                    })

        # Update Cash and Commission
        self.current_holdings['commission'] += fill.commission
        self.current_holdings['cash'] -= (trade_value + fill.commission)
    
    def _record_closed_trade(self, symbol, exit_time, exit_price, quantity, side):
        """Helper to record a closed trade for metrics."""
        remaining_qty_to_close = quantity
        
        while remaining_qty_to_close > 0 and self.open_trades[symbol]:
            trade = self.open_trades[symbol][0] # FIFO
            closed_qty = min(remaining_qty_to_close, trade['quantity'])
            
            pnl = 0
            if side == 'LONG':
                pnl = (exit_price - trade['entry_price']) * closed_qty
            else: # SHORT
                pnl = (trade['entry_price'] - exit_price) * closed_qty
            
            # Calculate PnL percentage
            pnl_pct = 0.0
            if trade['entry_price'] != 0:
                pnl_pct = (pnl / (trade['entry_price'] * closed_qty)) * 100
            
            self.closed_trades.append({
                'symbol': symbol,
                'entry_time': trade['entry_time'],
                'exit_time': exit_time,
                'entry_price': trade['entry_price'],
                'exit_price': exit_price,
                'quantity': closed_qty,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'side': side,
                'duration': (exit_time - trade['entry_time']).total_seconds() / 3600.0 # hours
            })
            
            trade['quantity'] -= closed_qty
            remaining_qty_to_close -= closed_qty
            
            if trade['quantity'] <= 0:
                self.open_trades[symbol].pop(0)

    def update_fill(self, event):
        """Updates the portfolio based on a fill."""
        if event.type == 'FILL':
            self.update_positions_from_fill(event)
            self.update_holdings_from_fill(event)
    
    def generate_naive_order(self, signal):
        """Generates a risk-adjusted order."""
        order = None
        
        symbol = signal.symbol
        direction = signal.signal_type
        order_type = 'MKT'
        
        # Get current metrics for risk calculation
        close_price = self.bars.get_latest_bar_value(symbol, 'close')
        cur_quantity = self.current_positions[symbol]
        equity = self.current_holdings['total']
        
        # 1. RISK-BASED POSITION SIZING
        # Calculate quantity based on % of equity
        mkt_quantity = self.risk_manager.calculate_quantity(symbol, close_price, equity)
        
        if mkt_quantity == 0 and direction != 'EXIT':
            print("RiskManager: Calculated quantity is 0 for %s. Skipping signal." % symbol)
            return None

        if direction == 'LONG' and cur_quantity == 0:
            order = OrderEvent(symbol, order_type, mkt_quantity, 'BUY')
        elif direction == 'SHORT' and cur_quantity == 0:
            order = OrderEvent(symbol, order_type, mkt_quantity, 'SELL')
        elif direction == 'EXIT' and cur_quantity > 0:
            order = OrderEvent(symbol, order_type, abs(cur_quantity), 'SELL')
        elif direction == 'EXIT' and cur_quantity < 0:
            order = OrderEvent(symbol, order_type, abs(cur_quantity), 'BUY')
        
        if order:
            # 2. RISK VALIDATION (Drawdown, Exposure, etc.)
            latest_prices = {s: self.bars.get_latest_bar_value(s, 'close') for s in self.symbol_list}
            valid, reason = self.risk_manager.validate_order(order, self.current_holdings, self.current_positions, latest_prices)
            
            if not valid:
                print("RiskManager: Order REJECTED for %s. Reason: %s" % (symbol, reason))
                return None
            else:
                return order
        
        return None
    
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
# RISK MANAGEMENT
# ============================================================================

class RiskManager(object):
    """
    Handles risk management rules for order generation.
    - Max Drawdown: Reject new orders if portfolio is in a deep drawdown.
    - Position Sizing: Calculate quantity based on % of equity.
    - Exposure Limit: Ensure total portfolio exposure stays below a cap.
    """
    def __init__(self, **kwargs):
        self.max_drawdown = kwargs.get('max_drawdown', 0.20)      # Default 20%
        self.pos_size_pct = kwargs.get('pos_size_pct', 0.10)      # Default 10% per trade
        self.max_exposure_pct = kwargs.get('max_exposure_pct', 1.0) # Default 100%
    
    def calculate_quantity(self, symbol, current_price, equity):
        """Calculates quantity based on current equity and pos_size_pct."""
        import math
        if current_price == 0 or current_price is None or math.isnan(current_price):
            return 0
        target_value = equity * self.pos_size_pct
        return int(target_value / current_price)

    def validate_order(self, order_event, current_holdings, current_positions, latest_prices):
        """
        Validates an order against risk rules.
        Returns (valid: bool, reason: str)
        """
        # 1. ALLOW ALL EXITS (Always allow closing positions to reduce risk)
        if order_event.direction == 'SELL' and current_positions[order_event.symbol] > 0:
            return True, "Exit Allowed"
        if order_event.direction == 'BUY' and current_positions[order_event.symbol] < 0:
            return True, "Exit Allowed"

        # 2. CHECK DRAWDOWN
        current_total = current_holdings['total']
        running_max = current_holdings.get('running_max', current_total)
        drawdown = (running_max - current_total) / running_max if running_max > 0 else 0
        
        if drawdown > self.max_drawdown:
            return False, "Order rejected: Max Drawdown Exceeded (%0.2f%%)" % (drawdown * 100)

        # 3. CHECK EXPOSURE LIMIT
        total_exposure = 0.0
        for s, qty in current_positions.items():
            total_exposure += abs(qty * latest_prices[s])
        
        # Add potential new order exposure
        new_order_value = order_event.quantity * latest_prices[order_event.symbol]
        if (total_exposure + new_order_value) > (current_total * self.max_exposure_pct):
            return False, "Order rejected: Max Exposure Limit Exceeded"

        return True, "Valid"


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
    Simulates order execution with Spread, Slippage, and Transaction Costs.
    Includes support for Indian Equity Delivery transaction models.
    """
    def __init__(self, events, bars, **kwargs):
        self.events = events
        self.bars = bars
        
        # Execution Models Parameters
        self.commission_pct = kwargs.get('commission_pct', 0.0) # Base brokerage
        self.slippage_pct = kwargs.get('slippage_pct', 0.0005) # 0.05% default
        self.spread_pct = kwargs.get('spread_pct', 0.001)      # 0.1% default
        
        # Indian Transaction Cost specific params
        self.stt_pct = kwargs.get('stt_pct', 0.001)            # 0.1% for Delivery
        self.gst_pct = kwargs.get('gst_pct', 0.18)             # 18% on (Brokerage + Transaction Charge)
        self.txn_charge_pct = kwargs.get('txn_charge_pct', 0.0000345) # NSE Transaction charge
        self.stamp_duty_pct = kwargs.get('stamp_duty_pct', 0.00015)   # 0.015% for Delivery Buy
    
    def calculate_execution_price(self, symbol, direction):
        """
        Calculates execution price factoring in simulated spread and slippage.
        """
        mid_price = self.bars.get_latest_bar_value(symbol, 'close')
        
        # Half spread logic: Buy at Ask (higher), Sell at Bid (lower)
        half_spread = self.spread_pct / 2.0
        
        if direction == 'BUY':
            # Ask Price
            price = mid_price * (1 + half_spread)
            # Add slippage (buy at an even higher price)
            execution_price = price * (1 + self.slippage_pct)
        elif direction == 'SELL':
            # Bid Price
            price = mid_price * (1 - half_spread)
            # Add slippage (sell at an even lower price)
            execution_price = price * (1 - self.slippage_pct)
        else:
            execution_price = mid_price
            
        return execution_price

    def calculate_commission(self, execution_price, quantity, direction):
        """
        Calculates granular transaction costs for Indian Markets.
        Includes: Brokerage, STT, Transaction Charges, GST, Stamp Duty.
        """
        trade_value = execution_price * quantity
        
        # 1. Base Brokerage
        brokerage = trade_value * self.commission_pct
        
        # 2. STT (Securities Transaction Tax) - 0.1% on Buy and Sell for Delivery
        stt = trade_value * self.stt_pct
        
        # 3. Transaction Charges (NSE/BSE)
        txn_charges = trade_value * self.txn_charge_pct
        
        # 4. GST (18% on Brokerage + Transaction Charges)
        gst = (brokerage + txn_charges) * self.gst_pct
        
        # 5. Stamp Duty (0.015% on Buy Side only for Delivery)
        stamp_duty = 0
        if direction == 'BUY':
            stamp_duty = trade_value * self.stamp_duty_pct
            
        total_costs = brokerage + stt + txn_charges + gst + stamp_duty
        return total_costs

    def execute_order(self, event):
        """Simulates executing an order."""
        if event.type == 'ORDER':
            execution_price = self.calculate_execution_price(event.symbol, event.direction)
            commission = self.calculate_commission(execution_price, event.quantity, event.direction)
            
            fill_event = FillEvent(
                symbol=event.symbol,
                timeindex=self.bars.get_latest_bar_datetime(event.symbol),
                exchange='SIMULATED',
                quantity=event.quantity,
                direction=event.direction,
                fill_cost=execution_price,
                commission=commission
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
        strategy,
        execution_kwargs=None,
        **kwargs
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
        execution_kwargs : dict
            Keyword arguments for the execution handler (slippage, spread, etc.)
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
        self.execution_kwargs = execution_kwargs if execution_kwargs else {}
        self.end_date = kwargs.get('end_date', None)
        
        self.events = queue.Queue()
        
        self.signals = 0
        self.orders = 0
        self.fills = 0
        
        self._generate_trading_instances()
    
    def _generate_trading_instances(self):
        """Generate trading instance objects from classes."""
        print("Creating DataHandler, Strategy, Portfolio and ExecutionHandler")
        
        # Pass all execution_kwargs to DataHandler for benchmark loading
        self.data_handler = self.data_handler_cls(
            self.events, self.csv_dir, self.symbol_list, **(self.execution_kwargs)
        )
        
        # -------------------------------------------------------------------
        # ADVANCED: REGIME DETECTION
        # -------------------------------------------------------------------
        regime_detector = None
        if self.execution_kwargs.get('use_regime_detection', False):
            print("Initializing RegimeDetector...")
            regime_detector = RegimeDetector(self.data_handler)

        # Strategy can take an alpha_model or a regime_detector
        self.strategy = self.strategy_cls(
            self.data_handler, self.events, 
            regime_detector=regime_detector
        )
        
        # Portfolio needs execution_kwargs for benchmark_symbol and risk_kwargs
        self.portfolio = self.portfolio_cls(
            self.data_handler, self.events,
            self.start_date, self.initial_capital,
            **(self.execution_kwargs)
        )
        
        self.execution_handler = self.execution_handler_cls(
            self.events, self.data_handler, **self.execution_kwargs
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
                
                # Check for end_date to support Walk-Forward/Windowing
                if self.end_date:
                    latest_dt = self.data_handler.get_latest_bar_datetime(self.symbol_list[0])
                    if latest_dt > self.end_date:
                        self.data_handler.continue_backtest = False
                        break
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
        print(self.symbol_list)
        print("Signals: %s" % self.signals)
        print("Orders: %s" % self.orders)
        print("Fills: %s" % self.fills)
        print("\n=== PERFORMANCE STATS ===")
        for stat in stats:
            print("%s: %s" % (stat[0], stat[1]))
        
        print("\n=== EQUITY CURVE (last 100 bars) ===")
        print(self.portfolio.equity_curve[['total', 'cash', 'realized_pnl', 'unrealized_pnl']].tail(100))
    
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
        print("Backtest created successfully :", self.strategy)
        print("commission:", self.portfolio.current_holdings['commission'])

    def get_summary_json(self):
        """
        Returns a JSON-serializable dictionary of backtest results.
        Suitable for web API responses.
        """
        from riskstats import PerformanceStats
        
        # Use full advanced stats if available
        if hasattr(self.portfolio, 'equity_curve') and self.portfolio.equity_curve is not None and not self.portfolio.equity_curve.empty:
            adv_stats = PerformanceStats(
                equity_df=self.portfolio.equity_curve,
                cash_flows=self.portfolio.cash_flows,
                closed_trades=self.portfolio.closed_trades
            )
            stats_dict = adv_stats.summary()
        else:
            stats_list = self.portfolio.output_summary_stats()
            stats_dict = {k: v for k, v in stats_list}
            
        # Dynamically inject Final Technical Indicators (RSI, MACD)
        try:
            symbol = self.symbol_list[0]
            bars_list = self.data_handler.latest_symbol_data.get(symbol, [])
            if len(bars_list) > 30:
                closes = pd.Series([getattr(b[1], 'close') for b in bars_list])
                
                # RSI 14
                delta = closes.diff()
                up = delta.clip(lower=0)
                down = -1 * delta.clip(upper=0)
                ema_up = up.ewm(com=13, adjust=False).mean()
                ema_down = down.ewm(com=13, adjust=False).mean()
                rs = ema_up / ema_down
                rsi = 100 - (100 / (1 + rs))
                
                # MACD
                exp1 = closes.ewm(span=12, adjust=False).mean()
                exp2 = closes.ewm(span=26, adjust=False).mean()
                macd = exp1 - exp2
                
                stats_dict['Final RSI (14)'] = round(float(rsi.iloc[-1]), 2)
                stats_dict['Final MACD'] = round(float(macd.iloc[-1]), 2)
        except Exception as e:
            pass # Keep it robust if dataframe sizes are too small

        
        # Prepare equity curve for JSON (limit to last 500 points for performance)
        equity_curve = self.portfolio.equity_curve.tail(500)
        
        chart_data = []
        for index, row in equity_curve.iterrows():
            chart_data.append({
                "date": index.strftime('%Y-%m-%d'),
                "equity": float(row['equity_curve']),
                "benchmark": float(row['benchmark']) if 'benchmark' in row else None,
                "drawdown": float(row['drawdown']) if 'drawdown' in row else 0.0
            })
            
        trade_data = []
        for t in self.portfolio.closed_trades[-50:]:  # Last 50 trades
            trade_data.append({
                "symbol": t['symbol'],
                "entry_time": t['entry_time'].strftime('%Y-%m-%d'),
                "exit_time": t['exit_time'].strftime('%Y-%m-%d'),
                "pnl": float(t['pnl']),
                "pnl_pct": float(t.get('pnl_pct', 0.0)),
                "side": t['side']
            })

        return {
            "metadata": {
                "symbols": self.symbol_list,
                "initial_capital": self.initial_capital,
                "signals": self.signals,
                "orders": self.orders,
                "fills": self.fills
            },
            "stats": stats_dict,
            "charts": chart_data,
            "recent_trades": trade_data
        }
# ============================================================================
# WALK-FORWARD TESTING
# ============================================================================

class WalkForwardBacktest(object):
    """
    Orchestrates multiple backtest runs to perform Walk-Forward Analysis.
    """
    def __init__(
        self, csv_dir, symbol_list, initial_capital, start_date, 
        data_handler_cls, execution_handler_cls, portfolio_cls, strategy_cls,
        windows, execution_kwargs=None
    ):
        self.csv_dir = csv_dir
        self.symbol_list = symbol_list
        self.initial_capital = initial_capital
        self.start_date = start_date
        self.data_handler_cls = data_handler_cls
        self.execution_handler_cls = execution_handler_cls
        self.portfolio_cls = portfolio_cls
        self.strategy_cls = strategy_cls
        self.windows = windows # List of (train_start, train_end, test_start, test_end)
        self.execution_kwargs = execution_kwargs if execution_kwargs else {}
        
        self.results = []
        self.combined_equity = []

    def run(self):
        """Runs the backtest for each window."""
        current_capital = self.initial_capital
        
        for i, (train_s, train_e, test_s, test_e) in enumerate(self.windows):
            print("\n" + "-"*30)
            print("RUNNING WALK-FORWARD WINDOW %d" % (i+1))
            print("Test Period: %s to %s" % (test_s, test_e))
            print("-"*30)

            # In a real WFO, we would 'optimize' on train period here.
            # For this simplified version, we just run on the test period to showcase stitching.
            
            backtest = Backtest(
                self.csv_dir, self.symbol_list, current_capital, 0.0,
                test_s, self.data_handler_cls, self.execution_handler_cls,
                self.portfolio_cls, self.strategy_cls, self.execution_kwargs
            )
            
            # Hook into the DataHandler to stop at test_e
            # (Note: Requires modification to loop or data filter)
            
            backtest.simulate_trading()
            
            # Record results
            res = backtest.portfolio.equity_curve
            self.results.append(res)
            
            # Update capital for next window (compounding)
            current_capital = res['total'].iloc[-1]


class CostSensitivityAnalyzer(object):
    """ Runs backtests across varying cost parameters. """
    def __init__(self, backtest_config, commission_range, slippage_range):
        self.config = backtest_config
        self.commission_range = commission_range
        self.slippage_range = slippage_range
        self.results = []

    def run_analysis(self):
        print("\n=== STARTING COST SENSITIVITY ANALYSIS ===")
        for comm in self.commission_range:
            for slip in self.slippage_range:
                print(f"Testing: Comm={comm}, Slip={slip}...")
                
                # Update config
                self.config['execution_kwargs']['commission_pct'] = comm
                self.config['execution_kwargs']['slippage_pct'] = slip
                
                # Run backtest (Simplified for analysis)
                bt = Backtest(**self.config)
                bt.simulate_trading()
                
                res = bt.portfolio.output_summary_stats()
                # Find Total Return index (it's a list of tuples)
                cagr = next((s[1] for s in res if "Total" in s[0]), "0.00%")
                
                self.results.append({
                    'commission': comm,
                    'slippage': slip,
                    'cagr': cagr,
                    'total_trades': bt.portfolio.closed_trades
                })
        print("=== ANALYSIS COMPLETE ===\n")


# Import strategies here to avoid circular imports but still be available for the __main__ block
from active_strategies import *

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
    import os
    csv_dir = os.path.join(os.getcwd(), 'data')  # Corrected path
    symbol_list = ['NVDA']  # We use NVDA because that data exists locally

    initial_capital = 50000.0
    heartbeat = 0.0  # 0 for max speed
    start_date = datetime.datetime(2020,1,1 , 0, 0, 0)
    end_date = datetime.datetime(2023,12,29, 0, 0, 0)
    
    # Execution Configuration (Indian Equity Delivery example)
    execution_kwargs = {
        'commission_pct': 0.00,        # Zero brokerage (for some brokers)
        'slippage_pct': 0.0005,      # 0.05% slippage
        'spread_pct': 0.001,         # 0.1% spread
        'stt_pct': 0.001,            # 0.1% STT for Delivery
        'gst_pct': 0.18,             # 18% GST
        'txn_charge_pct': 0.0000345, # NSE Charges
        'stamp_duty_pct': 0.00015,    # 0.015% Stamp Duty
        
        # RISK MANAGEMENT CONFIGURATION
        'risk_kwargs': {
            'max_drawdown': 0.15,      # Reject new trades if drawdown > 15%
            'pos_size_pct': 0.10,      # Each trade uses 10% of current equity
            'max_exposure_pct': 0.80   # Total portfolio exposure capped at 80%
        },
        
        # BENCHMARK CONFIGURATION
        'benchmark_symbol': 'HDFCBANK.NS'
    }

    # Create backtest with SIMULATED execution
    # -----------------------------------------------------------------------
    # DATA SOURCE: Switch between CSV files and live Yahoo Finance API
    # -----------------------------------------------------------------------
    # Option A: Read from local CSV files (reproducible, offline-safe)
    #   data_handler=HistoricCSVDataHandler,
    # Option B: Live API pull from Yahoo Finance (no CSV files needed!)
    #   data_handler=YFinanceDataHandler,
    #   (requires 'start_date' and 'end_date' in execution_kwargs)
    # -----------------------------------------------------------------------
    backtest = Backtest(
        csv_dir=csv_dir,
        symbol_list=symbol_list,
        initial_capital=initial_capital,
        heartbeat=heartbeat,
        start_date=start_date,
        data_handler=HistoricCSVDataHandler,  # Swap to YFinanceDataHandler for live API
        execution_handler=SimulatedExecutionHandler,
        portfolio=Portfolio,
        strategy=MomentumStrategy,
        execution_kwargs=execution_kwargs,
        benchmark_symbol='HDFCBANK.NS'
    )

    # ----------------------------------------------------------------------------
    # ADVANCED DEMO: ALPHAMODEL INTEGRATION
    # ----------------------------------------------------------------------------
    # You can now inject an AlphaModel into the Strategy constructor
    # sma_alpha = SMAAlphaModel(backtest.data_handler, short_window=20, long_window=100)
    # backtest.strategy.alpha_model = sma_alpha
    
    # Run the backtest
    backtest.simulate_trading()
    
    from riskstats import PerformanceStats, PerformanceVisuals

    # Access the portfolio from the backtest instance
    portfolio = backtest.portfolio
    
    equity_df = portfolio.equity_curve
    
    # Check if we have data
    if equity_df is not None and not equity_df.empty:
        stats = PerformanceStats(
            equity_df=equity_df,
            cash_flows=portfolio.cash_flows,
            closed_trades=portfolio.closed_trades
        )
        results = stats.summary()
        print("\n=== PERFORMANCE STATS ===")

        for k, v in results.items():
            print(f"{k}: {v}")
        print("\n=== PERFORMANCE CURVE ===")
        visuals = PerformanceVisuals(equity_df)
        visuals.plot_all()

        # Log trades
        logger = TradeLogger("backtest_trades.csv")
        logger.log_trades(portfolio.closed_trades)
    else:
        print("No trades generated or backtest failed.")

    # ============================================================================
    # WALK-FORWARD DEMONSTRATION
    # ============================================================================
    print("\n" + "="*50)
    print("DEMONSTRATING WALK-FORWARD ANALYSIS")
    print("="*50)
    
    # Define windows (test periods)
    wf_windows = [
        (None, None, datetime.datetime(2021, 1, 1), datetime.datetime(2021, 12, 31)),
        (None, None, datetime.datetime(2022, 1, 1), datetime.datetime(2022, 12, 31)),
        (None, None, datetime.datetime(2023, 1, 1), datetime.datetime(2023, 12, 29))
    ]
    
    wf = WalkForwardBacktest(
        csv_dir, symbol_list, initial_capital, start_date,
        HistoricCSVDataHandler, SimulatedExecutionHandler, Portfolio, MomentumStrategy,
        wf_windows, execution_kwargs
    )
    
    # wf.run() # Uncomment to run full Walk-Forward
    print("Walk-Forward Engine initialized with %d windows." % len(wf_windows))
    print("="*50 + "\n")

    # ============================================================================
    # COST SENSITIVITY DEMONSTRATION
    # ============================================================================
    print("\n" + "="*50)
    print("DEMONSTRATING COST SENSITIVITY ANALYSIS")
    print("="*50)
    
    config = {
        'csv_dir': csv_dir, 'symbol_list': symbol_list, 'initial_capital': initial_capital,
        'heartbeat': 0.0, 'start_date': start_date, 'end_date': datetime.datetime(2022,12,31),
        'data_handler': HistoricCSVDataHandler, 'execution_handler': SimulatedExecutionHandler,
        'portfolio': Portfolio, 'strategy': MovingAverageCrossStrategy,
        'execution_kwargs': execution_kwargs.copy()
    }
    
    analyzer = CostSensitivityAnalyzer(config, [0.0, 0.001], [0.0005, 0.002])
    # analyzer.run_analysis() # Uncomment to run full sensitivity report
    print("Cost Sensitivity Analyzer initialized for 4 scenarios.")
    print("="*50 + "\n")

    
