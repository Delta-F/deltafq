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
data = dfq.data.fetch_stock_data('AAPL', start='2023-01-01')

# Create and test a strategy
strategy = dfq.strategy.MovingAverageStrategy(fast_period=10, slow_period=20)
results = dfq.backtest.run_backtest(strategy, data)

# Run paper trading
simulator = dfq.trading.PaperTradingSimulator(initial_capital=100000)
simulator.run_strategy(strategy, data)
```

## Documentation

- [API Reference](docs/api_reference/)
- [Tutorials](docs/tutorials/)
- [Examples](examples/)

## Contributing

Please read our [Contributing Guide](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.