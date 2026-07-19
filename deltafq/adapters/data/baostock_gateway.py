"""
baostock 行情，类 BaostockDataGateway。

对外
    connect              bs.login
    subscribe            追加标的并 5m 暖机回放
    start                开 daemon 线程轮询最新 5m
    stop                 停线程并 logout
    get_today_ohlc       当日开高低（日线）
    get_depths           合成盘口（价由最新 close 铺档）

私有
    _warm_up             最近交易日 5m 逐根暖机 tick
    _run                 主循环：bar 时间戳变化才推送
    _fetch_bars          已登录会话上拉 K 线
"""
import random
import threading
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd

from .baostock_bars import to_bs_code
from ...live.gateways import DataGateway
from ...live.models import TickData


class BaostockDataGateway(DataGateway):
    """轮询 baostock 5m 最新价；无真实 tick / Level2。"""

    def __init__(self, interval: float = 60.0, **kwargs: Any) -> None:
        """轮询间隔（秒）。"""
        super().__init__(**kwargs)
        self.interval = interval
        self._symbols: List[str] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._bs = None
        self._last_bar_ts: Dict[str, Any] = {}
        self.logger.info(f"Initialized BaostockDataGateway with interval: {self.interval}s")

    def connect(self) -> bool:
        """登录 baostock。"""
        try:
            import baostock as bs  # type: ignore

            bs.login()
            self._bs = bs
            self.logger.info("Connected to baostock")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect: {e}")
            return False

    def subscribe(self, symbols: List[str]) -> bool:
        """追加订阅；新标的拉最近交易日 5m 暖机并逐根回调。"""
        new_symbols = [s for s in symbols if s not in self._symbols]
        for symbol in new_symbols:
            self._symbols.append(symbol)
            self._warm_up(symbol)
        return True

    def start(self) -> None:
        """启动轮询线程。"""
        if self._running:
            return
        self.logger.info("Starting baostock polling")
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """停止轮询线程并 logout。"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        if self._bs is not None:
            self._bs.logout()
            self._bs = None
        self.logger.info("Stopped baostock polling")

    def get_today_ohlc(self, symbol: str) -> Optional[Dict[str, float]]:
        """从最近日线取开、高、低；缺数据返回 None。"""
        try:
            data = self._fetch_bars(symbol, "d")
            if data is None or data.empty:
                return None
            row = data.iloc[-1]
            return {"open": float(row["Open"]), "high": float(row["High"]), "low": float(row["Low"])}
        except Exception as e:
            self.logger.error(f"Failed to get today's OHLC for {symbol}: {e}")
            return None

    def get_depths(self, symbol: str, levels: int = 5) -> Dict[str, List[Dict[str, float]]]:
        """
        合成盘口（非真实 L2）：价由最新 5m close 按相对价差铺档；
        各档量在 [~5%·volume, volume] 内独立随机。
        """
        levels = max(1, min(int(levels), 10))
        try:
            data = self._fetch_bars(symbol, "5")
            if data is None or data.empty:
                return {"bids": [], "asks": []}
            row = data.iloc[-1]
            last_f = float(row["Close"])
            if last_f <= 0:
                return {"bids": [], "asks": []}
            vol_raw = row["Volume"]
            base = int(vol_raw) if pd.notna(vol_raw) and int(vol_raw) > 0 else 1000
        except Exception as e:
            self.logger.debug(f"get_depths {symbol}: {e}")
            return {"bids": [], "asks": []}

        lo = max(1, base // 20)
        hi = max(lo, base)
        step = max(last_f * 1e-4, 0.01)
        bids: List[Dict[str, float]] = []
        asks: List[Dict[str, float]] = []
        for i in range(levels):
            lv = float(i + 1)
            bids.append({"level": lv, "price": round(last_f - lv * step, 6), "volume": float(random.randint(lo, hi))})
            asks.append({"level": lv, "price": round(last_f + lv * step, 6), "volume": float(random.randint(lo, hi))})
        return {"bids": bids, "asks": asks}

    # ---------- 私有 ----------

    def _warm_up(self, symbol: str) -> None:
        """最近交易日 5m K 线，逐根合成暖机 tick（source=baostock_warmup）。"""
        self.logger.debug(f"Warming up {symbol} with baostock 5m history...")
        try:
            data = self._fetch_bars(symbol, "5")
            if data is None or data.empty:
                self.logger.warning(f"No warm-up data for {symbol}")
                return
            last_day = pd.Timestamp(data.index[-1]).normalize()
            data = data[data.index.normalize() == last_day]
            pushed_count = 0
            for timestamp, row in data.iterrows():
                tick = TickData(
                    symbol=symbol,
                    price=float(row["Close"]),
                    timestamp=timestamp.to_pydatetime().replace(tzinfo=None),
                    volume=int(row["Volume"]),
                    source="baostock_warmup",
                )
                if self._tick_handler:
                    self._tick_handler(tick)
                pushed_count += 1
            self._last_bar_ts[symbol] = data.index[-1]
            self.logger.info(f"Subscribed & Warmed up {symbol} ({pushed_count} bars)")
        except Exception as e:
            self.logger.warning(f"Warm-up failed for {symbol}: {e}")

    def _run(self) -> None:
        """轮询各标的最新 5m；仅 bar 时间变化时组 TickData 回调。"""
        while self._running:
            for symbol in self._symbols:
                try:
                    data = self._fetch_bars(symbol, "5")
                    if data is None or data.empty:
                        continue
                    bar_ts = data.index[-1]
                    if self._last_bar_ts.get(symbol) == bar_ts:
                        continue
                    self._last_bar_ts[symbol] = bar_ts
                    row = data.iloc[-1]
                    tick = TickData(
                        symbol=symbol,
                        price=float(row["Close"]),
                        timestamp=bar_ts.to_pydatetime().replace(tzinfo=None),
                        volume=int(row["Volume"]),
                        source="baostock",
                    )
                    if self._tick_handler:
                        self._tick_handler(tick)
                except Exception as e:
                    self.logger.error(f"Error fetching data for {symbol}: {str(e)}")
                    continue
            time.sleep(self.interval)

    def _fetch_bars(self, symbol: str, freq: str) -> Optional[pd.DataFrame]:
        """已登录会话上拉近 7 日 K 线（frequency: d / 5）。"""
        if self._bs is None:
            return None
        end = datetime.now().strftime("%Y-%m-%d")
        start = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        fields = "date,time,open,high,low,close,volume" if freq != "d" else "date,open,high,low,close,volume"
        rs = self._bs.query_history_k_data_plus(
            to_bs_code(symbol), fields, start_date=start, end_date=end, frequency=freq, adjustflag="3"
        )
        rows = []
        while rs.error_code == "0" and rs.next():
            rows.append(rs.get_row_data())
        if not rows:
            return pd.DataFrame()
        raw = pd.DataFrame(rows, columns=rs.fields)
        idx = (
            pd.to_datetime(raw["time"].str[:14], format="%Y%m%d%H%M%S")
            if "time" in raw.columns
            else pd.to_datetime(raw["date"])
        )
        return pd.DataFrame(
            {
                "Open": pd.to_numeric(raw["open"]).to_numpy(),
                "High": pd.to_numeric(raw["high"]).to_numpy(),
                "Low": pd.to_numeric(raw["low"]).to_numpy(),
                "Close": pd.to_numeric(raw["close"]).to_numpy(),
                "Volume": pd.to_numeric(raw["volume"]).to_numpy(),
            },
            index=pd.DatetimeIndex(idx),
        ).sort_index()
