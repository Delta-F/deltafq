"""
Moving Average Strategy Example.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import deltafq as dfq
import pandas as pd
import numpy as np


class MovingAverageStrategy(dfq.strategy.BaseStrategy):
    """Simple moving average crossover strategy."""
    
    def __init__(self, fast_period=10, slow_period=20, **kwargs):
        """Initialize moving average strategy."""
        super().__init__(**kwargs)
        self.fast_period = fast_period
        self.slow_period = slow_period
    
    def generate_signals(self, data):
        """Generate signals based on moving average crossover."""
        if 'close' not in data.columns:
            raise ValueError("Data must contain 'close' column")
        
        # Calculate moving averages
        fast_ma = data['close'].rolling(window=self.fast_period).mean()
        slow_ma = data['close'].rolling(window=self.slow_period).mean()
        
        # Generate signals: 1 for buy, -1 for sell, 0 for hold
        signals = np.where(fast_ma > slow_ma, 1, np.where(fast_ma < slow_ma, -1, 0))
        
        return pd.Series(signals, index=data.index)


def run_moving_average_example():
    """Run moving average strategy example."""
    print("=== Moving Average Strategy Example ===")
    
    # Create sample data
    dates = pd.date_range('2023-01-01', periods=200, freq='D')
    prices = 100 + np.cumsum(np.random.randn(200) * 0.5)
    
    data = pd.DataFrame({
        'date': dates,
        'close': prices,
        'high': prices * 1.02,
        'low': prices * 0.98,
        'open': prices,
        'volume': np.random.randint(1000, 10000, 200)
    })
    
    # Create and run strategy
    strategy = MovingAverageStrategy(fast_period=10, slow_period=20)
    strategy.initialize()
    
    results = strategy.run(data)
    
    print(f"Strategy: {results['strategy_name']}")
    print(f"Fast MA Period: {strategy.fast_period}")
    print(f"Slow MA Period: {strategy.slow_period}")
    print(f"Total signals: {len(results['signals'])}")
    print(f"Buy signals: {(results['signals'] == 1).sum()}")
    print(f"Sell signals: {(results['signals'] == -1).sum()}")
    print(f"Hold signals: {(results['signals'] == 0).sum()}")
    
    # Show signal distribution
    signal_changes = (results['signals'] != results['signals'].shift()).sum()
    print(f"Signal changes: {signal_changes}")


if __name__ == "__main__":
    run_moving_average_example()

