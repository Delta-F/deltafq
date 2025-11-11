"""
Minimal example: generate signals from technical indicators.
"""

import os
import sys

import pandas as pd

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from deltafq.data import DataFetcher
from deltafq.indicators import TechnicalIndicators
from deltafq.strategy import SignalGenerator


def main() -> None:
    fetcher = DataFetcher()
    indicators = TechnicalIndicators()
    signals = SignalGenerator()

    data = fetcher.fetch_data(symbol="AAPL", start_date="2024-01-01", end_date="2024-03-31", clean=True)

    close = data["Close"]
    high = data["High"]
    low = data["Low"]
    volume = data["Volume"]

    sma_fast = indicators.sma(close, period=10)
    sma_slow = indicators.sma(close, period=20)
    ema = indicators.ema(close, period=20)
    rsi = indicators.rsi(close, period=14, method="rma")
    kdj = indicators.kdj(high, low, close, n=9, m1=3, m2=3, method="sma")
    boll = indicators.boll(close, period=20, std_dev=2, method="population")
    obv = indicators.obv(close, volume)

    signal_table = pd.DataFrame({
        "sma": signals.sma_signals(sma_fast, sma_slow),
        "ema": signals.ema_signals(close, ema),
        "rsi": signals.rsi_signals(rsi),
        "kdj": signals.kdj_signals(kdj),
        "boll_touch": signals.boll_signals(close, boll, method="touch"),
        "boll_cross": signals.boll_signals(close, boll, method="cross"),
        "obv": signals.obv_signals(obv),
    })

    signal_table["combined"] = signals.combine_signals(
        {
            "sma": signal_table["sma"],
            "ema": signal_table["ema"],
            "rsi": signal_table["rsi"],
            "kdj": signal_table["kdj"],
            "boll_cross": signal_table["boll_cross"],
            "boll_touch": signal_table["boll_touch"],
            "obv": signal_table["obv"],
        },
        method="vote",
    )

    print(signal_table)


if __name__ == "__main__":
    main()
