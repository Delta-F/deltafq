"""miniQMT 分笔推送示例：需本机启动 miniQMT 且已安装 xtquant。仅开盘时间有持续推送。"""

import os
import sys
from datetime import datetime

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from deltafq.data.miniqmt_xtdata import import_xtdata

SYMBOL = "000001.SZ"

xtdata = import_xtdata()


def _fmt_ts(ms: object) -> str:
    if ms is None:
        return ""
    try:
        x = float(ms)
        if x > 1e12:
            x /= 1000.0
        return datetime.fromtimestamp(x).strftime("%Y-%m-%d %H:%M:%S")
    except (TypeError, ValueError, OSError):
        return str(ms)


def on_data(datas: dict) -> None:
    for code, rows in datas.items():
        for row in rows or []:
            if not isinstance(row, dict):
                print(code, row)
                continue
            bid1 = (row.get("bidPrice") or [None])[0]
            ask1 = (row.get("askPrice") or [None])[0]
            print(
                f"{code}\t{_fmt_ts(row.get('time'))}\t"
                f"最新 {row.get('lastPrice')}\t量 {row.get('volume')}\t额 {row.get('amount')}\t"
                f"买一 {bid1}\t卖一 {ask1}"
            )


def main() -> None:
    seq = xtdata.subscribe_quote(SYMBOL, period="tick", start_time="", end_time="", count=0, callback=on_data)
    if seq < 0:
        sys.exit(f"subscribe_quote failed: {seq}")

    try:
        xtdata.run()
    except KeyboardInterrupt:
        pass
    finally:
        xtdata.unsubscribe_quote(seq)

if __name__ == "__main__":
    main()
    """
    输出示例：
    000001.SZ       2026-04-17 09:36:51     最新 11.08      量 38311        额 42440871.0   买一 11.08      卖一 11.09
    000001.SZ       2026-04-17 09:36:54     最新 11.08      量 38721        额 42895181.0   买一 11.08      卖一 11.09
    000001.SZ       2026-04-17 09:36:57     最新 11.08      量 38848        额 43035902.0   买一 11.08      卖一 11.09
    000001.SZ       2026-04-17 09:37:00     最新 11.08      量 39150        额 43370518.0   买一 11.08      卖一 11.09
    """