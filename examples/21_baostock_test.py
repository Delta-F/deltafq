"""baostock 测试入口。需: pip install baostock"""

import sys
import os
import time

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from deltafq.adapters.data.baostock_bars import to_bs_code
from deltafq.data import DataFetcher
from deltafq.live import create_data_gateway


def main() -> None:
    assert to_bs_code("600000.SH") == "sh.600000"
    # 历史日线
    print(DataFetcher(source="baostock").fetch_data("sh.600000", "2024-01-01", "2024-01-10").head())

    # 实时：暖机后持续轮询（Ctrl+C 退出）
    gw = create_data_gateway("baostock", interval=5.0)
    gw.set_tick_handler(lambda t: print(f"[{t.source}] {t.symbol} {t.price} {t.timestamp}"))
    assert gw.connect()
    gw.subscribe(["sh.600000"])
    print("today_ohlc:", gw.get_today_ohlc("sh.600000"))
    gw.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        gw.stop()


if __name__ == "__main__":
    main()
