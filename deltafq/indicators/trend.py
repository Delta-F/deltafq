"""
Trend indicators for DeltaFQ.
"""

import pandas as pd
import numpy as np
from ..core.base import BaseComponent


class TrendIndicators(BaseComponent):
    """Trend-based technical indicators."""
    
    def initialize(self) -> bool:
        """Initialize trend indicators."""
        self.logger.info("Initializing trend indicators")
        return True
    
    def adx(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.DataFrame:
        """Average Directional Index."""
        # True Range
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Directional Movement
        dm_plus = np.where((high.diff() > low.diff().abs()) & (high.diff() > 0), high.diff(), 0)
        dm_minus = np.where((low.diff().abs() > high.diff()) & (low.diff() < 0), low.diff().abs(), 0)
        
        dm_plus = pd.Series(dm_plus, index=high.index)
        dm_minus = pd.Series(dm_minus, index=high.index)
        
        # Smoothed values
        atr = tr.rolling(window=period).mean()
        di_plus = 100 * (dm_plus.rolling(window=period).mean() / atr)
        di_minus = 100 * (dm_minus.rolling(window=period).mean() / atr)
        
        # ADX
        dx = 100 * abs(di_plus - di_minus) / (di_plus + di_minus)
        adx = dx.rolling(window=period).mean()
        
        return pd.DataFrame({
            'adx': adx,
            'di_plus': di_plus,
            'di_minus': di_minus
        })
    
    def parabolic_sar(self, high: pd.Series, low: pd.Series, close: pd.Series, 
                      acceleration: float = 0.02, maximum: float = 0.2) -> pd.Series:
        """Parabolic SAR."""
        # Simplified implementation
        psar = pd.Series(index=close.index, dtype=float)
        trend = pd.Series(index=close.index, dtype=int)
        af = pd.Series(index=close.index, dtype=float)
        ep = pd.Series(index=close.index, dtype=float)
        
        # Initialize
        psar.iloc[0] = low.iloc[0]
        trend.iloc[0] = 1
        af.iloc[0] = acceleration
        ep.iloc[0] = high.iloc[0]
        
        for i in range(1, len(close)):
            if trend.iloc[i-1] == 1:  # Uptrend
                psar.iloc[i] = psar.iloc[i-1] + af.iloc[i-1] * (ep.iloc[i-1] - psar.iloc[i-1])
                
                if low.iloc[i] <= psar.iloc[i]:
                    trend.iloc[i] = -1
                    psar.iloc[i] = ep.iloc[i-1]
                    ep.iloc[i] = low.iloc[i]
                    af.iloc[i] = acceleration
                else:
                    trend.iloc[i] = 1
                    if high.iloc[i] > ep.iloc[i-1]:
                        ep.iloc[i] = high.iloc[i]
                        af.iloc[i] = min(af.iloc[i-1] + acceleration, maximum)
                    else:
                        ep.iloc[i] = ep.iloc[i-1]
                        af.iloc[i] = af.iloc[i-1]
            else:  # Downtrend
                psar.iloc[i] = psar.iloc[i-1] + af.iloc[i-1] * (ep.iloc[i-1] - psar.iloc[i-1])
                
                if high.iloc[i] >= psar.iloc[i]:
                    trend.iloc[i] = 1
                    psar.iloc[i] = ep.iloc[i-1]
                    ep.iloc[i] = high.iloc[i]
                    af.iloc[i] = acceleration
                else:
                    trend.iloc[i] = -1
                    if low.iloc[i] < ep.iloc[i-1]:
                        ep.iloc[i] = low.iloc[i]
                        af.iloc[i] = min(af.iloc[i-1] + acceleration, maximum)
                    else:
                        ep.iloc[i] = ep.iloc[i-1]
                        af.iloc[i] = af.iloc[i-1]
        
        return psar
    
    def ichimoku(self, high: pd.Series, low: pd.Series, close: pd.Series,
                 conversion_period: int = 9, base_period: int = 26, 
                 leading_span_b_period: int = 52, displacement: int = 26) -> pd.DataFrame:
        """Ichimoku Cloud."""
        # Conversion Line (Tenkan-sen)
        conversion_line = (high.rolling(window=conversion_period).max() + 
                          low.rolling(window=conversion_period).min()) / 2
        
        # Base Line (Kijun-sen)
        base_line = (high.rolling(window=base_period).max() + 
                    low.rolling(window=base_period).min()) / 2
        
        # Leading Span A (Senkou Span A)
        leading_span_a = ((conversion_line + base_line) / 2).shift(displacement)
        
        # Leading Span B (Senkou Span B)
        leading_span_b = ((high.rolling(window=leading_span_b_period).max() + 
                          low.rolling(window=leading_span_b_period).min()) / 2).shift(displacement)
        
        # Lagging Span (Chikou Span)
        lagging_span = close.shift(-displacement)
        
        return pd.DataFrame({
            'conversion_line': conversion_line,
            'base_line': base_line,
            'leading_span_a': leading_span_a,
            'leading_span_b': leading_span_b,
            'lagging_span': lagging_span
        })

