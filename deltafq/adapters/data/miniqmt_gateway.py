import threading
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from ...data.miniqmt_xtdata import fetch_miniqmt_bars, import_xtdata as _import_xtdata
from ...live.gateways import DataGateway
from ...live.models import TickData


def _get_full_tick(symbol: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Snapshot via ``xtdata.get_full_tick`` (poll mode)."""
    try:
        xtdata = _import_xtdata()
        data = xtdata.get_full_tick([symbol])
        if not data or symbol not in data:
            return None, f"No tick for {symbol}"
        return data[symbol], None
    except Exception as e:
        return None, str(e)


class MiniQmtDataGateway(DataGateway):
    """
    Market data via miniQMT (xtquant ``xtdata``).

    - ``mode="poll"``: ``get_full_tick`` on an interval (same idea as yfinance polling).
    - ``mode="push"``: ``subscribe_quote`` + ``xtdata.run()`` in a daemon thread (finer ticks when market is open).

    Symbols: xt-style codes, e.g. ``000001.SZ``, ``600000.SH``.
    """

    def __init__(
        self,
        interval: float = 3.0,
        dividend_type: str = "none",
        mode: str = "poll",
        **kwargs: Any,
    ) -> None:
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
        try:
            _import_xtdata()
            self.logger.info("xtquant xtdata loaded (ensure miniQMT is running)")
            return True
        except Exception as e:
            self.logger.error(f"miniQMT connect failed: {e}")
            return False

    def subscribe(self, symbols: List[str]) -> bool:
        new_symbols = [s for s in symbols if s not in self._symbols]
        for symbol in new_symbols:
            self._symbols.append(symbol)
            self._warm_up(symbol)
        return True

    def _warm_up(self, symbol: str) -> None:
        """Replay recent 1m bars as synthetic ticks (aligned with yfinance warm-up)."""
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

    def start(self) -> None:
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
        self._running = False
        if self.mode == "push":
            self._unsubscribe_push()
        if self._thread:
            self._thread.join(timeout=5.0)
        self._thread = None
        self.logger.info(f"Stopped MiniQmtDataGateway ({self.mode})")

    def _unsubscribe_push(self) -> None:
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

    def get_today_ohlc(self, symbol: str) -> Optional[Dict[str, float]]:
        tick, err = _get_full_tick(symbol)
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

    def _run_poll(self) -> None:
        while self._running:
            for symbol in self._symbols:
                tick, err = _get_full_tick(symbol)
                if err or not tick:
                    self.logger.debug(f"tick skip {symbol}: {err}")
                    continue
                try:
                    last = tick.get("lastPrice") or tick.get("last") or tick.get("price")
                    vol = tick.get("volume") or tick.get("lastVolume") or 0
                    if last is None:
                        continue
                    ts = _ts_from_millis_or_now(tick.get("time"))
                    t = TickData(
                        symbol=symbol,
                        price=float(last),
                        timestamp=ts,
                        volume=int(vol) if vol is not None else None,
                        source="miniqmt",
                    )
                    if self._tick_handler:
                        self._tick_handler(t)
                except Exception as e:
                    self.logger.error(f"Error polling {symbol}: {e}")
            time.sleep(self.interval)

    def _run_push(self) -> None:
        # Same lifecycle as yfinance example: start() may run before subscribe(); wait for symbols.
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
                ts = _ts_from_millis_or_now(row.get("time"))
                t = TickData(
                    symbol=code,
                    price=float(last),
                    timestamp=ts,
                    volume=int(vol) if vol is not None else None,
                    source="miniqmt_push",
                )
                if self._tick_handler:
                    self._tick_handler(t)


def _ts_from_millis_or_now(raw: Any) -> datetime:
    if raw is None:
        return datetime.now().replace(tzinfo=None)
    try:
        n = int(raw)
        if n > 10**12:
            n = n // 1000
        return datetime.fromtimestamp(n)
    except (TypeError, ValueError, OSError):
        return datetime.now().replace(tzinfo=None)
