"""
Backtest metrics calculation.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List
from ..core.base import BaseComponent


class MetricsCalculator(BaseComponent):
    """Calculate various backtest metrics."""
    
    def initialize(self) -> bool:
        """Initialize metrics calculator."""
        self.logger.info("Initializing metrics calculator")
        return True
    
    # ==================== Return Metrics ====================
    
    def calculate_returns(self, equity: pd.Series) -> pd.Series:
        """Calculate daily returns from equity series."""
        if len(equity) < 2:
            return pd.Series(dtype=float)
        return equity.pct_change().dropna()
    
    def compute_cumulative_returns(self, returns: pd.Series) -> pd.Series:
        """Calculate cumulative returns from daily returns."""
        if len(returns) == 0:
            return pd.Series(dtype=float)
        return (1 + returns).cumprod() - 1
    
    def calculate_return_metrics(self, equity: pd.Series, returns: pd.Series = None) -> Dict[str, float]:
        """Calculate return-related metrics."""
        if len(equity) < 2:
            return {}
        
        if returns is None:
            returns = self.calculate_returns(equity)
        
        if len(returns) == 0:
            return {}
        
        total_return = (equity.iloc[-1] / equity.iloc[0]) - 1
        annualized_return = (1 + returns.mean()) ** 252 - 1
        avg_daily_return = float(returns.mean())
        return_std = float(returns.std())
        
        return {
            'total_return': float(total_return),
            'annualized_return': float(annualized_return),
            'avg_daily_return': avg_daily_return,
            'return_std': return_std
        }
    
    # ==================== Risk Metrics ====================
    
    def compute_drawdown_series_from_returns(self, returns: pd.Series) -> pd.Series:
        """Calculate drawdown series from returns."""
        if len(returns) == 0:
            return pd.Series(dtype=float)
        
        cumulative = (1 + returns).cumprod()
        peak = cumulative.expanding().max()
        drawdown = (cumulative - peak) / peak
        return drawdown
    
    def calculate_max_drawdown(self, equity: pd.Series) -> float:
        """Calculate maximum drawdown from equity series."""
        if len(equity) < 2:
            return 0.0
        
        peak = equity.expanding().max()
        drawdown = (equity - peak) / peak
        return float(drawdown.min())
    
    # ==================== Performance Metrics ====================
    
    def calculate_trade_metrics(self, trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate trade-based performance metrics."""
        if not trades:
            return {
                'total_trades': 0,
                'total_pnl': 0.0,
                'win_rate': 0.0,
                'winning_trades': 0,
                'losing_trades': 0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'profit_loss_ratio': 0.0
            }
        
        trade_df = pd.DataFrame(trades)
        
        # Use profit_loss if available, otherwise calculate from buy/sell pairs
        if 'profit_loss' in trade_df.columns:
            pnl_series = trade_df['profit_loss'].dropna()
        else:
            # Fallback: calculate P&L from buy/sell pairs
            buy_trades = trade_df[trade_df['type'] == 'buy']
            sell_trades = trade_df[trade_df['type'] == 'sell']
            pnl = []
            for _, sell_trade in sell_trades.iterrows():
                matching_buys = buy_trades[buy_trades['symbol'] == sell_trade['symbol']]
                if len(matching_buys) > 0:
                    buy_trade = matching_buys.iloc[0]
                    trade_pnl = (sell_trade['price'] - buy_trade['price']) * sell_trade['quantity']
                    pnl.append(trade_pnl)
            pnl_series = pd.Series(pnl) if pnl else pd.Series(dtype=float)
        
        if len(pnl_series) == 0:
            return {
                'total_trades': 0,
                'total_pnl': 0.0,
                'win_rate': 0.0,
                'winning_trades': 0,
                'losing_trades': 0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'profit_loss_ratio': 0.0
            }
        
        total_pnl = float(pnl_series.sum())
        winning_trades = int((pnl_series > 0).sum())
        losing_trades = int((pnl_series < 0).sum())
        win_rate = float((pnl_series > 0).mean())
        
        avg_win = float(pnl_series[pnl_series > 0].mean()) if (pnl_series > 0).any() else 0.0
        avg_loss = float(pnl_series[pnl_series < 0].mean()) if (pnl_series < 0).any() else 0.0
        profit_loss_ratio = float(avg_win / abs(avg_loss)) if avg_loss != 0 else (float('inf') if avg_win > 0 else 0.0)
        
        return {
            'total_trades': len(pnl_series),
            'total_pnl': total_pnl,
            'win_rate': win_rate,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_loss_ratio': profit_loss_ratio
        }
    
    def calculate_portfolio_metrics(self, equity: pd.Series) -> Dict[str, float]:
        """Calculate portfolio-level performance metrics."""
        if len(equity) < 2:
            return {}
        
        returns = self.calculate_returns(equity)
        if len(returns) == 0:
            return {}
        
        # Return metrics
        total_return = (equity.iloc[-1] / equity.iloc[0]) - 1
        annualized_return = (1 + returns.mean()) ** 252 - 1
        
        # Risk metrics
        volatility = returns.std() * np.sqrt(252)
        sharpe_ratio = (returns.mean() / returns.std() * np.sqrt(252)) if returns.std() > 0 else 0.0
        max_drawdown = self.calculate_max_drawdown(equity)
        
        # Calmar ratio
        calmar_ratio = float('inf')
        if max_drawdown != 0:
            calmar_ratio = abs(annualized_return / max_drawdown)
        elif annualized_return > 0:
            calmar_ratio = float('inf')
        else:
            calmar_ratio = 0.0
        
        return {
            'total_return': float(total_return),
            'annualized_return': float(annualized_return),
            'volatility': float(volatility),
            'sharpe_ratio': float(sharpe_ratio),
            'max_drawdown': float(max_drawdown),
            'calmar_ratio': calmar_ratio
        }
    
    def calculate_trading_metrics(self, trades_df: pd.DataFrame, total_trading_days: int) -> Dict[str, float]:
        """Calculate trading-related metrics."""
        if trades_df.empty:
            return {
                'total_commission': 0.0,
                'total_turnover': 0.0,
                'avg_daily_pnl': 0.0,
                'avg_daily_commission': 0.0,
                'avg_daily_turnover': 0.0,
                'avg_daily_trade_count': 0.0
            }
        
        total_commission = float(trades_df.get('commission', pd.Series(dtype=float)).sum())
        total_turnover = float(trades_df.get('gross_revenue', pd.Series(dtype=float)).sum())
        total_pnl = float(trades_df.get('profit_loss', pd.Series(dtype=float)).sum())
        
        if total_trading_days > 0:
            avg_daily_pnl = total_pnl / total_trading_days
            avg_daily_commission = total_commission / total_trading_days
            avg_daily_turnover = total_turnover / total_trading_days
            avg_daily_trade_count = len(trades_df) / total_trading_days
        else:
            avg_daily_pnl = 0.0
            avg_daily_commission = 0.0
            avg_daily_turnover = 0.0
            avg_daily_trade_count = 0.0
        
        return {
            'total_commission': total_commission,
            'total_turnover': total_turnover,
            'avg_daily_pnl': avg_daily_pnl,
            'avg_daily_commission': avg_daily_commission,
            'avg_daily_turnover': avg_daily_turnover,
            'avg_daily_trade_count': avg_daily_trade_count
        }
