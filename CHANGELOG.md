# Changelog

All notable changes to this project will be documented here. The format follows Keep a Changelog and Semantic Versioning.

## [0.4.1] - 2025-11-10
- Quick-start backtest scripts (`05_backtest_report.py`, `05_backtest_charts.py`, `06_baseStrategy_backtestEngine.py`).
- Unified chart styling with red buys / green sells and consistent P&L colouring.
- Core modules trimmed to the public APIs with updated docs.

## [0.3.1] - 2025-11-07
- New examples covering base strategy execution, chart previews, and fast historical data pulls.
- Performance charts gained optional Plotly export; chart modules now share simplified APIs and colour rules.
- `PerformanceReporter` computes metrics internally; helper dataclasses removed. Docs and `DataFetcher` polished to match the flow.
- Deprecated `deltafq/backtest/reporter.py`; normalised distribution plots and benchmark comparisons.

## [0.3.0] - 2025-11-06
- Signal and performance charts received benchmark overlays, Plotly support, and richer panels.
- Strategy signals added Bollinger `cross_current`; examples and READMEs refreshed for the new workflow.
- Packaging extras (`viz`, `talib`) introduced alongside the `VERSION` tracker.
- Backtest engine now delegates execution, metrics module slimmed, reporter prints summaries in zh/en.
- Removed Seaborn from core dependencies.

---

Previous versions prior to 0.3.0 were internal iterations.


