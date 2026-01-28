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
        """Dynamically subscribe to a list of symbols."""
        for symbol in symbols:
            if symbol not in self._symbols:
                self._symbols.append(symbol)
                self.logger.info(f"Subscribed to {symbol}")
        return True

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

                    tick = TickData(symbol=symbol, price=float(price), timestamp=datetime.now(), volume=int(volume), source="yfinance")
                    self._tick_handler(tick)
                except Exception as e:
                    self.logger.error(f"Error fetching data for {symbol}: {str(e)}")

            time.sleep(self.interval)
