"""
Mean Reversion Strategy Example.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import deltafq as dfq
import pandas as pd
import numpy as np


class MeanReversionStrategy(dfq.strategy.BaseStrategy):
    """Mean reversion strategy based on Bollinger Bands."""
    
    def __init__(self, period=20, std_dev=2, **kwargs):
        """Initialize mean reversion strategy."""
        super().__init__(**kwargs)
        self.period = period
        self.std_dev = std_dev
    
    def generate_signals(self, data):
        """Generate signals based on mean reversion."""
        if 'close' not in data.columns:
            raise ValueError("Data must contain 'close' column")
        
        # Calculate Bollinger Bands
        sma = data['close'].rolling(window=self.period).mean()
        std = data['close'].rolling(window=self.period).std()
        
        upper_band = sma + (std * self.std_dev)
        lower_band = sma - (std * self.std_dev)
        
        # Generate signals
        # Buy when price touches lower band (oversold)
        # Sell when price touches upper band (overbought)
        signals = np.where(data['close'] <= lower_band, 1,
                          np.where(data['close'] >= upper_band, -1, 0))
        
        return pd.Series(signals, index=data.index)


def run_mean_reversion_example():
    """Run mean reversion strategy example."""
    print("=== Mean Reversion Strategy Example ===")
    
    # Create sample data with mean reversion characteristics
    dates = pd.date_range('2023-01-01', periods=200, freq='D')
    
    # Generate mean-reverting price series
    returns = np.random.randn(200) * 0.01
    for i in range(1, len(returns)):
        returns[i] = returns[i] * 0.3 + returns[i-1] * 0.7  # Add mean reversion
    
    prices = 100 * np.exp(np.cumsum(returns))
    
    data = pd.DataFrame({
        'date': dates,
        'close': prices,
        'high': prices * 1.02,
        'low': prices * 0.98,
        'open': prices,
        'volume': np.random.randint(1000, 10000, 200)
    })
    
    # Create and run strategy
    strategy = MeanReversionStrategy(period=20, std_dev=2)
    strategy.initialize()
    
    results = strategy.run(data)
    
    print(f"Strategy: {results['strategy_name']}")
    print(f"Period: {strategy.period}")
    print(f"Standard Deviation: {strategy.std_dev}")
    print(f"Total signals: {len(results['signals'])}")
    print(f"Buy signals: {(results['signals'] == 1).sum()}")
    print(f"Sell signals: {(results['signals'] == -1).sum()}")
    print(f"Hold signals: {(results['signals'] == 0).sum()}")
    
    # Show signal distribution
    signal_changes = (results['signals'] != results['signals'].shift()).sum()
    print(f"Signal changes: {signal_changes}")


if __name__ == "__main__":
    run_mean_reversion_example()

