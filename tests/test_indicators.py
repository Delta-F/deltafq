"""技术指标测试"""

import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from deltafq.indicators import SMA, EMA, MACD, RSI, BOLL


class TestIndicators:
    @pytest.fixture
    def sample_data(self):
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        prices = pd.Series(100 + np.random.randn(100).cumsum(), index=dates)
        return prices
    
    def test_sma(self, sample_data):
        ma = SMA(sample_data, 5)
        assert isinstance(ma, pd.Series)
        assert len(ma) == len(sample_data)
        assert pd.isna(ma.iloc[:4]).all()
    
    def test_ema(self, sample_data):
        ema = EMA(sample_data, 5)
        assert isinstance(ema, pd.Series)
        assert len(ema) == len(sample_data)
    
    def test_macd(self, sample_data):
        macd = MACD(sample_data)
        assert isinstance(macd, pd.DataFrame)
        assert 'dif' in macd.columns
        assert 'dea' in macd.columns
        assert 'macd' in macd.columns
    
    def test_rsi(self, sample_data):
        rsi = RSI(sample_data, 14)
        assert isinstance(rsi, pd.Series)
        valid_rsi = rsi.dropna()
        assert (valid_rsi >= 0).all() and (valid_rsi <= 100).all()
    
    def test_boll(self, sample_data):
        boll = BOLL(sample_data, 20)
        assert isinstance(boll, pd.DataFrame)
        assert 'upper' in boll.columns
        assert 'middle' in boll.columns
        assert 'lower' in boll.columns
        valid_idx = ~boll['upper'].isna()
        assert (boll.loc[valid_idx, 'upper'] >= boll.loc[valid_idx, 'middle']).all()
        assert (boll.loc[valid_idx, 'middle'] >= boll.loc[valid_idx, 'lower']).all()

