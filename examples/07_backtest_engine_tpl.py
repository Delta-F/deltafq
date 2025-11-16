"""Minimal BacktestEngine usage example."""

import os
import sys
from typing import Any

import pandas as pd

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from deltafq.backtest import BacktestEngine
from deltafq.strategy.base import BaseStrategy


class SimpleMAStrategy(BaseStrategy):
    """Simple moving-average crossover strategy."""

    def __init__(self, fast_period: int = 5, slow_period: int = 20, **kwargs: Any) -> None:
        super().__init__(name="SimpleMA", **kwargs)
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


def main() -> None:
    # initialize backtest engine
    engine = BacktestEngine()
    
    # set parameters
    engine.set_parameters(
        symbol="AAPL",
        start_date="2024-01-01",
        end_date="2024-06-30",
        benchmark="SPY"
    )
    
    # load data
    engine.load_data()    
    # add strategy
    strategy = SimpleMAStrategy(fast_period=10, slow_period=30)
    engine.add_strategy(strategy)
    # run backtest
    engine.run_backtest()
    # calculate metrics
    engine.calculate_metrics()
    # show report
    engine.show_report()
    # show chart
    engine.show_chart(use_plotly=True)
    # save backtest results
    engine.save_backtest_results()
    
    # print results
    print("Data:")
    print(pd.DataFrame(engine.data))
    print("Trades:")
    print(pd.DataFrame(engine.trades_df))
    print("Values:")
    print(pd.DataFrame(engine.values_df))
    print("Metrics:")
    print(pd.DataFrame([engine.metrics]).T)


if __name__ == "__main__":
    main()

