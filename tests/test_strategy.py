"""策略模块测试"""

import pytest
import pandas as pd
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from deltafq.strategy import Strategy


class SimpleStrategy(Strategy):
    def on_bar(self, bar):
        if bar.close > 100:
            self.buy()
        else:
            self.sell()


class TestStrategy:
    def test_strategy_initialization(self):
        strategy = SimpleStrategy()
        assert strategy.position == 0
        assert strategy.cash == 100000
        assert len(strategy.signals) == 0
    
    def test_buy_signal(self):
        strategy = SimpleStrategy()
        strategy.buy()
        assert len(strategy.signals) == 1
        assert strategy.signals[0]['action'] == 'buy'
    
    def test_sell_signal(self):
        strategy = SimpleStrategy()
        strategy.sell()
        assert len(strategy.signals) == 1
        assert strategy.signals[0]['action'] == 'sell'
    
    def test_on_bar(self):
        strategy = SimpleStrategy()
        bar = pd.Series({'close': 110})
        strategy.on_bar(bar)
        assert strategy.signals[-1]['action'] == 'buy'
        bar = pd.Series({'close': 90})
        strategy.on_bar(bar)
        assert strategy.signals[-1]['action'] == 'sell'

