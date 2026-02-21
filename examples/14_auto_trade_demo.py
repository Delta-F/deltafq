"""Minimal demo: strategy automation — 5m signal every 5 min, daily signal once per day."""

import os
import sys
import time
from datetime import datetime

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pandas as pd
from deltafq.data import DataFetcher, DataStorage
from deltafq.strategy.base import BaseStrategy
from deltafq.trader.engine import ExecutionEngine


class SimpleMAStrategy(BaseStrategy):
    def __init__(self, fast_period: int = 5, slow_period: int = 20, **kwargs):
        super().__init__(**kwargs)
        self.fast_period = fast_period
        self.slow_period = slow_period

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        closes = data["Close"].astype(float)
        fast_ma = closes.rolling(window=self.fast_period, min_periods=1).mean()
        slow_ma = closes.rolling(window=self.slow_period, min_periods=1).mean()
        signals = pd.Series(0, index=closes.index, dtype=int)
        signals = signals.mask(fast_ma > slow_ma, 1).mask(fast_ma < slow_ma, -1)
        return signals


def run_signal(fetcher, strategy, symbol, start, end, interval, storage=None):
    data = fetcher.fetch_data(symbol, start, end, clean=True, interval=interval)
    if storage is not None and not data.empty:
        storage.save_price_data(data, symbol, start, end)
    if data.empty or len(data) < 2:
        return 0, None
    strategy.run(data)
    return int(strategy.signals.iloc[-1]), float(data["Close"].iloc[-1])


def try_trade(engine, symbol, signal, price, qty, now):
    if signal == 1 and price:
        buy_qty = min(qty, int(engine.cash / (price * (1 + engine.commission))))
        if buy_qty > 0:
            engine.execute_order(symbol, buy_qty, "limit", price=price, timestamp=now)
    elif signal == -1 and price:
        pos = engine.position_manager.get_position(symbol)
        if pos > 0:
            engine.execute_order(symbol, -pos, "limit", price=price, timestamp=now)


def main():
    symbol = "000001.SS"
    fetcher = DataFetcher()
    storage = DataStorage()
    engine = ExecutionEngine(broker=None, initial_capital=100_000, commission=0.001, match_on_tick=False)
    engine.initialize()
    qty = 100
    # (interval, strategy, start, end, daily_only)
    tasks = [
        ("5m", SimpleMAStrategy(name="MA5m", fast_period=3, slow_period=8), "2026-02-01", "2026-02-14", False),
        ("1d", SimpleMAStrategy(name="MA1d", fast_period=5, slow_period=20), "2025-08-01", "2026-02-21", True),
    ]
    last_day_done = None

    while True:
        now = datetime.now()
        for interval, strategy, start, end, daily_only in tasks:
            if daily_only and last_day_done == now.date():
                continue
            s, p = run_signal(fetcher, strategy, symbol, start, end, interval, storage)
            print(now.isoformat(), interval, s)
            try_trade(engine, symbol, s, p, qty, now)
            if daily_only:
                last_day_done = now.date()
        time.sleep(5 * 60)


if __name__ == "__main__":
    main()
