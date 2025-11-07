# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project adheres to Semantic Versioning.

## [0.3.1] - 2025-11-07
### Added
- Example `06_base_strategy`: moving-average cross built on `BaseStrategy`, including end-to-end backtest.
- Example `05_visualize_charts.py`: quick way to preview performance, price, and signal charts (Matplotlib & Plotly).
- Example `01_history_data`: minimal script for pulling historical market data with `DataFetcher`.
- Performance charts: Plotly export now available via `use_plotly` flag in `PerformanceChart.plot_backtest_charts`.

### Changed
- `PerformanceReporter` focuses on console summaries; `print_summary` computes metrics internally and no longer requires `initial_capital` or pre-built metrics tuples.
- `PerformanceReporter.compute` returns `(values_df, metrics)` and drops the `PerformanceSummary` dataclass plus the `run` helper.
- `metrics.py` trimmed to pure calculation helpers with no validation boilerplate; exports updated accordingly.
- Chart modules (`charts/performance.py`, `charts/price.py`, `charts/signals.py`) simplified APIs, normalized benchmark overlays, refined colors, and added Plotly parity fixes.
- `DataFetcher` got minor polish to align with revised examples/docs.
- README (EN/中文) refreshed to showcase the new workflow and examples, including direct chart usage.

### Removed
- Legacy `deltafq/backtest/reporter.py` module in favour of the streamlined `PerformanceReporter`.

### Fixed
- Matplotlib distribution plot now keeps numeric axes; timeline formatting limited to relevant subplots.
- Price comparison and net value panels normalize benchmark and strategy series consistently.

## [0.3.0] - 2025-11-06
### Added
- SignalChart: benchmark comparison subplot and timeline; improved app-like styling.
- PerformanceChart: Plotly interactive charts with HTML export; optional `use_plotly` flag.
- PerformanceChart: close price comparison subplot (now 5 panels when data provided).
- Strategy signals: `boll_signals` new method `cross_current` aligning with current-band crossover logic.
- Examples: simple Bollinger backtest and report script.
- Documentation: refreshed `README.md` and `README_CN.md` with quick start and module overview.
- Packaging: optional extras `viz` (plotly) and `talib` in `pyproject.toml`.
- Version file `VERSION` for release tracking.

### Changed
- Backtest engine delegates execution to `ExecutionEngine` only; removed portfolio helpers from engine.
- Metrics: modularized and trimmed to what `performance.py` uses.
- Reporter: prints summary directly and supports zh/en output.

### Removed
- Seaborn from core dependencies (still can emulate style via Matplotlib theme).

---

Previous versions prior to 0.3.0 were internal iterations.


