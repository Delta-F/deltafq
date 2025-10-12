"""
Technical indicators for DeltaFQ.
"""

import pandas as pd
import numpy as np
from ..core.base import BaseComponent


class TechnicalIndicators(BaseComponent):
    """Basic technical indicators."""
    
    def initialize(self) -> bool:
        """Initialize technical indicators."""
        self.logger.info("Initializing technical indicators")
        return True
    
    def sma(self, data: pd.Series, period: int) -> pd.Series:
        """Simple Moving Average."""
        return data.rolling(window=period).mean()
    
    def ema(self, data: pd.Series, period: int) -> pd.Series:
        """Exponential Moving Average."""
        return data.ewm(span=period).mean()
    
    def rsi(self, data: pd.Series, period: int = 14) -> pd.Series:
        """Relative Strength Index."""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def macd(self, data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """MACD indicator."""
        ema_fast = self.ema(data, fast)
        ema_slow = self.ema(data, slow)
        macd_line = ema_fast - ema_slow
        signal_line = self.ema(macd_line, signal)
        histogram = macd_line - signal_line
        
        return pd.DataFrame({
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        })
    
    def bollinger_bands(self, data: pd.Series, period: int = 20, std_dev: float = 2) -> pd.DataFrame:
        """Bollinger Bands."""
        sma = self.sma(data, period)
        std = data.rolling(window=period).std()
        
        return pd.DataFrame({
            'upper': sma + (std * std_dev),
            'middle': sma,
            'lower': sma - (std * std_dev)
        })

