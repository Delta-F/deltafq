"""策略基类"""

from abc import ABC, abstractmethod
from typing import Dict, Any
import pandas as pd


class Strategy(ABC):
    """策略抽象基类"""
    
    def __init__(self):
        self.position = 0  # 当前持仓
        self.cash = 100000  # 初始资金
        self.signals = []  # 信号记录
        
    @abstractmethod
    def on_bar(self, bar: pd.Series) -> None:
        """处理每根K线
        
        Args:
            bar: 包含OHLCV数据的Series
        """
        pass
    
    def buy(self, size: float = 1.0) -> None:
        """买入信号
        
        Args:
            size: 交易数量
        """
        self.signals.append({'action': 'buy', 'size': size})
    
    def sell(self, size: float = 1.0) -> None:
        """卖出信号
        
        Args:
            size: 交易数量
        """
        self.signals.append({'action': 'sell', 'size': size})
    
    def get_signals(self) -> list:
        """获取所有交易信号"""
        return self.signals

