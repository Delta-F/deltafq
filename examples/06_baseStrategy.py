"""Minimal example: run a BaseStrategy subclass through BacktestEngine."""

import os
import sys
from dataclasses import dataclass

import pandas as pd

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from deltafq.data import DataFetcher
from deltafq.strategy.base import BaseStrategy
from deltafq.backtest.engine import BacktestEngine


@dataclass
class SMACrossoverStrategy(BaseStrategy):
    fast_period: int = 5
    slow_period: int = 20

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        closes = data["Close"].astype(float)
        fast = closes.rolling(self.fast_period, min_periods=1).mean()
        slow = closes.rolling(self.slow_period, min_periods=1).mean()

        signal = pd.Series(0, index=closes.index, dtype=int)
        signal = signal.mask(fast > slow, 1)
        signal = signal.mask(fast < slow, -1)

        return pd.DataFrame({"Signal": signal})


def main() -> None:
    fetcher = DataFetcher()
    engine = BacktestEngine() # initial_capital=200_000, commission=0.001
    strategy = SMACrossoverStrategy(name="SMA_Crossover")

    symbol = "AAPL"
    start_date = "2024-01-01"
    end_date = "2024-06-30"

    data = fetcher.fetch_data(symbol=symbol, start_date=start_date, end_date=end_date, clean=True)

    result = strategy.run(data)
    signals = result["signals"]["Signal"]

    trades_df, values_df = engine.run_backtest(
        symbol=symbol,
        signals=signals,
        price_series=data["Close"],
        strategy_name=strategy.name,
    )

    print("Backtest complete.")
    print("Trades:")
    print(trades_df.tail())
    print("Portfolio values:")
    print(values_df.tail())


if __name__ == "__main__":
    main()

