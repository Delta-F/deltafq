# DeltaFQ

![Version](https://img.shields.io/badge/version-0.4.3-7C3AED.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-D97706.svg)
![Python](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10%20%7C%203.11-2563EB.svg)
![Build](https://img.shields.io/badge/build-manual-lightgrey.svg)
![License](https://img.shields.io/badge/license-MIT-10B981.svg)

> 现代化 Python 量化交易框架，聚焦策略研究、回测执行与业绩展示。

[English README](README_EN.md)

---

## 概述

- 轻量化、模块化的量化研发基础设施，覆盖 **数据 → 指标 → 策略 → 回测 → 可视化** 全链条。
- 内置一致的信号标准（`Series` 类型），实现策略复用与组件解耦。
- 适配桌面研究流与脚本自动化，支持快速验证与持续集成。

---

## 核心能力

- **数据接入**：统一的数据抓取、清洗、校验流程。
- **指标库**：`TechnicalIndicators`/`SignalGenerator` 提供主流指标及多种组合方式。
- **策略层**：`BaseStrategy` 抽象策略生命周期，便于扩展与回测复用。
- **回测执行**：`BacktestEngine` 集成底层执行、仓位管理、绩效指标。
- **绩效展示**：`PerformanceReporter`（中/英）与 `PerformanceChart`（Matplotlib / Plotly）。

---

## 模块架构

```
deltafq/
├── data        # 数据获取、清洗、存储接口
├── indicators  # 技术指标与因子计算
├── strategy    # 信号生成器与策略基类
├── backtest    # 回测执行、绩效度量、报告
├── charts      # 信号/绩效图表组件
└── trader      # 交易执行与风控（持续扩展）
```

示例脚本位于 `examples/` 目录，涵盖信号对比、回测执行、报告生成等场景。

---

## 安装

```bash
pip install deltafq
```

- 依赖 Python ≥ 3.8。  
- Plotly、TA-Lib 等可选组件可通过 `pip install deltafq[viz]`、`pip install deltafq[talib]` 安装。

---

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

---

## 示例与工具

- `03_compare_signals.py`：常见指标信号对比。
- `04_backtest_execution.py`：单策略回测全流程。
- `05_backtest_report.py / 05_backtest_charts.py`：绩效报表与图表化展示。
- `06_base_strategy_demo.py`：基于 `BaseStrategy` 实现的均线交叉样例。

---

## 社区与贡献

- 欢迎通过 Issue / PR 反馈问题、提交改进。
- 项目遵循简洁的代码风格，建议在提交前运行基本的 lint/测试。

---

## 许可证

MIT License，详见 [LICENSE](LICENSE)。