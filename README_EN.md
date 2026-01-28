# DeltaFQ

<div align="center">

[中文](README.md) | [English](README_EN.md)

![Version](https://img.shields.io/badge/version-0.6.1-7C3AED.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-D97706.svg)
![Python](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-2563EB.svg)
![Build](https://img.shields.io/badge/build-manual-lightgrey.svg)
![License](https://img.shields.io/badge/license-MIT-10B981.svg)

Python Open-source Quantitative Framework: Covering the full "Research, Backtest, Trade" lifecycle, building an industrial-grade closed-loop quantitative workflow from scratch to production.

<p align="center">
  <img src="https://raw.githubusercontent.com/Delta-F/deltafq/main/assets/signals.png" width="48%" alt="Strategy Signals" />
  <img src="https://raw.githubusercontent.com/Delta-F/deltafq/main/assets/overview.png" width="48%" alt="Backtest Overview" />
</p>

</div>


## Exclusive Tutorials

iMOOC - AI Quantitative System Course: https://class.imooc.com/sale/aiqwm


## Installation

```bash
pip install deltafq
```

## Key Features

- 📥 Fetch Historical Data - Built-in free data sources, supporting global markets.
- 🧪 Common Indicators - Fast calculation of MACD, Bollinger Bands, etc., with TA-Lib support.
- 🧠 Fast Prototyping - Write logic in a few lines using signal generators and templates.
- 📉 High-Performance Backtesting - Rapid testing with multi-strategy comparison and performance analysis.
- ⚡ Live Market Distribution - Event-driven architecture for second-level distribution and Tick processing.
- 🤖 Paper & Live Trading - Pluggable design for seamless switching between simulation and live brokers.
- 📊 Interactive Visualization - Auto-generated Plotly charts for precise insights into backtest details.
- 📝 System Logging - Unified status management with multi-level logging and file storage.


## Interface Integration

DeltaFQ flexibly connects to various external interfaces through pluggable Adapters:

- ✅ **yfinance** - Integrated, supporting multi-market historical and real-time market data.
- ✅ **PaperTrade** - Integrated, supporting multi-market local simulation and position management.
- 🛠️ **qmt** - Planned, supporting A-share live market snapshots and broker execution.
- 🛠️ **Tushare** - Planned, providing richer financial fundamental data for A-shares.

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
DeltaFStation is an open-source quantitative trading cloud platform based on deltafq, integrating data services, strategy management, and trading access with paper and live support. Project: https://github.com/Delta-F/deltafstation/

<table align="center">
  <tr>
    <td><img src="https://raw.githubusercontent.com/Delta-F/deltafq/main/assets/deltafstation_1.png" height="260" alt="DeltaFStation Architecture" /></td>
    <td><img src="https://raw.githubusercontent.com/Delta-F/deltafq/main/assets/deltafstation_2.png" height="260" alt="DeltaFStation Backtest Engine" /></td>
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
    <td><img src="https://raw.githubusercontent.com/Delta-F/deltafq/main/assets/deltafq_arch.png" height="400" alt="Project Architecture" /></td>
    <td><img src="https://raw.githubusercontent.com/Delta-F/deltafq/main/assets/deltafq_wf.png" height="400" alt="Workflow" /></td>
  </tr>
</table>


## Contributing

- Feedback: Contributions and bug reports are welcome via [Issue](https://github.com/Delta-F/deltafq/issues) or PRs.
- WeChat Account: Follow `DeltaFQ开源量化` for updates, strategies, and resources.

<p align="center">
  <img src="https://raw.githubusercontent.com/Delta-F/deltafq/main/assets/wechat_qr.png" width="150" alt="WeChat Official Account" />
</p>


## License

MIT License. See [LICENSE](LICENSE) for details.
