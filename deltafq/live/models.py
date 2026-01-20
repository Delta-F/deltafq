from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class TickData:
    symbol: str
    price: float
    timestamp: datetime
    volume: Optional[int] = None
    source: Optional[str] = None


@dataclass
class OrderRequest:
    symbol: str
    quantity: int
    price: float
    order_type: str = "limit"
    timestamp: Optional[datetime] = None
