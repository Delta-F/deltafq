from typing import Any, Dict, Type

from .gateways import DataGateway, TradeGateway
from ..adapters.data import MiniQmtDataGateway, YFinanceDataGateway
from ..adapters.trade import MiniQmtTradeGateway, PaperTradeGateway

DATA_GATEWAYS: Dict[str, Type[DataGateway]] = {
    "yfinance": YFinanceDataGateway,
    "miniqmt": MiniQmtDataGateway,
}

TRADE_GATEWAYS: Dict[str, Type[TradeGateway]] = {
    "paper": PaperTradeGateway,
    "miniqmt": MiniQmtTradeGateway,
}


def create_data_gateway(name: str, **params: Any) -> DataGateway:
    if name not in DATA_GATEWAYS:
        raise ValueError(f"Unknown data gateway: {name}")
    return DATA_GATEWAYS[name](**params)


def create_trade_gateway(name: str, **params: Any) -> TradeGateway:
    if name not in TRADE_GATEWAYS:
        raise ValueError(f"Unknown trade gateway: {name}")
    return TRADE_GATEWAYS[name](**params)
