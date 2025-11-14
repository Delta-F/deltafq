# DeltaFQ

![Version](https://img.shields.io/badge/version-0.5.0-7C3AED.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-D97706.svg)
![Python](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-2563EB.svg)
![Build](https://img.shields.io/badge/build-manual-lightgrey.svg)
![License](https://img.shields.io/badge/license-MIT-10B981.svg)

> 现代化 Python 量化交易框架，聚焦策略研究、回测执行与业绩展示。

**Language / 语言**: [中文](README.md) | [English](README_EN.md)

---

## 安装

```bash
pip install deltafq
```

- 依赖 Python ≥ 3.9。  
- Plotly、TA-Lib 等可选组件可通过 `pip install deltafq[viz]`、`pip install deltafq[talib]` 安装。

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

### API 接口

- **data**: `DataFetcher`（使用 yfinance 获取 Yahoo Finance 数据）、`DataCleaner`、`DataStorage`
- **indicators**: `TechnicalIndicators`（SMA/EMA/RSI/KDJ/BOLL/OBV/MACD等）、`TalibIndicators`（可选，需安装TA-Lib）、`FundamentalIndicators`
- **strategy**: `BaseStrategy`（策略基类）、`SignalGenerator`（信号生成与组合）
- **backtest**: `BacktestEngine`（回测引擎）、`PerformanceReporter`（绩效报告，支持中英文）
- **charts**: `PerformanceChart`（使用 Matplotlib/Plotly 实现可视化）、`PriceChart`、`SignalChart`
- **trader**: `ExecutionEngine`（交易执行引擎）、`OrderManager`、`PositionManager`、`Broker`（暂未接入券商API接口）

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

- `01_fetch_yahoo_data.py`：使用 yfinance 获取 Yahoo Finance 历史数据
- `02_compare_indicators.py`：技术指标计算与对比
- `03_compare_signals.py`：多指标信号生成与组合
- `04_backtest_execution.py`：单策略回测执行流程
- `05_backtest_report.py / 05_backtest_charts.py`：绩效报表与图表可视化
- `06_base_strategy_demo.py`：基于 `BaseStrategy` 的均线交叉策略示例
- `07_backtest_engine_tpl.py`：`BacktestEngine` 模板使用示例
- `08_deltafq_template.ipynb`：策略模板完整示例（BOLL策略，两种实现方式）
- `09_multi_factor_strategy.ipynb`：多因子策略示例（SMA/EMA/RSI/KDJ/BOLL/OBV组合）

---

## 社区与贡献

- 欢迎通过 Issue / PR 反馈问题、提交改进。
---

## 许可证

MIT License，详见 [LICENSE](LICENSE)。