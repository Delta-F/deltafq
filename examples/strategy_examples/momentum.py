"""
Momentum Strategy Example.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import deltafq as dfq
import pandas as pd
import numpy as np


class MomentumStrategy(dfq.strategy.BaseStrategy):
    """Momentum strategy based on RSI and price momentum."""
    
    def __init__(self, rsi_period=14, momentum_period=10, rsi_oversold=30, rsi_overbought=70, **kwargs):
        """Initialize momentum strategy."""
        super().__init__(**kwargs)
        self.rsi_period = rsi_period
        self.momentum_period = momentum_period
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
    
    def generate_signals(self, data):
        """Generate signals based on momentum indicators."""
        if 'close' not in data.columns:
            raise ValueError("Data must contain 'close' column")
        
        # Calculate RSI
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # Calculate momentum
        momentum = data['close'] / data['close'].shift(self.momentum_period) - 1
        
        # Generate signals
        # Buy when RSI is oversold and momentum is positive
        # Sell when RSI is overbought and momentum is negative
        buy_condition = (rsi < self.rsi_oversold) & (momentum > 0)
        sell_condition = (rsi > self.rsi_overbought) & (momentum < 0)
        
        signals = np.where(buy_condition, 1,
                          np.where(sell_condition, -1, 0))
        
        return pd.Series(signals, index=data.index)


def run_momentum_example():
    """Run momentum strategy example."""
    print("=== Momentum Strategy Example ===")
    
    # Create sample data with momentum characteristics
    dates = pd.date_range('2023-01-01', periods=200, freq='D')
    
    # Generate trending price series
    trend = np.linspace(0, 0.5, 200)  # Upward trend
    noise = np.random.randn(200) * 0.02
    prices = 100 * np.exp(trend + noise)
    
    data = pd.DataFrame({
        'date': dates,
        'close': prices,
        'high': prices * 1.02,
        'low': prices * 0.98,
        'open': prices,
        'volume': np.random.randint(1000, 10000, 200)
    })
    
    # Create and run strategy
    strategy = MomentumStrategy(rsi_period=14, momentum_period=10)
    strategy.initialize()
    
    results = strategy.run(data)
    
    print(f"Strategy: {results['strategy_name']}")
    print(f"RSI Period: {strategy.rsi_period}")
    print(f"Momentum Period: {strategy.momentum_period}")
    print(f"RSI Oversold: {strategy.rsi_oversold}")
    print(f"RSI Overbought: {strategy.rsi_overbought}")
    print(f"Total signals: {len(results['signals'])}")
    print(f"Buy signals: {(results['signals'] == 1).sum()}")
    print(f"Sell signals: {(results['signals'] == -1).sum()}")
    print(f"Hold signals: {(results['signals'] == 0).sum()}")
    
    # Show signal distribution
    signal_changes = (results['signals'] != results['signals'].shift()).sum()
    print(f"Signal changes: {signal_changes}")


if __name__ == "__main__":
    run_momentum_example()

