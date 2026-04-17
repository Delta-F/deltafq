"""
Minimal example: fetch A-share OHLCV via DataFetcher with source=miniqmt (xtquant / miniQMT).
"""

import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from deltafq.data import DataFetcher, DataStorage

# 需本机启动 miniQMT、已安装 xtquant；标的为 xt 代码，如 000001.SZ、600000.SH

def main() -> None:
    symbol = "600000.SH"
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
    print(data)
    print(f"Saved to: {path}")


if __name__ == "__main__":
    main()
