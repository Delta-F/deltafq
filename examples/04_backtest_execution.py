"""Minimal example: run the backtest engine and execute the trades."""

import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from deltafq.data import DataFetcher
from deltafq.indicators import TechnicalIndicators
from deltafq.strategy import SignalGenerator
from deltafq.backtest import BacktestEngine


def main() -> None:
    fetcher = DataFetcher()
    indicators = TechnicalIndicators()
    generator = SignalGenerator()
    engine = BacktestEngine(initial_capital=10000, commission=0.0005) # default initial_capital=1000000, commission=0.001

    symbol = "AAPL"
    start_date = "2024-01-01"
    end_date = "2024-06-30"
    data = fetcher.fetch_data(symbol=symbol, start_date=start_date, end_date=end_date, clean=True)

    # Take BOLL as signal
    boll = indicators.boll(data["Close"], period=20, std_dev=2, method="population")
    signals = generator.boll_signals(price=data["Close"], bands=boll, method="touch")

    trades_df, values_df = engine.run_backtest(symbol=symbol, signals=signals, price_series=data["Close"], strategy_name="BOLL")

    print("Trades:")
    print(trades_df)
    print("\nPortfolio values:")
    print(values_df)


if __name__ == "__main__":
    main()