#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ACTIVE TRADING STRATEGIES
These strategies generate MANY more trades than Buy & Hold
"""

import numpy as np
from complete_backtest_system import Strategy, SignalEvent


# =============================================================================
# 1. MOVING AVERAGE CROSSOVER STRATEGY (Many trades!)
# =============================================================================

class MovingAverageCrossStrategy(Strategy):
    """
    Generates signals based on a simple Moving Average crossover.
    - BUY when short MA crosses above long MA
    - SELL when short MA crosses below long MA
    
    This generates MANY more trades than Buy & Hold!
    """
    
    def __init__(self, bars, events, short_window=50, long_window=200):
        """
        Parameters:
        -----------
        short_window : int
            Short moving average period (default: 50 days)
        long_window : int
            Long moving average period (default: 200 days)
        """
        self.bars = bars
        self.symbol_list = self.bars.symbol_list
        self.events = events
        self.short_window = short_window
        self.long_window = long_window
        
        # Track which symbols we're currently long
        self.bought = self._calculate_initial_bought()
    
    def _calculate_initial_bought(self):
        """Initialize bought dictionary for all symbols."""
        bought = {}
        for s in self.symbol_list:
            bought[s] = 'OUT'  # 'OUT', 'LONG', or 'SHORT'
        return bought
    
    def calculate_signals(self, event):
        """Generate signals based on MA crossover."""
        if event.type == 'MARKET':
            for symbol in self.symbol_list:
                bars = self.bars.get_latest_bars(symbol, N=self.long_window)
                
                if bars is not None and len(bars) >= self.long_window:
                    # Calculate moving averages
                    close_prices = np.array([b[1].close for b in bars])
                    short_ma = np.mean(close_prices[-self.short_window:])
                    long_ma = np.mean(close_prices[-self.long_window:])
                    
                    # Previous MAs for crossover detection
                    prev_short_ma = np.mean(close_prices[-(self.short_window+1):-1])
                    prev_long_ma = np.mean(close_prices[-(self.long_window+1):-1])
                    
                    dt = bars[-1][0]
                    
                    # Signal: Short MA crosses above Long MA
                    if prev_short_ma <= prev_long_ma and short_ma > long_ma:
                        if self.bought[symbol] == 'OUT':
                            signal = SignalEvent(1, symbol, dt, 'LONG', 1.0)
                            self.events.put(signal)
                            self.bought[symbol] = 'LONG'
                    
                    # Signal: Short MA crosses below Long MA
                    elif prev_short_ma >= prev_long_ma and short_ma < long_ma:
                        if self.bought[symbol] == 'LONG':
                            signal = SignalEvent(1, symbol, dt, 'EXIT', 1.0)
                            self.events.put(signal)
                            self.bought[symbol] = 'OUT'


# =============================================================================
# 2. MEAN REVERSION STRATEGY (Even more trades!)
# =============================================================================

class MeanReversionStrategy(Strategy):
    """
    Mean reversion strategy using Bollinger Bands.
    - BUY when price touches lower band
    - SELL when price touches upper band
    
    Generates LOTS of trades!
    """
    
    def __init__(self, bars, events, period=20, num_std=2):
        """
        Parameters:
        -----------
        period : int
            Period for Bollinger Bands (default: 20)
        num_std : float
            Number of standard deviations (default: 2)
        """
        self.bars = bars
        self.symbol_list = self.bars.symbol_list
        self.events = events
        self.period = period
        self.num_std = num_std
        self.bought = self._calculate_initial_bought()
    
    def _calculate_initial_bought(self):
        bought = {}
        for s in self.symbol_list:
            bought[s] = 'OUT'
        return bought
    
    def calculate_signals(self, event):
        """Generate signals based on Bollinger Bands."""
        if event.type == 'MARKET':
            for symbol in self.symbol_list:
                bars = self.bars.get_latest_bars(symbol, N=self.period)
                
                if bars is not None and len(bars) >= self.period:
                    # Calculate Bollinger Bands
                    close_prices = np.array([b[1].close for b in bars])
                    sma = np.mean(close_prices)
                    std = np.std(close_prices)
                    
                    upper_band = sma + (self.num_std * std)
                    lower_band = sma - (self.num_std * std)
                    
                    current_price = close_prices[-1]
                    dt = bars[-1][0]
                    
                    # BUY signal: Price at or below lower band
                    if current_price <= lower_band:
                        if self.bought[symbol] == 'OUT':
                            signal = SignalEvent(1, symbol, dt, 'LONG', 1.0)
                            self.events.put(signal)
                            self.bought[symbol] = 'LONG'
                    
                    # SELL signal: Price at or above upper band
                    elif current_price >= upper_band:
                        if self.bought[symbol] == 'LONG':
                            signal = SignalEvent(1, symbol, dt, 'EXIT', 1.0)
                            self.events.put(signal)
                            self.bought[symbol] = 'OUT'


# =============================================================================
# 3. MOMENTUM STRATEGY (High frequency!)
# =============================================================================

class MomentumStrategy(Strategy):
    """
    Momentum strategy based on rate of change.
    - BUY when momentum is positive and increasing
    - SELL when momentum is negative or decreasing
    
    Very active strategy!
    """
    
    def __init__(self, bars, events, lookback=10, threshold=0.02):
        """
        Parameters:
        -----------
        lookback : int
            Lookback period for momentum calculation (default: 10)
        threshold : float
            Minimum momentum threshold to trigger signal (default: 2%)
        """
        self.bars = bars
        self.symbol_list = self.bars.symbol_list
        self.events = events
        self.lookback = lookback
        self.threshold = threshold
        self.bought = self._calculate_initial_bought()
    
    def _calculate_initial_bought(self):
        bought = {}
        for s in self.symbol_list:
            bought[s] = 'OUT'
        return bought
    
    def calculate_signals(self, event):
        """Generate signals based on momentum."""
        if event.type == 'MARKET':
            for symbol in self.symbol_list:
                bars = self.bars.get_latest_bars(symbol, N=self.lookback + 1)
                
                if bars is not None and len(bars) >= self.lookback + 1:
                    # Calculate momentum (rate of change)
                    close_prices = np.array([b[1].close for b in bars])
                    momentum = (close_prices[-1] - close_prices[-self.lookback]) / close_prices[-self.lookback]
                    
                    dt = bars[-1][0]
                    
                    # BUY signal: Positive momentum above threshold
                    if momentum > self.threshold:
                        if self.bought[symbol] == 'OUT':
                            signal = SignalEvent(1, symbol, dt, 'LONG', 1.0)
                            self.events.put(signal)
                            self.bought[symbol] = 'LONG'
                    
                    # SELL signal: Negative momentum or below threshold
                    elif momentum < -self.threshold:
                        if self.bought[symbol] == 'LONG':
                            signal = SignalEvent(1, symbol, dt, 'EXIT', 1.0)
                            self.events.put(signal)
                            self.bought[symbol] = 'OUT'


# =============================================================================
# 4. RSI STRATEGY (Classic oscillator!)
# =============================================================================

class RSIStrategy(Strategy):
    """
    RSI (Relative Strength Index) strategy.
    - BUY when RSI < 30 (oversold)
    - SELL when RSI > 70 (overbought)
    
    Good for ranging markets!
    """
    
    def __init__(self, bars, events, period=14, oversold=30, overbought=70):
        """
        Parameters:
        -----------
        period : int
            RSI period (default: 14)
        oversold : float
            Oversold threshold (default: 30)
        overbought : float
            Overbought threshold (default: 70)
        """
        self.bars = bars
        self.symbol_list = self.bars.symbol_list
        self.events = events
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
        self.bought = self._calculate_initial_bought()
    
    def _calculate_initial_bought(self):
        bought = {}
        for s in self.symbol_list:
            bought[s] = 'OUT'
        return bought
    
    def _calculate_rsi(self, prices):
        """Calculate RSI."""
        deltas = np.diff(prices)
        seed = deltas[:self.period]
        up = seed[seed >= 0].sum() / self.period
        down = -seed[seed < 0].sum() / self.period
        
        if down == 0:
            return 100
        
        rs = up / down
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_signals(self, event):
        """Generate signals based on RSI."""
        if event.type == 'MARKET':
            for symbol in self.symbol_list:
                bars = self.bars.get_latest_bars(symbol, N=self.period + 1)
                
                if bars is not None and len(bars) >= self.period + 1:
                    close_prices = np.array([b[1].close for b in bars])
                    rsi = self._calculate_rsi(close_prices)
                    
                    dt = bars[-1][0]
                    
                    # BUY signal: RSI below oversold threshold
                    if rsi < self.oversold:
                        if self.bought[symbol] == 'OUT':
                            signal = SignalEvent(1, symbol, dt, 'LONG', 1.0)
                            self.events.put(signal)
                            self.bought[symbol] = 'LONG'
                    
                    # SELL signal: RSI above overbought threshold
                    elif rsi > self.overbought:
                        if self.bought[symbol] == 'LONG':
                            signal = SignalEvent(1, symbol, dt, 'EXIT', 1.0)
                            self.events.put(signal)
                            self.bought[symbol] = 'OUT'


# =============================================================================
# 5. REBALANCING STRATEGY (Periodic trades)
# =============================================================================

class RebalancingStrategy(Strategy):
    """
    Simple rebalancing strategy that trades every N days.
    Keeps position at target level.
    
    Guaranteed number of trades!
    """
    
    def __init__(self, bars, events, rebalance_days=30):
        """
        Parameters:
        -----------
        rebalance_days : int
            Rebalance every N days (default: 30)
        """
        self.bars = bars
        self.symbol_list = self.bars.symbol_list
        self.events = events
        self.rebalance_days = rebalance_days
        self.last_rebalance = {}
        self.day_counter = 0
        
        for s in self.symbol_list:
            self.last_rebalance[s] = 0
    
    def calculate_signals(self, event):
        """Generate signals based on rebalancing schedule."""
        if event.type == 'MARKET':
            self.day_counter += 1
            
            for symbol in self.symbol_list:
                # Rebalance if enough days have passed
                if self.day_counter - self.last_rebalance[symbol] >= self.rebalance_days:
                    bars = self.bars.get_latest_bars(symbol, N=1)
                    if bars is not None and bars != []:
                        dt = bars[0][0]
                        
                        # Simple: Exit and re-enter to simulate rebalancing
                        signal_exit = SignalEvent(1, symbol, dt, 'EXIT', 1.0)
                        self.events.put(signal_exit)
                        
                        signal_long = SignalEvent(1, symbol, dt, 'LONG', 1.0)
                        self.events.put(signal_long)
                        
                        self.last_rebalance[symbol] = self.day_counter


# =============================================================================
# USAGE EXAMPLE
# =============================================================================

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║               ACTIVE TRADING STRATEGIES                      ║
    ╚══════════════════════════════════════════════════════════════╝
    
    These strategies generate MANY more trades than Buy & Hold!
    
    Available strategies:
    1. MovingAverageCrossStrategy - Classic MA crossover
    2. MeanReversionStrategy - Bollinger Bands
    3. MomentumStrategy - Rate of change
    4. RSIStrategy - Relative Strength Index
    5. RebalancingStrategy - Periodic rebalancing
    
    To use, replace in complete_backtest_system.py:
    
        from active_strategies import MovingAverageCrossStrategy
        
        backtest = Backtest(
            ...
            strategy=MovingAverageCrossStrategy  # ← Use active strategy
        )
    """)
