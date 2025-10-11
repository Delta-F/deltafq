# DeltaFQ

[![PyPI version](https://badge.fury.io/py/deltafq.svg)](https://badge.fury.io/py/deltafq)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A professional Python quantitative trading library providing a complete toolkit for quantitative strategy development and research.

## Features

- 📊 **Multi-source Data Support** - Unified data interface supporting multiple data sources
- 📈 **Rich Technical Indicators** - Built-in common technical indicators with custom extension support
- 🎯 **Flexible Strategy Framework** - Clean API for rapid trading strategy development
- ⚡ **Efficient Backtest Engine** - Vectorized computation for fast strategy validation
- 📉 **Comprehensive Risk Management** - Position management, risk control, and performance analysis
- 🔧 **Parameter Optimization Tools** - Multiple optimization algorithms for finding optimal parameters
- 📱 **Live Trading Interface** - Unified trading interface for seamless simulation and live trading

## Installation

```bash
pip install deltafq
```

Or install from source:

```bash
git clone https://github.com/Delta-F/deltafq.git
cd deltafq
pip install -e .
```

## Quick Start

### Get Data

```python
import deltafq as dfq

# Get stock data
data = dfq.data.get_stock_daily('000001.SZ', start='2020-01-01', end='2023-12-31')
print(data.head())
```

### Calculate Technical Indicators

```python
# Calculate moving averages
data['ma5'] = dfq.indicators.SMA(data['close'], 5)
data['ma20'] = dfq.indicators.SMA(data['close'], 20)

# Calculate MACD
macd = dfq.indicators.MACD(data['close'])
data = data.join(macd)
```

### Build Trading Strategy

```python
class MAStrategy(dfq.strategy.Strategy):
    """Dual Moving Average Strategy"""
    
    def on_bar(self, bar):
        if bar.ma5 > bar.ma20:
            self.buy()
        elif bar.ma5 < bar.ma20:
            self.sell()
```

### Run Backtest

```python
# Create backtest engine
engine = dfq.backtest.BacktestEngine(
    initial_cash=100000,
    commission=0.0003
)

# Run backtest
result = engine.run(data, MAStrategy())

# View results
print(result.summary())
result.plot()
```

## Module Overview

- **data** - Data acquisition and management
- **indicators** - Technical indicator calculations
- **strategy** - Strategy development framework
- **backtest** - Backtest engine
- **risk** - Risk management
- **performance** - Performance analysis
- **optimization** - Parameter optimization
- **trade** - Live trading interface
- **utils** - Utility functions

## Examples

Check the `examples/` directory for more example code:

- `ma_strategy.py` - Dual Moving Average Strategy
- `macd_strategy.py` - MACD Strategy
- `optimization_example.py` - Parameter Optimization Example

## Documentation

- **User Guide**: [docs/GUIDE.md](docs/GUIDE.md)
- **API Reference**: [docs/API.md](docs/API.md)
- **Development Guide**: [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)
- **Changelog**: [docs/CHANGELOG.md](docs/CHANGELOG.md)

## Dependencies

- Python >= 3.8
- pandas >= 1.3.0
- numpy >= 1.21.0

## Development

```bash
# Clone repository
git clone https://github.com/Delta-F/deltafq.git
cd deltafq

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Code formatting
black deltafq/

# Type checking
mypy deltafq/
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Issues and Pull Requests are welcome!

## Contact

- Project Homepage: [https://github.com/Delta-F/deltafq](https://github.com/Delta-F/deltafq)
- PyPI Homepage: [https://pypi.org/project/deltafq/](https://pypi.org/project/deltafq/)
- Issue Tracker: [https://github.com/Delta-F/deltafq/issues](https://github.com/Delta-F/deltafq/issues)

---

⚠️ **Risk Warning**: Quantitative trading involves risk. This library is for educational and research purposes only and does not constitute investment advice. Please exercise caution when trading live, as you bear the risk yourself.

## Language Support

This project supports both English and Chinese documentation:

- **English**: [README.md](README.md) (current)
- **中文**: [README_zh.md](README_zh.md)