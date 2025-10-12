"""
Performance analysis for backtests.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any
from ..core.base import BaseComponent


class PerformanceAnalyzer(BaseComponent):
    """Analyze backtest performance."""
    
    def initialize(self) -> bool:
        """Initialize performance analyzer."""
        self.logger.info("Initializing performance analyzer")
        return True
    
    def calculate_returns(self, prices: pd.Series) -> pd.Series:
        """Calculate returns from price series."""
        return prices.pct_change().dropna()
    
    def calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio."""
        if len(returns) == 0 or returns.std() == 0:
            return 0.0
        
        excess_returns = returns - risk_free_rate / 252  # Daily risk-free rate
        return excess_returns.mean() / returns.std() * np.sqrt(252)
    
    def calculate_max_drawdown(self, returns: pd.Series) -> float:
        """Calculate maximum drawdown."""
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min()
    
    def calculate_volatility(self, returns: pd.Series) -> float:
        """Calculate annualized volatility."""
        return returns.std() * np.sqrt(252)
    
    def analyze_performance(self, returns: pd.Series, benchmark_returns: pd.Series = None) -> Dict[str, float]:
        """Comprehensive performance analysis."""
        analysis = {
            'total_return': (1 + returns).prod() - 1,
            'annualized_return': (1 + returns).prod() ** (252 / len(returns)) - 1,
            'volatility': self.calculate_volatility(returns),
            'sharpe_ratio': self.calculate_sharpe_ratio(returns),
            'max_drawdown': self.calculate_max_drawdown(returns),
            'win_rate': (returns > 0).mean(),
            'profit_factor': self._calculate_profit_factor(returns)
        }
        
        if benchmark_returns is not None:
            analysis['alpha'] = self._calculate_alpha(returns, benchmark_returns)
            analysis['beta'] = self._calculate_beta(returns, benchmark_returns)
        
        return analysis
    
    def _calculate_profit_factor(self, returns: pd.Series) -> float:
        """Calculate profit factor."""
        positive_returns = returns[returns > 0].sum()
        negative_returns = abs(returns[returns < 0].sum())
        
        if negative_returns == 0:
            return float('inf') if positive_returns > 0 else 0.0
        
        return positive_returns / negative_returns
    
    def _calculate_alpha(self, returns: pd.Series, benchmark_returns: pd.Series) -> float:
        """Calculate alpha."""
        # Simplified calculation
        return returns.mean() - benchmark_returns.mean()
    
    def _calculate_beta(self, returns: pd.Series, benchmark_returns: pd.Series) -> float:
        """Calculate beta."""
        if benchmark_returns.var() == 0:
            return 0.0
        return returns.cov(benchmark_returns) / benchmark_returns.var()

