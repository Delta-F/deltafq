import threading
import time
from datetime import datetime
from typing import List, Optional

from ...live.gateways import DataGateway
from ...live.models import TickData


class AkshareDataGateway(DataGateway):
    def __init__(self, interval: float = 2.0, source: str = "em") -> None:
        super().__init__()
        self.interval = interval
        self.source = source
        self._symbols: List[str] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._ak = None

    def connect(self) -> bool:
        try:
            import akshare as ak  # type: ignore
        except Exception:
            return False
        self._ak = ak
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
        if self._ak is None:
            return
        while self._running:
            try:
                if self.source == "em":
                    df = self._ak.stock_zh_a_spot_em()
                else:
                    df = self._ak.stock_zh_a_spot()
                if not self._symbols:
                    time.sleep(self.interval)
                    continue
                code_series = df["代码"].astype(str)
                sub_df = df[code_series.str.endswith(tuple(self._symbols))]
                for _, row in sub_df.iterrows():
                    if self._tick_handler:
                        self._tick_handler(
                            TickData(
                                symbol=str(row["代码"]),
                                price=float(row["最新价"]),
                                timestamp=datetime.now(),
                                volume=int(row["成交量"]),
                                source="akshare",
                            )
                        )
            except Exception:
                pass
            time.sleep(self.interval)
