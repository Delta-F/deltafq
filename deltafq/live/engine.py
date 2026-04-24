"""
实盘引擎：在实时 Tick 上运行策略，并通过数据/交易网关拉行情、下单。

典型用法::
    engine = LiveEngine(symbol="BTC-USD", signal_interval="1m", lookback_bars=50)
    engine.set_trade_gateway("paper", initial_capital=100000)
    engine.add_strategy(MyStrategy())
    engine.run_live()
    # KeyboardInterrupt 时: engine.stop()

函数与方法索引（按模块）
------------------------
模块级
    _vol_str              将成交量格式化为 B/M/K 或整数字符串

LiveEngine — 配置与策略
    __init__              构造：symbol、轮询间隔、回看根数、信号周期、网关名
    set_parameters        更新 symbol / interval / lookback_bars / signal_interval
    set_data_gateway      指定数据网关名与参数，清空已缓存网关实例
    set_trade_gateway     指定交易网关名与参数，清空已缓存网关实例
    add_strategy          绑定用于 generate_signals 的策略实例

LiveEngine — 运行
    run_live              连接网关、注册 Tick 处理、订阅标的并启动数据流
    stop                  停止数据网关与交易网关

LiveEngine — 对外查询与绩效
    get_chart_data        返回缓存 K 线与信号列表（不落库、不重算）
    get_trades_df         从交易网关的执行引擎取成交明细 DataFrame
    get_values_df         权益曲线记录（去重按日期取最后一条）
    calculate_metrics     基于成交与权益计算绩效指标（与回测接口一致）

LiveEngine — 内部：数据与网关
    _ensure_gateways      懒创建数据/交易网关；非 tick 模式时创建 DataFetcher
    _fetch_bars           按 signal_interval 拉取最近 lookback_bars 根 K 线

LiveEngine — 内部：账户与挂单
    _account_snapshot     当前现金、持仓股数、佣金率（纸面引擎或 miniQMT 查询）
    _pending_order_no_cancel_needed  判断挂单是否已终态，可跳过撤单

LiveEngine — 内部：Tick
    _on_tick_match              将 Tick 交给纸面撮合引擎（若有）；打印非 warmup 的 Tick 日志
    _build_signal_df            由 tick 与缓存构造策略用 K 线 / tick 序列 DataFrame
    _append_values_record       追加一条权益曲线记录（与回测 values 形状一致）
    _size_and_log_action        按信号与策略 order_* 计算买卖数量并打一行 Signal 日志
    _handle_signal_transition   信号相对上次变化时：撤挂单、下限价、更新 _last_signal
    _on_tick_strategy           编排：建 df → 信号 → 快照 → 权益 → sizing 日志 → 翻转处理
"""

import time
from collections import deque
from datetime import datetime, timedelta, timezone
from typing import Optional, Any, Dict, List, NamedTuple, Tuple

import pandas as pd

from ..backtest.performance import PerformanceReporter
from ..core.base import BaseComponent
from ..data import DataFetcher
from ..data.source_map import fetcher_source_for_data_gateway
from ..strategy.base import BaseStrategy
from .event_engine import EventEngine, EVENT_TICK
from .gateway_registry import create_data_gateway, create_trade_gateway
from .models import OrderRequest


# 各周期下「多久重拉一次 K 线」（秒）
_REFETCH_SEC = {"1m": 60, "5m": 300, "15m": 900, "1h": 3600, "1d": 86400}
# 按信号周期估算「每根 K 线对应多少日历日」，用于拉足 lookback（1d≈252 交易日/365 日）
_FETCH_DAYS_PER_BAR = {"1d": 365 / 252, "1wk": 365 / 52, "1mo": 365 / 12}
_SIG_ICON = {1: "↑", -1: "↓", 0: "-"}
_ACTION_ICON = {"buy": "↑", "sell": "↓", "skip": "x", "no_change": "-"}

