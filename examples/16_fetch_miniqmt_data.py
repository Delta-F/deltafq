"""
Minimal example: fetch A-share OHLCV via DataFetcher with source=miniqmt (xtquant / miniQMT).

Requires a running miniQMT client and the xtquant package on PYTHONPATH.
Symbol must be xt-style, e.g. 000001.SZ, 600000.SH.
"""

import os
import sys
import time
from datetime import datetime

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from deltafq.data import DataFetcher, DataStorage
from deltafq.data.miniqmt_xtdata import import_xtdata


def demo_fetch_history() -> None:
    """Fetch daily bars and save to local cache."""
    symbol = "000001.SZ"
    start_date = "2026-04-01"
    end_date = "2026-04-16"

    fetcher = DataFetcher(source="miniqmt")
    data = fetcher.fetch_data(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        interval="1m",
    )
    storage = DataStorage()
    path = storage.save_price_data(data, symbol=symbol, start_date=start_date, end_date=end_date)

    print(data.head())
    print(f"Saved to: {path}")


def demo_realtime_quote() -> None:
    """Poll real-time snapshot via xtdata.get_full_tick."""
    symbol = "000001.SZ" # 平安银行
    xtdata = import_xtdata()

    print(f"Realtime quote test: {symbol} (10 snapshots)")
    for i in range(10):
        tick = (xtdata.get_full_tick([symbol]) or {}).get(symbol) or {}
        last = tick.get("lastPrice") or tick.get("last") or tick.get("price")
        volume = tick.get("volume")
        ts_raw = tick.get("time")
        ts_text = ts_raw
        if ts_raw:
            try:
                ts_num = int(ts_raw)
                if ts_num > 10**12:  # ms timestamp
                    ts_num = ts_num / 1000
                ts_text = datetime.fromtimestamp(ts_num).strftime("%Y-%m-%d %H:%M:%S")
            except (TypeError, ValueError):
                pass
        print(f"[{i + 1}/10] last={last} volume={volume} time={ts_text}")
        time.sleep(1)


if __name__ == "__main__":
    # demo_fetch_history()
    demo_realtime_quote()
