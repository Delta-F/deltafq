import threading
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from ...data.miniqmt_xtdata import fetch_miniqmt_bars, import_xtdata as _import_xtdata


def _get_full_tick(symbol: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """快照：``xtdata.get_full_tick``，仅供网关轮询使用。"""
    try:
        xtdata = _import_xtdata()
        data = xtdata.get_full_tick([symbol])
        if not data or symbol not in data:
            return None, f"No tick for {symbol}"
        return data[symbol], None
    except Exception as e:
        return None, str(e)
from ...live.gateways import DataGateway
from ...live.models import TickData


class MiniQmtDataGateway(DataGateway):
    """
    Market data via miniQMT (xtquant ``xtdata``).

    Symbols must be xt-style codes, e.g. ``000001.SZ``, ``600000.SH``.
    Timestamps use naive local time (exchange time) for ticks, consistent with stripping tz from yfinance.
    """

    def __init__(self, interval: float = 3.0, dividend_type: str = "none", **kwargs) -> None:
        super().__init__(**kwargs)
        self.interval = interval
        self.dividend_type = dividend_type
        self._symbols: List[str] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self.logger.info(f"Initialized MiniQmtDataGateway interval={self.interval}s")

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
        """Replay recent 1m bars as synthetic ticks (same idea as yfinance warm-up)."""
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
        self.logger.info("Starting miniQMT tick polling")
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        self.logger.info("Stopped miniQMT polling")

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

    def _run(self) -> None:
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
                    ts = datetime.now().replace(tzinfo=None)
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
