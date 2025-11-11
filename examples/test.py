# test the data fetcher

import os
import sys
# 如何确保引用的是本地项目的最新测试库，而非pip install安装的库
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 引用本地库中的datafetcher类
from deltafq.data import DataFetcher

symbol = "AAPL"
benchmark = "^GSPC"
start_date = "2024-01-01"
end_date = "2024-06-30"

# 01 test the data fetcher
fetcher = DataFetcher()
data = fetcher.fetch_data(symbol=symbol, start_date=start_date, end_date=end_date, clean=True)
benchmark_data = fetcher.fetch_data(symbol=benchmark, start_date=start_date, end_date=end_date)
# print(data)

# # 02 test the indicators
from deltafq.indicators import TechnicalIndicators
indicators = TechnicalIndicators()
# # sma_10 = indicators.sma(data["Close"], period=10)
# # sma_20 = indicators.sma(data["Close"], period=20)
boll = indicators.boll(data["Close"], period=20, std_dev=2, method="population")
# # print(sma)
# # print(boll)

# # 03 test the signals
from deltafq.strategy import SignalGenerator
signals = SignalGenerator()
# # sma_signals = signals.sma_signals(sma_10, sma_20)
boll_signals = signals.boll_signals(data["Close"], boll, method="touch")
# # print(sma_signals)
# print(boll_signals)

# # 04 test the backtest engine  
from deltafq.backtest import BacktestEngine,PerformanceReporter
engine = BacktestEngine()
trades_df, values_df = engine.run_backtest(symbol=symbol, signals=boll_signals, price_series=data["Close"])
print(trades_df)
print(values_df)

# # 05 test the performance reporter
reporter = PerformanceReporter()
reporter.print_summary(symbol=symbol, trades_df=trades_df, values_df=values_df)

# 06 test the price chart
from deltafq.charts import PriceChart, SignalChart, PerformanceChart
price_chart = PriceChart()
# price_chart.plot_prices(data=data, title="Price Chart", use_plotly=True)
# price_chart.plot_prices(data=data, title="Price Chart", use_plotly=False) # matplotlib

# data_dict = {symbol: data, benchmark: benchmark_data}
# price_chart.plot_prices(data=data_dict, title="Price Comparison", use_plotly=True)

# 对比指数价格：标普、纳斯达克、上证、沪深300
# indices = ["^GSPC", "^IXIC", "000001.SS", "000300.SS"]
# data_dict = fetcher.fetch_data_multiple(symbols=indices, start_date=start_date, end_date=end_date)
# price_chart.plot_prices(data=data_dict, title="Index Price Comparison", use_plotly=True)

# 07 test the signal chart
# signal_chart = SignalChart()
# signal_chart.plot_boll_signals(data=data, bands=boll, signals=boll_signals, use_plotly=True)
# signal_chart.plot_boll_signals(data=data, bands=boll, signals=boll_signals, use_plotly=False)

# 08 test the performance chart
performance_chart = PerformanceChart()
performance_chart.plot_backtest_charts(values_df=values_df,benchmark_close=benchmark_data["Close"],use_plotly=True)
performance_chart.plot_backtest_charts(values_df=values_df,benchmark_close=benchmark_data["Close"],use_plotly=False)