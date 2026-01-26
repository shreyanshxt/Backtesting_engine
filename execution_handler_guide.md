# Execution Handler Guide: When to Use What

## Overview
Your backtesting system has two execution handlers:

### 1. SimulatedExecutionHandler
**Purpose:** For BACKTESTING on historical data
**When to use:** Testing strategies without real money

```python
from events import FillEvent
import datetime

class SimulatedExecutionHandler(ExecutionHandler):
    def __init__(self, events):
        self.events = events
    
    def execute_order(self, event):
        """
        Simulates order execution immediately
        No actual broker connection needed
        """
        if event.type == 'ORDER':
            fill_event = FillEvent(
                event.symbol,
                datetime.datetime.utcnow(),
                'SIMULATED',  # exchange
                event.quantity,
                event.direction,
                None,  # fill_cost (calculated from data)
                None   # commission (calculated)
            )
            self.events.put(fill_event)
```

### 2. IBExecutionHandler
**Purpose:** For LIVE TRADING with Interactive Brokers
**When to use:** Real trading with real money through IB TWS

```python
from ib_insync import IB, Stock, Order

class IBExecutionHandler(ExecutionHandler):
    def __init__(self, events, order_routing='SMART', currency='USD'):
        self.events = events
        self.order_routing = order_routing
        self.currency = currency
        self.fill_dict = {}
        self.tws_conn = self.create_tws_connection()
        self.order_id = self.create_initial_order_id()
        self.register_handlers()
    
    # ... (full implementation connects to real IB TWS)
```

## Comparison Table

| Feature | SimulatedExecutionHandler | IBExecutionHandler |
|---------|--------------------------|-------------------|
| **Purpose** | Backtesting | Live Trading |
| **Cost** | FREE | Real money |
| **Speed** | Very fast | Real-time |
| **Broker** | None needed | Requires IB account |
| **Fills** | Instant/Simulated | Market dependent |
| **Slippage** | Not modeled (can add) | Real slippage |
| **Risk** | Zero | Real money risk |

## Complete Backtest Example

### For BACKTESTING (Recommended to start):

```python
import datetime
import queue

# Create event queue
events = queue.Queue()

# Setup backtest parameters
csv_dir = '/path/to/data'
symbol_list = ['AAPL', 'MSFT']
initial_capital = 100000.0
start_date = datetime.datetime(2020, 1, 1)

# Create components
data_handler = HistoricCSVDataHandler(events, csv_dir, symbol_list)
strategy = YourStrategy(data_handler, events)
portfolio = Portfolio(data_handler, events, start_date, initial_capital)
execution_handler = SimulatedExecutionHandler(events)  # ← SIMULATED for backtest

# Create and run backtest
backtest = Backtest(
    csv_dir=csv_dir,
    symbol_list=symbol_list,
    initial_capital=initial_capital,
    heartbeat=0.0,
    start_date=start_date,
    data_handler=HistoricCSVDataHandler,
    execution_handler=SimulatedExecutionHandler,  # ← Use this
    portfolio=Portfolio,
    strategy=YourStrategy
)

backtest.simulate_trading()
```

### For LIVE TRADING (After testing):

```python
# Same setup as above, but with IBExecutionHandler

execution_handler = IBExecutionHandler(
    events, 
    order_routing='SMART', 
    currency='USD'
)  # ← IB for live trading

backtest_live = Backtest(
    csv_dir=csv_dir,
    symbol_list=symbol_list,
    initial_capital=initial_capital,
    heartbeat=0.5,  # slower for live
    start_date=start_date,
    data_handler=LiveIBDataHandler,  # also need live data
    execution_handler=IBExecutionHandler,  # ← Use this for live
    portfolio=Portfolio,
    strategy=YourStrategy
)

backtest_live.simulate_trading()
```

## Key Differences in Your Code

### SimulatedExecutionHandler Issues (Fixed):
The original had a bug - wrong parameters passed to FillEvent:
```python
# WRONG (from your original code):
fill_event = FillEvent(
    event.symbol,
    datetime.datetime.utcnow(),
    event.order_type,  # ❌ This should be exchange, not order_type
    event.quantity,
    event.direction
)

# CORRECT:
fill_event = FillEvent(
    symbol=event.symbol,
    timeindex=datetime.datetime.utcnow(),
    exchange='SIMULATED',  # ✅ Exchange name
    quantity=event.quantity,
    direction=event.direction,
    fill_cost=None,  # Calculate from data
    commission=None  # Calculate using commission_ib
)
```

### IBExecutionHandler Issues (To fix):
Your IBExecutionHandler has several issues:
1. Missing `order_routing` and `currency` parameters in `__init__`
2. Uses old IB API instead of ib_insync
3. `execute_order` signature wrong - should accept `event`, not `contract, order`

## Recommendation

**For your current situation (creating backtest class):**
1. ✅ Use **SimulatedExecutionHandler** 
2. ✅ Test thoroughly with historical data
3. ✅ Verify strategy performance
4. ⏳ Only after successful backtesting, consider IBExecutionHandler for live trading

**Implementation Steps:**
1. Fix SimulatedExecutionHandler (use my version)
2. Complete Backtest class (use my version)
3. Create a simple strategy (e.g., Buy and Hold)
4. Run backtest with simulated execution
5. Analyze results
6. Only then consider live trading with IBExecutionHandler

## Questions to Ask Yourself

Before using IBExecutionHandler:
- [ ] Have I thoroughly backtested my strategy?
- [ ] Do I have an Interactive Brokers account?
- [ ] Is IB TWS/Gateway installed and running?
- [ ] Am I ready to risk real money?
- [ ] Do I understand slippage and commission costs?

If you answered "No" to any of these, stick with SimulatedExecutionHandler!
