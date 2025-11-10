"""
Minimal example: compare all custom indicators with TA-Lib equivalents.
"""

import os
import sys

import pandas as pd

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from deltafq.data import DataFetcher
from deltafq.indicators import TechnicalIndicators, TalibIndicators


def compare_series(name: str, custom_series: pd.Series, talib_series: pd.Series) -> None:
    diff = pd.DataFrame(
        {"custom": custom_series, "talib": talib_series, "diff": custom_series - talib_series}
    ).dropna().head()
    print(f"\n{name} (first rows)")
    print(diff)


def compare_frame(name: str, custom_df: pd.DataFrame, talib_df: pd.DataFrame) -> None:
    diff = custom_df.subtract(talib_df).dropna().head()
    print(f"\n{name} diff (first rows)")
    print(diff)


def main() -> None:
    fetcher = DataFetcher()
    data = fetcher.fetch_data(symbol="AAPL", start_date="2024-01-01", end_date="2024-01-31")

    close = data["Close"]
    high = data["High"]
    low = data["Low"]
    volume = data["Volume"]

    custom = TechnicalIndicators()
    talib = TalibIndicators()

    compare_series("SMA(14)", custom.sma(close, period=14), talib.sma(close, period=14))
    compare_series("EMA(14)", custom.ema(close, period=14, method="talib"), talib.ema(close, period=14))
    compare_series("RSI(14)", custom.rsi(close, period=14, method="rma"), talib.rsi(close, period=14))
    compare_frame(
        "KDJ(9,3,3)",
        custom.kdj(high, low, close, n=9, m1=3, m2=3, method="sma"),
        talib.kdj(high, low, close, n=9, m1=3, m2=3),
    )
    compare_frame(
        "BOLL(20,2)",
        custom.boll(close, period=20, std_dev=2, method="population"),
        talib.boll(close, period=20, std_dev=2),
    )
    compare_series(
        "ATR(14)",
        custom.atr(high, low, close, period=14, method="rma"),
        talib.atr(high, low, close, period=14),
    )
    compare_series("OBV", custom.obv(close, volume), talib.obv(close, volume))


if __name__ == "__main__":
    main()