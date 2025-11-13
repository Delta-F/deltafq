"""
Technical indicators for DeltaFQ.
"""

import pandas as pd
import numpy as np
from ..core.base import BaseComponent


class TechnicalIndicators(BaseComponent):
    """Basic technical indicators."""
    
    def __init__(self, **kwargs):
        """Initialize technical indicators."""
        super().__init__(**kwargs)
        self.logger.info("Initializing technical indicators")
    
    def sma(self, data: pd.Series, period: int) -> pd.Series:
        """Calculate Simple Moving Average (SMA)."""
        self.logger.info(f"Calculating SMA(period={period})")
        return data.rolling(window=period).mean()
    
    def ema(self, data: pd.Series, period: int, method: str = 'pandas') -> pd.Series:
        """
        Calculate Exponential Moving Average (EMA).
        Args:
            data: Price series
            period: Period for EMA calculation
            method: 'pandas' uses pandas ewm (default), 'talib' uses inline calculation matching TA-Lib.
                   Talib method is more precise but slightly slower.
        """
        self.logger.info(f"Calculating EMA(period={period}, method={method})")
        
        if method == 'talib':
            # TA-Lib compatible: seed with SMA of the first full window
            ema = pd.Series(index=data.index, dtype=float)
            if len(data) == 0:
                return ema
            
            alpha = 2.0 / (period + 1.0)
            first_valid_idx = data.first_valid_index()
            if first_valid_idx is None:
                return ema
            
            first_valid_pos = data.index.get_loc(first_valid_idx)
            # Require a full window for initial SMA
            start = first_valid_pos
            end = start + period  # exclusive
            if end > len(data):
                # Not enough data to seed
                return ema
            
            # Attempt to find a clean initial window without NaNs
            seed_pos = end - 1
            initial_window = data.iloc[start:end]
            if initial_window.isna().any():
                clean_found = False
                for shift in range(0, len(data) - start - period + 1):
                    window = data.iloc[start + shift:start + shift + period]
                    if not window.isna().any():
                        seed_pos = start + shift + period - 1
                        initial_window = window
                        clean_found = True
                        break
                if not clean_found:
                    return ema
            
            ema.iloc[seed_pos] = float(initial_window.mean())
            
            # Forward recursion from the next bar after seed
            for i in range(seed_pos + 1, len(data)):
                x = data.iloc[i]
                prev = ema.iloc[i - 1]
                if pd.isna(x):
                    # Output NaN for this bar but keep previous state for the next step
                    ema.iloc[i] = np.nan
                else:
                    # Use last non-NaN ema value as previous
                    j = i - 1
                    while j >= 0 and pd.isna(prev):
                        j -= 1
                        prev = ema.iloc[j] if j >= 0 else np.nan
                    if pd.isna(prev):
                        ema.iloc[i] = float(x)
                    else:
                        ema.iloc[i] = float(alpha * x + (1.0 - alpha) * prev)
            return ema
        else:
            # Default: pandas ewm
            return data.ewm(span=period, adjust=False).mean()

    def rsi(self, data: pd.Series, period: int = 14, method: str = 'sma') -> pd.Series:
        """
        Calculate Relative Strength Index (RSI).
        Args:
            data: Price series
            period: Period for RSI calculation. Default is 14.
            method: 'sma' uses SMA for smoothing (default), 'rma' uses RMA (Wilder's Smoothing) matching TA-Lib.
                   RMA gives more weight to historical data, making it less responsive to recent changes.
        """
        self.logger.info(f"Calculating RSI(period={period}, method={method})")
        delta = data.diff()
        gains = delta.where(delta > 0, 0)
        losses = -delta.where(delta < 0, 0)
        
        if method == 'rma':
            # TA-Lib compatible: RMA (Wilder's Smoothing)
            avg_gain = pd.Series(index=data.index, dtype=float)
            avg_loss = pd.Series(index=data.index, dtype=float)
            
            if len(data) >= period + 1:
                avg_gain.iloc[period] = gains.iloc[1:period+1].mean()
                avg_loss.iloc[period] = losses.iloc[1:period+1].mean()
                
                for i in range(period + 1, len(data)):
                    if pd.notna(avg_gain.iloc[i - 1]) and pd.notna(gains.iloc[i]):
                        avg_gain.iloc[i] = (avg_gain.iloc[i - 1] * (period - 1) + gains.iloc[i]) / period
                    else:
                        avg_gain.iloc[i] = np.nan
                    
                    if pd.notna(avg_loss.iloc[i - 1]) and pd.notna(losses.iloc[i]):
                        avg_loss.iloc[i] = (avg_loss.iloc[i - 1] * (period - 1) + losses.iloc[i]) / period
                    else:
                        avg_loss.iloc[i] = np.nan
            
            rs = avg_gain / avg_loss
        else:
            # Default: SMA
            avg_gain = gains.rolling(window=period).mean()
            avg_loss = losses.rolling(window=period).mean()
            rs = avg_gain / avg_loss
        
        return 100 - (100 / (1 + rs))
      
    def kdj(self, high: pd.Series, low: pd.Series, close: pd.Series, 
            n: int = 9, m1: int = 3, m2: int = 3, method: str = 'ema') -> pd.DataFrame:
        """
        Calculate KDJ indicator (Stochastic Oscillator).
        Args:
            high: High price series
            low: Low price series
            close: Close price series
            n: Period for RSV calculation. Default is 9.
            m1: Period for K line smoothing. Default is 3.
            m2: Period for D line smoothing. Default is 3.
            method: 'ema' uses EMA for smoothing (default, more responsive),
                   'sma' uses SMA for smoothing matching TA-Lib STOCH.
        """
        self.logger.info(f"Calculating KDJ(n={n}, m1={m1}, m2={m2}, method={method})")
        
        # Calculate RSV (Raw Stochastic Value)
        lowest_low = low.rolling(window=n).min()
        highest_high = high.rolling(window=n).max()
        rsv = 100 * (close - lowest_low) / (highest_high - lowest_low)
        rsv = rsv.fillna(50)  # Fill NaN with neutral value
        
        if method == 'sma':
            # TA-Lib compatible: SMA smoothing
            k = self.sma(rsv, m1)
            d = self.sma(k, m2)
        else:
            # Default: EMA smoothing (more responsive)
            k = self.ema(rsv, m1)
            d = self.ema(k, m2)
        
        j = 3 * k - 2 * d
        
        return pd.DataFrame({
            'k': k,
            'd': d,
            'j': j
        })
    
    def boll(self, data: pd.Series, period: int = 20, std_dev: float = 2, method: str = 'sample') -> pd.DataFrame:
        """
        Calculate Bollinger Bands.
        Args:
            data: Price series
            period: Period for Bollinger Bands calculation. Default is 20.
            std_dev: Number of standard deviations. Default is 2.
            method: 'sample' uses sample std (ddof=1, default), 'population' uses population std (ddof=0) matching TA-Lib.
                   Population std is slightly smaller, making bands tighter. TA-Lib BBANDS uses population std.
        """
        self.logger.info(f"Calculating BOLL(period={period}, std_dev={std_dev}, method={method})")
        sma = self.sma(data, period)
        ddof = 0 if method == 'population' else 1
        std = data.rolling(window=period).std(ddof=ddof)
        
        return pd.DataFrame({
            'upper': sma + (std * std_dev),
            'middle': sma,
            'lower': sma - (std * std_dev)
        })
    
    def atr(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14, method: str = 'sma') -> pd.Series:
        """
        Calculate Average True Range (ATR).
        Args:
            high: High price series
            low: Low price series
            close: Close price series
            period: Period for ATR calculation. Default is 14.
            method: 'sma' uses SMA for smoothing (default), 'rma' uses RMA (Wilder's Smoothing) matching TA-Lib.
                   RMA gives more weight to historical data, making it less responsive to recent changes.
        """
        self.logger.info(f"Calculating ATR(period={period}, method={method})")

        # Calculate True Range
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        if method == 'rma':
            # TA-Lib compatible: RMA (Wilder's Smoothing)
            atr = pd.Series(index=tr.index, dtype=float)
            if len(tr) >= period + 1:
                atr.iloc[period] = tr.iloc[1:period+1].mean()
                for i in range(period + 1, len(tr)):
                    if pd.notna(atr.iloc[i - 1]) and pd.notna(tr.iloc[i]):
                        atr.iloc[i] = (atr.iloc[i - 1] * (period - 1) + tr.iloc[i]) / period
                    else:
                        atr.iloc[i] = np.nan
            return atr
        else:
            # Default: SMA
            return tr.rolling(window=period).mean()
    
    def obv(self, close: pd.Series, volume: pd.Series) -> pd.Series:
        """
        Calculate On-Balance Volume (OBV).
        Args:
            close: Close price series
            volume: Volume series
        """
        self.logger.info("Calculating OBV")
        
        # Calculate price change direction
        price_change = close.diff()
        
        # Calculate signed volume based on price direction
        signed_volume = volume.copy()
        signed_volume[price_change > 0] = volume[price_change > 0]  # Add volume when price up
        signed_volume[price_change < 0] = -volume[price_change < 0]  # Subtract volume when price down
        signed_volume[price_change == 0] = 0  # No change when price unchanged
        signed_volume.iloc[0] = volume.iloc[0]  # First value is first volume
        
        # Calculate cumulative OBV
        obv = signed_volume.cumsum()
        
        return obv
