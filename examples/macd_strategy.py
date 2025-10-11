"""MACD策略示例

DIF上穿DEA时买入，下穿时卖出。
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import deltafq as dfq


class MACDStrategy(dfq.strategy.Strategy):
    """MACD策略"""
    
    def __init__(self):
        super().__init__()
        self.prev_signal = None
    
    def on_bar(self, bar):
        dif = getattr(bar, 'dif', None)
        dea = getattr(bar, 'dea', None)
        
        if dif is None or dea is None:
            return
        
        if dif > dea and self.prev_signal != 'buy':
            self.buy()
            self.prev_signal = 'buy'
        elif dif < dea and self.prev_signal != 'sell':
            self.sell()
            self.prev_signal = 'sell'


def main():
    print("获取数据...")
    data = dfq.data.get_stock_daily('000001.SZ', start='2020-01-01', end='2023-12-31')
    
    print("计算MACD指标...")
    macd = dfq.indicators.MACD(data['close'])
    data = data.join(macd)
    
    strategy = MACDStrategy()
    
    print("运行回测...")
    engine = dfq.backtest.BacktestEngine(initial_cash=100000, commission=0.0003)
    result = engine.run(data, strategy)
    
    print("\n回测结果:")
    print("-" * 50)
    for key, value in result.summary().items():
        print(f"{key}: {value}")


if __name__ == '__main__':
    main()

