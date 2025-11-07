"""
Backtest result with performance chart and performance report.
"""

import os
import sys
import pandas as pd

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from deltafq.data import DataFetcher
from deltafq.indicators import TechnicalIndicators
from deltafq.strategy import SignalGenerator
from deltafq.backtest import BacktestEngine, PerformanceReporter

# Initialize components
fetcher = DataFetcher()
engine = BacktestEngine(initial_capital=1000000, commission=0.001)
performance_report = PerformanceReporter()

# Fetch data
symbol = '601398.SS'
benchmark = '000001.SS'
start_date = '2025-06-01'
end_date = '2025-10-30'
data = fetcher.fetch_data(symbol, start_date, end_date, clean=True)
benchmark_data = fetcher.fetch_data(benchmark, start_date, end_date, clean=True)

indicators = TechnicalIndicators()
generator = SignalGenerator()

bbands = indicators.boll(data['Close'], period=5, std_dev=1.5)
signals = generator.boll_signals(price=data['Close'], bands=bbands, method='touch')

trades_df, values_df = engine.run_backtest(symbol, signals, data['Close'], strategy_name='BOLL')
print(values_df)

performance_report.print_summary(
    symbol=symbol,
    trades_df=trades_df,
    values_df=values_df,
    title='策略回测报告',
    language='zh'
)