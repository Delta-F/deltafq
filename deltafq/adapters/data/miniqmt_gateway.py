"""
miniQMT 行情（xtdata），类 MiniQmtDataGateway。

对外
    connect              加载 xtdata，需 miniQMT 已开
    subscribe            追加标的并 1m 暖机回放
    start                开 daemon：poll 轮询或 push 订分笔
    stop                 停线程，push 会退订
    get_today_ohlc       当日开高低（从快照解析）
    get_depths           买卖盘口（从快照解析）

私有
    _warm_up             近一日 1m 合成暖机 tick
    _unsubscribe_push    push 停时退订
    _run_poll            按间隔拉全快照轮询
    _run_push            订分笔并阻塞 run
    _on_push_datas       分笔回调里组 TickData
    _get_full_tick       封装 get_full_tick
    _bid_ask_from_dict   快照 dict 取买一卖一
    _ts_from_millis_or_now  行情时间转 datetime
"""
import threading
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from ...data.miniqmt_xtdata import fetch_miniqmt_bars, import_xtdata as _import_xtdata
from ...live.gateways import DataGateway
from ...live.models import TickData


class MiniQmtDataGateway(DataGateway):
    """poll 定时拉全快照，push 订分笔推送；xt 标的代码，Tick 含最新价及可选买卖盘。"""

    def __init__(
        self,
        interval: float = 3.0,
        dividend_type: str = "none",
        mode: str = "poll",
        **kwargs: Any,
    ) -> None:
        """轮询间隔秒、K 线除权类型、模式 poll 或 push。"""
        super().__init__(**kwargs)
        self.interval = interval
        self.dividend_type = dividend_type
        self.mode = (mode or "poll").strip().lower()
        if self.mode not in ("poll", "push"):
            raise ValueError('mode must be "poll" or "push"')
        self._symbols: List[str] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._quote_seqs: List[int] = []
        self.logger.info(f"Initialized MiniQmtDataGateway mode={self.mode} interval={self.interval}s")

    def connect(self) -> bool:
        """加载 xtdata，本机需已启动 miniQMT。"""
        try:
            _import_xtdata()
            self.logger.info("xtquant xtdata loaded (ensure miniQMT is running)")
            return True
        except Exception as e:
            self.logger.error(f"miniQMT connect failed: {e}")
            return False

    def subscribe(self, symbols: List[str]) -> bool:
        """追加订阅；新标的用近一日 1m K 线逐根暖机回调。"""
        new_symbols = [s for s in symbols if s not in self._symbols]
        for symbol in new_symbols:
            self._symbols.append(symbol)
            self._warm_up(symbol)
        return True

    def start(self) -> None:
        """起后台线程：poll 轮询快照，push 订分笔并跑 xtdata.run。"""
        if self._running:
            return
        self._running = True
        if self.mode == "poll":
            self.logger.info("Starting miniQMT poll loop")
            self._thread = threading.Thread(target=self._run_poll, daemon=True)
        else:
            self.logger.info("Starting miniQMT subscribe_quote + xtdata.run()")
            self._thread = threading.Thread(target=self._run_push, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """停线程；push 会退订并调 stop（若有）；join 等线程结束。"""
        self._running = False
        if self.mode == "push":
            self._unsubscribe_push()
        if self._thread:
            self._thread.join(timeout=5.0)
        self._thread = None
        self.logger.info(f"Stopped MiniQmtDataGateway ({self.mode})")

    def get_today_ohlc(self, symbol: str) -> Optional[Dict[str, float]]:
        """从快照取当日开、高、低三个 float；缺或错返回 None。"""
        tick, err = self._get_full_tick(symbol)
        if err or not tick:
            self.logger.warning(f"get_today_ohlc: {err}")
            return None
        try:
            o = tick.get("open")
            h = tick.get("high") or tick.get("highPrice")
            l_ = tick.get("low") or tick.get("lowPrice")
            if o is None or h is None or l_ is None:
                return None
            return {"open": float(o), "high": float(h), "low": float(l_)}
        except Exception as e:
            self.logger.error(f"get_today_ohlc parse error: {e}")
            return None

    def get_depths(self, symbol: str, levels: int = 5) -> Dict[str, List[Dict[str, float]]]:
        """返回买卖盘口深度（价格+委托量）。"""
        tick, err = self._get_full_tick(symbol)
        if err or not tick:
            self.logger.debug(f"get_depths {symbol}: {err}")
            return {"bids": [], "asks": []}
        lv = max(1, min(int(levels), 10))
        bids: List[Dict[str, float]] = []
        asks: List[Dict[str, float]] = []

        for i in range(1, lv + 1):
            bp = self._level_value(tick, "bid", "price", i)
            bv = self._level_value(tick, "bid", "volume", i)
            ap = self._level_value(tick, "ask", "price", i)
            av = self._level_value(tick, "ask", "volume", i)
            if bp is not None:
                bids.append({"level": float(i), "price": bp, "volume": float(bv or 0.0)})
            if ap is not None:
                asks.append({"level": float(i), "price": ap, "volume": float(av or 0.0)})
        return {"bids": bids, "asks": asks}

    # ---------- 私有 ----------

    def _warm_up(self, symbol: str) -> None:
        """近一日 1m 收盘合成暖机 tick，来源标记 miniqmt_warmup。"""
        self.logger.debug(f"Warming up {symbol} with miniQMT 1m history...")
        try:
            end = datetime.now()
            start = end - timedelta(days=1)
            data = fetch_miniqmt_bars(
                symbol,
                start.strftime("%Y-%m-%d"),
                None,
                interval="1m",
                dividend_type=self.dividend_type,
            )
            if data.empty:
                self.logger.warning(f"No warm-up data for {symbol}")
                return
            pushed = 0
            for timestamp, row in data.iterrows():
                ts = timestamp.to_pydatetime() if hasattr(timestamp, "to_pydatetime") else timestamp
                if getattr(ts, "tzinfo", None) is not None:
                    ts = ts.replace(tzinfo=None)
                price = float(row["Close"])
                volume = int(row["Volume"])
                tick = TickData(
                    symbol=symbol,
                    price=price,
                    timestamp=ts,
                    volume=volume,
                    source="miniqmt_warmup",
                )
                if self._tick_handler:
                    self._tick_handler(tick)
                pushed += 1
            self.logger.info(f"Subscribed & warmed up {symbol} ({pushed} bars)")
        except Exception as e:
            self.logger.warning(f"Warm-up failed for {symbol}: {e}")

    def _unsubscribe_push(self) -> None:
        """push 停时逐个退订 quote，再调 xtdata.stop（有则调）。"""
        if not self._quote_seqs:
            return
        try:
            xd = _import_xtdata()
            for seq in self._quote_seqs:
                try:
                    xd.unsubscribe_quote(seq)
                except Exception as e:
                    self.logger.debug(f"unsubscribe_quote {seq}: {e}")
            self._quote_seqs.clear()
            stop_fn = getattr(xd, "stop", None)
            if callable(stop_fn):
                stop_fn()
        except Exception as e:
            self.logger.warning(f"push cleanup: {e}")

    def _run_poll(self) -> None:
        """对每个标的拉全快照，组 TickData，调 tick 回调。"""
        while self._running:
            for symbol in self._symbols:
                tick, err = self._get_full_tick(symbol)
                if err or not tick:
                    self.logger.debug(f"tick skip {symbol}: {err}")
                    continue
                try:
                    last = tick.get("lastPrice") or tick.get("last") or tick.get("price")
                    vol = tick.get("volume") or tick.get("lastVolume") or 0
                    if last is None:
                        continue
                    ts = self._ts_from_millis_or_now(tick.get("time"))
                    bid, ask = self._bid_ask_from_dict(tick)
                    t = TickData(
                        symbol=symbol,
                        price=float(last),
                        timestamp=ts,
                        volume=int(vol) if vol is not None else None,
                        source="miniqmt",
                        bid=bid,
                        ask=ask,
                    )
                    if self._tick_handler:
                        self._tick_handler(t)
                except Exception as e:
                    self.logger.error(f"Error polling {symbol}: {e}")
            time.sleep(self.interval)

    def _run_push(self) -> None:
        """等标的有列表后逐只 subscribe_quote，最后阻塞 xd.run。"""
        # 启动可能早于订阅，先空转等到标的非空。
        while self._running and not self._symbols:
            time.sleep(0.1)
        if not self._running:
            return
        xd = _import_xtdata()
        self._quote_seqs = []
        for symbol in list(self._symbols):
            if not self._running:
                break
            seq = xd.subscribe_quote(
                symbol,
                period="tick",
                start_time="",
                end_time="",
                count=0,
                callback=self._on_push_datas,
            )
            if seq < 0:
                self.logger.error(f"subscribe_quote failed {symbol}: {seq}")
                continue
            self._quote_seqs.append(seq)
        if not self._running or not self._quote_seqs:
            return
        try:
            xd.run()
        except Exception as e:
            if self._running:
                self.logger.error(f"xtdata.run: {e}")

    def _on_push_datas(self, datas: dict) -> None:
        """分笔推送回调：行转 TickData 再交 tick 回调。"""
        if not self._running:
            return
        for code, rows in (datas or {}).items():
            for row in rows or []:
                if not isinstance(row, dict):
                    continue
                last = row.get("lastPrice") or row.get("last_price") or row.get("price")
                if last is None:
                    continue
                vol = row.get("volume") or row.get("lastVolume")
                ts = self._ts_from_millis_or_now(row.get("time"))
                bid, ask = self._bid_ask_from_dict(row)
                t = TickData(
                    symbol=code,
                    price=float(last),
                    timestamp=ts,
                    volume=int(vol) if vol is not None else None,
                    source="miniqmt_push",
                    bid=bid,
                    ask=ask,
                )
                if self._tick_handler:
                    self._tick_handler(t)

    def _get_full_tick(self, symbol: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """调 get_full_tick；成功返回快照和 None，失败返回 None 和错误说明。"""
        try:
            xtdata = _import_xtdata()
            data = xtdata.get_full_tick([symbol])
            if not data or symbol not in data:
                return None, f"{symbol} 无快照"
            return data[symbol], None
        except Exception as e:
            return None, str(e)

    @staticmethod
    def _bid_ask_from_dict(d: Dict[str, Any]) -> Tuple[Optional[float], Optional[float]]:
        """从行情 dict 取买一卖一；若买价大于卖价则对调一次。"""
        def _to_f(v: Any) -> Optional[float]:
            if v is None:
                return None
            if isinstance(v, (list, tuple)) and len(v) > 0:
                v = v[0]
            try:
                return float(v)
            except (TypeError, ValueError):
                return None

        bid = d.get("bid1") or d.get("bidPrice") or d.get("bid") or d.get("bidPx")
        ask = d.get("ask1") or d.get("askPrice") or d.get("ask") or d.get("askPx")
        b, a = _to_f(bid), _to_f(ask)
        if b is not None and a is not None and b > a:
            return a, b
        return b, a

    @classmethod
    def _level_value(cls, d: Dict[str, Any], side: str, kind: str, idx: int) -> Optional[float]:
        """取指定档位字段，兼容数组字段和逐档字段。"""
        if side == "bid":
            arr_keys = ["bidPrice", "bid", "bidPx"] if kind == "price" else ["bidVol", "bidVolume", "bidQty"]
            scalar_keys = (
                [f"bid{idx}", f"bidPrice{idx}", f"bidPx{idx}"]
                if kind == "price"
                else [f"bidVol{idx}", f"bidVolume{idx}", f"bidQty{idx}"]
            )
        else:
            arr_keys = ["askPrice", "ask", "askPx"] if kind == "price" else ["askVol", "askVolume", "askQty"]
            scalar_keys = (
                [f"ask{idx}", f"askPrice{idx}", f"askPx{idx}"]
                if kind == "price"
                else [f"askVol{idx}", f"askVolume{idx}", f"askQty{idx}"]
            )

        for key in arr_keys:
            arr = d.get(key)
            if isinstance(arr, (list, tuple)) and len(arr) >= idx:
                return cls._to_float(arr[idx - 1])
        for key in scalar_keys:
            if key in d:
                return cls._to_float(d.get(key))
        return None

    @staticmethod
    def _to_float(v: Any) -> Optional[float]:
        """将任意值转为 float，失败返回 None。"""
        if v is None:
            return None
        if isinstance(v, (list, tuple)) and len(v) > 0:
            v = v[0]
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _ts_from_millis_or_now(raw: Any) -> datetime:
        """时间戳毫秒太长则按毫秒除；坏了或没有就用本机当前时间。"""
        if raw is None:
            return datetime.now().replace(tzinfo=None)
        try:
            n = int(raw)
            if n > 10**12:
                n = n // 1000
            return datetime.fromtimestamp(n)
        except (TypeError, ValueError, OSError):
            return datetime.now().replace(tzinfo=None)
