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
                self.logger.info("Aligned signal indices with data indices")

            if show_timeline:
                fig, axes = plt.subplots(2, 1, figsize=figsize, height_ratios=[3, 1])
                ax_price = axes[0]
                ax_indicator = axes[1]
            else:
                fig, ax_price = plt.subplots(1, 1, figsize=figsize)
                ax_indicator = None

            price_data = data[price_column]

            # Prefer candlesticks if OHLC present, fallback to line
            if all(col in data.columns for col in ['Open', 'High', 'Low', 'Close']):
                open_ = data['Open']
                high = data['High']
                low = data['Low']
                close = data['Close']
                x = mdates.date2num(data.index.to_pydatetime())

                def draw_candles(ax, o, h, l, c, xvals, width=0.5):
                    wick_color = '#666666'
                    up_fill = '#555555'      # dark gray
                    down_fill = '#B3B3B3'    # light gray
                    edge_color = '#666666'
                    for xi, oi, hi, li, ci in zip(xvals, o, h, l, c):
                        is_up = ci >= oi
                        color = up_fill if is_up else down_fill
                        # wick
                        ax.vlines(xi, li, hi, color=wick_color, linewidth=0.8, alpha=0.9)
                        # body
                        body_low = min(oi, ci)
                        body_h = abs(ci - oi)
                        if body_h == 0:
                            ax.hlines(ci, xi - width/2, xi + width/2, color=edge_color, linewidth=1.0, alpha=0.9)
                        else:
                            rect = Rectangle((xi - width/2, body_low), width, body_h,
                                             facecolor=color, edgecolor=edge_color, alpha=0.95)
                            ax.add_patch(rect)

                draw_candles(ax_price, open_.values, high.values, low.values, close.values, x, width=0.6)
                ax_price.xaxis_date()
                ax_price.xaxis.set_major_locator(mdates.AutoDateLocator())
                ax_price.xaxis.set_major_formatter(mdates.ConciseDateFormatter(mdates.AutoDateLocator()))
            else:
                ax_price.plot(price_data.index, price_data.values,
                              label='Price', linewidth=1.5, color='black', alpha=0.8)

            if indicators:
                # Try to style Bollinger-like keys specially
                style_map = {
                    'upper': dict(color='#1f77b4', linewidth=1.6, linestyle='-'),   # blue
                    'middle': dict(color='#7f7f7f', linewidth=1.2, linestyle='--'), # dashed gray
                    'lower': dict(color='#9467bd', linewidth=1.6, linestyle='-'),   # purple
                }
                palette = plt.cm.tab10(range(10))
                for i, (name, indicator_series) in enumerate(indicators.items()):
                    if len(indicator_series) != len(data):
                        indicator_series = indicator_series.reindex(data.index)
                    key = name.lower()
                    chosen = None
                    for k in ('upper', 'middle', 'lower'):
                        if k in key:
                            chosen = style_map[k]
                            break
                    if chosen is None:
                        chosen = dict(color=palette[i % 10], linewidth=1.2, linestyle='-')
                    ax_price.plot(
                        indicator_series.index,
                        indicator_series.values,
                        label=name,
                        alpha=0.9,
                        **chosen,
                    )

            buy_signals = signals == 1
            if buy_signals.any():
                buy_idx = price_data.index[buy_signals]
                ax_price.scatter(
                    buy_idx,
                    price_data.loc[buy_idx],
                    marker='^',
                    s=60,
                    facecolors='#FFD700',  # yellow fill
                    edgecolors='#8B8000',   # dark yellow edge
                    linewidths=0.8,
                    label='Buy',
                    zorder=4,
                )

            sell_signals = signals == -1
            if sell_signals.any():
                sell_idx = price_data.index[sell_signals]
                ax_price.scatter(
                    sell_idx,
                    price_data.loc[sell_idx],
                    marker='v',
                    s=60,
                    facecolors='#d62728',  # red fill
                    edgecolors='#000000',   # black edge
                    linewidths=0.8,
                    label='Sell',
                    zorder=4,
                )

            ax_price.set_xlabel('Date', fontsize=10)
            ax_price.set_ylabel('Price', fontsize=10)
            if not title:
                title = f"Trading Signals Chart - {price_column}"
            ax_price.set_title(title, fontsize=12, fontweight='bold')
            ax_price.legend(loc='best', fontsize=9)
            ax_price.grid(True, alpha=0.3)
            ax_price.tick_params(axis='x', rotation=45)

            if show_timeline:
                signal_values = signals.astype(float)
                signal_values[signal_values == 0] = None
                ax_indicator.plot(signal_values.index, signal_values.values,
                                  marker='o', markersize=3, linestyle='-', linewidth=0.5, alpha=0.5)
                ax_indicator.axhline(y=0, color='gray', linestyle='--', linewidth=0.5, alpha=0.5)
                ax_indicator.fill_between(signal_values.index, 0, signal_values.values,
                                          where=(signal_values > 0),
                                          color='green', alpha=0.2, label='Buy Zone')
                ax_indicator.fill_between(signal_values.index, 0, signal_values.values,
                                          where=(signal_values < 0),
                                          color='red', alpha=0.2, label='Sell Zone')
                ax_indicator.set_xlabel('Date', fontsize=9)
                ax_indicator.set_ylabel('Signal', fontsize=9)
                ax_indicator.set_title('Signal Timeline', fontsize=10)
                ax_indicator.set_ylim(-1.5, 1.5)
                ax_indicator.set_yticks([-1, 0, 1])
                ax_indicator.set_yticklabels(['Sell', 'Hold', 'Buy'])
                ax_indicator.grid(True, alpha=0.3)
                ax_indicator.tick_params(axis='x', rotation=45)

            plt.tight_layout()

            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                self.logger.info(f"Chart saved to {save_path}")

            if show:
                plt.show()

            return fig
        except Exception as e:
            self.logger.info(f"Error generating signal chart: {str(e)}")
            raise


