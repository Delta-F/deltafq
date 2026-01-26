# DeltaFQ

<div align="center">

[中文](README.md) | [English](README_EN.md)

![Version](https://img.shields.io/badge/version-0.6.0-7C3AED.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-D97706.svg)
![Python](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-2563EB.svg)
![Build](https://img.shields.io/badge/build-manual-lightgrey.svg)
![License](https://img.shields.io/badge/license-MIT-10B981.svg)

An all-in-one A-share low-frequency quantitative solution: Covering the full "Research-Backtest-Execution" lifecycle, with built-in simulation environments and live gateway interfaces to build industrial-grade Python quantitative workflows from scratch to production.

<p align="center">
  <img src="assets/signals.png" width="48%" alt="Strategy Signals" />
  <img src="assets/overview.png" width="48%" alt="Backtest Overview" />
</p>

</div>


## Exclusive Tutorials

慕课网 - 程序员AI量化理财体系课：https://class.imooc.com/sale/aiqwm


## Installation

```bash
pip install deltafq
```

## Key Features

- 📥 Data Engine - Integrated yfinance; planned support for tushare and QMT
- 🧪 Indicators - Native pandas technical indicators and built-in TA-Lib support
- 🧠 Strategy Lab - Fast prototyping with signal generators and `BaseStrategy` templates
- 📉 Backtest Pro - High-performance engine with detailed metrics and drawdown analysis
- 🤖 Trade Execution - Pluggable gateway architecture for paper trading and live API integration
- 📊 Visualization - Interactive Plotly-based charts and multi-language performance reports
- 📝 Logging - Unified logging and output management with multi-level support and file storage


## Quick Start

```python
import deltafq as dfq

# 1. Define strategy logic
class MyStrategy(dfq.strategy.BaseStrategy):
    def generate_signals(self, data):
        bands = dfq.indicators.TechnicalIndicators().boll(data["Close"])
        return dfq.strategy.SignalGenerator().boll_signals(data["Close"], bands)

# 2. Minimal backtest & results
engine = dfq.backtest.BacktestEngine()
engine.set_parameters("GOOGL", "2025-07-26", "2026-01-26")
engine.load_data()
engine.add_strategy(MyStrategy(name="BOLL"))
engine.run_backtest()
engine.show_report()
engine.show_chart(use_plotly=False)
```


## Application Example
DeltaFStation targets A-share low-frequency trading and is built on deltafq, integrating data services, strategy management, and trading access with paper and live support. Project: https://github.com/Delta-F/deltafstation/

<table align="center">
  <tr>
    <td><img src="assets/deltafstation_1.png" height="260" alt="DeltaFStation Architecture" /></td>
    <td><img src="assets/deltafstation_2.png" height="260" alt="DeltaFStation Backtest Engine" /></td>
  </tr>
</table>


## Project Architecture

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

<table align="center">
  <tr>
    <td><img src="assets/deltafq_arch.png" height="400" alt="Project Architecture" /></td>
    <td><img src="assets/deltafq_wf.png" height="400" alt="Workflow" /></td>
  </tr>
</table>


## Contributing

- Feedback: Contributions and bug reports are welcome via [Issue](https://github.com/Delta-F/deltafq/issues) or PRs.
- WeChat Account: Follow `DeltaFQ开源量化` for updates, strategies, and resources.

<p align="center">
  <img src="assets/wechat_qr.png" width="150" alt="WeChat Official Account" />
</p>


## License

MIT License. See [LICENSE](LICENSE) for details.
