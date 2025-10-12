"""
Signal generator for trading strategies.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any
from ..core.base import BaseComponent


class SignalGenerator(BaseComponent):
    """Generate trading signals from market data."""
    
    def initialize(self) -> bool:
        """Initialize signal generator."""
        self.logger.info("Initializing signal generator")
        return True
    
    def moving_average_crossover(self, data: pd.DataFrame, fast_period: int = 10, slow_period: int = 20) -> pd.Series:
        """Generate signals based on moving average crossover."""
        if 'close' not in data.columns:
            raise ValueError("Data must contain 'close' column")
        
        # Calculate moving averages
        fast_ma = data['close'].rolling(window=fast_period).mean()
        slow_ma = data['close'].rolling(window=slow_period).mean()
        
        # Generate signals: 1 for buy, -1 for sell, 0 for hold
        signals = np.where(fast_ma > slow_ma, 1, np.where(fast_ma < slow_ma, -1, 0))
        
        self.logger.info(f"Generated MA crossover signals: {fast_period}/{slow_period}")
        return pd.Series(signals, index=data.index)
    
    def rsi_signals(self, data: pd.DataFrame, period: int = 14, oversold: float = 30, overbought: float = 70) -> pd.Series:
        """Generate signals based on RSI."""
        if 'close' not in data.columns:
            raise ValueError("Data must contain 'close' column")
        
        # Calculate RSI (simplified)
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # Generate signals
        signals = np.where(rsi < oversold, 1, np.where(rsi > overbought, -1, 0))
        
        self.logger.info(f"Generated RSI signals: period={period}")
        return pd.Series(signals, index=data.index)

