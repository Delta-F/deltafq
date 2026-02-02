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
    history_counts = {}

    def on_tick(t):
        if t.source == "yf_warmup":
            # Summary display for historical data to avoid console flooding
            history_counts[t.symbol] = history_counts.get(t.symbol, 0) + 1
            if history_counts[t.symbol] % 100 == 1:  # Print every 100th bar as a progress indicator
                print(f"[History] {t.symbol} loading... (count: {history_counts[t.symbol]})")
        else:
            # Simulate real-time data update
            print(f"[Live]    {t.symbol} -> {t.price} | Vol: {t.volume} ({t.timestamp.strftime('%H:%M:%S')})")

    event_engine.on(EVENT_TICK, on_tick)
    gateway.set_tick_handler(lambda tick: event_engine.emit(EVENT_TICK, tick))
    
    # 3. Connect and start
    if not gateway.connect():
        return
        
    gateway.start()
    
    # 4. Subscribe: This will trigger the _warm_up sequence first
    symbols = ["000001.SS", "GOOGL", "BTC-USD"]
    print(f"\n>>> Subscribing to {symbols} (includes historical warm-up)...")
    gateway.subscribe(symbols)
    
    # 5. Get today's OHLC (example)
    ohlc = gateway.get_today_ohlc("GOOGL")
    if ohlc:
        print(f"\n>>> Today's OHLC for GOOGL: {ohlc}")
    
    # 6. Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping system...")
        gateway.stop()
        print("Exited.")

if __name__ == "__main__":
    main()