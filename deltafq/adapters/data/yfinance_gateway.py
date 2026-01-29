import threading
import time
from datetime import datetime
from typing import List, Optional, Dict
import yfinance as yf

from ...live.gateways import DataGateway
from ...live.models import TickData

class YFinanceDataGateway(DataGateway):
    """
    Market data gateway implementation using yfinance.
    Note: All timestamps are standardized to Naive UTC.
    """
    
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
            self.logger.info("Connected to yfinance")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect: {e}")
            return False

    def subscribe(self, symbols: List[str]) -> bool:
        """Dynamically subscribe to a list of symbols with warm-up data."""
        for symbol in symbols:
            if symbol not in self._symbols:
                self._symbols.append(symbol)
                # Perform data warm-up for new symbol
                self._warm_up(symbol)
        return True

    def _warm_up(self, symbol: str) -> None:
        """Fetch and push today's historical 1m data to fill charts."""
        self.logger.debug(f"Warming up {symbol} with intraday history...")
        try:
            # Fetch last 1 day of 1-minute data
            data = yf.download(symbol, period="1d", interval="1m", progress=False)
            if data.empty:
                self.logger.warning(f"No warm-up data for {symbol}")
                return

            pushed_count = 0

            for timestamp, row in data.iterrows():
                # Standardize to Naive UTC: yfinance returns UTC aware, we strip tzinfo for consistency
                local_ts = timestamp.to_pydatetime().replace(tzinfo=None)
                
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
                
            self.logger.info(f"Subscribed & Warmed up {symbol} ({pushed_count} bars)")
        except Exception as e:
            self.logger.warning(f"Warm-up failed for {symbol}: {e}")

    def start(self) -> None:
        """Start the polling thread."""
        if self._running:
            return
        
        self.logger.info("Starting yfinance polling")
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the polling thread."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        self.logger.info("Stopped yfinance polling")

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

                    # Update last data for reference
                    self._last_data[symbol] = (price, volume)

                    tick = TickData(
                        symbol=symbol, 
                        price=float(price), 
                        timestamp=datetime.utcnow(), 
                        volume=int(volume), 
                        source="yfinance"
                    )
                    self._tick_handler(tick)
                except Exception as e:
                    self.logger.error(f"Error fetching data for {symbol}: {str(e)}")

            time.sleep(self.interval)
