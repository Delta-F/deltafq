# DeltaFQ

<div align="center">

[中文](README.md) | [English](README_EN.md)

![Version](https://img.shields.io/badge/version-0.5.0-7C3AED.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-D97706.svg)
![Python](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-2563EB.svg)
![Build](https://img.shields.io/badge/build-manual-lightgrey.svg)
![License](https://img.shields.io/badge/license-MIT-10B981.svg)

基于 Python 的量化交易系统开发框架，专注于策略研究、回测执行与绩效可视化。<em style="color: red;">模拟交易与实时交易功能正在开发中。</em>

</div>


## 安装

```bash
pip install deltafq
```

- Plotly、TA-Lib 等可选组件可通过 `pip install deltafq[viz]`、`pip install deltafq[talib]` 安装。


## 核心模块

```
deltafq/
├── data        # 数据获取、清洗、存储接口
├── indicators  # 技术指标与因子计算
├── strategy    # 信号生成器与策略基类
├── backtest    # 回测执行、绩效度量、报告
├── charts      # 信号、绩效图表组件
└── trader      # 交易执行与风控（持续扩展）
```


## 快速上手（BOLL 策略）

```python
import deltafq as dfq

symbol = "AAPL"
fetcher = dfq.data.DataFetcher()
indicators = dfq.indicators.TechnicalIndicators()
signals = dfq.strategy.SignalGenerator()
engine = dfq.backtest.BacktestEngine(initial_capital=100_000)
reporter = dfq.backtest.PerformanceReporter()
chart = dfq.charts.PerformanceChart()

data = fetcher.fetch_data(symbol, "2023-01-01", "2023-12-31", clean=True)
bands = indicators.boll(data["Close"], period=20, std_dev=2)
signal_series = signals.boll_signals(price=data["Close"], bands=bands, method="cross_current")

trades_df, values_df = engine.run_backtest(symbol, signal_series, data["Close"], strategy_name="BOLL")

reporter.print_summary(symbol, trades_df, values_df, title=f"{symbol} BOLL 策略", language="zh")
chart.plot_backtest_charts(values_df=values_df, benchmark_close=data["Close"], title=f"{symbol} BOLL 策略")
```

- 更多示例脚本：[examples](examples/)


## 社区与贡献

- 欢迎通过 [Issue](https://github.com/Delta-F/deltafq/issues)或 PR 反馈问题、提交改进。


## 许可证

MIT License，详见 [LICENSE](LICENSE)。