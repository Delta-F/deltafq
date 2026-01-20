from ...live.gateways import TradeGateway
from ...live.models import OrderRequest
from ...trader.engine import ExecutionEngine


class PaperTradeGateway(TradeGateway):
    def __init__(self, initial_capital: float = 100000.0, commission: float = 0.001) -> None:
        self._engine = ExecutionEngine(
            broker=None,
            initial_capital=initial_capital,
            commission=commission,
        )

    def connect(self) -> bool:
        return self._engine.initialize()

    def send_order(self, req: OrderRequest) -> str:
        return self._engine.execute_order(
            symbol=req.symbol,
            quantity=req.quantity,
            order_type=req.order_type,
            price=req.price,
            timestamp=req.timestamp,
        )

    def cancel_order(self, order_id: str) -> bool:
        return self._engine.order_manager.cancel_order(order_id)
