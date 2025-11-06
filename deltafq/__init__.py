"""
DeltaFQ - A comprehensive Python quantitative finance library.

This library provides tools for strategy development, backtesting, 
paper trading, and live trading.
"""

__version__ = "0.2.0"
__author__ = "DeltaF"

# Import core modules
from . import core
from . import data
from . import strategy
from . import backtest
from . import indicators
from . import trader
from . import live

__all__ = [
    "core",
    "data", 
    "strategy",
    "backtest",
    "indicators",
    "trader",
    "live"
]

