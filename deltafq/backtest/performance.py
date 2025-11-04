"""Performance analysis utilities for backtests."""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
from ..core.base import BaseComponent
from .metrics import MetricsCalculator


class PerformanceAnalyzer(BaseComponent):
    """Analyze and summarize backtest performance."""
    
    def __init__(self, **kwargs):
        """Initialize performance analyzer."""
        super().__init__(**kwargs)
        self.metrics_calculator = MetricsCalculator()
    
    def initialize(self) -> bool:
        """Initialize analyzer."""
        self.logger.info("Init performance analyzer")
        self.metrics_calculator.initialize()
        return True

    def get_performance_metrics(
        self,
        symbol: str,
        trades_df: pd.DataFrame,
        values_df: pd.DataFrame,
        initial_capital: float,
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Summarize metrics from equity (values_df) and trades (trades_df).    

        Returns: (values_df_with_returns_drawdown, metrics_dict)
        """
        # Ensure datetime indexes/columns
        if 'date' in values_df.columns:
            values_df['date'] = pd.to_datetime(values_df['date'])
            values_df = values_df.set_index('date')
        if 'timestamp' in trades_df.columns:
            trades_df['timestamp'] = pd.to_datetime(trades_df['timestamp'])     

        # Basic date info
        first_trade_date = values_df.index[0]
        last_trade_date = values_df.index[-1]
        total_trading_days = len(values_df)
        trading_years = max(total_trading_days / 252, 1e-9)

        profitable_days = int((values_df['daily_pnl'] > 0).sum())
        losing_days = int((values_df['daily_pnl'] < 0).sum())

        # Capital
        start_capital = float(initial_capital)
        end_capital = float(values_df['total_value'].iloc[-1])

        # Prepare equity series and returns
        values_df = values_df.copy()
        equity = values_df['total_value'].astype(float)
        returns = self.calculate_returns(equity).reindex(values_df.index).fillna(0.0)
        values_df['returns'] = returns
        values_df['cumulative_returns'] = self.compute_cumulative_returns(returns)
        values_df['drawdown'] = self.compute_drawdown_series_from_returns(returns)

        # Use MetricsCalculator to calculate portfolio metrics
        portfolio_metrics = self.metrics_calculator.calculate_portfolio_metrics(equity)
        
        # Extract portfolio metrics
        total_return = float(portfolio_metrics.get('total_return', 0.0))
        annualized_return = float(portfolio_metrics.get('annualized_return', 0.0))
        volatility = float(portfolio_metrics.get('volatility', 0.0))
        sharpe_ratio = float(portfolio_metrics.get('sharpe_ratio', 0.0))
        max_drawdown = float(portfolio_metrics.get('max_drawdown', 0.0))
        calmar_ratio = portfolio_metrics.get('calmar_ratio', float('inf'))
        
        # Additional return metrics
        avg_daily_return = float(returns.mean())
        return_std = float(returns.std())
        return_drawdown_ratio = calmar_ratio if calmar_ratio != float('inf') else (abs(annualized_return / max_drawdown) if max_drawdown != 0 else float('inf'))

        # Convert trades_df to list format for MetricsCalculator
        trades_list = trades_df.to_dict('records') if not trades_df.empty else []
        
        # Use MetricsCalculator to calculate trade metrics
        trade_metrics = self.metrics_calculator.calculate_trade_metrics(trades_list)
        
        # Extract trade metrics
        total_pnl = float(trade_metrics.get('total_pnl', 0.0))
        win_rate = float(trade_metrics.get('win_rate', 0.0))
        avg_win = float(trade_metrics.get('avg_win', 0.0))
        avg_loss = float(trade_metrics.get('avg_loss', 0.0))
        total_trade_count = int(trade_metrics.get('total_trades', 0))
        
        profit_loss_ratio = float(avg_win / abs(avg_loss)) if avg_loss != 0 else float('inf')
        
        # Trading stats from trades_df (not in MetricsCalculator, keep original logic)
        total_commission = float(trades_df.get('commission', pd.Series(dtype=float)).sum()) if not trades_df.empty else 0.0
        total_turnover = float(trades_df.get('gross_revenue', pd.Series(dtype=float)).sum()) if not trades_df.empty else 0.0

        # Daily averages
        avg_daily_pnl = float(total_pnl / total_trading_days) if total_trading_days > 0 else 0.0
        avg_daily_commission = float(total_commission / total_trading_days) if total_trading_days > 0 else 0.0
        avg_daily_turnover = float(total_turnover / total_trading_days) if total_trading_days > 0 else 0.0
        avg_daily_trade_count = float(total_trade_count / total_trading_days) if total_trading_days > 0 else 0.0

        metrics: Dict[str, Any] = {
            'symbol': symbol,
            'first_trade_date': first_trade_date,
            'last_trade_date': last_trade_date,
            'total_trading_days': total_trading_days,
            'profitable_days': profitable_days,
            'losing_days': losing_days,
            'start_capital': start_capital,
            'end_capital': end_capital,
            'total_return': total_return,
            'annualized_return': annualized_return,
            'avg_daily_return': avg_daily_return,
            'max_drawdown': max_drawdown,
            'return_std': return_std,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'return_drawdown_ratio': return_drawdown_ratio,
            'total_pnl': total_pnl,
            'total_commission': total_commission,
            'total_turnover': total_turnover,
            'total_trade_count': total_trade_count,
            'win_rate': win_rate,
            'profit_loss_ratio': profit_loss_ratio,
            'avg_daily_pnl': avg_daily_pnl,
            'avg_daily_commission': avg_daily_commission,
            'avg_daily_turnover': avg_daily_turnover,
            'avg_daily_trade_count': avg_daily_trade_count,
        }

        return values_df, metrics

