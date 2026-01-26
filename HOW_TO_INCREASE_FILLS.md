# 📈 How to Increase Fill Orders in Your Backtest

## 🎯 The Problem

**Buy & Hold Strategy** only generates **1 fill per symbol** (buy once, never sell).

For NVDA with Buy & Hold:
- Signals: 1
- Orders: 1  
- Fills: 1

**You want MORE fills!**

---

## ✅ Solution: Use an Active Trading Strategy

I've created **5 active strategies** that generate MANY more fills!

---

## 🚀 Quick Start - Run Active Strategy NOW

```bash
cd /Users/shreyanshsingh/mp_env
source bin/activate
python run_active_backtest.py
```

This uses **Moving Average Crossover** strategy and will generate MANY MORE fills!

---

## 📊 Strategy Comparison

| Strategy | Expected Fills (1 year) | Suitable For | Complexity |
|----------|------------------------|--------------|------------|
| **Buy & Hold** | 1 | Long-term investing | ⭐ |
| **MA Crossover** | 3-10 | Trending markets | ⭐⭐ |
| **Bollinger Bands** | 10-30 | Ranging markets | ⭐⭐ |
| **Momentum** | 20-50 | Trending markets | ⭐⭐⭐ |
| **RSI** | 15-40 | Ranging markets | ⭐⭐⭐ |
| **Rebalancing** | 12 (guaranteed) | Any market | ⭐ |

---

## 🔧 Method 1: Use Different Strategies (RECOMMENDED)

### 1. Moving Average Crossover (Moderate fills)

```python
from active_strategies import MovingAverageCrossStrategy

backtest = Backtest(
    csv_dir='/Users/shreyanshsingh/mp_env/data',
    symbol_list=['NVDA'],
    initial_capital=600000.0,
    heartbeat=0.0,
    start_date=datetime.datetime(2020, 1, 1),
    data_handler=HistoricCSVDataHandler,
    execution_handler=SimulatedExecutionHandler,
    portfolio=Portfolio,
    strategy=MovingAverageCrossStrategy  # ← Generates 3-10 fills/year
)
```

**Parameters you can adjust:**
```python
# Make it trade MORE frequently (shorter MAs)
strategy=lambda bars, events: MovingAverageCrossStrategy(
    bars, events, short_window=20, long_window=50  # Faster signals
)
```

---

### 2. Mean Reversion / Bollinger Bands (High fills)

```python
from active_strategies import MeanReversionStrategy

backtest = Backtest(
    ...
    strategy=MeanReversionStrategy  # ← Generates 10-30 fills/year
)
```

**Parameters:**
```python
# Trade MORE in volatile markets
strategy=lambda bars, events: MeanReversionStrategy(
    bars, events, period=20, num_std=1.5  # Tighter bands = more trades
)
```

---

### 3. Momentum Strategy (Very high fills)

```python
from active_strategies import MomentumStrategy

backtest = Backtest(
    ...
    strategy=MomentumStrategy  # ← Generates 20-50 fills/year
)
```

**Parameters:**
```python
# Trade VERY frequently
strategy=lambda bars, events: MomentumStrategy(
    bars, events, lookback=5, threshold=0.01  # Lower threshold = more trades
)
```

---

### 4. RSI Strategy (Oscillator-based)

```python
from active_strategies import RSIStrategy

backtest = Backtest(
    ...
    strategy=RSIStrategy  # ← Generates 15-40 fills/year
)
```

**Parameters:**
```python
# Get MORE signals
strategy=lambda bars, events: RSIStrategy(
    bars, events, period=14, oversold=40, overbought=60  # Wider range = more trades
)
```

---

### 5. Rebalancing Strategy (Guaranteed fills)

```python
from active_strategies import RebalancingStrategy

backtest = Backtest(
    ...
    strategy=RebalancingStrategy  # ← Trades every N days (guaranteed!)
)
```

**Parameters:**
```python
# Trade EVERY WEEK (52 fills/year guaranteed!)
strategy=lambda bars, events: RebalancingStrategy(
    bars, events, rebalance_days=7  # Trade every 7 days
)

# Or EVERY DAY (252 fills/year!)
strategy=lambda bars, events: RebalancingStrategy(
    bars, events, rebalance_days=1  # Trade daily
)
```

---

## 🔧 Method 2: Modify Portfolio (Position Sizing)

Currently, the portfolio trades 100 shares per order. Make smaller, more frequent trades:

### Edit in `complete_backtest_system.py`:

Find the `generate_naive_order` method in Portfolio class (around line 305):

```python
def generate_naive_order(self, signal):
    """Generates a simple order."""
    # ... existing code ...
    
    mkt_quantity = 100  # ← CHANGE THIS!
    # Try:
    # mkt_quantity = 20   # Smaller size = can trade 5x more
    # mkt_quantity = 10   # Even smaller = 10x more trades
```

**BUT:** This doesn't increase SIGNALS, only changes position size.

---

## 🔧 Method 3: Add Multiple Symbols

More symbols = more potential fills:

```python
symbol_list = ['NVDA', 'AAPL', 'MSFT', 'GOOGL', 'AMZN']  # 5 symbols = 5x more fills
```

