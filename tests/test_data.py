"""数据模块测试"""

import pytest
import pandas as pd
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from deltafq.data import get_stock_daily


class TestDataModule:
    def test_get_stock_daily(self):
        data = get_stock_daily('000001.SZ', start='2023-01-01', end='2023-12-31')
        assert isinstance(data, pd.DataFrame)
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            assert col in data.columns
        assert len(data) > 0
    
    def test_data_integrity(self):
        data = get_stock_daily('000001.SZ', start='2023-01-01', end='2023-01-31')
        assert (data['high'] >= data['low']).all()
        assert (data['volume'] >= 0).all()

