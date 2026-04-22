"""
miniQMT 交易（xttrader），类 MiniQmtXtTraderClient。

模块
    import_xttrader_modules   导入 xttrader、xtconstant、StockAccount，缺包则抛 ImportError
    market_by_stock_code    证券代码后缀推市场枚举，供按合同号撤单等

对外
    __init__                  userdata_mini 路径、资金账号、会话号（可用环境变量）
    xt / account              连接后 XtQuantTrader 与 StockAccount
    is_connected              是否已连接并订阅账号
    connect                   启动、连接、订阅资金账号
    disconnect                停止并清空引用
    order_stock_limit         限价买卖，返回柜台委托号
    cancel_order_stock        按委托号撤单
    cancel_order_stock_sysid  按合同号撤单（需市场枚举）
    query_account_infos       账号信息
    query_account_status      账号状态
    query_stock_asset         资金资产
    query_stock_positions     持仓列表
    query_stock_position      单只标的持仓
    query_stock_orders        委托列表
    query_stock_trades        成交列表
"""

from __future__ import annotations

import logging
import os
import random
from typing import Any, List, Optional

logger = logging.getLogger(__name__)


def import_xttrader_modules() -> tuple[Any, Any, Any]:
    """导入 xtquant 交易模块；未安装则抛 ImportError 并提示安装与环境。"""
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
    """根据代码后缀 .SH / .SZ 返回对应市场常量；不识别的后缀返回 None。"""
    suffix = str(stock_code).upper()[-3:]
    return {".SH": xtconstant.SH_MARKET, ".SZ": xtconstant.SZ_MARKET}.get(suffix)


class MiniQmtXtTraderClient:
    """封装 XtQuantTrader：连柜台下限价撤单，查资金持仓委托成交；不做本地仿真。"""

    def __init__(
        self,
        userdata_mini_path: Optional[str] = None,
        account_id: Optional[str] = None,
        session_id: Optional[int] = None,
    ) -> None:
        """路径与账号可传参或用 QMT_USERDATA_MINI、QMT_ACCOUNT_ID；会话号不传则随机。"""
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
        """已连接时为 XtQuantTrader 实例，否则为 None。"""
        return self._xt

    @property
    def account(self) -> Any:
        """已连接时为 StockAccount，否则为 None。"""
        return self._acc

    def is_connected(self) -> bool:
        """同时持有交易实例与资金账号对象时视为已连接。"""
        return self._xt is not None and self._acc is not None

    def connect(self) -> bool:
        """校验路径与账号后 start、connect、subscribe；失败会 stop 并返回 False。"""
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
        """调用底层 stop 并清空交易实例与账号引用。"""
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
        """限价委托；返回柜台委托号，失败多为 -1 或 0，以柜台为准。"""
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
        """按本地委托号撤单；返回 0 表示成功，以柜台为准。"""
        if self._xt is None or self._acc is None:
            raise RuntimeError("not connected; call connect() first")
        return int(self._xt.cancel_order_stock(self._acc, int(order_id)))

    def cancel_order_stock_sysid(self, stock_code: str, order_sysid: str) -> int:
        """按合同号撤单；需股票代码推市场；不识别的代码返回 -1。"""
        if self._xt is None or self._acc is None:
            raise RuntimeError("not connected; call connect() first")
        m = market_by_stock_code(stock_code, self._xtconstant)
        if m is None:
            return -1
        return int(self._xt.cancel_order_stock_sysid(self._acc, m, order_sysid))

    def query_account_infos(self) -> Any:
        """未连接抛错；否则透传柜台 query_account_infos。"""
        if self._xt is None:
            raise RuntimeError("not connected")
        return self._xt.query_account_infos()

    def query_account_status(self) -> Any:
        """未连接抛错；否则透传柜台 query_account_status。"""
        if self._xt is None:
            raise RuntimeError("not connected")
        return self._xt.query_account_status()

    def query_stock_asset(self) -> Any:
        """未连接抛错；否则透传柜台 query_stock_asset。"""
        if self._xt is None or self._acc is None:
            raise RuntimeError("not connected")
        return self._xt.query_stock_asset(self._acc)

    def query_stock_positions(self) -> List[Any]:
        """持仓列表；无则空列表。"""
        if self._xt is None or self._acc is None:
            raise RuntimeError("not connected")
        return list(self._xt.query_stock_positions(self._acc) or [])

    def query_stock_position(self, stock_code: str) -> Any:
        """单只标的持仓；未连接抛错。"""
        if self._xt is None or self._acc is None:
            raise RuntimeError("not connected")
        return self._xt.query_stock_position(self._acc, stock_code)

    def query_stock_orders(self, cancelable_only: bool = False) -> List[Any]:
        """委托列表；cancelable_only 为 True 时仅可撤委托。"""
        if self._xt is None or self._acc is None:
            raise RuntimeError("not connected")
        return list(self._xt.query_stock_orders(self._acc, cancelable_only=cancelable_only) or [])

    def query_stock_trades(self) -> List[Any]:
        """当日成交列表；无则空列表。"""
        if self._xt is None or self._acc is None:
            raise RuntimeError("not connected")
        return list(self._xt.query_stock_trades(self._acc) or [])
