import sys
import os
import time

# Setup project root path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from deltafq.live.event_engine import EventEngine, EVENT_TICK
from deltafq.live.gateway_registry import create_data_gateway

def main():
    # 1. Initialize engine and gateway
    event_engine = EventEngine()
    gateway = create_data_gateway("yfinance", interval=5.0)
    
    # 2. Setup handlers: engine for printing, gateway for emitting
    event_engine.on(EVENT_TICK, lambda t: print(f"[EventBus] Tick -> {t.symbol}: {t.price} ({t.volume}) ({t.timestamp.strftime('%H:%M:%S')})"))
    gateway.set_tick_handler(lambda tick: event_engine.emit(EVENT_TICK, tick))
    
    # 3. Connect and start polling thread
    if not gateway.connect():
        print("Connection failed, please check network.")
        return
        
    gateway.start()
    
    # 4. Demo dynamic subscription
    print("\n>>> Subscribing: 000001.SS")
    gateway.subscribe(["000001.SS"])
    print(f"symbols: {gateway._symbols}")
    
    time.sleep(10) # Run for 10 seconds
    
    print("\n>>> Dynamically subscribing: 000300.SS")
    gateway.subscribe(["000300.SS"])
    print(f"symbols: {gateway._symbols}")
    
    # 5. Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping system...")
        gateway.stop()
        print("Exited.")

if __name__ == "__main__":
    main()
    # Output Example:
    """
    [10:12:50] YFinanceDataGateway   >>> INFO     >>> Initialized YFinanceDataGateway with interval: 5.0s
    [10:12:50] YFinanceDataGateway   >>> INFO     >>> Connecting to yfinance API...
    [10:12:52] YFinanceDataGateway   >>> INFO     >>> Connection successful
    [10:12:52] YFinanceDataGateway   >>> INFO     >>> Starting yfinance polling thread
    
    >>> Subscribing: 000001.SS
    [10:12:52] YFinanceDataGateway   >>> INFO     >>> Subscribed to 000001.SS
    symbols: ['000001.SS']
    [EventBus] Tick -> 000001.SS: 4145.4501953125 (3722420116) (10:12:55)

    >>> Dynamically subscribing: 000300.SS
    [10:13:02] YFinanceDataGateway   >>> INFO     >>> Subscribed to 000300.SS
    symbols: ['000001.SS', '000300.SS']
    [EventBus] Tick -> 000001.SS: 4145.4501953125 (3722420116) (10:13:11)
    [EventBus] Tick -> 000300.SS: 4718.44970703125 (3598123204) (10:13:12)
    [EventBus] Tick -> 000001.SS: 4146.8525390625 (3830388816) (10:13:18)
    [EventBus] Tick -> 000300.SS: 4718.44970703125 (3598123204) (10:13:19)
    """
