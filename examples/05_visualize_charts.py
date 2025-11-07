"""
Visualize charts for the Bollinger Bands strategy.
"""

import os
import sys
import pandas as pd

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from deltafq.data import DataFetcher
from deltafq.charts import PerformanceChart, PriceChart, SignalChart
from deltafq.indicators import TechnicalIndicators
from deltafq.strategy import SignalGenerator
from deltafq.backtest import BacktestEngine, PerformanceReporter

# Initialize components
fetcher = DataFetcher()
price_chart = PriceChart()
engine = BacktestEngine(initial_capital=1000000, commission=0.001)
performance_chart = PerformanceChart()
performance_report = PerformanceReporter()

# Fetch data
symbol = '601398.SS'
benchmark = '000001.SS'
start_date = '2025-06-01'
end_date = '2025-10-30'
data = fetcher.fetch_data(symbol, start_date, end_date, clean=True)
benchmark_data = fetcher.fetch_data(benchmark, start_date, end_date, clean=True)

# Plot price chart
# data_dict = {symbol: data, benchmark: benchmark_data}
# price_chart.plot_prices(data_dict, normalize=True, title='Price Chart', use_plotly=True)
# price_chart.plot_prices(data_dict, normalize=False, title='Price Chart', use_plotly=True)

# Plot Signal Chart
signal_chart = SignalChart()
indicators = TechnicalIndicators()
generator = SignalGenerator()

bbands = indicators.boll(data['Close'], period=5, std_dev=1.5)
signals = generator.boll_signals(price=data['Close'], bands=bbands, method='touch')

# signal_chart.plot_boll_signals(data, bbands, signals, title="Signal Demo", use_plotly=True)
# signal_chart.plot_boll_signals(data, bbands, signals, title="Signal Demo", use_plotly=False)

# Plot Performance Chart 
trades_df, values_df = engine.run_backtest(symbol, signals, data['Close'], strategy_name='BOLL')
print(values_df)

performance_chart = PerformanceChart()
performance_chart.plot_backtest_charts(values_df=values_df, benchmark_close=benchmark_data['Close'], title="Performance Demo")
performance_chart.plot_backtest_charts(values_df=values_df, benchmark_close=benchmark_data['Close'], title="Performance Demo", use_plotly=True)