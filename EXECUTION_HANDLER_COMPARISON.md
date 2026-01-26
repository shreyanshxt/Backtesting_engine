# Execution Handler Comparison

## Quick Answer to Your Question

**Q: "I want to use IBExecutionHandler for backtest"**  
**A: ❌ NO! Use SimulatedExecutionHandler for backtesting.**

IBExecutionHandler is only for **live trading** with real money.

---

## Side-by-Side Comparison

### SimulatedExecutionHandler ✅

```python
class SimulatedExecutionHandler(ExecutionHandler):
    """FOR BACKTESTING ONLY"""
    
    def __init__(self, events):
        self.events = events
    
    def execute_order(self, event):
        if event.type == 'ORDER':
            # Creates a SIMULATED fill instantly
            fill_event = FillEvent(
                symbol=event.symbol,
                timeindex=datetime.datetime.utcnow(),
                exchange='SIMULATED',
                quantity=event.quantity,
                direction=event.direction,
                fill_cost=None,
                commission=None
            )
            self.events.put(fill_event)
```

**Characteristics:**
- ✅ Simple and fast
- ✅ No external dependencies
- ✅ No broker connection needed
- ✅ Instant fills (unrealistic but good for testing)
- ✅ Zero risk
- ✅ Free to use

**When to use:**
- Testing strategies on historical data
- Developing and debugging trading logic
- Performance analysis
- Learning algorithmic trading

---

### IBExecutionHandler 🔴

```python
class IBExecutionHandler(ExecutionHandler):
    """FOR LIVE TRADING ONLY - REAL MONEY AT RISK!"""
    
    def __init__(self, events, order_routing='SMART', currency='USD'):
        self.events = events
        self.order_routing = order_routing  # Where to route orders
        self.currency = currency
        self.fill_dict = {}
        
        # CONNECTS TO REAL IB TWS/GATEWAY!
        self.tws_conn = self.create_tws_connection()
        self.order_id = self.create_initial_order_id()
        self.register_handlers()
    
    def create_tws_connection(self):
        """Connects to Interactive Brokers TWS"""
        tws_conn = ibConnection()
        tws_conn.connect()  # REAL CONNECTION!
        return tws_conn
    
    def execute_order(self, event):
        if event.type == 'ORDER':
            # Creates REAL contract and order
            ib_contract = self.create_contract(...)
            ib_order = self.create_order(...)
            
            # SENDS REAL ORDER TO MARKET!
            self.tws_conn.placeOrder(ib_contract, ib_order)
```

**Characteristics:**
- 🔴 Requires IB account
- 🔴 Requires TWS/Gateway running
- 🔴 Real money at risk
- 🔴 Real commissions charged
- 🔴 Subject to market conditions (slippage, rejection, etc.)
- 🔴 Complex error handling needed
- 🔴 Slower execution

**When to use:**
- ONLY after thorough backtesting
- ONLY when you're ready to trade live
- ONLY with money you can afford to lose
- ONLY when you understand all risks

---

## Feature Comparison Table

| Feature | SimulatedExecutionHandler | IBExecutionHandler |
|---------|---------------------------|-------------------|
| **Purpose** | Backtesting | Live Trading |
| **Broker Account** | Not needed | Required (IB) |
| **TWS/Gateway** | Not needed | Must be running |
| **Order Execution** | Instant/Simulated | Real market orders |
| **Fill Guarantee** | Always fills | May be rejected |
| **Slippage** | Not modeled* | Real slippage |
| **Commissions** | Calculated | Real charges |
| **Money Risk** | $0 | Real money |
| **Speed** | Very fast | Real-time |
| **Connection** | None | TCP to IB |
| **Error Handling** | Simple | Complex |
| **Testing** | Perfect for it | Not for testing |

\* Can be added to SimulatedExecutionHandler if desired

---

## Code Example: Creating a Backtest

### ✅ CORRECT - Using SimulatedExecutionHandler

```python
from complete_backtest_system import *
import datetime

# Setup
csv_dir = '/path/to/data'
symbol_list = ['AAPL']
initial_capital = 100000.0

# Create backtest with SIMULATED execution
backtest = Backtest(
    csv_dir=csv_dir,
    symbol_list=symbol_list,
    initial_capital=initial_capital,
    heartbeat=0.0,
    start_date=datetime.datetime(2020, 1, 1),
    data_handler=HistoricCSVDataHandler,
    execution_handler=SimulatedExecutionHandler,  # ✅ CORRECT
    portfolio=Portfolio,
    strategy=BuyAndHoldStrategy
)

backtest.simulate_trading()
```