# miniQMT order_status：终态、无需再撤（见 documents/MiniQmtTrade.md）
_MINIQMT_ORDER_STATUS_TERMINAL = frozenset({53, 54, 56, 57})


class _SizingLogResult(NamedTuple):
    """单次 tick 上用于日志与发单的买卖数量（买用 qty，卖用 sell_order_qty）。"""

    action_key: str
    action: str
    qty: int
    sell_order_qty: int


def _vol_str(v: float) -> str:
    """成交量友好显示：≥1e9 为 B，≥1e6 为 M，≥1e3 为 K，否则整数。"""
    if v >= 1e9:
        return f"{v / 1e9:.1f}B"
    if v >= 1e6:
        return f"{v / 1e6:.1f}M"
    if v >= 1e3:
        return f"{v / 1e3:.1f}K"
    return str(int(v))


class LiveEngine(BaseComponent):
    """
    在实盘数据上跑策略并通过网关下单。

    策略可选属性：``order_quantity``（股）买卖均封顶；未设时 ``order_amount`` 仅限制买入，
    卖出用满仓。二者皆无时买入用可承受现金。有纸面引擎时资金/持仓来自引擎，否则 miniQMT 查询。
    同时设置时买入侧 ``order_quantity`` 优先于 ``order_amount``。
    """

    # ---------- 配置与策略 ----------

    def __init__(
        self,
        symbol: Optional[str] = None,
        interval: float = 10.0,
        lookback_bars: int = 100,
        signal_interval: str = "5m",
        data_gateway_name: str = "yfinance",
        trade_gateway_name: str = "paper",
        **kwargs,
    ):
        """构造；run_live 前可用 set_data_gateway / set_trade_gateway 传入网关参数。"""
        super().__init__(**kwargs)
        self.symbol = symbol
        self.interval = interval
        self.lookback_bars = lookback_bars
        self.signal_interval = (signal_interval or "5m").lower()
        self.data_gateway_name = data_gateway_name
        self.trade_gateway_name = trade_gateway_name
        self._data_gateway_params: dict = {}
        self._trade_gateway_params: dict = {}

        self._event_engine = EventEngine()
        self._data_gw = None
        self._trade_gw = None
        self._data_fetcher: Optional[DataFetcher] = None
        self._strategy: Optional[BaseStrategy] = None
        self._prices: deque = deque(maxlen=lookback_bars + 100)
        self._timestamps: deque = deque(maxlen=lookback_bars + 100)
        self._last_signal = 0
        self._last_pending_order_id: Optional[str] = None
        self._last_fetch_time = 0.0
        self._cached_bars: Optional[pd.DataFrame] = None
        self._cached_signals: Optional[pd.Series] = None
        self._values_records: List[Dict[str, Any]] = []

    def set_parameters(
        self,
        symbol: Optional[str] = None,
        interval: Optional[float] = None,
        lookback_bars: Optional[int] = None,
        signal_interval: Optional[str] = None,
    ) -> None:
        """更新 symbol、轮询间隔、回看根数或信号周期。"""
        if symbol is not None:
            self.symbol = symbol
        if interval is not None:
            self.interval = interval
        if lookback_bars is not None:
            self.lookback_bars = lookback_bars
            self._prices = deque(self._prices, maxlen=lookback_bars + 100)
            self._timestamps = deque(self._timestamps, maxlen=lookback_bars + 100)
        if signal_interval is not None:
            self.signal_interval = signal_interval.lower()

    def set_data_gateway(self, name: str, **params: Any) -> None:
        """设置数据网关；params 传给工厂（如 interval）；会清空已创建实例。"""
        self.data_gateway_name = name
        self._data_gateway_params = dict(params)
        self._data_gw = None
        self._data_fetcher = None

    def set_trade_gateway(self, name: str, **params: Any) -> None:
        """设置交易网关；params 含 initial_capital、commission 等；会清空已创建实例。"""
        self.trade_gateway_name = name
        self._trade_gateway_params = dict(params)
        self._trade_gw = None

    def add_strategy(self, strategy: BaseStrategy) -> None:
        """绑定用于产生信号的策略。"""
        self._strategy = strategy

    # ---------- 运行 ----------

    def run_live(self) -> None:
        """连接网关、注册 Tick、订阅标的并启动推送。"""
        self._ensure_gateways()
        if not self._trade_gw.connect() or not self._data_gw.connect():
            raise RuntimeError("网关连接失败")

        self._event_engine.on(EVENT_TICK, self._on_tick_match)
        self._event_engine.on(EVENT_TICK, self._on_tick_strategy)
        self._data_gw.set_tick_handler(lambda t: self._event_engine.emit(EVENT_TICK, t))

        self._data_gw.subscribe([self.symbol])
        self._data_gw.start()
        self.logger.info(f"Running: {self.symbol} {self.signal_interval} lookback={self.lookback_bars}")

    def stop(self) -> None:
        """停止数据流与交易网关。"""
        if self._data_gw:
            self._data_gw.stop()
        if self._trade_gw:
            self._trade_gw.stop()

    # ---------- 对外查询与绩效 ----------

    def get_chart_data(self) -> Dict[str, Any]:
        """
        返回缓存 K 线与信号（不重拉、不重算）。尚无缓存时 candles/signals 为空列表。

        返回:
            candles: [{date, open, high, low, close}, ...]；signals: [int, ...]
        """
        if self._cached_bars is None or self._cached_signals is None or self._cached_bars.empty:
            return {"candles": [], "signals": []}

        date_fmt = "%Y-%m-%d" if self.signal_interval == "1d" else "%Y-%m-%d %H:%M:%S"

        candles: List[Dict[str, Any]] = []
        for idx, row in self._cached_bars.iterrows():
            c = float(row.get("Close", 0) or 0)
            o = float(row.get("Open", c) or c)
            h = float(row.get("High", c) or c)
            l_ = float(row.get("Low", c) or c)
            date_str = idx.strftime(date_fmt) if hasattr(idx, "strftime") else str(idx)[:16]
            candles.append({"date": date_str, "open": o, "high": h, "low": l_, "close": c})

        sigs = self._cached_signals.reindex(self._cached_bars.index, fill_value=0)
        signals = [int(x) if pd.notna(x) else 0 for x in sigs]

        return {"candles": candles, "signals": signals}

    def get_trades_df(self) -> pd.DataFrame:
        """从交易网关内嵌执行引擎取成交列表（结构与回测一致）。"""
        if self._trade_gw is None or not hasattr(self._trade_gw, "_engine"):
            return pd.DataFrame()
        eng = getattr(self._trade_gw, "_engine", None)
        if eng is None or not hasattr(eng, "trades"):
            return pd.DataFrame()
        return pd.DataFrame(eng.trades)

    def get_values_df(self) -> pd.DataFrame:
        """权益曲线 DataFrame；按 date 去重保留最后一条。"""
        if not self._values_records:
            return pd.DataFrame()
        df = pd.DataFrame(self._values_records)
        if "date" not in df.columns:
            return df
        df = df.drop_duplicates(subset=["date"], keep="last")
        df = df.sort_values("date").reset_index(drop=True)
        return df

    def calculate_metrics(self) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """由成交与权益计算绩效；接口同 BacktestEngine.calculate_metrics；可在 run 中或结束后调用。"""
        trades_df = self.get_trades_df()
        values_df = self.get_values_df()
        if values_df.empty:
            return pd.DataFrame(), {}
        reporter = PerformanceReporter()
        return reporter.compute(self.symbol, trades_df, values_df)

    # ---------- 内部：数据与网关 ----------

    def _ensure_gateways(self) -> None:
        """懒创建数据/交易网关；非 tick 时创建 DataFetcher。"""
        if self.symbol is None:
            raise ValueError("请先设置 symbol（构造参数或 set_parameters）")
        if self._data_gw is None:
            gw_params = dict(self._data_gateway_params)
            gw_params.setdefault("interval", self.interval)
            self._data_gw = create_data_gateway(self.data_gateway_name, **gw_params)
        if self._trade_gw is None:
            self._trade_gw = create_trade_gateway(self.trade_gateway_name, **self._trade_gateway_params)
        if self._data_fetcher is None and self.signal_interval != "tick":
            src = fetcher_source_for_data_gateway(self.data_gateway_name)
            self._data_fetcher = DataFetcher(source=src)

    def _fetch_bars(self) -> Optional[pd.DataFrame]:
        """用 DataFetcher 拉当前 signal_interval 下最近 lookback_bars 根 K 线。"""
        if self._data_fetcher is None or self.signal_interval == "tick":
            return None
        now = datetime.now(timezone.utc)
        days_per_bar = _FETCH_DAYS_PER_BAR.get(self.signal_interval)
        if days_per_bar is not None:
            cal_days = int(self.lookback_bars * days_per_bar) + 60
            start = (now - timedelta(days=max(cal_days, 60))).strftime("%Y-%m-%d")
        else:
            start = (now - timedelta(days=max(7, min(60, self.lookback_bars // 10)))).strftime(
                "%Y-%m-%d"
            )
        end = (now + timedelta(days=1)).strftime("%Y-%m-%d")
        try:
            data = self._data_fetcher.fetch_data(
                self.symbol, start, end, clean=True, interval=self.signal_interval
            )
        except Exception as e:
            self.logger.warning(f"DataFetcher failed: {e}")
            return None
        if data.empty:
            return None
        n = min(len(data), self.lookback_bars)
        if len(data) < self.lookback_bars:
            self.logger.warning(
                f"Insufficient bars: got {len(data)}, need {self.lookback_bars}; using available {n} bars"
            )
        return data.tail(n)

    # ---------- 内部：账户与挂单 ----------

    def _account_snapshot(self, tick: Any) -> Tuple[float, int, float]:
        """返回 (现金, 持仓股数, 佣金率)，用于仓位与日志；纸面用引擎，否则 miniQMT 查询。"""
        gw = self._trade_gw
        eng = getattr(gw, "_engine", None)
        if eng is not None:
            position = int(eng.position_manager.get_position(self.symbol))
            cash = float(eng.cash or 0.0)
            commission = float(getattr(eng, "commission", 0.0) or 0.0)
            return cash, position, commission
        client = getattr(gw, "client", None)
        if client is None or not getattr(client, "is_connected", lambda: False)():
            return 0.0, 0, 0.001
        try:
            asset = client.query_stock_asset()
            cash = float(getattr(asset, "cash", 0.0) or 0.0) if asset is not None else 0.0
        except Exception as e:
            self.logger.warning(f"query_stock_asset failed: {e}")
            cash = 0.0
        position = 0
        try:
            for p in client.query_stock_positions() or []:
                if (getattr(p, "stock_code", "") or "") == self.symbol:
                    position = int(
                        getattr(p, "can_use_volume", None)
                        or getattr(p, "volume", 0)
                        or 0
                    )
                    break
        except Exception as e:
            self.logger.warning(f"query_stock_positions failed: {e}")
            position = 0
        return cash, position, 0.001

    def _pending_order_no_cancel_needed(self, order_id: str) -> bool:
        """
        若上一笔委托已结束则返回 True：不必再向柜台撤单，并应清空本地 pending id。
        纸面：OrderManager 状态；miniQMT：order_status 属终态或委托列表中已无该单。
        """
        gw = self._trade_gw
        eng = getattr(gw, "_engine", None)
        if eng is not None:
            o = eng.order_manager.get_order(order_id)
            if o is None:
                return True
            st = (o.get("status") or "").lower()
            return st in ("executed", "cancelled")

        client = getattr(gw, "client", None)
        if client is None or not getattr(client, "is_connected", lambda: False)():
            return False
        try:
            target = int(str(order_id).strip())
        except ValueError:
            return True
        try:
            for row in client.query_stock_orders(cancelable_only=False) or []:
                brid = getattr(row, "order_id", None)
                if brid is None:
                    continue
                try:
                    if int(brid) != target:
                        continue
                except (TypeError, ValueError):
                    if str(brid).strip() != str(order_id).strip():
                        continue
                st = int(getattr(row, "order_status", -1))
                return st in _MINIQMT_ORDER_STATUS_TERMINAL
            return True
        except Exception as e:
            self.logger.warning(f"query_stock_orders for pending {order_id}: {e}")
            return False

    # ---------- 内部：Tick ----------

    def _on_tick_match(self, tick: Any) -> None:
        """非 warmup：打 Tick 日志；若网关带执行引擎则转发 on_tick 做限价撮合。"""
        if getattr(tick, "source", None) not in ("yf_warmup", "miniqmt_warmup"):
            t = tick.timestamp
            ts = t.strftime("%H:%M:%S")
            v = tick.volume
            ba = ""
            if tick.bid is not None and tick.ask is not None:
                ba = f" bid={tick.bid:.4f} ask={tick.ask:.4f}"
            elif tick.bid is not None:
                ba = f" bid={tick.bid:.4f}"
            elif tick.ask is not None:
                ba = f" ask={tick.ask:.4f}"
            self.logger.info(
                f"Tick: [{tick.symbol}] {tick.price:.4f}{ba} vol={v}({_vol_str(v)}) @ {ts}"
            )
        eng = getattr(self._trade_gw, "_engine", None) if self._trade_gw else None
        if eng is not None:
            eng.on_tick(tick)

    def _build_signal_df(self, tick: Any) -> Optional[pd.DataFrame]:
        """由当前 tick 构造策略输入 DataFrame；数据不足或未到重拉间隔时返回 None。"""
        if self.signal_interval == "tick":
            self._prices.append(float(tick.price))
            self._timestamps.append(tick.timestamp)
            if len(self._prices) < self.lookback_bars:
                return None
            n = self.lookback_bars
            return pd.DataFrame(
                {"Close": list(self._prices)[-n:]},
                index=list(self._timestamps)[-n:],
            )
        refetch_sec = _REFETCH_SEC.get(self.signal_interval, 60)
        if time.time() - self._last_fetch_time < refetch_sec:
            return None
        df = self._fetch_bars()
        if df is None:
            return None
        self._last_fetch_time = time.time()
        return df

    def _append_values_record(
        self, tick: Any, signal: int, px: float, cash: float, position: int
    ) -> None:
        """追加一条权益记录，供 get_values_df / calculate_metrics 使用。"""
        position_value = position * px
        total_value = cash + position_value
        prev_total = self._values_records[-1]["total_value"] if self._values_records else total_value
        daily_pnl = total_value - prev_total
        self._values_records.append({
            "date": tick.timestamp,
            "signal": signal,
            "price": px,
            "cash": cash,
            "position": position,
            "position_value": position_value,
            "total_value": total_value,
            "daily_pnl": daily_pnl,
        })

    def _size_and_log_action(
        self,
        signal: int,
        px: float,
        cash: float,
        position: int,
        commission: float,
        last_signal: int,
        order_quantity: Optional[Any],
        order_amount: Optional[Any],
    ) -> _SizingLogResult:
        """按当前信号与上次信号计算买卖数量，并打一行 Signal 日志。"""
        action_key = "no_change"
        action = "no_change"
        qty = 0
        sell_order_qty = 0

        oq_cap: Optional[int] = None
        if order_quantity is not None and int(order_quantity) > 0:
            oq_cap = int(order_quantity)

        if signal == 1 and last_signal <= 0:
            max_qty = max(0, int(cash / (px * (1 + commission))))
            if oq_cap is not None:
                qty = min(oq_cap, max_qty)
            elif order_amount is not None and order_amount > 0:
                qty = min(max(0, int(order_amount / (px * (1 + commission)))), max_qty)
            else:
                qty = max_qty
            if qty > 0:
                action_key, action = "buy", f"BUY qty={qty}"
            else:
                action_key, action = "skip", "BUY skip (qty=0)"
        elif signal == -1 and last_signal >= 0:
            if position > 0:
                if oq_cap is not None:
                    sell_order_qty = min(position, oq_cap)
                else:
                    sell_order_qty = position
                action_key, action = "sell", f"SELL qty={sell_order_qty}"
            else:
                action_key, action = "skip", "SELL skip (position=0)"

        icon = _SIG_ICON.get(signal, "?")
        act_icon = _ACTION_ICON.get(action_key, "?")
        self.logger.info(
            f"Signal: {icon} {signal} [{self.symbol}] {px:.4f} cash={cash:.0f} pos={position} -> {act_icon} {action}"
        )
        return _SizingLogResult(action_key, action, qty, sell_order_qty)

    def _handle_signal_transition(
        self, signal: int, px: float, position: int, sizing: _SizingLogResult, tick: Any
    ) -> None:
        """相对 _last_signal 发生变化时：尝试撤上一笔挂单，再按规则下限价单。"""
        last = self._last_signal
        if signal == last:
            return

        if self._last_pending_order_id:
            oid = self._last_pending_order_id
            if self._pending_order_no_cancel_needed(oid):
                self.logger.info(f"Pending order {oid} already finished; skip cancel")
                self._last_pending_order_id = None
            else:
                cancelled = self._trade_gw.cancel_order(oid)
                if cancelled:
                    self.logger.info(f"Cancelled pending order: {oid}")
                else:
                    self.logger.warning(f"Cancel pending order {oid} returned false")
                self._last_pending_order_id = None

        if signal == 1 and last <= 0:
            if sizing.qty > 0:
                buy_px = float(getattr(tick, "ask", None)) if getattr(tick, "ask", None) is not None else px
                req = OrderRequest(symbol=self.symbol, quantity=sizing.qty, price=buy_px, order_type="limit")
                self._last_pending_order_id = self._trade_gw.send_order(req)
                self.logger.info(f"Order sent: BUY [{self.symbol}] qty={sizing.qty} @ {buy_px:.4f}")
        elif signal == -1 and last >= 0 and position > 0:
            if sizing.sell_order_qty <= 0:
                self._last_signal = signal
                return
            sell_px = float(getattr(tick, "bid", None)) if getattr(tick, "bid", None) is not None else px
            req = OrderRequest(
                symbol=self.symbol, quantity=-sizing.sell_order_qty, price=sell_px, order_type="limit"
            )
            self._last_pending_order_id = self._trade_gw.send_order(req)
            self.logger.info(f"Order sent: SELL [{self.symbol}] qty={sizing.sell_order_qty} @ {sell_px:.4f}")

        self._last_signal = signal

    def _on_tick_strategy(self, tick: Any) -> None:
        """编排：建 df → 信号 → 账户快照 → 权益 → sizing 与日志 → 信号翻转时撤单/下单。"""
        if getattr(tick, "source", None) in ("yf_warmup", "miniqmt_warmup"):
            return
        if tick.symbol != self.symbol or self._strategy is None:
            return

        df = self._build_signal_df(tick)
        if df is None:
            return

        try:
            signals = self._strategy.generate_signals(df)
        except Exception as e:
            self.logger.warning(f"Strategy signal failed: {e}")
            return

        if signals.empty:
            return

        self._cached_bars = df
        self._cached_signals = signals

        signal = int(signals.iloc[-1])
        px = float(tick.price)
        cash, position, commission = self._account_snapshot(tick)

        self._append_values_record(tick, signal, px, cash, position)

        order_quantity = getattr(self._strategy, "order_quantity", None)
        order_amount = getattr(self._strategy, "order_amount", None)
        sizing = self._size_and_log_action(
            signal, px, cash, position, commission, self._last_signal, order_quantity, order_amount
        )

        self._handle_signal_transition(signal, px, position, sizing, tick)
