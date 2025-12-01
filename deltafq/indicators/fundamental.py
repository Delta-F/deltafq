"""
Fundamental indicators for DeltaFQ.
"""

import pandas as pd
from ..core.base import BaseComponent


class FundamentalIndicators(BaseComponent):
    """Basic fundamental indicators computed from preloaded fundamentals."""

    def __init__(self, **kwargs):
        """Initialize fundamental indicators."""
        super().__init__(**kwargs)
        self.logger.info("Initializing fundamental indicators")
                         
    def pe(self, price: pd.Series, eps_ttm: pd.Series) -> pd.Series:
        """PE = price / EPS"""
        eps = eps_ttm.reindex(price.index).ffill()
        return price / eps

    def pb(self, price: pd.Series, bvps: pd.Series) -> pd.Series:
        """PB = price / BVPS"""
        bvps = bvps.reindex(price.index).ffill()
        return price / bvps

    def ps(self, market_cap: pd.Series, revenue: pd.Series) -> pd.Series:
        """PS = market cap / revenue"""
        revenue = revenue.reindex(market_cap.index).ffill()
        return market_cap / revenue

    def roa(self, net_income: pd.Series, total_assets: pd.Series) -> pd.Series:
        """ROA = net income / average total assets"""
        assets = total_assets.reindex(net_income.index).ffill()
        return net_income / assets

    def roe(self, net_income: pd.Series, shareholders_equity: pd.Series) -> pd.Series:
        """ROE = net income / average shareholders equity"""
        equity = shareholders_equity.reindex(net_income.index).ffill()
        return net_income / equity

    def gross_margin(self, gross_profit: pd.Series, revenue: pd.Series) -> pd.Series:
        """gross margin = gross profit / revenue"""
        revenue_aligned = revenue.reindex(gross_profit.index).ffill()
        return gross_profit / revenue_aligned