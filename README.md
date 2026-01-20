# DeltaFQ

<div align="center">

[中文](README.md) | [English](README_EN.md)

![Version](https://img.shields.io/badge/version-0.6.0-7C3AED.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-D97706.svg)
![Python](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-2563EB.svg)
![Build](https://img.shields.io/badge/build-manual-lightgrey.svg)
![License](https://img.shields.io/badge/license-MIT-10B981.svg)

面向 A 股低频量化的 Python 框架，覆盖研究、回测与执行，内置本地模拟交易并可对接实盘网关。

<p align="center">
  <img src="assets/signals.png" width="48%" alt="策略信号图" />
  <img src="assets/overview.png" width="48%" alt="回测结果面板" />
</p>

</div>


## 安装

```bash
pip install deltafq
```

## 核心模块

```
deltafq/
├── data        # 数据获取、清洗、存储接口（支持股票、基金数据）
├── indicators  # 技术指标与因子计算
├── strategy    # 信号生成器与策略基类
├── backtest    # 回测执行、绩效度量、报告
├── live        # 事件引擎、网关抽象与路由
├── adapters    # 行情/交易适配器（可插拔）
├── trader      # 交易执行与订单/持仓管理
└── charts      # 信号、绩效图表组件
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


## 应用示例
DeltaFStation 面向 A 股低频量化，基于 deltafq 集成数据服务、策略管理与交易接入，支持模拟与实盘。项目地址：https://github.com/Delta-F/deltafstation/

<p align="center">
  <img src="assets/deltafstation_1.png" width="48%" height="260" style="object-fit:contain" alt="DeltaFStation Architecture" />
  <img src="assets/deltafstation_2.png" width="48%" height="260" style="object-fit:contain" alt="DeltaFStation Backtest Engine" />
</p>


## 社区与贡献

欢迎通过 [Issue](https://github.com/Delta-F/deltafq/issues)或 PR 反馈问题、提交改进。


## 许可证

MIT License，详见 [LICENSE](LICENSE)。