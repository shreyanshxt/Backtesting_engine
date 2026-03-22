
import time
import datetime
import queue
import threading
import asyncio

# Fix for "There is no current event loop" error on some Python versions/envs
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())
from active_strategies import MomentumStrategy
from ib_insync import IB, Stock, MarketOrder, RealTimeBarList, BarData
from complete_backtest_system import DataHandler, ExecutionHandler, MarketEvent, FillEvent, OrderEvent, Backtest
  # Or whatever strategy the user wants

# ============================================================================
# IB DATA HANDLER
# ============================================================================

class IBDataHandler(DataHandler):
    """
    DataHandler that streams data from Interactive Brokers.
    """
    def __init__(self, events, symbol_list, ib_connection):
        self.events = events
        self.symbol_list = symbol_list
        self.ib = ib_connection
        self.latest_symbol_data = {}
        self.continue_backtest = True
        
        # Initialize empty lists for symbols
        for s in self.symbol_list:
            self.latest_symbol_data[s] = []
            
        # Start subscriptions
        self._subscribe_market_data()

    def _subscribe_market_data(self):
        """
        Subscribes to real-time bars for all symbols.
        """
        for s in self.symbol_list:
            # Create a Contract object
            # ASSUMPTION: Symbols are NSE stocks or similar. Adjust exchange/currency as needed.
            # Example: RELIANCE.NS -> Symbol: RELIANCE, Exchange: NSE, Currency: INR
            # Or simplified: User passes "RELIANCE" and we hardcode NSE. 
            # For now, let's assume the symbol_list contains "Ticker" and we default to SMART/USD or NSE/INR
            # based on format.
            
            # Simple parsing logic (can be made more robust)
            if 'NS' in s: # NSE India
                ticker = s.split('.')[0]
                contract = Stock(ticker, 'NSE', 'INR')
            else: # US Stocks default
                contract = Stock(s, 'SMART', 'USD')
            
            print(f"Subscribing to {contract.symbol}")
            
            # Request Real Time Bars (5 second bars)
            self.ib.reqRealTimeBars(contract, 5, "MIDPOINT", False)
            
            # Identify the bar series by the raw symbol string
            contract.symbol_raw = s 
            
            # Hook the update function
            self.ib.barUpdateEvent += self._on_bar_update

    def _on_bar_update(self, bars, hasNewBar):
        """
        Callback when new bars are received from IB.
        """
        if hasNewBar:
            bar = bars[-1]
            contract = bars.contract
            
            # We need to map the contract back to our symbol_list string
            # In ib_insync, bars.contract should hold the contract
            # We attached symbol_raw to it (monkey patch) or we can try to key it
            
            # To be safe/standard:
            symbol = None
            if contract.exchange == 'NSE':
                symbol = f"{contract.symbol}.NS"
            else:
                symbol = contract.symbol
            
            # If we can't match exactly, we might have issues. 
            # Let's hope the monkeyatch works or the logic above is sufficient.
            
            if hasattr(contract, 'symbol_raw'):
                symbol = contract.symbol_raw
            
            if symbol and symbol in self.latest_symbol_data:
                # Format to match Backtest system expectations:
                # (datetime, object_with_ohlcv_attrs)
                # The existing system expects Access via getattr(obj, 'close')
                
                # Ib_insync BarData has date, open, high, low, close, volume, barCount, average
                # We can just store the BarData object as the second element
                
                # Convert IB date (datetime or timestamp) to python datetime if needed
                # RealTimeBar date is a timestamp (int) usually, wait, ib_insync converts it?
                # RealTimeBar: (time: int, open, high, low, close...)
                # We might need to convert 'time' to datetime
                
                dt = bar.time
                if isinstance(dt, int):
                    dt = datetime.datetime.fromtimestamp(dt)
                    
                self.latest_symbol_data[symbol].append(
                    (dt, bar)
                )
                
                # Trigger Market Event
                self.events.put(MarketEvent())
                print(f"New Bar for {symbol}: {bar.close} at {dt}")

    # -----------------------------------------------
    # INTERFACE IMPLEMENTATION
    # -----------------------------------------------

    def get_latest_bar(self, symbol):
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print(f"Symbol {symbol} not found.")
            raise
        else:
            return bars_list[-1]

    def get_latest_bars(self, symbol, N=1):
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print(f"Symbol {symbol} not found.")
            raise
        else:
            return bars_list[-N:]

    def get_latest_bar_datetime(self, symbol):
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print(f"Symbol {symbol} not found.")
            raise
        else:
            return bars_list[-1][0]

    def get_latest_bar_value(self, symbol, val_type):
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print(f"Symbol {symbol} not found.")
            raise
        else:
            # ib_insync bars have lowercase attributes: open, high, low, close
            return getattr(bars_list[-1][1], val_type)

    def get_latest_bar_values(self, symbol, val_type, N=1):
        try:
            bars_list = self.get_latest_bars(symbol, N)
        except KeyError:
            print(f"Symbol {symbol} not found.")
            raise
        else:
            return np.array([getattr(b[1], val_type) for b in bars_list])

    def update_bars(self):
        # In live mode, this is event driven by _on_bar_update.
        # Check if IB connection is still alive
        if not self.ib.isConnected():
            print("IB Disconnected. Stopping.")
            self.continue_backtest = False
        
        # We can also use this to pump ib events if not using ib.run()
        # But we will use loop elsewhere
        pass


