"""
Fundamental indicators (placeholders).
"""

import pandas as pd
from ..core.base import BaseComponent


class FundamentalIndicators(BaseComponent):
    """Basic fundamental indicators computed from preloaded fundamentals."""

    def initialize(self) -> bool:
        self.logger.info("Initializing fundamental indicators")
        return True

    def pe(self, price: pd.Series, eps_ttm: pd.Series) -> pd.Series:
        eps = eps_ttm.reindex(price.index).ffill()
        return price / eps

    def pb(self, price: pd.Series, bvps: pd.Series) -> pd.Series:
        bvps = bvps.reindex(price.index).ffill()
        return price / bvps

    def earnings_yield(self, price: pd.Series, eps_ttm: pd.Series) -> pd.Series:
        pe_series = self.pe(price, eps_ttm)
        return 1.0 / pe_series


