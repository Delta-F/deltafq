"""
Volatility indicators for DeltaFQ.
"""

import pandas as pd
import numpy as np
from ..core.base import BaseComponent


class VolatilityIndicators(BaseComponent):
    """Volatility-based technical indicators."""
    
    def initialize(self) -> bool:
        """Initialize volatility indicators."""
        self.logger.info("Initializing volatility indicators")
        return True
    
    def atr(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Average True Range."""
        # True Range
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Average True Range
        return tr.rolling(window=period).mean()
    
    def bollinger_bandwidth(self, data: pd.Series, period: int = 20, std_dev: float = 2) -> pd.Series:
        """Bollinger Band Width."""
        sma = data.rolling(window=period).mean()
        std = data.rolling(window=period).std()
        
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        
        return (upper_band - lower_band) / sma
    
    def keltner_channels(self, high: pd.Series, low: pd.Series, close: pd.Series, 
                        period: int = 20, multiplier: float = 2) -> pd.DataFrame:
        """Keltner Channels."""
        typical_price = (high + low + close) / 3
        middle_line = typical_price.rolling(window=period).mean()
        atr = self.atr(high, low, close, period)
        
        return pd.DataFrame({
            'upper': middle_line + (multiplier * atr),
            'middle': middle_line,
            'lower': middle_line - (multiplier * atr)
        })
    
    def donchian_channels(self, high: pd.Series, low: pd.Series, period: int = 20) -> pd.DataFrame:
        """Donchian Channels."""
        return pd.DataFrame({
            'upper': high.rolling(window=period).max(),
            'lower': low.rolling(window=period).min(),
            'middle': (high.rolling(window=period).max() + low.rolling(window=period).min()) / 2
        })
    
    def volatility_ratio(self, data: pd.Series, short_period: int = 10, long_period: int = 30) -> pd.Series:
        """Volatility Ratio."""
        short_vol = data.rolling(window=short_period).std()
        long_vol = data.rolling(window=long_period).std()
        
        return short_vol / long_vol

