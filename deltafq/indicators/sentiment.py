"""
Sentiment indicators (placeholders).
"""

import pandas as pd
from ..core.base import BaseComponent


class SentimentIndicators(BaseComponent):
    """Basic sentiment indicators from precomputed series."""

    def initialize(self) -> bool:
        self.logger.info("Initializing sentiment indicators")
        return True

    def zscore(self, series: pd.Series, window: int = 60) -> pd.Series:
        mean = series.rolling(window=window).mean()
        std = series.rolling(window=window).std(ddof=0)
        return (series - mean) / std

    def combine(self, signals: dict) -> pd.Series:
        """Simple average of normalized sentiment series."""
        df = pd.DataFrame(signals)
        return df.mean(axis=1)


