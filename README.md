# DeltaFQ

Modern Python library for strategy research, backtesting, paper/live trading, and beautiful reporting.

## Highlights

- **Clean architecture**: `data` → `strategy` (signals) → `backtest` (execution) → `performance` (metrics) → `reporter` (text + charts)
- **Execution engine**: Unified order execution for paper/live trading via a `Broker` abstraction
- **Indicators**: Rich `TechnicalIndicators` (SMA/EMA/RSI/KDJ/BOLL/ATR/…)
- **Signals**: Simple, composable `SignalGenerator` (e.g., Bollinger `touch`/`cross`/`cross_current`)
- **Charts**: Matplotlib by default, optional Plotly interactive performance charts
- **Reports**: Console-friendly summary with i18n (Chinese/English) + visual charts

## Install

```bash
pip install deltafq
```

## 60-second Quick Start (Bollinger strategy)

```python
import deltafq as dfq

symbol = 'AAPL'
fetcher = dfq.data.DataFetcher(); indicators = dfq.indicators.TechnicalIndicators()
generator = dfq.strategy.SignalGenerator()
engine = dfq.backtest.BacktestEngine(initial_capital=100000)
perf = dfq.backtest.PerformanceAnalyzer(); reporter = dfq.backtest.BacktestReporter()

data = fetcher.fetch_data(symbol, '2023-01-01', '2023-12-31', clean=True)
bands = indicators.boll(data['Close'], period=20, std_dev=2)
signals = generator.boll_signals(price=data['Close'], bands=bands, method='cross_current')

trades_df, values_df = engine.run_backtest(symbol, signals, data['Close'], strategy_name='BOLL')
values_df, metrics = perf.get_performance_metrics(symbol, trades_df, values_df, engine.initial_capital)

# Text + charts; pass use_plotly=True inside reporter if you want interactive charts
reporter.generate_visual_report(metrics=metrics, values_df=values_df, title=f'{symbol} BOLL Strategy')
```

## What’s inside

- `deltafq/data`: fetching, cleaning, validation
- `deltafq/indicators`: classic TA indicators
- `deltafq/strategy`: signal generation + signal combination
- `deltafq/backtest`: execution via `ExecutionEngine`; performance via `PerformanceAnalyzer`; reporting via `BacktestReporter`
- `deltafq/charts`: signal and performance charts (Matplotlib + optional Plotly)

## Examples

See the `examples/` folder for ready-to-run scripts:

- Compare indicators and signals
- Run a Bollinger strategy and generate a full report

## Contributing

Contributions are welcome! Please open an issue or submit a PR.

## License

MIT License – see [LICENSE](LICENSE).