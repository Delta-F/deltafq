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
from deltafq.charts import PriceChart, PerformanceChart
from deltafq.indicators import TechnicalIndicators
from deltafq.strategy import SignalGenerator
from deltafq.trading.simulator import PaperTradingSimulator
from deltafq.backtest.performance import PerformanceAnalyzer
from deltafq.backtest.reporter import BacktestReporter

# 初始化组件
fetcher = DataFetcher()
chart = PriceChart()
perf_chart = PerformanceChart()
indicators = TechnicalIndicators()
generator = SignalGenerator()
sim = PaperTradingSimulator(initial_capital=1000000, commission=0.001)
perf = PerformanceAnalyzer()
rep = BacktestReporter()

# 获取标的与基准数据：工商银行A股(601398.SS)，沪深300ETF(510300.SS)
symbol = '601398.SS'         # 工商银行 A 股（上海）
benchmark_symbol = '000300.SS'  # 沪深300指数
start_date = '2023-01-01'
end_date = '2025-10-30'

data = fetcher.fetch_stock_data(symbol, start_date, end_date, clean=True)
benchmark = fetcher.fetch_stock_data(benchmark_symbol, start_date, end_date, clean=True)

# 可视化价格数据
# data_dict = {symbol: data, benchmark_symbol: benchmark}
# chart.plot_normalized_price(data_dict, symbols=[symbol, benchmark_symbol])

# 计算技术指标：Boll
bollinger_bands = indicators.bollinger_bands(data['Close'], period=5, std_dev=1.5)
data_bollinger_bands = pd.concat([data, bollinger_bands], axis=1)
to_csv = data_bollinger_bands.to_csv('data_bollinger_bands.csv', index=False)

# quit()

# 生成布林带信号
signals = generator.bollinger_bands_signals(
    data=data,
    method='cross', # 'touch', 'breakout', 'mean_reversion'
    period=5,
    std_dev=1.5
)
print(signals[signals!=0])

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
trades_df, values_df = sim.run_signals(
    symbol=symbol,
    signals=signals,              # Series
    price_series=data['Close'],   # 补充价格
    save_csv=True
)
print(f"Trades: {trades_df}, Values: {values_df}")
      
      
# 计算性能指标
values_df, metrics = perf.run_backtest_metrics(
    symbol=symbol,
    trades_df=trades_df,
    values_df=values_df,
    initial_capital=sim.initial_capital
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