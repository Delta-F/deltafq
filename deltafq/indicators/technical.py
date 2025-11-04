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
        """
        Calculate Simple Moving Average (SMA).
        
        SMA is a trend-following indicator that smooths out price data by creating
        a constantly updated average price. It is calculated by taking the arithmetic
        mean of a given set of prices over a specified number of periods.
        
        Args:
            data: Price series (typically close prices).
            period: Number of periods to calculate the moving average (e.g., 20, 50, 200).
        
        Returns:
            A pandas Series containing the SMA values. The first (period-1) values
            will be NaN until enough data points are available.
        
        Example:
            >>> sma_20 = indicators.sma(close_prices, period=20)
            >>> sma_50 = indicators.sma(close_prices, period=50)
        """
        if period <= 0:
            self.logger.info(f"Invalid period {period} for SMA. Period must be positive.")
            raise ValueError("Period must be positive")
        
        if len(data) < period:
            self.logger.info(f"Insufficient data points ({len(data)}) for SMA period {period}. "
                              f"Result will contain NaN values.")
        
        self.logger.info(f"Calculating SMA with period={period}, data_length={len(data)}")
        result = data.rolling(window=period).mean()
        self.logger.info(f"SMA calculation completed. Non-null values: {result.notna().sum()}")
        return result
    
    def ema(self, data: pd.Series, period: int) -> pd.Series:
        """
        Calculate Exponential Moving Average (EMA).
        
        EMA gives more weight to recent prices and reacts more quickly to price
        changes than SMA. It applies more weight to the most recent data points,
        making it more responsive to new information.
        
        Args:
            data: Price series (typically close prices).
            period: Number of periods for the exponential moving average.
        
        Returns:
            A pandas Series containing the EMA values. The first value is calculated
            using the initial price, subsequent values use exponential weighting.
        
        Example:
            >>> ema_12 = indicators.ema(close_prices, period=12)
            >>> ema_26 = indicators.ema(close_prices, period=26)
        """
        if period <= 0:
            self.logger.info(f"Invalid period {period} for EMA. Period must be positive.")
            raise ValueError("Period must be positive")
        
        if len(data) < period:
            self.logger.info(f"Insufficient data points ({len(data)}) for EMA period {period}. "
                              f"Result may be less reliable.")
        
        self.logger.info(f"Calculating EMA with period={period}, data_length={len(data)}")
        result = data.ewm(span=period).mean()
        self.logger.info(f"EMA calculation completed. Non-null values: {result.notna().sum()}")
        return result
    
    def rsi(self, data: pd.Series, period: int = 14) -> pd.Series:
        """
        Calculate Relative Strength Index (RSI).
        
        RSI is a momentum oscillator that measures the speed and magnitude of price
        changes. It oscillates between 0 and 100 and is used to identify overbought
        (typically > 70) and oversold (typically < 30) conditions.
        
        Args:
            data: Price series (typically close prices).
            period: Number of periods for RSI calculation. Default is 14.
        
        Returns:
            A pandas Series containing RSI values ranging from 0 to 100.
            - RSI > 70: Generally considered overbought
            - RSI < 30: Generally considered oversold
            - RSI = 50: Neutral level
        
        Example:
            >>> rsi = indicators.rsi(close_prices, period=14)
            >>> overbought = rsi > 70
            >>> oversold = rsi < 30
        """
        if period <= 0:
            self.logger.info(f"Invalid period {period} for RSI. Period must be positive.")
            raise ValueError("Period must be positive")
        
        if len(data) < period + 1:
            self.logger.info(f"Insufficient data points ({len(data)}) for RSI period {period}. "
                              f"Need at least {period + 1} data points.")
        
        self.logger.info(f"Calculating RSI with period={period}, data_length={len(data)}")
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        result = 100 - (100 / (1 + rs))
        
        # Check for invalid RSI values
        invalid_count = ((result < 0) | (result > 100)).sum()
        if invalid_count > 0:
            self.logger.info(f"RSI calculation produced {invalid_count} invalid values "
                              f"(outside 0-100 range).")
        
        self.logger.info(f"RSI calculation completed. Non-null values: {result.notna().sum()}")
        return result
    
    def macd(self, data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """
        Calculate Moving Average Convergence Divergence (MACD).
        
        MACD is a trend-following momentum indicator that shows the relationship
        between two moving averages of prices. It consists of:
        - MACD Line: The difference between fast EMA and slow EMA
        - Signal Line: EMA of the MACD line (used for generating trading signals)
        - Histogram: The difference between MACD line and Signal line
        
        Args:
            data: Price series (typically close prices).
            fast: Period for fast EMA. Default is 12.
            slow: Period for slow EMA. Default is 26.
            signal: Period for signal line EMA. Default is 9.
        
        Returns:
            A pandas DataFrame with columns:
            - 'macd': The MACD line (fast EMA - slow EMA)
            - 'signal': The signal line (EMA of MACD line)
            - 'histogram': The difference between MACD and signal line
            
            Trading signals:
            - Bullish: MACD crosses above signal line, histogram turns positive
            - Bearish: MACD crosses below signal line, histogram turns negative
        
        Example:
            >>> macd_data = indicators.macd(close_prices)
            >>> bullish_signal = (macd_data['macd'] > macd_data['signal']) & 
            ...                   (macd_data['histogram'] > 0)
        """
        if fast <= 0 or slow <= 0 or signal <= 0:
            self.logger.info(f"Invalid MACD parameters: fast={fast}, slow={slow}, signal={signal}. "
                            f"All periods must be positive.")
            raise ValueError("All periods must be positive")
        
        if fast >= slow:
            self.logger.info(f"MACD fast period ({fast}) should be less than slow period ({slow}).")
        
        if len(data) < slow:
            self.logger.info(f"Insufficient data points ({len(data)}) for MACD slow period {slow}.")
        
        self.logger.info(f"Calculating MACD with fast={fast}, slow={slow}, signal={signal}, "
                         f"data_length={len(data)}")
        ema_fast = self.ema(data, fast)
        ema_slow = self.ema(data, slow)
        macd_line = ema_fast - ema_slow
        signal_line = self.ema(macd_line, signal)
        histogram = macd_line - signal_line
        
        result = pd.DataFrame({
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        })
        
        self.logger.info(f"MACD calculation completed. Non-null MACD values: "
                         f"{result['macd'].notna().sum()}")
        return result
    
    def bollinger_bands(self, data: pd.Series, period: int = 20, std_dev: float = 2) -> pd.DataFrame:
        """
        Calculate Bollinger Bands.
        
        Bollinger Bands are volatility indicators that consist of:
        - Upper Band: SMA + (Standard Deviation × multiplier)
        - Middle Band: Simple Moving Average (SMA)
        - Lower Band: SMA - (Standard Deviation × multiplier)
        
        The bands expand and contract based on volatility. Prices touching the upper
        band may indicate overbought conditions, while touching the lower band may
        indicate oversold conditions.
        
        Args:
            data: Price series (typically close prices).
            period: Number of periods for SMA calculation. Default is 20.
            std_dev: Number of standard deviations for band width. Default is 2.
        
        Returns:
            A pandas DataFrame with columns:
            - 'upper': Upper Bollinger Band
            - 'middle': Middle band (SMA)
            - 'lower': Lower Bollinger Band
            
            Trading insights:
            - Price near upper band: Potentially overbought
            - Price near lower band: Potentially oversold
            - Band width indicates volatility (narrow = low volatility, wide = high volatility)
        
        Example:
            >>> bands = indicators.bollinger_bands(close_prices, period=20, std_dev=2)
            >>> price_touches_upper = close_prices >= bands['upper']
            >>> price_touches_lower = close_prices <= bands['lower']
        """
        if period <= 0:
            self.logger.info(f"Invalid period {period} for Bollinger Bands. Period must be positive.")
            raise ValueError("Period must be positive")
        
        if std_dev <= 0:
            self.logger.info(f"Invalid std_dev {std_dev} for Bollinger Bands. "
                            f"Standard deviation must be positive.")
            raise ValueError("Standard deviation must be positive")
        
        if len(data) < period:
            self.logger.info(f"Insufficient data points ({len(data)}) for Bollinger Bands "
                              f"period {period}. Result will contain NaN values.")
        
        self.logger.info(f"Calculating Bollinger Bands with period={period}, std_dev={std_dev}, "
                         f"data_length={len(data)}")
        sma = self.sma(data, period)
        std = data.rolling(window=period).std()
        
        result = pd.DataFrame({
            'upper': sma + (std * std_dev),
            'middle': sma,
            'lower': sma - (std * std_dev)
        })
        
        self.logger.info(f"Bollinger Bands calculation completed. Non-null values: "
                         f"{result['middle'].notna().sum()}")
        return result

