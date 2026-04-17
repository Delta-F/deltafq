"""
miniQMT / xtquant 交易封装（``xttrader``）。

需本机已安装 ``xtquant``、启动 miniQMT，并配置 ``userdata_mini`` 与资金账号。
环境变量（可选）：``QMT_USERDATA_MINI``、``QMT_ACCOUNT_ID``。
"""

from __future__ import annotations

import logging
import os
import random
from typing import Any, List, Optional

logger = logging.getLogger(__name__)


def import_xttrader_modules() -> tuple[Any, Any, Any]:
    try:
        from xtquant import xtconstant  # type: ignore
        from xtquant import xttrader  # type: ignore
        from xtquant.xttype import StockAccount  # type: ignore
    except ImportError as e:
        raise ImportError(
            "miniQMT trading requires xtquant (pip install xtquant). "
            "Ensure miniQMT is running and userdata_mini is configured."
        ) from e
    return xttrader, xtconstant, StockAccount


def market_by_stock_code(stock_code: str, xtconstant: Any) -> Optional[int]:
    """证券代码后缀 -> 市场枚举（用于 ``cancel_order_stock_sysid`` 等）。"""
    suffix = str(stock_code).upper()[-3:]
    return {".SH": xtconstant.SH_MARKET, ".SZ": xtconstant.SZ_MARKET}.get(suffix)


class MiniQmtXtTraderClient:
    """
    封装 ``XtQuantTrader``：连接、订阅账号、下单、撤单及常用查询。

    柜台状态以 miniQMT 为准；本类不负责本地仿真持仓。
    """

    def __init__(
        self,
        userdata_mini_path: Optional[str] = None,
        account_id: Optional[str] = None,
        session_id: Optional[int] = None,
    ) -> None:
        self.userdata_mini_path = (userdata_mini_path or os.environ.get("QMT_USERDATA_MINI") or "").strip()
        self.account_id = (account_id or os.environ.get("QMT_ACCOUNT_ID") or "").strip()
        self.session_id = session_id if session_id is not None else random.randint(100_000, 999_999)

        self._xt: Any = None
        self._acc: Any = None
        self._xttrader: Any = None
        self._xtconstant: Any = None
        self._StockAccount: Any = None

    @property
    def xt(self) -> Any:
        return self._xt

    @property
    def account(self) -> Any:
        """``StockAccount`` 实例，连接成功后可用。"""
        return self._acc

    def is_connected(self) -> bool:
        return self._xt is not None and self._acc is not None

    def connect(self) -> bool:
        """``start`` → ``connect`` → ``subscribe`` 资金账号。"""
        if not self.userdata_mini_path:
            logger.error("userdata_mini path is empty; set QMT_USERDATA_MINI or pass userdata_mini_path")
            return False
        if not os.path.isdir(self.userdata_mini_path):
            logger.error("userdata_mini path is not a directory: %s", self.userdata_mini_path)
            return False
        if not self.account_id:
            logger.error("account_id is empty; set QMT_ACCOUNT_ID or pass account_id")
            return False

        xttrader, xtconstant, StockAccount = import_xttrader_modules()
        self._xttrader = xttrader
        self._xtconstant = xtconstant
        self._StockAccount = StockAccount

        try:
            xt = xttrader.XtQuantTrader(self.userdata_mini_path, self.session_id)
            xt.start()
            rc = xt.connect()
            if rc != 0:
                logger.error("XtQuantTrader.connect failed rc=%s", rc)
                try:
                    xt.stop()
                except Exception:
                    pass
                return False

            acc = StockAccount(self.account_id)
            sub = xt.subscribe(acc)
            if sub != 0:
                logger.error("subscribe account failed sub=%s (0=ok)", sub)
                try:
                    xt.stop()
                except Exception:
                    pass
                return False

            self._xt = xt
            self._acc = acc
            logger.info(
                "miniQMT trader connected session_id=%s account=%s",
                self.session_id,
                self.account_id,
            )
            return True
        except Exception as e:
            logger.exception("miniQMT connect error: %s", e)
            self._xt = None
            self._acc = None
            return False

    def disconnect(self) -> None:
        if self._xt is None:
            return
        try:
            if hasattr(self._xt, "stop"):
                self._xt.stop()
        except Exception as e:
            logger.warning("XtQuantTrader.stop: %s", e)
        finally:
            self._xt = None
            self._acc = None

    def order_stock_limit(
        self,
        stock_code: str,
        volume: int,
        price: float,
        is_buy: bool,
        strategy_name: str = "deltafq",
        order_remark: str = "",
    ) -> int:
        """
        限价委托。返回柜台 ``order_id``（失败时多为 ``-1`` 或 ``0``，以 xtquant 为准）。
        """
        if self._xt is None or self._acc is None:
            raise RuntimeError("not connected; call connect() first")
        oc = self._xtconstant
        direction = oc.STOCK_BUY if is_buy else oc.STOCK_SELL
        oid = self._xt.order_stock(
            self._acc,
            stock_code,
            direction,
            int(volume),
            oc.FIX_PRICE,
            float(price),
            strategy_name,
            order_remark or "",
        )
        return int(oid) if oid is not None else -1

    def cancel_order_stock(self, order_id: int) -> int:
        """按本地委托号撤单；返回码 ``0`` 表示成功（以 xtquant 为准）。"""
        if self._xt is None or self._acc is None:
            raise RuntimeError("not connected; call connect() first")
        return int(self._xt.cancel_order_stock(self._acc, int(order_id)))

    def cancel_order_stock_sysid(self, stock_code: str, order_sysid: str) -> int:
        """按合同号撤单（``cancel_order_stock`` 失败时的兜底）。"""
        if self._xt is None or self._acc is None:
            raise RuntimeError("not connected; call connect() first")
        m = market_by_stock_code(stock_code, self._xtconstant)
        if m is None:
            return -1
        return int(self._xt.cancel_order_stock_sysid(self._acc, m, order_sysid))

    # --- queries（柜台真相，供实盘对账 / 展示） ---

    def query_account_infos(self) -> Any:
        if self._xt is None:
            raise RuntimeError("not connected")
        return self._xt.query_account_infos()

    def query_account_status(self) -> Any:
        if self._xt is None:
            raise RuntimeError("not connected")
        return self._xt.query_account_status()

    def query_stock_asset(self) -> Any:
        if self._xt is None or self._acc is None:
            raise RuntimeError("not connected")
        return self._xt.query_stock_asset(self._acc)

    def query_stock_positions(self) -> List[Any]:
        if self._xt is None or self._acc is None:
            raise RuntimeError("not connected")
        return list(self._xt.query_stock_positions(self._acc) or [])

    def query_stock_position(self, stock_code: str) -> Any:
        if self._xt is None or self._acc is None:
            raise RuntimeError("not connected")
        return self._xt.query_stock_position(self._acc, stock_code)

    def query_stock_orders(self, cancelable_only: bool = False) -> List[Any]:
        if self._xt is None or self._acc is None:
            raise RuntimeError("not connected")
        return list(self._xt.query_stock_orders(self._acc, cancelable_only=cancelable_only) or [])

    def query_stock_trades(self) -> List[Any]:
        if self._xt is None or self._acc is None:
            raise RuntimeError("not connected")
        return list(self._xt.query_stock_trades(self._acc) or [])
