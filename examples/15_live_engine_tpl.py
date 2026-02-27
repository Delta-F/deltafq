"""Minimal LiveEngine demo: set symbol/params -> add_strategy -> run_live. Capital/commission come from trade gateway (e.g. paper)."""

import sys
import os
import time

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pandas as pd
from deltafq.live import LiveEngine
from deltafq.strategy.base import BaseStrategy


class Every2BarFlipStrategy(BaseStrategy):
    """Every 2 strategy runs (each run = new bars) flip signal 1 / -1 for quick verification of matching."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._run_count = 0

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        self._run_count += 1
        sig = 1 if (self._run_count // 2) % 2 == 0 else -1
        n = len(data)
        return pd.Series([sig] * n, index=data.index)


def main():
    # Use a symbol with reliable 5m data on Yahoo (e.g. AAPL, BTC-USD). For 000001.SS use signal_interval="1d".
    engine = LiveEngine(
        symbol="BTC-USD",
        interval=10.0,
        lookback_bars=50,
        signal_interval="5m",
    )
    engine.set_trade_gateway("paper", initial_capital=880_000)
    engine.add_strategy(Every2BarFlipStrategy(name="Every2Flip"))
    engine.run_live()
    
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        engine.stop()
    
    # Paper gateway: positions and trades live on the trade gateway's execution engine
    if engine._trade_gw is not None:
        eng = engine._trade_gw._engine
        print("Positions:", eng.position_manager.get_all_positions())
        print("Trades:", len(eng.trades))


if __name__ == "__main__":
    main()
