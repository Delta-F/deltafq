# DeltaFQ

![Version](https://img.shields.io/badge/version-0.5.0-7C3AED.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-D97706.svg)
![Python](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-2563EB.svg)
![Build](https://img.shields.io/badge/build-manual-lightgrey.svg)
![License](https://img.shields.io/badge/license-MIT-10B981.svg)

> Modern Python quantitative finance framework focused on strategy research, backtesting execution, and performance visualization.

**Language / 语言**: [中文](README.md) | [English](README_EN.md)

---

## Installation

```bash
pip install deltafq
```

- Requires Python ≥ 3.9.  
- Optional components like Plotly and TA-Lib can be installed via `pip install deltafq[viz]` and `pip install deltafq[talib]`.

---

## Overview

- Lightweight, modular quantitative research infrastructure covering the full pipeline: **data → indicators → strategy → backtest → visualization**.
- Built-in consistent signal standard (`Series` type) for strategy reuse and component decoupling.
- Suitable for desktop research workflows and script automation, supporting rapid validation and continuous integration.

---

## Core Capabilities

- **Data Access**: Unified data fetching, cleaning, and validation processes.
- **Indicator Library**: `TechnicalIndicators`/`SignalGenerator` provide mainstream indicators and various combination methods.
- **Strategy Layer**: `BaseStrategy` abstracts strategy lifecycle for easy extension and backtest reuse.
- **Backtest Execution**: `BacktestEngine` integrates underlying execution, position management, and performance metrics.
- **Performance Visualization**: `PerformanceReporter` (bilingual) and `PerformanceChart` (Matplotlib / Plotly).

---

## Module Architecture

```
deltafq/
├── data        # Data acquisition, cleaning, storage interfaces
├── indicators  # Technical indicators and factor calculations
├── strategy    # Signal generators and strategy base classes
├── backtest    # Backtest execution, performance metrics, reporting
├── charts      # Signal/performance chart components
└── trader      # Trading execution and risk control (ongoing expansion)
```

### API Interfaces

- **data**: `DataFetcher` (fetch Yahoo Finance data using yfinance), `DataCleaner`, `DataStorage`
- **indicators**: `TechnicalIndicators` (SMA/EMA/RSI/KDJ/BOLL/OBV/MACD, etc.), `TalibIndicators` (optional, requires TA-Lib), `FundamentalIndicators`
- **strategy**: `BaseStrategy` (strategy base class), `SignalGenerator` (signal generation and combination)
- **backtest**: `BacktestEngine` (backtest engine), `PerformanceReporter` (performance reports, bilingual support)
- **charts**: `PerformanceChart` (visualization using Matplotlib/Plotly), `PriceChart`, `SignalChart`
- **trader**: `ExecutionEngine` (trading execution engine), `OrderManager`, `PositionManager`, `Broker` (broker API not yet integrated)

---

## Quick Start (BOLL Strategy)

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

reporter.print_summary(symbol, trades_df, values_df, title=f"{symbol} BOLL Strategy", language="en")
chart.plot_backtest_charts(values_df=values_df, benchmark_close=data["Close"], title=f"{symbol} BOLL Strategy")
```

---

## Examples & Tools

- `01_fetch_yahoo_data.py`: Fetch historical data from Yahoo Finance using yfinance
- `02_compare_indicators.py`: Technical indicator calculation and comparison
- `03_compare_signals.py`: Multi-indicator signal generation and combination
- `04_backtest_execution.py`: Single-strategy backtest execution workflow
- `05_backtest_report.py / 05_backtest_charts.py`: Performance reports and chart visualization
- `06_base_strategy_demo.py`: Moving average crossover strategy example based on `BaseStrategy`
- `07_backtest_engine_tpl.py`: `BacktestEngine` template usage example
- `08_deltafq_template.ipynb`: Complete strategy template example (BOLL strategy, two implementation methods)
- `09_multi_factor_strategy.ipynb`: Multi-factor strategy example (SMA/EMA/RSI/KDJ/BOLL/OBV combination)

---

## Community & Contributing

- Welcome to provide feedback and submit improvements via Issues / PRs.
- The project follows a clean code style; it's recommended to run basic lint/tests before submitting.

---

## License

MIT License. See [LICENSE](LICENSE) for details.
