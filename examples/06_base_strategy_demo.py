"""Minimal BaseStrategy usage example (fetch data + generate signals)."""

import os
import sys
from typing import Any

import pandas as pd

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from deltafq.data import DataFetcher
from deltafq.strategy.base import BaseStrategy


class DemoStrategy(BaseStrategy):
    """Simple moving-average crossover strategy."""

    def __init__(self, fast_period: int = 5, slow_period: int = 20, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.fast_period = fast_period
        self.slow_period = slow_period

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        closes = data["Close"].astype(float)
        fast_ma = closes.rolling(window=self.fast_period, min_periods=1).mean()
        slow_ma = closes.rolling(window=self.slow_period, min_periods=1).mean()

        signals = pd.Series(0, index=closes.index, dtype=int)
        signals = signals.mask(fast_ma > slow_ma, 1)
        signals = signals.mask(fast_ma < slow_ma, -1)

        return signals


def run_strategy_demo() -> None:
    print("=== BaseStrategy Demo Strategy ===")

    fetcher = DataFetcher()
    strategy = DemoStrategy(name="DemoStrategy", fast_period=10, slow_period=30)

    data = fetcher.fetch_data(
        symbol="AAPL",
        start_date="2024-01-01",
        end_date="2024-06-30",
        clean=True,
    )

    result = strategy.run(data)
    signals = result["signals"]

    print(f"Strategy name: {result['strategy_name']}")
    print(f"Signals:\n{signals}")
    print(f"Buy count: {(signals == 1).sum()}")
    print(f"Sell count: {(signals == -1).sum()}")
    print(f"Hold count: {(signals == 0).sum()}")


if __name__ == "__main__":
    run_strategy_demo()
