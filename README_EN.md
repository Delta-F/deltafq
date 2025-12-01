# DeltaFQ

<div align="center">

[中文](README.md) | [English](README_EN.md)

![Version](https://img.shields.io/badge/version-0.5.0-7C3AED.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-D97706.svg)
![Python](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-2563EB.svg)
![Build](https://img.shields.io/badge/build-manual-lightgrey.svg)
![License](https://img.shields.io/badge/license-MIT-10B981.svg)

A Python-based quantitative trading system development framework focused on strategy research, backtesting execution, and performance visualization. <em style="color: red;">Simulated trading and live trading features are under development.</em>

</div>


## Installation

```bash
pip install deltafq
```

- Optional components like Plotly and TA-Lib can be installed via `pip install deltafq[viz]` and `pip install deltafq[talib]`.


## Core Modules

```
deltafq/
├── data        # Data acquisition, cleaning, storage interfaces
├── indicators  # Technical indicators and factor calculations
├── strategy    # Signal generators and strategy base classes
├── backtest    # Backtest execution, performance metrics, reporting
├── charts      # Signal/performance chart components
└── trader      # Trading execution and risk control (ongoing expansion)
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

- More example scripts: [examples](examples/)


## Community & Contributing

- Welcome to provide feedback and submit improvements via [Issue](https://github.com/Delta-F/deltafq/issues) or PRs.


## License

MIT License. See [LICENSE](LICENSE) for details.
