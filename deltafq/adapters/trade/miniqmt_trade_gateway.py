"""
实盘交易网关：``TradeGateway`` + :class:`MiniQmtXtTraderClient`。

资金与持仓以柜台查询为准；本网关只负责发单/撤单及 ``order_id`` 字符串与柜台整数委托号对齐。
"""

from __future__ import annotations

import logging
from typing import Optional

from ...live.gateways import TradeGateway
from ...live.models import OrderRequest
from .miniqmt_client import MiniQmtXtTraderClient

logger = logging.getLogger(__name__)


class MiniQmtTradeGateway(TradeGateway):
    """
    miniQMT 实盘交易网关。

    - ``send_order`` / ``cancel_order`` 满足 :class:`LiveEngine` 与回测一致的调用方式。
    - 查询资金、持仓、委托、成交请使用 :attr:`client` 上对应方法。
    """

    def __init__(
        self,
        userdata_mini_path: Optional[str] = None,
        account_id: Optional[str] = None,
        session_id: Optional[int] = None,
        strategy_name: str = "deltafq",
        order_remark: str = "",
        lot_size: int = 100,
    ) -> None:
        self._strategy_name = strategy_name
        self._order_remark = order_remark
        self._lot_size = max(1, int(lot_size))
        self._client = MiniQmtXtTraderClient(
            userdata_mini_path=userdata_mini_path,
            account_id=account_id,
            session_id=session_id,
        )

    @property
    def client(self) -> MiniQmtXtTraderClient:
        return self._client

    def connect(self) -> bool:
        return self._client.connect()

    def stop(self) -> None:
        self._client.disconnect()

    def send_order(self, req: OrderRequest) -> str:
        if req.order_type != "limit":
            raise ValueError("MiniQmtTradeGateway currently supports limit orders only (order_type=limit)")
        qty = int(req.quantity)
        if qty == 0:
            raise ValueError("quantity must be non-zero")
        abs_vol = abs(qty)
        if abs_vol % self._lot_size != 0:
            aligned = (abs_vol // self._lot_size) * self._lot_size
            if aligned <= 0:
                raise ValueError(f"quantity {qty} is below one lot ({self._lot_size})")
            logger.warning("adjusting quantity %s -> %s (lot_size=%s)", abs_vol, aligned, self._lot_size)
            abs_vol = aligned
        is_buy = qty > 0
        oid = self._client.order_stock_limit(
            req.symbol,
            abs_vol,
            float(req.price),
            is_buy,
            strategy_name=self._strategy_name,
            order_remark=self._order_remark,
        )
        if oid is None or int(oid) <= 0:
            raise RuntimeError(f"order_stock failed: oid={oid!r}")
        return str(int(oid))

    def cancel_order(self, order_id: str) -> bool:
        try:
            oid = int(str(order_id).strip())
        except ValueError:
            return False
        if oid <= 0:
            return False
        try:
            rc = self._client.cancel_order_stock(oid)
        except Exception as e:
            logger.warning("cancel_order_stock %s: %s", oid, e)
            rc = -1
        if rc == 0:
            return True
        # 兜底：可撤委托里按 order_id 找合同号
        try:
            for o in self._client.query_stock_orders(cancelable_only=True):
                brid = getattr(o, "order_id", None)
                if brid is None:
                    continue
                try:
                    if int(brid) != oid:
                        continue
                except (TypeError, ValueError):
                    if str(brid).strip() != str(oid):
                        continue
                code = getattr(o, "stock_code", "") or ""
                sysid = getattr(o, "order_sysid", None)
                if code and sysid:
                    rc2 = self._client.cancel_order_stock_sysid(code, str(sysid))
                    return rc2 == 0
        except Exception as e:
            logger.warning("cancel fallback query: %s", e)
        return False
