"""交易接口抽象"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List


class Broker(ABC):
    """券商接口抽象基类"""
    
    @abstractmethod
    def submit_order(
        self,
        symbol: str,
        action: str,
        quantity: float,
        order_type: str = "market"
    ) -> str:
        """提交订单
        
        Args:
            symbol: 证券代码
            action: 动作 'buy' or 'sell'
            quantity: 数量
            order_type: 订单类型
            
        Returns:
            订单ID
        """
        pass
    
    @abstractmethod
    def get_position(self) -> List[Dict[str, Any]]:
        """获取持仓信息"""
        pass
    
    @abstractmethod
    def get_account(self) -> Dict[str, Any]:
        """获取账户信息"""
        pass

