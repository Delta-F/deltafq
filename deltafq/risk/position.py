"""仓位管理"""

from typing import Optional


class PositionManager:
    """仓位管理器"""
    
    def __init__(self, max_position: float = 1.0):
        """初始化仓位管理器
        
        Args:
            max_position: 最大持仓比例
        """
        self.max_position = max_position
        self.current_position = 0.0
        
    def calculate_size(
        self,
        signal: str,
        cash: float,
        price: float,
        method: str = "fixed"
    ) -> float:
        """计算交易数量
        
        Args:
            signal: 信号类型 'buy' or 'sell'
            cash: 可用资金
            price: 当前价格
            method: 计算方法
            
        Returns:
            交易数量
        """
        if method == "fixed":
            return cash * self.max_position / price
        return 0.0

