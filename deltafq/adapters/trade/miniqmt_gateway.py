"""
miniQMT 交易网关，类 MiniQmtTradeGateway。

对外
    __init__      注入连接参数、策略名、委托备注、手数
    client        暴露底层 MiniQmtXtTraderClient，便于查询柜台数据
    connect       连接 miniQMT 交易端
    stop          断开连接并清理
    send_order    接收统一 OrderRequest，转柜台限价单并返回字符串委托号
    cancel_order  按委托号撤单，失败时按合同号兜底再撤
"""

from __future__ import annotations

import logging
from typing import Optional

from ...live.gateways import TradeGateway
from ...live.models import OrderRequest
from .miniqmt_client import MiniQmtXtTraderClient

logger = logging.getLogger(__name__)


class MiniQmtTradeGateway(TradeGateway):
    """连接 miniQMT 并适配 LiveEngine 的下单撤单接口。"""

    def __init__(
        self,
        userdata_mini_path: Optional[str] = None,
        account_id: Optional[str] = None,
        session_id: Optional[int] = None,
        strategy_name: str = "deltafq",
        order_remark: str = "",
        lot_size: int = 100,
    ) -> None:
        """初始化柜台参数；lot_size 用于数量对齐，默认按 A 股 100 股一手。"""
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
        """底层交易客户端；可直接查资金、持仓、委托、成交。"""
        return self._client

    def connect(self) -> bool:
        """连接交易端并订阅资金账号。"""
        return self._client.connect()

    def stop(self) -> None:
        """断开交易端连接。"""
        self._client.disconnect()

    def send_order(self, req: OrderRequest) -> str:
        """仅支持限价单；数量按 lot_size 向下对齐；返回字符串委托号。"""
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
        """先按委托号撤；失败则在可撤委托里查合同号并兜底撤单。"""
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
