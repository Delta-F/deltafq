"""
Simple Bollinger Bands strategy backtest and report generation.
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
from deltafq.backtest import BacktestEngine, PerformanceAnalyzer, BacktestReporter

# Initialize components
fetcher = DataFetcher()
indicators = TechnicalIndicators()
generator = SignalGenerator()
engine = BacktestEngine(initial_capital=1000000, commission=0.001)
analyzer = PerformanceAnalyzer()
reporter = BacktestReporter()

# Fetch data
symbol = '518880.SS'
start_date = '2025-01-01'
end_date = '2025-10-30'
data = fetcher.fetch_data(symbol, start_date, end_date, clean=True)

# Generate Bollinger Bands and signals
bands = indicators.boll(data['Close'], period=5, std_dev=1.5)
signals = generator.boll_signals(price=data['Close'], bands=bands, method='cross')

# Save Close, Bollinger Bands and signals for inspection
# inspect_df = pd.DataFrame({
#     'Close': data['Close'],
#     'BB_upper': bands['upper'],
#     'BB_middle': bands['middle'],
#     'BB_lower': bands['lower'],
#     'signal': signals,
# })
# inspect_df.to_csv(f"{symbol}_bbands_signals.csv", encoding='utf-8-sig')

# Run backtest
trades_df, values_df = engine.run_backtest(
    symbol=symbol,
    signals=signals,
    price_series=data['Close'],
    strategy_name=f'{symbol} Bollinger Bands Strategy'
)

# Calculate performance metrics
values_df, metrics = analyzer.get_performance_metrics(
    symbol=symbol,
    trades_df=trades_df,
    values_df=values_df,
    initial_capital=engine.initial_capital
)

# Generate visual report
reporter.generate_visual_report(
    metrics=metrics,
    values_df=values_df,
    benchmark_close=data['Close'],
    title=f'{symbol} Bollinger Bands Strategy',
    language='en'
)

