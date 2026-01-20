import random
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional

from ...live.gateways import DataGateway
from ...live.models import TickData


class SimulatedDataGateway(DataGateway):
    def __init__(self, interval: float = 1.0, base_prices: Optional[Dict[str, float]] = None) -> None:
        super().__init__()
        self.interval = interval
        self.base_prices = base_prices or {"AAPL": 150.0}
        self._symbols: List[str] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_prices: Dict[str, float] = dict(self.base_prices)

    def connect(self) -> bool:
        return True

    def subscribe(self, symbols: List[str]) -> bool:
        for symbol in symbols:
            if symbol not in self._symbols:
                self._symbols.append(symbol)
        return True

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)

    def _run(self) -> None:
        rng = random.Random()
        while self._running:
            for symbol in self._symbols:
                price = self._last_prices.get(symbol, self.base_prices.get(symbol, 100.0))
                price = price * (1 + rng.uniform(-0.01, 0.01))
                self._last_prices[symbol] = price
                if self._tick_handler:
                    self._tick_handler(
                        TickData(
                            symbol=symbol,
                            price=price,
                            timestamp=datetime.now(),
                            volume=rng.randint(100, 1000),
                            source="sim",
                        )
                    )
            time.sleep(self.interval)
