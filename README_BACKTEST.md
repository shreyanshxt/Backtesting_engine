# Event-Driven Backtesting System - Quick Start Guide

## 🎯 Your Question: "I want to use IBExecutionHandler"

### ⚠️ IMPORTANT: For Backtesting, DON'T use IBExecutionHandler!

**You have TWO execution handlers:**

| Handler | Purpose | Use When |
|---------|---------|----------|
| **SimulatedExecutionHandler** | ✅ **Backtesting** | Testing strategies on historical data (NO real money) |
| **IBExecutionHandler** | 🔴 **Live Trading** | Real trading with Interactive Brokers (REAL money at risk!) |

## 📁 Files I Created For You

1. **`complete_backtest_system.py`** - Complete working system with:
   - ✅ All event classes (Market, Signal, Order, Fill)
   - ✅ Data handler for CSV files
   - ✅ Portfolio management
   - ✅ **SimulatedExecutionHandler** (for backtesting)
   - ✅ **Complete Backtest class** (what you were stuck on!)
   - ✅ Example Buy & Hold strategy
   
2. **`execution_handler_guide.md`** - Detailed guide on when to use which handler

3. **`backtest_complete.py`** - Simplified Backtest class only

## 🚀 How to Use the Backtest Class

### Step 1: Prepare Your Data

Create a `data` folder with CSV files:

```bash
mkdir /Users/shreyanshsingh/mp_env/data
```

Your CSV files should look like this (e.g., `AAPL.csv`):

```
datetime,open,high,low,close,volume
2020-01-02,296.24,300.60,295.47,300.35,33911864
2020-01-03,297.15,300.58,296.30,297.43,36028564
...
```

### Step 2: Run the Backtest

```python
from complete_backtest_system import Backtest, HistoricCSVDataHandler
from complete_backtest_system import SimulatedExecutionHandler, Portfolio
from complete_backtest_system import BuyAndHoldStrategy
import datetime

# Configure
csv_dir = '/Users/shreyanshsingh/mp_env/data'
symbol_list = ['AAPL']
initial_capital = 100000.0
heartbeat = 0.0
start_date = datetime.datetime(2020, 1, 1)

# Create backtest
backtest = Backtest(
    csv_dir=csv_dir,
    symbol_list=symbol_list,
    initial_capital=initial_capital,
    heartbeat=heartbeat,
    start_date=start_date,
    data_handler=HistoricCSVDataHandler,
    execution_handler=SimulatedExecutionHandler,  # ← Use this for backtest!
    portfolio=Portfolio,
    strategy=BuyAndHoldStrategy
)

# Run it!
backtest.simulate_trading()
```

## 📊 What the Backtest Class Does

The `Backtest` class you were stuck on orchestrates everything:

```python
class Backtest(object):
    def __init__(self, csv_dir, symbol_list, initial_capital, 
                 heartbeat, start_date, data_handler, 
                 execution_handler, portfolio, strategy):
        # 1. Store configuration
        # 2. Create event queue
        # 3. Initialize all components
        
    def _generate_trading_instances(self):
        # Creates instances of:
        # - DataHandler (reads market data)
        # - Strategy (generates signals)
        # - Portfolio (manages positions)
        # - ExecutionHandler (executes orders)
        
    def _run_backtest(self):
        # Main loop:
        # 1. Get new market data
        # 2. Process events:
        #    - MARKET → calculate signals
        #    - SIGNAL → generate orders
        #    - ORDER → execute (simulated)
        #    - FILL → update portfolio
        
    def simulate_trading(self):
        # Run everything and show results
```

## 🔧 How to Fix Your Code

Your original Events.ipynb had issues. Here's what I fixed:

### Issue 1: Incomplete Backtest Class
**Your code (line 490-491):**
```python
class Backtest(object):
    def __init__(self, symbol
```

**Fixed:** See `complete_backtest_system.py` for the complete implementation.

### Issue 2: Wrong FillEvent Parameters in SimulatedExecutionHandler
**Your code (line 367):**
```python
fill_event = FillEvent(
    event.symbol,
    datetime.datetime.utcnow(),
    event.order_type,  # ❌ WRONG! Should be exchange
    event.quantity,
    event.direction
)
```

**Fixed:**
```python
fill_event = FillEvent(
    symbol=event.symbol,
    timeindex=datetime.datetime.utcnow(),
    exchange='SIMULATED',  # ✅ Correct!
    quantity=event.quantity,
    direction=event.direction,
    fill_cost=None,
    commission=None
)
```

## 🎓 Understanding the Event Flow

```
1. Market Data Available
   ↓
2. MarketEvent created
   ↓
3. Strategy.calculate_signals() → creates SignalEvent
   ↓
4. Portfolio.update_signal() → creates OrderEvent
   ↓
5. ExecutionHandler.execute_order() → creates FillEvent
   ↓
6. Portfolio.update_fill() → updates positions & holdings
```

## ⚡ Quick Test

To test if everything works:

```bash
cd /Users/shreyanshsingh/mp_env
python complete_backtest_system.py
```

(Note: You'll need actual CSV data files first)

## 🆘 Common Errors & Solutions

### Error: "No module named 'ib_insync'"
**Solution:** You don't need it for backtesting! Only use SimulatedExecutionHandler.

### Error: "No data found for symbol"
**Solution:** Make sure your CSV files are in the csv_dir and named correctly (e.g., `AAPL.csv`).

### Error: "DataFrame is empty"
**Solution:** Check your data format matches the expected format (datetime,open,high,low,close,volume).

## 🎯 Summary

**For BACKTESTING (what you need now):**
```python
execution_handler = SimulatedExecutionHandler  # ✅ Use this
```

**For LIVE TRADING (only after successful backtesting):**
```python
execution_handler = IBExecutionHandler  # 🔴 Real money! Be careful!
```

## 📚 Next Steps

1. ✅ Use `complete_backtest_system.py` as your base
2. ✅ Test with SimulatedExecutionHandler first
3. ✅ Create your own strategy class (inherit from `Strategy`)
4. ✅ Backtest thoroughly with historical data
5. ⏸️ Only then consider IBExecutionHandler for live trading

## 💡 Key Takeaway

**The Backtest class is just a coordinator!** It:
- Creates all components (data, strategy, portfolio, execution)
- Runs the event loop
- Collects results

You pass the **classes** (not instances) to Backtest, and it creates the instances for you.

---

**Need help?** Check:
- `complete_backtest_system.py` - Full working example
- `execution_handler_guide.md` - When to use which handler
- Your original `Events.ipynb` - Reference (but use my fixed version)
