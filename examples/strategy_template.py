"""
Strategy test example using local DeltaFQ modules.
"""

import sys
import os

# Add project root to sys.path to use local DeltaFQ modules.
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import local DeltaFQ modules.
import pandas as pd
from deltafq.data import DataFetcher
from deltafq.charts import PriceChart, PerformanceChart, price
from deltafq.indicators import TechnicalIndicators
from deltafq.strategy import SignalGenerator
from deltafq.backtest import BacktestEngine
from deltafq.backtest import PerformanceAnalyzer
from deltafq.backtest import BacktestReporter
import warnings
warnings.filterwarnings('ignore')

# Initialize components.
fetcher = DataFetcher()
chart = PriceChart()
perf_chart = PerformanceChart()
indicators = TechnicalIndicators()
generator = SignalGenerator()
engine = BacktestEngine(initial_capital=1000000, commission=0.001)
perf = PerformanceAnalyzer()
rep = BacktestReporter()

# Get target and benchmark data: Industrial Bank A-shares (601398.SS), CSI 300 ETF (510300.SS)
symbol = '601398.SS'
# benchmark_symbol = '000300.SS'
start_date = '2025-01-01'
end_date = '2025-10-30'

data = fetcher.fetch_data(symbol, start_date, end_date, clean=True)
# benchmark = fetcher.fetch_data(benchmark_symbol, start_date, end_date, clean=True)

# Visualize price data.
# data_dict = {symbol: data, benchmark_symbol: benchmark, 'SPY': fetcher.fetch_data('SPY', start_date, end_date, clean=True)}
# chart.plot_prices(data_dict,normalize=True,base_value=100)

# Generate Bollinger Bands signals (precompute indicators first).
bollinger_bands = indicators.boll(data['Close'], period=5, std_dev=1.5)
signals = generator.bollinger_bands_signals(data['Close'], bollinger_bands, method='cross')
print(signals[signals!=0])
quit()
# Visualize technical indicators and trading signals.
# chart.plot_signals(
#     data=data,
#     signals=signals,
#     indicators={
#         'BB_upper': bollinger_bands['upper'],
#         'BB_middle': bollinger_bands['middle'],
#         'BB_lower': bollinger_bands['lower']
#     },
#     title=f'{symbol} Trading Signals with Bollinger Bands'
# )

# Execute backtest: all-in-all-out.
trades_df, values_df = engine.run_backtest(
    symbol=symbol,
    signals=signals,
    price_series=data['Close'],
    strategy_name=f'{symbol} Bollinger Bands Strategy',
    save_csv=True
)
print(f"Trades: {trades_df}, Values: {values_df}")

# Calculate performance metrics.
values_df, metrics = perf.calculate_metrics(
    symbol=symbol,
    trades_df=trades_df,
    values_df=values_df,
    initial_capital=engine.initial_capital
)

# Generate report.
summary = rep.generate_summary_report(metrics, title=f'{symbol} Bollinger Bands Strategy')
print(summary)

# Visualize backtest results.
fig = perf_chart.plot_backtest_charts(
    values_df=values_df,
    benchmark_close=benchmark['Close'],
    title=f'{symbol} Bollinger Bands Strategy Performance'
)