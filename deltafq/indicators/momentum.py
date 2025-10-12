"""
Momentum indicators for DeltaFQ.
"""

import pandas as pd
import numpy as np
from ..core.base import BaseComponent


class MomentumIndicators(BaseComponent):
    """Momentum-based technical indicators."""
    
    def initialize(self) -> bool:
        """Initialize momentum indicators."""
        self.logger.info("Initializing momentum indicators")
        return True
    
    def roc(self, data: pd.Series, period: int) -> pd.Series:
        """Rate of Change."""
        return data.pct_change(period) * 100
    
    def momentum(self, data: pd.Series, period: int) -> pd.Series:
        """Momentum indicator."""
        return data - data.shift(period)
    
    def williams_r(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Williams %R."""
        highest_high = high.rolling(window=period).max()
        lowest_low = low.rolling(window=period).min()
        return -100 * (highest_high - close) / (highest_high - lowest_low)
    
    def stochastic(self, high: pd.Series, low: pd.Series, close: pd.Series, 
                   k_period: int = 14, d_period: int = 3) -> pd.DataFrame:
        """Stochastic Oscillator."""
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()
        
        k_percent = 100 * (close - lowest_low) / (highest_high - lowest_low)
        d_percent = k_percent.rolling(window=d_period).mean()
        
        return pd.DataFrame({
            'k_percent': k_percent,
            'd_percent': d_percent
        })
    
    def cci(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 20) -> pd.Series:
        """Commodity Channel Index."""
        typical_price = (high + low + close) / 3
        sma_tp = typical_price.rolling(window=period).mean()
        mean_deviation = typical_price.rolling(window=period).apply(
            lambda x: np.mean(np.abs(x - x.mean()))
        )
        
        return (typical_price - sma_tp) / (0.015 * mean_deviation)

