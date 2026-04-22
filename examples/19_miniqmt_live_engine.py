"""Minimal example: LiveEngine + miniQMT 行情/交易；策略按次循环输出信号 0, 1, -1。"""

import os
import sys
import time

import pandas as pd

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from deltafq.live import LiveEngine
from deltafq.strategy.base import BaseStrategy

MIN_PATH = os.environ.get("QMT_USERDATA_MINI", r"D:\国金证券QMT交易端\userdata_mini")
ACCOUNT_ID = os.environ.get("QMT_ACCOUNT_ID", "8886180407")


class DemoStrategy(BaseStrategy):
    """信号按次循环输出：0 → 1 → -1 → 0 → …；order_quantity 统一买卖股数上限。"""

    _SEQ = (0, 1, -1)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.order_quantity = 100
        self._i = 0

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        sig = self._SEQ[self._i % len(self._SEQ)]
        self._i += 1
        return pd.Series([sig] * len(data), index=data.index)


def main() -> None:
    engine = LiveEngine(
        symbol="159118.SZ",
        interval=5.0,
        lookback_bars=10,
        signal_interval="1m",
        data_gateway_name="miniqmt",
        trade_gateway_name="miniqmt",
    )
    engine.set_data_gateway("miniqmt", interval=5.0, mode="poll")
    engine.set_trade_gateway(
        "miniqmt",
        userdata_mini_path=MIN_PATH,
        account_id=ACCOUNT_ID,
        strategy_name="deltafq_order_amount_demo",
        lot_size=100,
    )
    engine.add_strategy(DemoStrategy(name="SeqNeg010"))

    engine.run_live()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        engine.stop()


if __name__ == "__main__":
    main()