**Result:** Safe backtesting with no risk ✅

---

### ❌ WRONG - Using IBExecutionHandler for Backtest

```python
# DON'T DO THIS!
backtest = Backtest(
    csv_dir=csv_dir,
    symbol_list=symbol_list,
    initial_capital=initial_capital,
    heartbeat=0.0,
    start_date=datetime.datetime(2020, 1, 1),
    data_handler=HistoricCSVDataHandler,
    execution_handler=IBExecutionHandler,  # ❌ WRONG for backtest!
    portfolio=Portfolio,
    strategy=BuyAndHoldStrategy
)

backtest.simulate_trading()
```

**Problems:**
1. ❌ Will try to connect to IB TWS (connection error if not running)
2. ❌ Might place real orders if connection succeeds
3. ❌ Extremely slow (real-time vs. historical)
4. ❌ Costs real money for no benefit
5. ❌ Not the intended use case

---

## Migration Path: Backtest → Live Trading

When you're ready to go live:

### Step 1: Thorough Backtesting
```python
# Use SimulatedExecutionHandler
backtest = Backtest(..., execution_handler=SimulatedExecutionHandler)
```

### Step 2: Paper Trading (Optional but Recommended)
```python
# Use IBExecutionHandler with IB paper trading account
live_test = Backtest(..., execution_handler=IBExecutionHandler)
```

### Step 3: Live Trading (Carefully!)
```python
# Use IBExecutionHandler with real IB account
# Start with small position sizes!
live_trading = Backtest(..., execution_handler=IBExecutionHandler)
```

---

## Your Original Code Issues

In your `Events.ipynb`, you had:

### Issue 1: Wrong Parameters in SimulatedExecutionHandler

**Your code (line 367):**
```python
fill_event = FillEvent(
    event.symbol,
    datetime.datetime.utcnow(),
    event.order_type,  # ❌ Should be exchange!
    event.quantity,
    event.direction
)
```

**Fixed version:**
```python
fill_event = FillEvent(
    symbol=event.symbol,
    timeindex=datetime.datetime.utcnow(),
    exchange='SIMULATED',  # ✅ Correct
    quantity=event.quantity,
    direction=event.direction,
    fill_cost=None,
    commission=None
)
```

### Issue 2: Missing Parameters in IBExecutionHandler.__init__

**Your code (line 380):**
```python
def __init__(self, events):
    self.events = events
    self.order_routing = order_routing  # ❌ Not defined!
    self.currency = currency            # ❌ Not defined!
```

**Fixed version:**
```python
def __init__(self, events, order_routing='SMART', currency='USD'):
    self.events = events
    self.order_routing = order_routing  # ✅ Now defined
    self.currency = currency            # ✅ Now defined
```

### Issue 3: Incomplete Backtest Class

**Your code (line 490-491):**
```python
class Backtest(object):
    def __init__(self, symbol  # ❌ Incomplete!
```

**See `complete_backtest_system.py` for the full implementation.**

---

## Summary

### For Backtesting (What You Need):
- ✅ Use **SimulatedExecutionHandler**
- ✅ Fast, safe, free
- ✅ Perfect for strategy development
- ✅ See `complete_backtest_system.py`

### For Live Trading (Future Use):
- 🔴 Use **IBExecutionHandler**  
- 🔴 Only after successful backtesting
- 🔴 Requires IB account and TWS
- 🔴 Real money at risk
- 🔴 Your code has bugs - use my fixed version

---

## Files to Use

1. **`complete_backtest_system.py`** - Complete working system ✅
2. **`README_BACKTEST.md`** - Quick start guide
3. **`execution_handler_guide.md`** - Detailed explanation
4. **This file** - Side-by-side comparison

All files include:
- ✅ Fixed SimulatedExecutionHandler
- ✅ Complete Backtest class
- ✅ Working examples
- ✅ Proper error handling

---

**Bottom Line:** For backtesting (which is what you're trying to do), always use **SimulatedExecutionHandler**. Save IBExecutionHandler for when you're ready to trade with real money!
