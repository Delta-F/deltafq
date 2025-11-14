"""
DeltaFQ - A comprehensive Python quantitative finance library.

This library provides tools for strategy development, backtesting, 
paper trading, and live trading.
"""

import os
from pathlib import Path

# Read version from VERSION file
_version_file = Path(__file__).parent.parent / "VERSION"
if _version_file.exists():
    __version__ = _version_file.read_text().strip()
else:
    __version__ = "0.5.0"

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

