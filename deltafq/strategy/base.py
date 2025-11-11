"""Common utilities for simple trading strategies."""

from abc import ABC, abstractmethod
from typing import Any, Dict

import pandas as pd

from ..core.base import BaseComponent
from ..core.exceptions import StrategyError


class BaseStrategy(BaseComponent, ABC):
    """Minimal base class: fetch signals from `generate_signals` and return them."""

    def __init__(self, name: str = None, **kwargs: Any) -> None:
        super().__init__(name=name, **kwargs)
        self.signals: pd.DataFrame = pd.DataFrame()

    def initialize(self) -> bool:
        self.logger.info("Initializing strategy: %s", self.name)
        return True

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Return a `DataFrame` containing strategy signals."""

    def run(self, data: pd.DataFrame) -> Dict[str, Any]:
        self.logger.info("Running strategy: %s", self.name)
        try:
            self.signals = self.generate_signals(data)
            return {"strategy_name": self.name, "signals": self.signals}
        except Exception as exc:  # pragma: no cover - thin wrapper
            raise StrategyError(f"Strategy execution failed: {exc}") from exc

