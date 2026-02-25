"""
Live engine: runs strategy on real-time tick stream and sends orders via gateways.
"""

import time
from collections import deque
from datetime import datetime, timedelta
from typing import Optional, Any

import pandas as pd

from ..core.base import BaseComponent
from ..data import DataFetcher
from ..strategy.base import BaseStrategy
from .event_engine import EventEngine, EVENT_TICK
from .gateway_registry import create_data_gateway, create_trade_gateway
from .models import OrderRequest

_REFETCH_SEC = {"1m": 60, "5m": 300, "15m": 900, "1d": 86400}


class LiveEngine(BaseComponent):
    """
    Runs strategy on live data and submits orders via gateways.
    signal_interval default "5m"; "tick" = tick prices as Close; "1d"/"5m"/"15m"/"1m" = DataFetcher bars.
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
        """Initialize engine: symbol, gateway names, signal period and lookback. Use set_data_gateway/set_trade_gateway to pass gateway params (e.g. initial_capital, commission)."""
        super().__init__(**kwargs)
        self.symbol = symbol
        self.interval = interval
        self.lookback_bars = lookback_bars
        self.signal_interval = signal_interval
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
        self._last_fetch_time = 0.0

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
        now = datetime.utcnow()
        if self.signal_interval == "1d":
            start = (now - timedelta(days=max(self.lookback_bars + 5, 60))).strftime("%Y-%m-%d")
        else:
            start = (now - timedelta(days=7)).strftime("%Y-%m-%d")
        end = now.strftime("%Y-%m-%d")
        try:
            data = self._data_fetcher.fetch_data(
                self.symbol, start, end, clean=True, interval=self.signal_interval
            )
        except Exception as e:
            self.logger.warning(f"DataFetcher failed: {e}")
            return None
        if data.empty or len(data) < self.lookback_bars:
            return None
        return data.tail(self.lookback_bars)

    def _on_tick_match(self, tick: Any) -> None:
        """Forward tick to execution engine for order matching."""
        if getattr(tick, "source", None) != "yf_warmup":
            self.logger.info(f"tick symbol={getattr(tick, 'symbol', '')} price={getattr(tick, 'price', 0):.2f} ts={getattr(tick, 'timestamp', '')}")
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
        signal = int(signals.iloc[-1])
        eng = self._trade_gw._engine
        px = tick.price
        position = eng.position_manager.get_position(self.symbol)
        cash = eng.cash or 0.0
        commission = getattr(eng, "commission", 0.0) or 0.0

        # One-line summary every time we have a signal
        action = "no_change"
        if signal == 1 and self._last_signal <= 0:
            qty = max(0, int(cash / (px * (1 + commission))))
            action = f"BUY qty={qty}" if qty > 0 else "BUY skip (qty=0)"
        elif signal == -1 and self._last_signal >= 0:
            action = f"SELL qty={position}" if position > 0 else "SELL skip (position=0)"
        elif signal == self._last_signal:
            action = "no_change"
        self.logger.info(
            f"signal={signal} last_signal={self._last_signal} price={px:.2f} cash={cash:.0f} position={position} -> {action}"
        )

        if signal == self._last_signal:
            return

        if signal == 1 and self._last_signal <= 0:
            qty = max(0, int(cash / (px * (1 + commission))))
            if qty > 0:
                req = OrderRequest(symbol=self.symbol, quantity=qty, price=px, order_type="limit")
                self._trade_gw.send_order(req)
        elif signal == -1 and self._last_signal >= 0 and position > 0:
            req = OrderRequest(symbol=self.symbol, quantity=-position, price=px, order_type="limit")
            self._trade_gw.send_order(req)

        self._last_signal = signal

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
        self.logger.info(
            f"LiveEngine running: symbol={self.symbol}, signal_interval={self.signal_interval}, lookback={self.lookback_bars}"
        )

    def stop(self) -> None:
        """Stop data gateway and release resources."""
        if self._data_gw:
            self._data_gw.stop()