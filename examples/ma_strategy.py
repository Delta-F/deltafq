"""双均线策略示例

当短期均线上穿长期均线时买入，下穿时卖出。
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import deltafq as dfq


class MAStrategy(dfq.strategy.Strategy):
    """双均线交叉策略"""
    
    def __init__(self, short_window=5, long_window=20):
        super().__init__()
        self.short_window = short_window
        self.long_window = long_window
        self.prev_signal = None
    
    def on_bar(self, bar):
        ma_short = getattr(bar, f'ma{self.short_window}', None)
        ma_long = getattr(bar, f'ma{self.long_window}', None)
        
        if ma_short is None or ma_long is None:
            return
        
        if ma_short > ma_long and self.prev_signal != 'buy':
            self.buy()
            self.prev_signal = 'buy'
        elif ma_short < ma_long and self.prev_signal != 'sell':
            self.sell()
            self.prev_signal = 'sell'


def main():
    print("获取数据...")
    data = dfq.data.get_stock_daily('000001.SZ', start='2020-01-01', end='2023-12-31')
    
    print("计算技术指标...")
    data['ma5'] = dfq.indicators.SMA(data['close'], 5)
    data['ma20'] = dfq.indicators.SMA(data['close'], 20)
    
    strategy = MAStrategy(short_window=5, long_window=20)
    
    print("运行回测...")
    engine = dfq.backtest.BacktestEngine(initial_cash=100000, commission=0.0003)
    result = engine.run(data, strategy)
    
    print("\n回测结果:")
    print("-" * 50)
    for key, value in result.summary().items():
        print(f"{key}: {value}")
    
    print("\n绘制图表...")
    result.plot()


if __name__ == '__main__':
    main()

