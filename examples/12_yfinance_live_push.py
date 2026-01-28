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
    
    # 2. Setup handlers: simulate frontend/backend data processing
    def on_tick(t):
        if t.source == "yf_warmup":
            # Simulate historical data loading (to fill charts)
            print(f"[History] {t.symbol} -> {t.price} ({t.timestamp.strftime('%H:%M')})")
        else:
            # Simulate real-time data update
            print(f"[Live]    {t.symbol} -> {t.price} ({t.timestamp.strftime('%H:%M:%S')})")

    event_engine.on(EVENT_TICK, on_tick)
    gateway.set_tick_handler(lambda tick: event_engine.emit(EVENT_TICK, tick))
    
    # 3. Connect and start
    if not gateway.connect():
        return
        
    gateway.start()
    
    # 4. Subscribe: This will trigger the _warm_up sequence first
    symbol = "BTC-USD"
    print(f"\n>>> Subscribing to {symbol} (includes historical warm-up)...")
    gateway.subscribe([symbol])
    
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
    [10:15:01] YFinanceDataGateway   >>> INFO     >>> Subscribed to BTC-USD
    [10:15:01] YFinanceDataGateway   >>> INFO     >>> Warming up BTC-USD with intraday history...
    [History] BTC-USD -> 102450.5 (00:01)
    [History] BTC-USD -> 102460.2 (00:02)
    ... (pushed today's history points) ...
    [10:15:03] YFinanceDataGateway   >>> INFO     >>> Warm-up complete for BTC-USD: 615 bars pushed
    
    [Live]    BTC-USD -> 103120.5 (10:15:05)
    [Live]    BTC-USD -> 103125.1 (10:15:10)
    """
