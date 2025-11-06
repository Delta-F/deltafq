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
from deltafq.charts import SignalChart


def main():
    symbol = '601398.SS'
    start_date = '2025-09-01'
    end_date = '2025-10-30'

    fetcher = DataFetcher()
    indicators = TechnicalIndicators()
    generator = SignalGenerator()
    signal_chart = SignalChart()

    data = fetcher.fetch_data(symbol, start_date, end_date, clean=True)
    bands = indicators.boll(data['Close'], period=5, std_dev=1)

    # Generate signals for different methods
    signals_touch = generator.boll_signals(price=data['Close'], bands=bands, method='touch')
    signals_cross = generator.boll_signals(price=data['Close'], bands=bands, method='cross')

    # Print comparison summary
    summary_data = {
        'touch': {
            'buy': int((signals_touch == 1).sum()),
            'sell': int((signals_touch == -1).sum()),
            'hold': int((signals_touch == 0).sum())
        },
        'cross': {
            'buy': int((signals_cross == 1).sum()),
            'sell': int((signals_cross == -1).sum()),
            'hold': int((signals_cross == 0).sum())
        }
    }
    summary_df = pd.DataFrame(summary_data).T
    print('Boll signal counts by method:')
    print(summary_df)
    print()

    # Prepare indicators dictionary
    indicators_dict = {
        'BB_upper': bands['upper'],
        'BB_middle': bands['middle'],
        'BB_lower': bands['lower']
    }

    # Plot signals for each method
    signal_chart.plot_signals(
        data=data,
        signals=signals_touch,
        indicators=indicators_dict,
        title=f'{symbol} - Touch Method'
    )

    signal_chart.plot_signals(
        data=data,
        signals=signals_cross,
        indicators=indicators_dict,
        title=f'{symbol} - Cross Method'
    )
    
    # Keep windows open until user closes them or presses Enter
    import matplotlib.pyplot as plt
    print("\nCharts displayed. Close windows or press Enter to exit...")
    try:
        input()
    except (EOFError, KeyboardInterrupt):
        pass
    plt.close('all')


if __name__ == '__main__':
    main()
