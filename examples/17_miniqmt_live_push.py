"""Minimal example: live push via DataGateway with source=miniqmt (xtquant / miniQMT)."""

import sys
import os
import time

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from deltafq.live.event_engine import EventEngine, EVENT_TICK
from deltafq.live.gateway_registry import create_data_gateway

# "poll" 轮询 | "push" 推送
MODE = "poll"


def main():
    event_engine = EventEngine()
    gateway = create_data_gateway("miniqmt", interval=5.0, mode=MODE)

    history_counts = {}

    def on_tick(t):
        if t.source == "miniqmt_warmup":
            history_counts[t.symbol] = history_counts.get(t.symbol, 0) + 1
            if history_counts[t.symbol] % 100 == 1:
                print(
                    f"[History] {t.symbol} loading... (count: {history_counts[t.symbol]})"
                )
        else:
            vol = t.volume if t.volume is not None else "-"
            src = t.source or ""
            px = f"{float(t.price):.3f}"
            print(
                f"[Live]    {t.symbol} -> {px} | Vol: {vol} "
                f"({t.timestamp.strftime('%H:%M:%S')}) [{src}]"
            )

    event_engine.on(EVENT_TICK, on_tick)
    gateway.set_tick_handler(lambda tick: event_engine.emit(EVENT_TICK, tick))

    if not gateway.connect():
        return

    gateway.start()

    symbols = ["000001.SZ", "600000.SH","159118.SZ"]
    print(f"\n>>> Subscribing to {symbols} (includes historical warm-up), mode={MODE!r}...")
    gateway.subscribe(symbols)

    ohlc = gateway.get_today_ohlc("000001.SZ")
    if ohlc:
        print(f"\n>>> Today's OHLC snapshot for 000001.SZ: {ohlc}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping system...")
        gateway.stop()
        print("Exited.")


if __name__ == "__main__":
    main()
