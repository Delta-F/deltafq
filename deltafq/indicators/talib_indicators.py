"""
Technical indicators using TA-Lib library.
"""

import pandas as pd
import talib
from ..core.base import BaseComponent


class TalibIndicators(BaseComponent):
    """Technical indicators using TA-Lib library."""
    
    def __init__(self, **kwargs):
        """Initialize technical indicators."""
        super().__init__(**kwargs)
        self.logger.info("Initializing TA-Lib technical indicators")
    
    def sma(self, data: pd.Series, period: int) -> pd.Series:
        """Calculate Simple Moving Average (SMA) using TA-Lib."""
        self.logger.info(f"Calculating SMA(period={period})")
        return pd.Series(talib.SMA(data.values.astype(float), timeperiod=period), index=data.index)
    
    def ema(self, data: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average (EMA) using TA-Lib."""
        self.logger.info(f"Calculating EMA(period={period})")
        return pd.Series(talib.EMA(data.values.astype(float), timeperiod=period), index=data.index)
    
    def rsi(self, data: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index (RSI) using TA-Lib."""
        self.logger.info(f"Calculating RSI(period={period})")
        return pd.Series(talib.RSI(data.values.astype(float), timeperiod=period), index=data.index)
    
    def kdj(self, high: pd.Series, low: pd.Series, close: pd.Series, 
            n: int = 9, m1: int = 3, m2: int = 3) -> pd.DataFrame:
        """Calculate KDJ indicator using TA-Lib."""
        self.logger.info(f"Calculating KDJ(n={n}, m1={m1}, m2={m2})")
        k, d = talib.STOCH(high.values.astype(float), low.values.astype(float), close.values.astype(float),
                           fastk_period=n, slowk_period=m1, slowd_period=m2)
        return pd.DataFrame({
            'k': pd.Series(k, index=close.index),
            'd': pd.Series(d, index=close.index),
            'j': pd.Series(3 * k - 2 * d, index=close.index)
        })
    
    def boll(self, data: pd.Series, period: int = 20, std_dev: float = 2) -> pd.DataFrame:
        """Calculate Bollinger Bands using TA-Lib."""
        self.logger.info(f"Calculating BOLL(period={period}, std_dev={std_dev})")
        upper, middle, lower = talib.BBANDS(data.values.astype(float), timeperiod=period, 
                                            nbdevup=std_dev, nbdevdn=std_dev, matype=0)
        return pd.DataFrame({
            'upper': pd.Series(upper, index=data.index),
            'middle': pd.Series(middle, index=data.index),
            'lower': pd.Series(lower, index=data.index)
        })
    
    # Note: No separate alias; use boll() for consistency across providers
    
    def atr(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Average True Range (ATR) using TA-Lib."""
        self.logger.info(f"Calculating ATR(period={period})")
        return pd.Series(talib.ATR(high.values.astype(float), low.values.astype(float), 
                                   close.values.astype(float), timeperiod=period), index=close.index)
    
    def obv(self, close: pd.Series, volume: pd.Series) -> pd.Series:
        """Calculate On-Balance Volume (OBV) using TA-Lib."""
        self.logger.info("Calculating OBV")
        return pd.Series(talib.OBV(close.values.astype(float), volume.values.astype(float)), index=close.index)
