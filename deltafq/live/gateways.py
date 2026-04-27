from abc import ABC, abstractmethod
from typing import Callable, Dict, List, Optional

from .models import TickData, OrderRequest
from ..core.base import BaseComponent


class DataGateway(BaseComponent, ABC):
    """实盘行情网关抽象：连接、订阅、推送与日内行情查询。"""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._tick_handler: Optional[Callable[[TickData], None]] = None

    def set_tick_handler(self, handler: Callable[[TickData], None]) -> None:
        """注册 Tick 回调。"""
        self._tick_handler = handler

    def emit_tick(self, tick: TickData) -> None:
        """分发 Tick（已注册回调时才触发）。"""
        if self._tick_handler:
            self._tick_handler(tick)

    @abstractmethod
    def connect(self) -> bool:
        """建立网关连接。"""
        raise NotImplementedError

    @abstractmethod
    def subscribe(self, symbols: List[str]) -> bool:
        """订阅一个或多个标的。"""
        raise NotImplementedError

    @abstractmethod
    def start(self) -> None:
        """启动行情循环（轮询或推送）。"""
        raise NotImplementedError

    @abstractmethod
    def stop(self) -> None:
        """停止网关并释放资源。"""
        raise NotImplementedError

    @abstractmethod
    def get_today_ohlc(self, symbol: str) -> Optional[Dict[str, float]]:
        """返回当日开高低；不可用时返回 None。"""
        raise NotImplementedError

    @abstractmethod
    def get_depths(self, symbol: str, levels: int = 5) -> Dict[str, List[Dict[str, float]]]:
        """返回盘口深度：bids/asks 各档价格与委托量。"""
        raise NotImplementedError

class TradeGateway(ABC):
    """实盘交易网关抽象：连接、下单、撤单、关闭。"""

    @abstractmethod
    def connect(self) -> bool:
        """建立交易连接。"""
        raise NotImplementedError

    @abstractmethod
    def send_order(self, req: OrderRequest) -> str:
        """发送委托，返回委托号。"""
        raise NotImplementedError

    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """撤销指定委托。"""
        raise NotImplementedError

    @abstractmethod
    def stop(self) -> None:
        """停止交易网关并释放资源。"""
        raise NotImplementedError
