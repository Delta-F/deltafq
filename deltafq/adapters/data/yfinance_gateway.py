"""
yfinance 行情，类 YFinanceDataGateway。

对外
    connect              探测网络与 yfinance 可用性
    subscribe            追加标的并 1m 暖机回放
    start                开 daemon 线程轮询 fast_info
    stop                 停线程
    get_today_ohlc       当日开高低（fast_info）
    get_depths           合成盘口（价由 last_price 铺档，量随机且尺度参考 last_volume）

私有
    _warm_up             近一日 1m K 线逐根暖机 tick
    _run                 主循环：按 interval 拉 last_price / last_volume
"""
import random
import threading
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import yfinance as yf

from ...live.gateways import DataGateway
from ...live.models import TickData


class YFinanceDataGateway(DataGateway):
    """轮询 yfinance fast_info；时间戳为 naive UTC；无真实 Level2。"""

    def __init__(self, interval: float = 60.0, **kwargs: Any) -> None:
        """轮询间隔（秒）。"""
        super().__init__(**kwargs)
        self.interval = interval
        self._symbols: List[str] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self.logger.info(f"Initialized YFinanceDataGateway with interval: {self.interval}s")

    def connect(self) -> bool:
        """验证网络与 yfinance 可访问。"""
        try:
            yf.Ticker("AAPL").fast_info
            self.logger.info("Connected to yfinance")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect: {e}")
            return False

    def subscribe(self, symbols: List[str]) -> bool:
        """追加订阅；新标的拉近一日 1m 数据暖机并逐根回调。"""
        new_symbols = [s for s in symbols if s not in self._symbols]
        for symbol in new_symbols:
            self._symbols.append(symbol)
            self._warm_up(symbol)
        return True

    def start(self) -> None:
        """启动轮询线程。"""
        if self._running:
            return
        self.logger.info("Starting yfinance polling")
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """停止轮询线程。"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        self.logger.info("Stopped yfinance polling")

    def get_today_ohlc(self, symbol: str) -> Optional[Dict[str, float]]:
        """从 fast_info 取当日开、高、低；缺字段返回 None。"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.fast_info
            open_price = info.open
            high_price = info.day_high
            low_price = info.day_low
            if open_price is None or high_price is None or low_price is None:
                self.logger.warning(
                    f"Incomplete OHLC data for {symbol}: open={open_price}, high={high_price}, low={low_price}"
                )
                return None
            return {"open": open_price, "high": high_price, "low": low_price}
        except Exception as e:
            self.logger.error(f"Failed to get today's OHLC for {symbol}: {e}")
            return None

    def get_depths(self, symbol: str, levels: int = 5) -> Dict[str, List[Dict[str, float]]]:
        """
        合成盘口（非真实 L2）：价由 fast_info.last_price 按相对价差铺档；
        各档成交量在 [~5%·last_volume, last_volume] 内独立随机（无 last_volume 时用默认尺度）。
        """
        levels = max(1, min(int(levels), 10))
        try:
            info = yf.Ticker(symbol).fast_info
            last = info.last_price
            if last is None:
                return {"bids": [], "asks": []}
            last_f = float(last)
            if last_f <= 0:
                return {"bids": [], "asks": []}
            vol_raw = info.last_volume
            base = int(vol_raw) if vol_raw is not None and int(vol_raw) > 0 else 1000
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
            vb = float(random.randint(lo, hi))
            va = float(random.randint(lo, hi))
            bids.append({"level": lv, "price": round(last_f - lv * step, 6), "volume": vb})
            asks.append({"level": lv, "price": round(last_f + lv * step, 6), "volume": va})
        return {"bids": bids, "asks": asks}

    # ---------- 私有 ----------

    def _warm_up(self, symbol: str) -> None:
        """下载近一日 1m K 线，逐根合成暖机 tick（source=yf_warmup）。"""
        self.logger.debug(f"Warming up {symbol} with intraday history...")
        try:
            data = yf.download(symbol, period="1d", interval="1m", progress=False)
            if data.empty:
                self.logger.warning(f"No warm-up data for {symbol}")
                return
            pushed_count = 0
            for timestamp, row in data.iterrows():
                local_ts = timestamp.to_pydatetime().replace(tzinfo=None)
                price = float(row["Close"])
                volume = int(row["Volume"])
                tick = TickData(
                    symbol=symbol,
                    price=price,
                    timestamp=local_ts,
                    volume=volume,
                    source="yf_warmup",
                )
                if self._tick_handler:
                    self._tick_handler(tick)
                pushed_count += 1
            self.logger.info(f"Subscribed & Warmed up {symbol} ({pushed_count} bars)")
        except Exception as e:
            self.logger.warning(f"Warm-up failed for {symbol}: {e}")

    def _run(self) -> None:
        """轮询各标的 fast_info，组 TickData 回调。"""
        while self._running:
            for symbol in self._symbols:
                try:
                    ticker = yf.Ticker(symbol)
                    info = ticker.fast_info
                    price = info.last_price
                    volume = info.last_volume
                    if price is None or volume is None:
                        continue
                    tick = TickData(
                        symbol=symbol,
                        price=float(price),
                        timestamp=datetime.utcnow(),
                        volume=int(volume),
                        source="yfinance",
                    )
                    if self._tick_handler:
                        self._tick_handler(tick)
                except Exception as e:
                    self.logger.error(f"Error fetching data for {symbol}: {str(e)}")
                    continue
            time.sleep(self.interval)
