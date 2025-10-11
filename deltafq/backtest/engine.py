"""回测引擎"""

import pandas as pd
from typing import Optional
from deltafq.strategy.base import Strategy
from deltafq.backtest.result import BacktestResult


class BacktestEngine:
    """回测引擎"""
    
    def __init__(
        self,
        initial_cash: float = 100000,
        commission: float = 0.0003,
        slippage: float = 0.0
    ):
        """初始化回测引擎
        
        Args:
            initial_cash: 初始资金
            commission: 手续费率
            slippage: 滑点
        """
        self.initial_cash = initial_cash
        self.commission = commission
        self.slippage = slippage
        
    def run(
        self,
        data: pd.DataFrame,
        strategy: Strategy
    ) -> BacktestResult:
        """运行回测
        
        Args:
            data: 历史数据
            strategy: 策略实例
            
        Returns:
            回测结果
        """
        for idx, bar in data.iterrows():
            strategy.on_bar(bar)
        
        result = BacktestResult(
            initial_cash=self.initial_cash,
            data=data,
            signals=strategy.get_signals()
        )
        return result

