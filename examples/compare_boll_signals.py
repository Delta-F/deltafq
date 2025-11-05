"""
Compare different Bollinger Bands signal methods on a single symbol.
"""

import os
import sys
import warnings
warnings.filterwarnings('ignore')

import pandas as pd

# Ensure project root on path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from deltafq.data.fetcher import DataFetcher
from deltafq.indicators import TechnicalIndicators
from deltafq.strategy import SignalGenerator
from deltafq.charts import PriceChart, SignalChart
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle


def main():
    symbol = '601398.SS'
    start_date = '2025-09-01'
    end_date = '2025-10-30'

    fetcher = DataFetcher()
    indicators = TechnicalIndicators()
    generator = SignalGenerator()
    chart = PriceChart()
    signal_chart = SignalChart()

    data = fetcher.fetch_data(symbol, start_date, end_date, clean=True)

    # Precompute Bollinger Bands
    bands = indicators.boll(data['Close'], period=5, std_dev=1)

    # Generate signals for different methods (two panels)
    methods = ['touch_and_breakout', 'cross']
    signals_map = {}
    for m in methods:
        sig = generator.boll_signals(price=data['Close'], bands=bands, method=m)
        signals_map[m] = sig

    # Simple comparison: counts and sample dates
    summary_rows = []
    for m, sig in signals_map.items():
        buys = int((sig == 1).sum())
        sells = int((sig == -1).sum())
        holds = int((sig == 0).sum())
        summary_rows.append({'method': m, 'buy': buys, 'sell': sells, 'hold': holds})
    summary_df = pd.DataFrame(summary_rows).set_index('method')
    print('Boll signal counts by method:')
    print(summary_df)

    # Plot two subplots for visual comparison (K-line candlesticks)
    try:
        rows = 2
        fig, axes = plt.subplots(rows, 1, figsize=(14, 2.8 * rows + 2), sharex=True)
        price = data['Close']
        open_ = data['Open'] if 'Open' in data.columns else price.shift(1).fillna(price)
        high = data['High'] if 'High' in data.columns else price
        low = data['Low'] if 'Low' in data.columns else price
        date_nums = mdates.date2num(data.index.to_pydatetime())

        def draw_candles(ax, o, h, l, c, x, width=0.5):
            wick_color = '#666666'
            up_fill = '#555555'      # dark gray
            down_fill = '#B3B3B3'    # light gray
            edge_color = '#666666'
            for xi, oi, hi, li, ci in zip(x, o, h, l, c):
                is_up = ci >= oi
                color = up_fill if is_up else down_fill
                # wick (shadow)
                ax.vlines(xi, li, hi, color=wick_color, linewidth=0.8, alpha=0.9)
                # body (rectangle or doji line)
                body_low = min(oi, ci)
                body_h = abs(ci - oi)
                if body_h == 0:
                    ax.hlines(ci, xi - width/2, xi + width/2, color=edge_color, linewidth=1.0, alpha=0.9)
                else:
                    rect = Rectangle((xi - width/2, body_low), width, body_h,
                                     facecolor=color, edgecolor=edge_color, alpha=0.95)
                    ax.add_patch(rect)

        method_titles = {'touch_and_breakout': 'Touch and Breakout', 'cross': 'Cross'}
        band_colors = {
            'upper': '#1f77b4',   # blue
            'middle': '#7f7f7f',  # gray
            'lower': '#9467bd',   # purple
        }
        for idx, m in enumerate(methods):
            ax = axes[idx]
            sig = signals_map[m]
            # plot candlesticks
            draw_candles(ax, open_.values, high.values, low.values, price.values, date_nums, width=0.6)
            # plot bands
            ax.plot(bands.index, bands['upper'].values, color=band_colors['upper'], alpha=0.9, linewidth=1.2, label='BB Upper', zorder=2)
            ax.plot(bands.index, bands['middle'].values, color=band_colors['middle'], alpha=0.9, linewidth=1.0, linestyle='--', label='BB Middle', zorder=2)
            ax.plot(bands.index, bands['lower'].values, color=band_colors['lower'], alpha=0.9, linewidth=1.2, label='BB Lower', zorder=2)
            # plot signals
            buy_idx = sig[sig == 1].index
            sell_idx = sig[sig == -1].index
            ax.scatter(buy_idx, price.loc[buy_idx], marker='^', facecolor='#2ca02c', edgecolor='#FFD700', linewidths=0.8, s=60, label='Buy', zorder=3)
            ax.scatter(sell_idx, price.loc[sell_idx], marker='v', facecolor='#d62728', edgecolor='#000000', linewidths=0.8, s=60, label='Sell', zorder=3)
            ax.set_title(f"{method_titles.get(m, m)}")
            ax.grid(True, alpha=0.3)
            ax.xaxis_date()
            ax.xaxis.set_major_locator(mdates.AutoDateLocator())
            ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(mdates.AutoDateLocator()))
        # Legends
        handles, labels = axes[0].get_legend_handles_labels()
        fig.legend(handles, labels, loc='upper center', ncol=5)
        fig.suptitle(f'{symbol} Boll Signals Comparison', fontsize=12, fontweight='bold')
        plt.tight_layout(rect=[0, 0, 1, 0.95])
        plt.show()
    except Exception as e:
        print(f'Plot failed: {e}')

    # Test SignalChart invocation with 'cross' signals
    try:
        signal_chart.plot_signals(
            data=data,
            signals=signals_map['cross'],
            indicators={
                'BB_upper': bands['upper'],
                'BB_middle': bands['middle'],
                'BB_lower': bands['lower']
            },
            title=f'{symbol} SignalChart Test (cross)'
        )
    except Exception as e:
        print(f'SignalChart plot failed: {e}')

if __name__ == '__main__':
    main()


