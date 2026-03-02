"""
Live engine: runs strategy on real-time tick stream and sends orders via gateways.

Typical usage:
    engine = LiveEngine(symbol="BTC-USD", signal_interval="1m", lookback_bars=50)
    engine.set_trade_gateway("paper", initial_capital=100000)
    engine.add_strategy(MyStrategy())
    engine.run_live()
    # ... on KeyboardInterrupt: engine.stop()
"""

import time
from collections import deque
from datetime import datetime, timedelta, timezone
from typing import Optional, Any, Dict, List

import pandas as pd

from ..core.base import BaseComponent
from ..data import DataFetcher
from ..strategy.base import BaseStrategy
from .event_engine import EventEngine, EVENT_TICK
from .gateway_registry import create_data_gateway, create_trade_gateway
from .models import OrderRequest


# Calendar days per bar by interval (for sizing fetch range). 1d: ~252 trading days / 365 calendar days.
# Example for lookback_bars=100:
#   signal_interval |  formula              | calendar days
#   ----------------|----------------------|---------------
#   1d              | 100 * (365/252) + 60 | 205
#   1wk             | 100 * (365/52) + 60  | 762
#   1mo             | 100 * (365/12) + 60  | 3102
#   1m/5m/15m/1h    | max(7, min(60, 100//10)) | 10
#   tick            | 0                       | 0

_REFETCH_SEC = {"1m": 60, "5m": 300, "15m": 900, "1h": 3600, "1d": 86400}
_FETCH_DAYS_PER_BAR = {"1d": 365 / 252, "1wk": 365 / 52, "1mo": 365 / 12}
_SIG_ICON = {1: "↑", -1: "↓", 0: "-"}
_ACTION_ICON = {"buy": "↑", "sell": "↓", "skip": "x", "no_change": "-"}


def _vol_str(v: float) -> str:
    """Format volume as 41.4B, 12.3M, 1.2K or plain number."""
    if v >= 1e9:
        return f"{v / 1e9:.1f}B"
    if v >= 1e6:
        return f"{v / 1e6:.1f}M"
    if v >= 1e3:
        return f"{v / 1e3:.1f}K"
    return str(int(v))


