"""
Signal charts for DeltaFQ.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
from typing import Optional, Dict
from ..core.base import BaseComponent


class SignalChart(BaseComponent):
    """Chart class for plotting price with indicators and trading signals."""

    def initialize(self) -> bool:
        self.logger.info("Initializing signal chart")
        plt.ion()
        return True

    def plot_signals(
        self,
        data: pd.DataFrame,
        signals: pd.Series,
        indicators: Optional[Dict[str, pd.Series]] = None,
        price_column: str = 'Close',
        title: Optional[str] = None,
        figsize: tuple = (14, 6),
        show: bool = True,
        save_path: Optional[str] = None,
        show_timeline: bool = False,
    ) -> plt.Figure:
        try:
            self.logger.info("Generating signal chart with price and indicators")

            if price_column not in data.columns:
                raise ValueError(f"Column '{price_column}' not found in data")

            if len(data) != len(signals):
                raise ValueError("Data and signals must have the same length")

            if not data.index.equals(signals.index):
                signals = signals.reindex(data.index)

            # Create figure and axes
            fig = plt.figure(figsize=figsize, facecolor='#F5F5F5')
            if show_timeline:
                gs = fig.add_gridspec(2, 1, height_ratios=[3, 1], hspace=0.15)
                ax_price = fig.add_subplot(gs[0])
                ax_indicator = fig.add_subplot(gs[1])
            else:
                ax_price = fig.add_subplot(111)
                ax_indicator = None

            ax_price.set_facecolor('#FFFFFF')
            if ax_indicator:
                ax_indicator.set_facecolor('#FFFFFF')

            price_data = data[price_column]

            # Draw price chart (candlesticks or line)
            if all(col in data.columns for col in ['Open', 'High', 'Low', 'Close']):
                self._draw_candlesticks(ax_price, data)
            else:
                ax_price.plot(price_data.index, price_data.values, label='Price', 
                             linewidth=2.0, color='#2C3E50', alpha=0.9)

            # Plot indicators
            if indicators:
                self._plot_indicators(ax_price, indicators, data)

            # Plot signals
            self._plot_signal_markers(ax_price, price_data, signals)

            # Apply styling
            self._apply_ax_style(ax_price, title or f"Trading Signals Chart - {price_column}")

            # Plot timeline if requested
            if show_timeline and ax_indicator:
                self._plot_timeline(ax_indicator, signals)

            plt.tight_layout()

            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='#F5F5F5')
                self.logger.info(f"Chart saved to {save_path}")

            if show:
                plt.show(block=False)
                plt.pause(0.1)
                fig.canvas.draw()
                fig.canvas.flush_events()

            return fig
        except Exception as e:
            self.logger.info(f"Error generating signal chart: {str(e)}")
            raise

    def _draw_candlesticks(self, ax, data: pd.DataFrame):
        """Draw candlestick chart."""
        color_up, color_down = '#E74C3C', '#27AE60'
        color_wick, color_edge = '#34495E', '#2C3E50'
        x = mdates.date2num(data.index.to_pydatetime())
        o, h, l, c = data['Open'].values, data['High'].values, data['Low'].values, data['Close'].values

        for xi, oi, hi, li, ci in zip(x, o, h, l, c):
            body_color = color_up if ci >= oi else color_down
            ax.vlines(xi, li, hi, color=color_wick, linewidth=1.0, alpha=0.7, zorder=1)
            body_low, body_h = min(oi, ci), abs(ci - oi)
            if body_h == 0:
                ax.hlines(ci, xi - 0.3, xi + 0.3, color=color_edge, linewidth=1.2, alpha=0.7, zorder=2)
            else:
                ax.add_patch(Rectangle((xi - 0.3, body_low), 0.6, body_h,
                                      facecolor=body_color, edgecolor=color_edge, 
                                      linewidth=0.8, alpha=0.7, zorder=2))
        ax.xaxis_date()
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(mdates.AutoDateLocator()))

    def _plot_indicators(self, ax, indicators: Dict[str, pd.Series], data: pd.DataFrame):
        """Plot technical indicators."""
        style_map = {
            'upper': {'color': '#3498DB', 'linewidth': 1.8, 'linestyle': '-', 'alpha': 0.85},
            'middle': {'color': '#95A5A6', 'linewidth': 1.5, 'linestyle': '--', 'alpha': 0.75},
            'lower': {'color': '#9B59B6', 'linewidth': 1.8, 'linestyle': '-', 'alpha': 0.85},
        }
        palette = ['#E67E22', '#F39C12', '#16A085', '#2980B9', '#8E44AD']

        for i, (name, series) in enumerate(indicators.items()):
            if len(series) != len(data):
                series = series.reindex(data.index)
            key = name.lower()
            style = next((style_map[k] for k in ('upper', 'middle', 'lower') if k in key), 
                        {'color': palette[i % len(palette)], 'linewidth': 1.5, 'linestyle': '-', 'alpha': 0.8})
            ax.plot(series.index, series.values, label=name, zorder=3, **style)

    def _plot_signal_markers(self, ax, price_data: pd.Series, signals: pd.Series):
        """Plot buy and sell signal markers."""
        signal_configs = [
            (signals == 1, '^', '#E74C3C', '#C0392B', 'Buy'),
            (signals == -1, 'v', '#27AE60', '#229954', 'Sell')
        ]
        for signal_mask, marker, face_color, edge_color, label in signal_configs:
            if signal_mask.any():
                idx = price_data.index[signal_mask]
                ax.scatter(idx, price_data.loc[idx], marker=marker, s=100,
                          facecolors=face_color, edgecolors=edge_color, linewidths=1.2,
                          label=label, zorder=5, alpha=0.9)

    def _apply_ax_style(self, ax, title: str):
        """Apply styling to axes."""
        ax.set_xlabel('Date', fontsize=11, color='#34495E', fontweight='medium')
        ax.set_ylabel('Price', fontsize=11, color='#34495E', fontweight='medium')
        ax.set_title(title, fontsize=14, fontweight='bold', color='#2C3E50', pad=15)
        ax.legend(loc='upper left', fontsize=10, framealpha=0.9, 
                 facecolor='white', edgecolor='#BDC3C7', fancybox=True, shadow=True)
        ax.grid(True, alpha=0.2, linestyle='--', linewidth=0.8, color='#BDC3C7')
        ax.set_axisbelow(True)
        for spine in ['top', 'right']:
            ax.spines[spine].set_visible(False)
        for spine in ['left', 'bottom']:
            ax.spines[spine].set_color('#BDC3C7')
        ax.tick_params(axis='x', rotation=45, colors='#34495E', labelsize=9)
        ax.tick_params(axis='y', colors='#34495E', labelsize=9)

    def _plot_timeline(self, ax, signals: pd.Series):
        """Plot signal timeline."""
        signal_values = signals.astype(float).replace(0, None)
        ax.plot(signal_values.index, signal_values.values, marker='o', markersize=4,
               linestyle='-', linewidth=1.0, alpha=0.6, color='#7F8C8D', zorder=2)
        ax.axhline(y=0, color='#95A5A6', linestyle='--', linewidth=1.0, alpha=0.5)
        ax.fill_between(signal_values.index, 0, signal_values.values, where=(signal_values > 0),
                       color='#E74C3C', alpha=0.25, label='Buy Zone', zorder=1)
        ax.fill_between(signal_values.index, 0, signal_values.values, where=(signal_values < 0),
                       color='#27AE60', alpha=0.25, label='Sell Zone', zorder=1)
        ax.set_xlabel('Date', fontsize=10, color='#34495E')
        ax.set_ylabel('Signal', fontsize=10, color='#34495E')
        ax.set_title('Signal Timeline', fontsize=11, fontweight='bold', color='#2C3E50')
        ax.set_ylim(-1.5, 1.5)
        ax.set_yticks([-1, 0, 1])
        ax.set_yticklabels(['Sell', 'Hold', 'Buy'])
        ax.grid(True, alpha=0.2, linestyle='--', linewidth=0.8, color='#BDC3C7')
        ax.set_axisbelow(True)
        for spine in ['top', 'right']:
            ax.spines[spine].set_visible(False)
        for spine in ['left', 'bottom']:
            ax.spines[spine].set_color('#BDC3C7')
        ax.tick_params(axis='x', rotation=45, colors='#34495E', labelsize=9)
        ax.tick_params(axis='y', colors='#34495E', labelsize=9)
