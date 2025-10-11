"""回测引擎测试"""

import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from deltafq.backtest import BacktestEngine
from deltafq.strategy import Strategy


class DummyStrategy(Strategy):
    def on_bar(self, bar):
        self.buy()


class TestBacktest:
    @pytest.fixture
    def sample_data(self):
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        data = pd.DataFrame({
            'open': 100 + np.random.randn(100),
            'high': 102 + np.random.randn(100),
            'low': 98 + np.random.randn(100),
            'close': 100 + np.random.randn(100),
            'volume': np.random.randint(1000000, 10000000, 100),
        }, index=dates)
        return data
    
    def test_engine_initialization(self):
        engine = BacktestEngine(initial_cash=100000, commission=0.0003)
        assert engine.initial_cash == 100000
        assert engine.commission == 0.0003
    
    def test_run_backtest(self, sample_data):
        engine = BacktestEngine()
        strategy = DummyStrategy()
        result = engine.run(sample_data, strategy)
        assert result is not None
        assert result.initial_cash == engine.initial_cash
    
    def test_backtest_result(self, sample_data):
        engine = BacktestEngine()
        strategy = DummyStrategy()
        result = engine.run(sample_data, strategy)
        summary = result.summary()
        assert 'initial_cash' in summary
        assert 'total_signals' in summary
        assert summary['total_signals'] > 0

