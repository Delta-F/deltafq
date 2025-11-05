"""
Macroeconomic indicators (placeholders).
"""

import pandas as pd
from ..core.base import BaseComponent


class MacroIndicators(BaseComponent):
    """Basic macro indicators alignment and transforms."""

    def initialize(self) -> bool:
        self.logger.info("Initializing macro indicators")
        return True

    def rate_spread(self, long_rate: pd.Series, short_rate: pd.Series) -> pd.Series:
        """Term spread (e.g., 10Y-2Y)."""
        if not long_rate.index.equals(short_rate.index):
            short_rate = short_rate.reindex(long_rate.index).ffill()
        return (long_rate - short_rate)

    def real_yield(self, nominal_yield: pd.Series, inflation_yoy: pd.Series) -> pd.Series:
        if not nominal_yield.index.equals(inflation_yoy.index):
            inflation_yoy = inflation_yoy.reindex(nominal_yield.index).ffill()
        return nominal_yield - inflation_yoy


