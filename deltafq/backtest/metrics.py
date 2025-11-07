"""Pure performance metric helpers."""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd


def calculate_returns(equity: pd.Series) -> pd.Series:
    """Daily percentage returns for an equity curve."""
    return equity.pct_change().fillna(0.0)


def compute_cumulative_returns(returns: pd.Series) -> pd.Series:
    """Cumulative returns from daily returns."""
    return (1 + returns).cumprod() - 1


def compute_drawdown_series(returns: pd.Series) -> pd.Series:
    """Drawdown series derived from cumulative returns."""
    cumulative = (1 + returns).cumprod()
    peak = cumulative.cummax()
    return (cumulative - peak) / peak


def calculate_total_return(equity: pd.Series) -> float:
    """Total return over an equity curve."""
    return float(equity.iloc[-1] / equity.iloc[0] - 1)


def calculate_annualized_return(returns: pd.Series, periods: int = 252) -> float:
    """Annualized return from periodic returns."""
    return float((1 + returns.mean()) ** periods - 1)


def calculate_volatility(returns: pd.Series, periods: int = 252) -> float:
    """Annualized volatility."""
    return float(returns.std() * np.sqrt(periods))


def calculate_sharpe_ratio(returns: pd.Series, risk_free: float = 0.0, periods: int = 252) -> float:
    """Annualized Sharpe ratio."""
    excess = returns - risk_free / periods
    return float(excess.mean() / excess.std() * np.sqrt(periods)) if excess.std() else 0.0


def calculate_max_drawdown(equity: pd.Series) -> float:
    """Maximum drawdown from an equity curve."""
    peak = equity.cummax()
    drawdown = (equity - peak) / peak
    return float(drawdown.min())


def calculate_calmar_ratio(annualized_return: float, max_drawdown: float) -> float:
    """Calmar ratio from annualized return and max drawdown."""
    if max_drawdown == 0:
        return float("inf") if annualized_return > 0 else 0.0
    return float(abs(annualized_return / max_drawdown))


__all__ = [
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

