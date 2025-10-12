"""
Backtest metrics calculation.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any
from ..core.base import BaseComponent


class MetricsCalculator(BaseComponent):
    """Calculate various backtest metrics."""
    
    def initialize(self) -> bool:
        """Initialize metrics calculator."""
        self.logger.info("Initializing metrics calculator")
        return True
    
    def calculate_trade_metrics(self, trades: list) -> Dict[str, Any]:
        """Calculate trade-based metrics."""
        if not trades:
            return {}
        
        trade_df = pd.DataFrame(trades)
        
        # Separate buy and sell trades
        buy_trades = trade_df[trade_df['type'] == 'buy']
        sell_trades = trade_df[trade_df['type'] == 'sell']
        
        # Calculate P&L for each trade (simplified)
        pnl = []
        for _, sell_trade in sell_trades.iterrows():
            # Find corresponding buy trade
            buy_trade = buy_trades[buy_trades['symbol'] == sell_trade['symbol']].iloc[0]
            trade_pnl = (sell_trade['price'] - buy_trade['price']) * sell_trade['quantity']
            pnl.append(trade_pnl)
        
        if pnl:
            pnl_series = pd.Series(pnl)
            return {
                'total_trades': len(pnl),
                'winning_trades': (pnl_series > 0).sum(),
                'losing_trades': (pnl_series < 0).sum(),
                'win_rate': (pnl_series > 0).mean(),
                'avg_win': pnl_series[pnl_series > 0].mean() if (pnl_series > 0).any() else 0,
                'avg_loss': pnl_series[pnl_series < 0].mean() if (pnl_series < 0).any() else 0,
                'total_pnl': pnl_series.sum()
            }
        
        return {}
    
    def calculate_risk_metrics(self, returns: pd.Series) -> Dict[str, float]:
        """Calculate risk-related metrics."""
        if len(returns) == 0:
            return {}
        
        # Value at Risk (VaR)
        var_95 = np.percentile(returns, 5)
        var_99 = np.percentile(returns, 1)
        
        # Conditional Value at Risk (CVaR)
        cvar_95 = returns[returns <= var_95].mean()
        cvar_99 = returns[returns <= var_99].mean()
        
        # Skewness and Kurtosis
        skewness = returns.skew()
        kurtosis = returns.kurtosis()
        
        return {
            'var_95': var_95,
            'var_99': var_99,
            'cvar_95': cvar_95,
            'cvar_99': cvar_99,
            'skewness': skewness,
            'kurtosis': kurtosis
        }
    
    def calculate_portfolio_metrics(self, portfolio_values: pd.Series) -> Dict[str, float]:
        """Calculate portfolio-level metrics."""
        if len(portfolio_values) < 2:
            return {}
        
        returns = portfolio_values.pct_change().dropna()
        
        # Rolling metrics
        rolling_returns = returns.rolling(window=252)  # Annual window
        
        return {
            'total_return': (portfolio_values.iloc[-1] / portfolio_values.iloc[0]) - 1,
            'annualized_return': (1 + returns.mean()) ** 252 - 1,
            'volatility': returns.std() * np.sqrt(252),
            'sharpe_ratio': returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0,
            'max_drawdown': self._calculate_max_drawdown(portfolio_values),
            'calmar_ratio': self._calculate_calmar_ratio(returns)
        }
    
    def _calculate_max_drawdown(self, values: pd.Series) -> float:
        """Calculate maximum drawdown."""
        peak = values.expanding().max()
        drawdown = (values - peak) / peak
        return drawdown.min()
    
    def _calculate_calmar_ratio(self, returns: pd.Series) -> float:
        """Calculate Calmar ratio."""
        annual_return = (1 + returns.mean()) ** 252 - 1
        max_dd = abs(self._calculate_max_drawdown((1 + returns).cumprod()))
        
        if max_dd == 0:
            return float('inf') if annual_return > 0 else 0.0
        
        return annual_return / max_dd

