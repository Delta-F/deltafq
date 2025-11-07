# DeltaFQ

Modern Python library for strategy research, backtesting, paper/live trading, and streamlined reporting.

## Highlights

- **Clean architecture**: `data` → `strategy` (signals) → `backtest` (execution + metrics)
- **Execution engine**: Unified order routing for paper/live trading via a `Broker` abstraction
- **Indicators**: Rich `TechnicalIndicators` (SMA/EMA/RSI/KDJ/BOLL/ATR/…)
- **Signals**: Simple, composable `SignalGenerator` helpers (e.g., Bollinger `touch`/`cross`/`cross_current`)
- **Reports**: Console-friendly summary with i18n (Chinese/English) powered by `PerformanceReporter`
- **Charts**: `PerformanceChart` delivers Matplotlib or Plotly (optional) performance dashboards

## Install

```bash
pip install deltafq
```

## 60-second Quick Start (Bollinger strategy)

```python
import deltafq as dfq

symbol = "AAPL"
fetcher = dfq.data.DataFetcher()
indicators = dfq.indicators.TechnicalIndicators()
generator = dfq.strategy.SignalGenerator()
engine = dfq.backtest.BacktestEngine(initial_capital=100_000)
reporter = dfq.backtest.PerformanceReporter()
chart = dfq.charts.PerformanceChart()

data = fetcher.fetch_data(symbol, "2023-01-01", "2023-12-31", clean=True)
bands = indicators.boll(data["Close"], period=20, std_dev=2)
signals = generator.boll_signals(price=data["Close"], bands=bands, method="cross_current")

trades_df, values_df = engine.run_backtest(symbol, signals, data["Close"], strategy_name="BOLL")

# Text summary (zh/en available)
reporter.print_summary(
    symbol=symbol,
    trades_df=trades_df,
    values_df=values_df,
    title=f"{symbol} BOLL Strategy",
    language="en",
)

# Optional performance dashboard (Matplotlib by default; set use_plotly=True for interactive charts)
chart.plot_backtest_charts(values_df=values_df, benchmark_close=data["Close"], title=f"{symbol} BOLL Strategy")
```

## What’s inside

- `deltafq/data`: fetching, cleaning, validation
- `deltafq/indicators`: classic TA indicators
- `deltafq/strategy`: signal generation + BaseStrategy helpers
- `deltafq/backtest`: execution via `ExecutionEngine`; reporting via `PerformanceReporter`
- `deltafq/charts`: signal and performance charts (Matplotlib + optional Plotly)

## Examples

See the `examples/` folder for ready-to-run scripts:

- `04_backtest_result.py`: Bollinger strategy summary + charts
- `05_visualize_charts.py`: standalone visualization demos
- `06_base_strategy`: implement a moving-average cross using `BaseStrategy`

## Contributing

Contributions are welcome! Please open an issue or submit a PR.

## License

MIT License – see [LICENSE](LICENSE).