# ============================================================================
# IB EXECUTION HANDLER
# ============================================================================

class IBExecutionHandler(ExecutionHandler):
    """
    Executes orders via Interactive Brokers.
    """
    def __init__(self, events, ib_connection):
        self.events = events
        self.ib = ib_connection
        self.ib.execDetailsEvent += self._on_exec_details

    def _on_exec_details(self, trade, fill):
        """
        Callback when an execution occurs.
        """
        # Create FillEvent
        # contract = trade.contract
        # execution = fill.execution
        
        # Map IB contract back to symbol
        symbol = trade.contract.symbol
        if trade.contract.exchange == 'NSE':
            symbol = f"{symbol}.NS"
        if hasattr(trade.contract, 'symbol_raw'):
             symbol = trade.contract.symbol_raw
             
        # Direction
        direction = 'BUY' if trade.order.action == 'BUY' else 'SELL'
        
        # Create Fill Event
        fe = FillEvent(
            symbol=symbol,
            timeindex=fill.time,
            exchange=fill.exchange,
            quantity=fill.shares,
            direction=direction,
            fill_cost=fill.price,
            commission=fill.commissionReport.commission if fill.commissionReport else 0.0
        )
        self.events.put(fe)
        print(f"Filled: {direction} {fill.shares} {symbol} @ {fill.price}")

    def execute_order(self, event):
        """
        Converts OrderEvent to IB Order and transmits.
        """
        if event.type == 'ORDER':
            # Create Contract
            if 'NS' in event.symbol:
                ticker = event.symbol.split('.')[0]
                contract = Stock(ticker, 'NSE', 'INR')
            else:
                contract = Stock(event.symbol, 'SMART', 'USD')
            contract.symbol_raw = event.symbol

            # Create Order
            action = 'BUY' if event.direction == 'BUY' else 'SELL'
            # Naive MKT order
            ib_order = MarketOrder(action, event.quantity)
            
            print(f"Placing Order: {action} {event.quantity} {event.symbol}")
            
            # Place Order
            trade = self.ib.placeOrder(contract, ib_order)
            
            # We could wait for fills here, but it's better to be async via _on_exec_details


# ============================================================================
# LIVE SESSION MANGER
# ============================================================================

def run_live_session():
    # 1. Connect to IB
    ib = IB()
    try:
        # Default TWS Paper Trading port is 7497, Gateway is 4002
        ib.connect('127.0.0.1', 7497, clientId=99)
    except Exception as e:
        print(f"Could not connect to IB: {e}")
        print("Ensure TWS or IB Gateway is running and API is enabled.")
        return

    print("Connected to IB.")

    # 2. Setup System
    events = queue.Queue()
    symbol_list = ['RELIANCE.NS'] # Example
    initial_capital = 100000.0
    start_date = datetime.datetime.now()

    # 3. Instantiate Components
    # Note: We pass the 'ib' object to Data and Execution handlers
    data_handler = IBDataHandler(events, symbol_list, ib)
    execution_handler = IBExecutionHandler(events, ib)
    
    # Use existing Portfolio and Strategy
    from complete_backtest_system import Portfolio
    portfolio = Portfolio(data_handler, events, start_date, initial_capital)
    
    # Use Momentum Strategy or Simple BuyAndHold
    strategy = MomentumStrategy(data_handler, events)
    
    print("System Initialized. Waiting for data...")
    
    # 4. Main Loop
    try:
        while True:
            # Process IB Messages
            ib.sleep(1) # This runs the collection loop for 1 sec
            
            # Process Event Queue
            while True:
                try:
                    event = events.get(False)
                except queue.Empty:
                    break
                else:
                    if event is not None:
                        if event.type == 'MARKET':
                            print(f"[MARKET] {datetime.datetime.now()}")
                            strategy.calculate_signals(event)
                            portfolio.update_timeindex(event)
                        
                        elif event.type == 'SIGNAL':
                            print(f"[SIGNAL] {event.symbol} {event.signal_type}")
                            portfolio.update_signal(event)
                        
                        elif event.type == 'ORDER':
                            print(f"[ORDER] {event.symbol} {event.direction}")
                            execution_handler.execute_order(event)
                        
                        elif event.type == 'FILL':
                            print(f"[FILL] {event.symbol} {event.quantity} @ {event.fill_cost}")
                            portfolio.update_fill(event)
            
            # Additional termination logic could go here
            
    except KeyboardInterrupt:
        print("Stopping Live Session...")
    finally:
        ib.disconnect()
        print("Disconnected.")

if __name__ == "__main__":
    run_live_session()
