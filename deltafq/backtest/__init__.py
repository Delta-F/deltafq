"""
Backtesting module for DeltaFQ.
"""

from .engine import BacktestEngine
from .performance import PerformanceReporter
from .metrics import (
    calculate_annualized_return,
    calculate_calmar_ratio,
    calculate_max_drawdown,
    calculate_returns,
    calculate_sharpe_ratio,
    calculate_total_return,
    calculate_volatility,
    compute_cumulative_returns,
    compute_drawdown_series,
)

__all__ = [
    "BacktestEngine",
    "PerformanceReporter",
    "calculate_returns",
    "compute_cumulative_returns",
    "compute_drawdown_series",
    "calculate_total_return",
    "calculate_annualized_return",
    "calculate_volatility",
    "calculate_sharpe_ratio",
    "calculate_max_drawdown",
    "calculate_calmar_ratio",
]

