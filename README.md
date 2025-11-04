# DeltaFQ

A comprehensive Python quantitative finance library for strategy development, backtesting, and live trading.

## Features

- **Data Management**: Efficient data fetching, cleaning, and storage
- **Strategy Framework**: Flexible strategy development framework
- **Backtesting**: High-performance historical data backtesting
- **Paper Trading**: Risk-free strategy testing with simulated trading
- **Live Trading**: Real-time trading with broker integration
- **Technical Indicators**: Rich library of technical analysis indicators
- **Risk Management**: Built-in risk control modules

## Installation

```bash
pip install deltafq
```

## Quick Start

```python
import deltafq as dfq

# Fetch market data
fetcher = dfq.data.DataFetcher()
fetcher.initialize()
data = fetcher.fetch_data('AAPL', '2023-01-01', '2023-12-31', clean=True)

# Clean data (remove NaN rows)
cleaner = dfq.data.DataCleaner()
cleaner.initialize()
cleaned_data = cleaner.dropna(data)

validator = dfq.data.DataValidator()
validator.initialize()
validator.validate_price_data(cleaned_data)

# Create and test a strategy
class SimpleMAStrategy(dfq.strategy.BaseStrategy):
    def __init__(self, fast_period=10, slow_period=20):
        super().__init__()
        self.fast_period = fast_period
        self.slow_period = slow_period
    
    def generate_signals(self, data):
        fast_ma = data['close'].rolling(window=self.fast_period).mean()
        slow_ma = data['close'].rolling(window=self.slow_period).mean()
        import numpy as np
        signals = np.where(fast_ma > slow_ma, 1, np.where(fast_ma < slow_ma, -1, 0))
        return pd.Series(signals, index=data.index)

strategy = SimpleMAStrategy()
strategy.initialize()
results = strategy.run(cleaned_data)

# Run backtest
engine = dfq.backtest.BacktestEngine(initial_capital=100000)
engine.initialize()
backtest_results = engine.run_backtest(strategy, cleaned_data)

# Run paper trading
simulator = dfq.trading.PaperTradingSimulator(initial_capital=100000)
simulator.initialize()
portfolio_summary = simulator.run_strategy(strategy, cleaned_data)
```

## Documentation

- [API Reference](docs/api_reference/)
- [Tutorials](docs/tutorials/)
- [Examples](examples/)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.