class LiveEngine(BaseComponent):
    """
    Runs strategy on live data and submits orders via gateways.

    Args:
        symbol: Trading symbol (e.g. "BTC-USD", "AAPL").
        interval: Data gateway poll interval in seconds.
        lookback_bars: Number of bars for strategy input.
        signal_interval: Bar interval for signals - "tick" (use tick as Close),
            "1m", "5m", "15m", "1h", "1d", "1wk", "1mo".
        data_gateway_name: Data source (default "yfinance").
        trade_gateway_name: Execution gateway (default "paper").

    Use set_data_gateway/set_trade_gateway before run_live() to pass gateway params.
    Strategy can set self.order_amount for fixed $ per buy; else full cash.
    """

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
        """Initialize engine. Call set_data_gateway/set_trade_gateway before run_live() for gateway params."""
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

    def set_parameters(
        self,
        symbol: Optional[str] = None,
        interval: Optional[float] = None,
        lookback_bars: Optional[int] = None,
        signal_interval: Optional[str] = None,
    ) -> None:
        """Update symbol, interval, lookback or signal_interval."""
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
        """Set data gateway by name; optional params (e.g. interval) passed to gateway. Clears cached gateway."""
        self.data_gateway_name = name
        self._data_gateway_params = dict(params)
        self._data_gw = None

    def set_trade_gateway(self, name: str, **params: Any) -> None:
        """Set trade gateway by name; params (e.g. initial_capital, commission) passed to gateway. Clears cached gateway."""
        self.trade_gateway_name = name
        self._trade_gateway_params = dict(params)
        self._trade_gw = None

    def add_strategy(self, strategy: BaseStrategy) -> None:
        """Set the strategy used for signal generation."""
        self._strategy = strategy

    def run_live(self) -> None:
        """Connect gateways, register tick handlers, subscribe and start data stream."""
        self._ensure_gateways()
        if not self._trade_gw.connect() or not self._data_gw.connect():
            raise RuntimeError("Gateway connect failed")

        self._event_engine.on(EVENT_TICK, self._on_tick_match)
        self._event_engine.on(EVENT_TICK, self._on_tick_strategy)
        self._data_gw.set_tick_handler(lambda t: self._event_engine.emit(EVENT_TICK, t))

        self._data_gw.subscribe([self.symbol])
        self._data_gw.start()
        self.logger.info(f"Running: {self.symbol} {self.signal_interval} lookback={self.lookback_bars}")

    def stop(self) -> None:
        """Stop gateways and release resources."""
        if self._data_gw:
            self._data_gw.stop()
        if self._trade_gw:
            self._trade_gw.stop()

    def get_chart_data(self) -> Dict[str, Any]:
        """
        Return cached K-lines and signals for charting.

        Called without re-fetching or re-calculating. Empty if no cache yet
        (e.g. before first tick cycle).

        Returns:
            dict with keys: candles (list of {date, open, high, low, close}),
            signals (list of int).
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

    def _ensure_gateways(self) -> None:
        """Lazy-create data gateway, trade gateway and (if not tick) DataFetcher."""
        if self.symbol is None:
            raise ValueError("symbol must be set (set_parameters or constructor)")
        if self._data_gw is None:
            self._data_gw = create_data_gateway(
                self.data_gateway_name, interval=self.interval, **self._data_gateway_params
            )
        if self._trade_gw is None:
            self._trade_gw = create_trade_gateway(self.trade_gateway_name, **self._trade_gateway_params)
        if self._data_fetcher is None and self.signal_interval != "tick":
            self._data_fetcher = DataFetcher(source="yahoo")

    def _fetch_bars(self) -> Optional[pd.DataFrame]:
        """Fetch last lookback_bars of K-line data via DataFetcher for current signal_interval."""
        if self._data_fetcher is None or self.signal_interval == "tick":
            return None
        now = datetime.now(timezone.utc)
        # Request enough calendar days to cover lookback_bars. 1d: ~1.45 cal days per trading day.
        days_per_bar = _FETCH_DAYS_PER_BAR.get(self.signal_interval)
        if days_per_bar is not None:
            cal_days = int(self.lookback_bars * days_per_bar) + 60  # buffer for holidays/missing
            start = (now - timedelta(days=max(cal_days, 60))).strftime("%Y-%m-%d")
        else:
            # Intraday (1m, 5m, 15m, 1h): 7 days usually enough; scale if lookback is large
            start = (now - timedelta(days=max(7, min(60, self.lookback_bars // 10)))).strftime(
                "%Y-%m-%d"
            )
        # yfinance end_date is exclusive; use next day to include today
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

    def _on_tick_match(self, tick: Any) -> None:
        """Forward tick to execution engine for order matching."""
        if getattr(tick, "source", None) != "yf_warmup":
            t = tick.timestamp
            ts = t.strftime("%H:%M:%S")
            v = tick.volume
            self.logger.info(f"Tick: [{tick.symbol}] {tick.price:.2f} vol={v}({_vol_str(v)}) @ {ts}")
        if self._trade_gw:
            self._trade_gw._engine.on_tick(tick)

    def _on_tick_strategy(self, tick: Any) -> None:
        """Build data (tick or fetched bars), run strategy, send order on signal change."""
        if getattr(tick, "source", None) == "yf_warmup":
            return
        if tick.symbol != self.symbol or self._strategy is None:
            return

        if self.signal_interval == "tick":
            self._prices.append(float(tick.price))
            self._timestamps.append(tick.timestamp)
            if len(self._prices) < self.lookback_bars:
                return
            n = self.lookback_bars
            df = pd.DataFrame(
                {"Close": list(self._prices)[-n:]},
                index=list(self._timestamps)[-n:],
            )
        else:
            refetch_sec = _REFETCH_SEC.get(self.signal_interval, 60)
            if time.time() - self._last_fetch_time < refetch_sec:
                return
            df = self._fetch_bars()
            if df is None:
                return
            self._last_fetch_time = time.time()

        try:
            signals = self._strategy.generate_signals(df)
        except Exception as e:
            self.logger.warning(f"Strategy signal failed: {e}")
            return

        if signals.empty:
            return

        # Cache bars and signals for chart / application consumption
        self._cached_bars = df
        self._cached_signals = signals

        signal = int(signals.iloc[-1])
        eng = self._trade_gw._engine
        px = tick.price
        position = eng.position_manager.get_position(self.symbol)
        cash = eng.cash or 0.0
        commission = getattr(eng, "commission", 0.0) or 0.0

        # One-line summary every time we have a signal
        action_key = "no_change"
        action = "no_change"
        if signal == 1 and self._last_signal <= 0:
            am = getattr(self._strategy, "order_amount", None)
            max_qty = max(0, int(cash / (px * (1 + commission))))
            if am is not None and am > 0:
                qty = min(max(0, int(am / (px * (1 + commission)))), max_qty)
            else:
                qty = max_qty
            if qty > 0:
                action_key, action = "buy", f"BUY qty={qty}"
            else:
                action_key, action = "skip", "BUY skip (qty=0)"
        elif signal == -1 and self._last_signal >= 0:
            if position > 0:
                action_key, action = "sell", f"SELL qty={position}"
            else:
                action_key, action = "skip", "SELL skip (position=0)"
        icon = _SIG_ICON.get(signal, "?")
        act_icon = _ACTION_ICON.get(action_key, "?")
        self.logger.info(
            f"Signal: {icon} {signal} [{self.symbol}] {px:.2f} cash={cash:.0f} pos={position} -> {act_icon} {action}"
        )

        if signal == self._last_signal:
            return

        # Cancel pending order when signal flips to avoid contradictory fills
        if self._last_pending_order_id:
            self._trade_gw.cancel_order(self._last_pending_order_id)
            self.logger.info(f"Cancelled pending order: {self._last_pending_order_id}")
            self._last_pending_order_id = None

        if signal == 1 and self._last_signal <= 0:
            if qty > 0:
                req = OrderRequest(symbol=self.symbol, quantity=qty, price=px, order_type="limit")
                order_id = self._trade_gw.send_order(req)
                self._last_pending_order_id = order_id
        elif signal == -1 and self._last_signal >= 0 and position > 0:
            req = OrderRequest(symbol=self.symbol, quantity=-position, price=px, order_type="limit")
            order_id = self._trade_gw.send_order(req)
            self._last_pending_order_id = order_id

        self._last_signal = signal