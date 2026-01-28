from abc import ABC, abstractmethod
from typing import Callable, List, Optional

from .models import TickData, OrderRequest
from ..core.base import BaseComponent


class DataGateway(BaseComponent, ABC):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._tick_handler: Optional[Callable[[TickData], None]] = None

    def set_tick_handler(self, handler: Callable[[TickData], None]) -> None:
        self._tick_handler = handler

    @abstractmethod
    def connect(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def subscribe(self, symbols: List[str]) -> bool:
        raise NotImplementedError

    @abstractmethod
    def start(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def stop(self) -> None:
        raise NotImplementedError


class TradeGateway(ABC):
    @abstractmethod
    def connect(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def send_order(self, req: OrderRequest) -> str:
        raise NotImplementedError

    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        raise NotImplementedError
