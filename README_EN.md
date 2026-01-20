# DeltaFQ

<div align="center">

[中文](README.md) | [English](README_EN.md)

![Version](https://img.shields.io/badge/version-0.6.0-7C3AED.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-D97706.svg)
![Python](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-2563EB.svg)
![Build](https://img.shields.io/badge/build-manual-lightgrey.svg)
![License](https://img.shields.io/badge/license-MIT-10B981.svg)

A Python-based A-share low-frequency quantitative trading framework covering research, backtesting, and execution, with built-in paper trading and pluggable live gateways.

<p align="center">
  <img src="assets/signals.png" width="48%" alt="Strategy Signals" />
  <img src="assets/overview.png" width="48%" alt="Backtest Overview" />
</p>

</div>


## Installation

```bash
pip install deltafq
```

## Core Modules

```
deltafq/
├── data        # Data acquisition, cleaning, storage interfaces (stocks, funds)
├── indicators  # Technical indicators and factor calculations
├── strategy    # Signal generators and strategy base classes
├── backtest    # Backtest execution, performance metrics, reporting
├── live        # Event engine, gateway abstraction, routing
├── adapters    # Pluggable data/trade adapters
├── trader      # Execution with order/position management
└── charts      # Signal/performance chart components
```


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


## Application Example
DeltaFStation targets A-share low-frequency trading and is built on deltafq, integrating data services, strategy management, and trading access with paper and live support. Project: https://github.com/Delta-F/deltafstation/

<p align="center">
  <img src="assets/deltafstation_1.png" width="48%" height="260" style="object-fit:contain" alt="DeltaFStation Architecture" />
  <img src="assets/deltafstation_2.png" width="48%" height="260" style="object-fit:contain" alt="DeltaFStation Backtest Engine" />
</p>


## Community & Contributing

Welcome to provide feedback and submit improvements via [Issue](https://github.com/Delta-F/deltafq/issues) or PRs.


## License

MIT License. See [LICENSE](LICENSE) for details.
