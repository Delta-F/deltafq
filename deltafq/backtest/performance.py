"""Performance analysis utilities for backtests."""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
from ..core.base import BaseComponent


class PerformanceAnalyzer(BaseComponent):
    """Analyze and summarize backtest performance."""
    
    def initialize(self) -> bool:
        """Initialize analyzer."""
        self.logger.info("Init performance analyzer")
        return True
    
    def calculate_returns(self, prices: pd.Series) -> pd.Series:
        """Daily returns from equity/price series."""
        return prices.pct_change().dropna()
    
    def calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """Annualized Sharpe ratio using daily returns."""
        if len(returns) == 0 or returns.std() == 0:
            return 0.0
        
        excess_returns = returns - risk_free_rate / 252  # Daily risk-free rate
        return excess_returns.mean() / returns.std() * np.sqrt(252)
    
    def calculate_max_drawdown(self, returns: pd.Series) -> float:
        """Maximum drawdown (min of drawdown series)."""
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min()
    
    def calculate_volatility(self, returns: pd.Series) -> float:
        """Annualized volatility from daily returns."""
        return returns.std() * np.sqrt(252)
    
    def analyze_performance(self, returns: pd.Series, benchmark_returns: pd.Series = None) -> Dict[str, float]:
        """Quick metric bundle from daily returns."""
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
        """Profit factor based on summed wins/losses."""
        positive_returns = returns[returns > 0].sum()
        negative_returns = abs(returns[returns < 0].sum())
        
        if negative_returns == 0:
            return float('inf') if positive_returns > 0 else 0.0
        
        return positive_returns / negative_returns
    
    def _calculate_alpha(self, returns: pd.Series, benchmark_returns: pd.Series) -> float:
        """Simple alpha (mean excess vs benchmark)."""
        # Simplified calculation
        return returns.mean() - benchmark_returns.mean()
    
    def _calculate_beta(self, returns: pd.Series, benchmark_returns: pd.Series) -> float:
        """Beta as cov/var(bm)."""
        if benchmark_returns.var() == 0:
            return 0.0
        return returns.cov(benchmark_returns) / benchmark_returns.var()

    # --- Utility helpers for composition ---
    def compute_cumulative_returns(self, returns: pd.Series) -> pd.Series:
        """Cumulative returns from daily returns."""
        returns = returns.fillna(0.0)
        return (1.0 + returns).cumprod() - 1.0

    def compute_drawdown_series_from_returns(self, returns: pd.Series) -> pd.Series:
        """Full drawdown series from daily returns."""
        cumulative = (1.0 + returns).cumprod()
        running_max = cumulative.cummax()
        return (cumulative - running_max) / running_max

    # --- High-level backtest metrics ---
    def run_backtest_metrics(
        self,
        symbol: str,
        trades_df: pd.DataFrame,
        values_df: pd.DataFrame,
        initial_capital: float,
        risk_free_rate: float = 0.02,
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

        # Returns and drawdown (decoupled via helpers)
        values_df = values_df.copy()
        equity = values_df['total_value'].astype(float)
        returns = self.calculate_returns(equity).reindex(values_df.index).fillna(0.0)
        values_df['returns'] = returns
        values_df['cumulative_returns'] = self.compute_cumulative_returns(returns)

        total_return = float(values_df['cumulative_returns'].iloc[-1])
        annualized_return = float((1.0 + total_return) ** (1.0 / trading_years) - 1.0)
        avg_daily_return = float(returns.mean())

        # Drawdown series consistent with calculate_max_drawdown
        values_df['drawdown'] = self.compute_drawdown_series_from_returns(returns)
        max_drawdown = float(values_df['drawdown'].min())

        # Risk metrics using atomic methods
        return_std = float(returns.std())
        volatility = float(self.calculate_volatility(returns))
        sharpe_ratio = float(self.calculate_sharpe_ratio(returns, risk_free_rate=risk_free_rate))
        return_drawdown_ratio = float(abs(annualized_return / max_drawdown)) if max_drawdown != 0 else float('inf')

        # Trading stats
        sell_trades = trades_df[trades_df.get('type') == 'sell'] if not trades_df.empty else pd.DataFrame()
        win_trades = int((trades_df.get('profit_loss', pd.Series(dtype=float)) > 0).sum()) if not trades_df.empty else 0
        win_rate = float(win_trades / len(sell_trades)) if len(sell_trades) > 0 else 0.0

        avg_win = float(sell_trades.loc[sell_trades.get('profit_loss', pd.Series(dtype=float)) > 0, 'profit_loss'].mean()) if not sell_trades.empty else 0.0
        avg_loss_series = sell_trades.loc[sell_trades.get('profit_loss', pd.Series(dtype=float)) < 0, 'profit_loss'] if not sell_trades.empty else pd.Series(dtype=float)
        avg_loss = float(avg_loss_series.mean()) if not avg_loss_series.empty else 0.0
        profit_loss_ratio = float(avg_win / abs(avg_loss)) if avg_loss != 0 else float('inf')

        total_pnl = float(sell_trades.get('profit_loss', pd.Series(dtype=float)).sum()) if not sell_trades.empty else 0.0
        total_commission = float(trades_df.get('commission', pd.Series(dtype=float)).sum()) if not trades_df.empty else 0.0
        total_turnover = float(trades_df.get('gross_revenue', pd.Series(dtype=float)).sum()) if not trades_df.empty else 0.0
        total_trade_count = int(len(trades_df))

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

