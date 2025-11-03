"""
Strategy performance analysis charts for DeltaFQ.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
from typing import Dict, Any, Optional
from ..core.base import BaseComponent


class PerformanceChart(BaseComponent):
    """Chart class for strategy performance visualization."""
    
    def initialize(self) -> bool:
        """Initialize the performance chart component."""
        self.logger.info("Init performance chart")
        # Set default style
        plt.style.use('seaborn-v0_8-darkgrid' if 'seaborn-v0_8-darkgrid' in plt.style.available else 'default')
        return True
    
    def plot_performance(
        self,
        results: Dict[str, Any],
        title: Optional[str] = None,
        figsize: tuple = (12, 8),
        show: bool = True,
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Plot strategy performance analysis chart.
        
        Args:
            results: Dictionary containing backtest results
            title: Chart title
            figsize: Figure size tuple (width, height)
            show: Whether to display the chart
            save_path: Optional path to save the chart
            
        Returns:
            matplotlib Figure object
        """
        try:
            self.logger.info("Generating performance analysis chart")
            
            # Placeholder implementation - to be extended later
            fig, ax = plt.subplots(figsize=figsize)
            
            if not title:
                title = "Strategy Performance Analysis"
            
            ax.text(0.5, 0.5, 
                   'Performance Chart Module\n(Implementation coming soon)',
                   horizontalalignment='center',
                   verticalalignment='center',
                   transform=ax.transAxes,
                   fontsize=14)
            
            ax.set_title(title, fontsize=12, fontweight='bold')
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                self.logger.info(f"Chart saved to {save_path}")
            
            if show:
                plt.show()
            
            return fig
            
        except Exception as e:
            self.logger.error(f"Error generating performance chart: {str(e)}")
            raise

    def plot_backtest_charts(
        self,
        values_df: pd.DataFrame,
        benchmark_close: Optional[pd.Series] = None,
        title: Optional[str] = None,
        figsize: tuple = (16, 12),
        show: bool = True,
        save_path: Optional[str] = None,
    ) -> plt.Figure:
        """
        Visualize strategy performance with four stacked plots:
        1) Equity curve (normalized) with optional benchmark
        2) Drawdown (%), filled area
        3) Daily returns (%) bar chart
        4) Returns distribution (histogram)

        Expects values_df to include columns: 'total_value', optional 'returns', optional 'drawdown'.
        Index should be datetime; if a 'date' column exists, it will be used as index.
        """
        try:
            self.logger.info("Generating backtest charts")

            # Prepare index
            df = values_df.copy()
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df = df.set_index('date')
            df.index = pd.to_datetime(df.index)

            # Sanity checks
            if 'total_value' not in df.columns:
                raise ValueError("values_df must contain 'total_value' column")

            # Compute returns/drawdown if missing
            if 'returns' not in df.columns:
                df['returns'] = df['total_value'].pct_change().fillna(0.0)
            if 'drawdown' not in df.columns:
                rolling_max = df['total_value'].expanding().max()
                df['drawdown'] = (df['total_value'] - rolling_max) / rolling_max

            # Palette
            color_eq = '#2575FC'       # strategy line
            color_bm = '#F25F5C'       # benchmark line
            color_pos = '#00B894'      # positive bar
            color_neg = '#E17055'      # negative bar
            color_dd_fill = '#F8A5A5'  # drawdown fill
            color_dd_line = '#D63031'  # drawdown line

            fig, axes = plt.subplots(4, 1, figsize=figsize)
            if not title:
                title = 'Backtest Performance'
            fig.suptitle(title, fontsize=18, fontweight='bold', y=0.97)

            # 1) Equity curve normalized
            ax1 = axes[0]
            strategy_nv = df['total_value'] / float(df['total_value'].iloc[0])
            ax1.plot(df.index, strategy_nv.values, linewidth=2.2, color=color_eq, label='Strategy')

            if benchmark_close is not None and not benchmark_close.empty:
                b = pd.Series(benchmark_close).dropna()
                b.index = pd.to_datetime(b.index)
                b_ret = b.pct_change().fillna(0.0)
                b_nv = (1.0 + b_ret).cumprod()
                b_nv = b_nv / float(b_nv.iloc[0])
                ax1.plot(b_nv.index, b_nv.values, linewidth=2.0, color=color_bm, linestyle='--', label='Benchmark')
                ax1.legend(loc='upper left', frameon=False)

            ax1.set_title('Equity (normalized)', fontsize=14)
            ax1.set_xlabel('Date', fontsize=10)
            ax1.set_ylabel('Net Value', fontsize=11)
            ax1.grid(True, alpha=0.25, linestyle='--')
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
            plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
            for spine in ['top','right']:
                ax1.spines[spine].set_visible(False)

            # 2) Drawdown (%)
            ax2 = axes[1]
            dd_pct = df['drawdown'] * 100.0
            ax2.fill_between(df.index, dd_pct.values, 0, color=color_dd_fill, alpha=0.6)
            ax2.plot(df.index, dd_pct.values, color=color_dd_line, linewidth=1.2)
            ax2.set_title('Drawdown', fontsize=14)
            ax2.set_xlabel('Date', fontsize=10)
            ax2.set_ylabel('Drawdown', fontsize=11)
            ax2.yaxis.set_major_formatter(FuncFormatter(lambda y,_: f"{y:.0f}%"))
            ax2.grid(True, alpha=0.25, linestyle='--')
            ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
            plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
            for spine in ['top','right']:
                ax2.spines[spine].set_visible(False)

            # 3) Daily returns (%)
            ax3 = axes[2]
            returns_pct = df['returns'] * 100.0
            colors = [color_pos if x > 0 else color_neg for x in returns_pct]
            ax3.bar(df.index, returns_pct.values, color=colors, alpha=0.8, width=0.8)
            ax3.axhline(y=0, color='black', linewidth=0.5, linestyle='-')
            y_abs_max = max(abs(returns_pct.max()), abs(returns_pct.min()))
            y_abs_max = y_abs_max if y_abs_max > 0 else 1.0
            ax3.set_ylim(-y_abs_max * 1.1, y_abs_max * 1.1)
            ax3.set_title('Daily Return', fontsize=14)
            ax3.set_xlabel('Date', fontsize=10)
            ax3.set_ylabel('Return', fontsize=11)
            ax3.yaxis.set_major_formatter(FuncFormatter(lambda y,_: f"{y:.1f}%"))
            ax3.grid(True, alpha=0.25, linestyle='--', axis='y')
            ax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            ax3.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
            plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45, ha='right')
            for spine in ['top','right']:
                ax3.spines[spine].set_visible(False)

            # 4) Returns distribution (hist)
            ax4 = axes[3]
            ret_nonzero = returns_pct[returns_pct != 0]
            if len(ret_nonzero) > 0:
                ax4.hist(ret_nonzero.values, bins=40, color='#7f8c8d', alpha=0.85, edgecolor='white')
                ax4.axvline(x=0, color='gray', linestyle='--', linewidth=1, alpha=0.8)
            ax4.set_title('Return Distribution (trading days)', fontsize=14)
            ax4.set_xlabel('Return (%)', fontsize=11)
            ax4.set_ylabel('Frequency', fontsize=11)
            ax4.grid(True, alpha=0.25, linestyle='--', axis='y')
            for spine in ['top','right']:
                ax4.spines[spine].set_visible(False)

            plt.tight_layout(rect=[0, 0, 1, 0.96])

            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                self.logger.info(f"Chart saved to {save_path}")

            if show:
                plt.show()

            return fig

        except Exception as e:
            self.logger.error(f"Error generating backtest charts: {str(e)}")
            raise

