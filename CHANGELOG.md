# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project adheres to Semantic Versioning.

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