Don't forget to download the data:
```bash
source bin/activate
python quick_download.py  # Select option 2 for tech stocks
```

---

## 🔧 Method 4: Use Shorter Timeframes (Advanced)

Currently using daily data. Switch to:
- **Hourly data** → 6.5x more bars → more potential signals
- **Minute data** → 390x more bars → TONS of signals

**Note:** Yahoo Finance doesn't provide intraday data easily. Need different data source.

---

## 🔧 Method 5: Combine Strategies (Advanced)

Create a strategy that uses multiple indicators:

```python
class CombinedStrategy(Strategy):
    """Uses BOTH MA Crossover AND RSI"""
    
    def calculate_signals(self, event):
        # Generate signals from both strategies
        # More conditions = more opportunities
        pass
```

---

## 📈 Example Results Comparison

### Buy & Hold (Current)
```
Signals: 1
Orders: 1
Fills: 1
Total trades: 1 per symbol
```

### Moving Average Crossover
```
Signals: 6-12
Orders: 6-12
Fills: 6-12
Total trades: 3-6 round trips per year
```

### RSI Strategy
```
Signals: 30-80
Orders: 30-80
Fills: 30-80
Total trades: 15-40 round trips per year
```

### Rebalancing (Daily)
```
Signals: 252
Orders: 252
Fills: 252
Total trades: 252 per year (guaranteed!)
```

---

## ⚡ Quick Action Steps

### Step 1: Run Active Strategy (NOW!)
```bash
cd /Users/shreyanshsingh/mp_env
source bin/activate
python run_active_backtest.py
```

### Step 2: Try Different Strategies

Edit `run_active_backtest.py` and change this line:
```python
strategy=MovingAverageCrossStrategy  # Try different strategies
```

To:
```python
# Try these for MORE fills:
strategy=MeanReversionStrategy   # Bollinger Bands
strategy=MomentumStrategy         # Momentum-based
strategy=RSIStrategy             # RSI oscillator
strategy=RebalancingStrategy     # Periodic rebalancing
```

### Step 3: Adjust Parameters

Make strategies MORE aggressive:
```python
# Original (moderate)
strategy=lambda bars, events: MovingAverageCrossStrategy(
    bars, events, short_window=50, long_window=200
)

# MORE AGGRESSIVE (more fills!)
strategy=lambda bars, events: MovingAverageCrossStrategy(
    bars, events, short_window=10, long_window=30  # Shorter = more crossovers
)
```

---

## 🎯 Recommendations

### For NVDA (2020-2026 data):

**Best for learning:**
1. Start with **Moving Average Crossover** (moderate fills, easy to understand)
2. Try **RSI Strategy** (more fills, still straightforward)
3. Experiment with **parameters** to tune fill frequency

**Best for maximum fills:**
1. **Rebalancing Strategy** with `rebalance_days=1` (daily trades = 252 fills/year)
2. **Momentum Strategy** with low threshold (50+ fills/year)

**Best for realistic trading:**
1. **MA Crossover** with 50/200 (classic golden cross)
2. **RSI** with 30/70 thresholds (standard settings)

---

## 📊 Testing Different Strategies

Create a comparison script:

```python
# test_strategies.py
strategies = [
    ('Buy & Hold', BuyAndHoldStrategy),
    ('MA Cross', MovingAverageCrossStrategy),
    ('Mean Reversion', MeanReversionStrategy),
    ('Momentum', MomentumStrategy),
    ('RSI', RSIStrategy),
]

for name, strategy in strategies:
    backtest = Backtest(..., strategy=strategy)
    backtest.simulate_trading()
    print(f"{name}: Fills = {backtest.fills}")
```

---

## ⚠️ Important Notes

### 1. More Fills ≠ Better Performance
- More trades = more commissions
- Over-trading can reduce returns
- Quality > Quantity

### 2. Data Requirements
- Longer timeframes need more data
- Some strategies need minimum bars (e.g., 200-day MA needs 200 bars)

### 3. Commission Impact
With 100 fills/year:
- Commission per trade: ~$1.30
- Total yearly commissions: ~$130
- On $600,000 capital: 0.02% (minimal)

### 4. Slippage
SimulatedExecutionHandler assumes perfect fills. Real trading has slippage!

---

## 🆘 Troubleshooting

### "IndexError: list index out of range"
**Solution:** Strategy needs more historical data. Increase data range or use shorter indicator periods.

### "Only getting 1-2 fills"
**Solutions:**
1. Check data range (need more data)
2. Use more aggressive parameters
3. Try different strategy
4. Add more symbols

### "Too many fills (100+)"
**Solutions:**
1. Increase indicator periods (longer MA, longer RSI period)
2. Widen thresholds
3. Add filters to reduce false signals

---

## 🚀 Summary

**To increase fills:**

✅ **Use active strategy** (MovingAverageCrossStrategy, RSIStrategy, etc.)  
✅ **Adjust parameters** (shorter periods, lower thresholds)  
✅ **Add more symbols** (5 symbols = 5x potential fills)  
✅ **Use rebalancing** (guaranteed fills every N days)  

**Quick action:**
```bash
python run_active_backtest.py  # Run RIGHT NOW for more fills!
```

---

**Happy trading! 📈**

*Files: active_strategies.py, run_active_backtest.py*
