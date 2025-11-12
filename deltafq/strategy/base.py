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
        self.signals: pd.Series = pd.Series(dtype=int)

    def initialize(self) -> bool:
        self.logger.info(f"Initializing strategy: {self.name}")
        return True

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Return a `Series` containing {-1, 0, 1} strategy signals."""
        pass

    def run(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Run the strategy and return the signals."""
        self.logger.info(f"Running strategy: {self.name}")
        try:
            self.signals = self.generate_signals(data)
            return {"strategy_name": self.name, "signals": self.signals.astype(int)}
        except Exception as exc:
            raise StrategyError(f"Strategy execution failed: {exc}") from exc
