"""
Strategy test example using local DeltaFQ modules.
"""

import sys
import os

# 将项目根目录添加到 sys.path 的最前面，确保优先使用本地代码
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 从本地项目模块导入
import pandas as pd
from deltafq.data.fetcher import DataFetcher
from deltafq.charts import PriceChart, PerformanceChart, price
from deltafq.indicators import TechnicalIndicators
from deltafq.strategy import SignalGenerator
from deltafq.backtest.engine import BacktestEngine
from deltafq.backtest.performance import PerformanceAnalyzer
from deltafq.backtest.reporter import BacktestReporter
import warnings
warnings.filterwarnings('ignore')

# 初始化组件
fetcher = DataFetcher()
chart = PriceChart()
perf_chart = PerformanceChart()
indicators = TechnicalIndicators()
generator = SignalGenerator()
engine = BacktestEngine(initial_capital=1000000, commission=0.001)
perf = PerformanceAnalyzer()
rep = BacktestReporter()

# 获取标的与基准数据：工商银行A股(601398.SS)，沪深300ETF(510300.SS)
symbol = '601398.SS'
benchmark_symbol = '000300.SS'
start_date = '2025-01-08'
end_date = '2025-10-30'

data = fetcher.fetch_data(symbol, start_date, end_date, clean=True)
benchmark = fetcher.fetch_data(benchmark_symbol, start_date, end_date, clean=True)

# 可视化价格数据
# data_dict = {symbol: data, benchmark_symbol: benchmark}
# chart.plot_prices(data_dict,normalize=True,base_value=100)

# 计算技术指标：Boll
# bollinger_bands = indicators.bollinger_bands(data['Close'], period=5, std_dev=1.5)
# data_boll = pd.concat([data, bollinger_bands], axis=1)
# print(data_boll.head(20))

# 生成布林带信号
signals = generator.bollinger_bands_signals(
    data=data,
    method='cross',
    period=5,
    std_dev=1.5
)
# print(signals[signals!=0])

# 技术指标与交易信号可视化
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

# 执行回测：全仓进出
trades_df, values_df = engine.run_backtest(
    symbol=symbol,
    signals=signals,
    price_series=data['Close'],
    strategy_name=f'{symbol} Bollinger Bands Strategy',
    save_csv=True
)
print(f"Trades: {trades_df}, Values: {values_df}")

# 计算性能指标
values_df, metrics = perf.calculate_metrics(
    symbol=symbol,
    trades_df=trades_df,
    values_df=values_df,
    initial_capital=engine.initial_capital
)

# 生成报告
summary = rep.generate_summary_report(metrics, title=f'{symbol} Bollinger Bands Strategy')
print(summary)

# 可视化回测结果
fig = perf_chart.plot_backtest_charts(
    values_df=values_df,
    benchmark_close=benchmark['Close'],
    title=f'{symbol} Bollinger Bands Strategy Performance'
)