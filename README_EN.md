# DeltaFQ

Modern, modular Python toolkit for quantitative research, backtesting, paper/live trading, and reporting.

[中文文档](README.md)

## Key Features

- **Composable pipeline**: `data` → `indicators` → `strategy` → `backtest` → `charts`
- **Execution layer**: `ExecutionEngine` with a pluggable `Broker` abstraction for paper or live trading
- **Indicators & signals**: `TechnicalIndicators` and `SignalGenerator` cover SMA, EMA, RSI, KDJ, Bollinger Bands, OBV, and more
- **Strategy baseline**: `BaseStrategy` enforces Series-based signals for straightforward backtests
- **Reporting tools**: `PerformanceReporter` prints bilingual summaries; `PerformanceChart` renders Matplotlib or optional Plotly dashboards

## Installation

```bash
pip install deltafq
```

## Quick Start (Bollinger example)

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

reporter.print_summary(
    symbol=symbol,
    trades_df=trades_df,
    values_df=values_df,
    title=f"{symbol} BOLL Strategy",
    language="en",
)

chart.plot_backtest_charts(
    values_df=values_df,
    benchmark_close=data["Close"],
    title=f"{symbol} BOLL Strategy",
    use_plotly=False,
)
```

## Project Structure

- `deltafq/data`: acquisition, cleaning, validation
- `deltafq/indicators`: classic technical indicators
- `deltafq/strategy`: reusable signal helpers and `BaseStrategy`
- `deltafq/backtest`: execution engine, metrics, textual reporting
- `deltafq/charts`: signal/performance visualisations (Matplotlib + optional Plotly)

Explore the `examples/` directory for end-to-end scripts that mirror the full workflow.

## Contributing

Issues and pull requests are welcome—help us improve the library!

## License

Released under the MIT License. See [LICENSE](LICENSE) for details.

