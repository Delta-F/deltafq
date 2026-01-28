import threading
import time
from datetime import datetime
from typing import List, Optional, Dict
import yfinance as yf

from ...live.gateways import DataGateway
from ...live.models import TickData

class YFinanceDataGateway(DataGateway):
    """Market data gateway implementation using yfinance."""
    
    def __init__(self, interval: float = 60.0, **kwargs) -> None:
        """Initialize the gateway."""
        super().__init__(**kwargs)
        self.interval = interval
        self._symbols: List[str] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._tickers: Dict[str, yf.Ticker] = {}
        # Track last pushed data to avoid duplicates at handover
        self._last_data: Dict[str, tuple] = {}
        self.logger.info(f"Initialized YFinanceDataGateway with interval: {self.interval}s")

    def connect(self) -> bool:
        """Verify network connectivity."""
        try:
            yf.Ticker("AAPL").fast_info
            self.logger.info("Connection successful")
            return True
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            return False

    def subscribe(self, symbols: List[str]) -> bool:
        """Dynamically subscribe to a list of symbols with warm-up data."""
        for symbol in symbols:
            if symbol not in self._symbols:
                self._symbols.append(symbol)
                self.logger.info(f"Subscribed to {symbol}")
                # Perform data warm-up for new symbol
                self._warm_up(symbol)
        return True

    def _warm_up(self, symbol: str) -> None:
        """Fetch and push today's historical 1m data to fill charts."""
        self.logger.info(f"Warming up {symbol} with intraday history...")
        try:
            # Fetch last 1 day of 1-minute data
            data = yf.download(symbol, period="1d", interval="1m", progress=False)
            if data.empty:
                return

            today = datetime.now().date()
            pushed_count = 0

            for timestamp, row in data.iterrows():
                # 转换时区：将 yfinance 的 UTC 时间转换为本地时间
                local_ts = timestamp.to_pydatetime()
                if local_ts.tzinfo:
                    local_ts = local_ts.astimezone() # 自动转换为本地时区
                
                # 移除时区标签以便统一处理，但此时小时数已经是本地时间了
                local_ts = local_ts.replace(tzinfo=None)

                # Only push data points for today (local time)
                if local_ts.date() != today:
                    continue
                
                price = float(row['Close'])
                volume = int(row['Volume'])
                
                tick = TickData(
                    symbol=symbol,
                    price=price,
                    timestamp=local_ts,
                    volume=volume,
                    source="yf_warmup"
                )
                
                if self._tick_handler:
                    self._tick_handler(tick)
                
                # Update last data to ensure handover to live is smooth
                self._last_data[symbol] = (price, volume)
                pushed_count += 1
                
            self.logger.info(f"Warm-up complete for {symbol}: {pushed_count} bars pushed")
        except Exception as e:
            self.logger.warning(f"Warm-up failed for {symbol}: {e}")

    def start(self) -> None:
        """Start the polling thread."""
        if self._running:
            return
        
        self.logger.info("Starting yfinance polling thread")
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the polling thread."""
        self.logger.info("Stopping yfinance polling thread")
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        self.logger.info("Gateway stopped")

    def _run(self) -> None:
        """Main loop for polling data."""
        while self._running:
            for symbol in self._symbols:
                try:
                    ticker = yf.Ticker(symbol)
                    
                    info = ticker.fast_info
                    price = info.last_price
                    volume = info.last_volume
                    if price is None or volume is None:
                        continue

                    # Skip if data hasn't changed (deduplication)
                    if self._last_data.get(symbol) == (price, volume):
                        continue
                    
                    self._last_data[symbol] = (price, volume)

                    tick = TickData(
                        symbol=symbol, 
                        price=float(price), 
                        timestamp=datetime.now(), 
                        volume=int(volume), 
                        source="yfinance"
                    )
                    self._tick_handler(tick)
                except Exception as e:
                    self.logger.error(f"Error fetching data for {symbol}: {str(e)}")

            time.sleep(self.interval)
