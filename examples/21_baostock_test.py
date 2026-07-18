"""baostock 测试入口（相关用例集中于此）。需: pip install baostock"""

import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from deltafq.adapters.data.baostock_bars import to_bs_code
from deltafq.data import DataFetcher


def main() -> None:
    # 代码：baostock 原生 / xt 风格均可
    assert to_bs_code("600000.SH") == "sh.600000"

    # 日线 OHLCV（end_date 排他，与 yahoo 一致）
    data = DataFetcher(source="baostock").fetch_data(
        "sh.600000", "2024-01-01", "2024-01-10", interval="1d"
    )
    print(data.head())


if __name__ == "__main__":
    main()
