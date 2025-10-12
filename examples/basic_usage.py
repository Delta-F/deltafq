"""
Basic usage examples for DeltaFQ.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import deltafq as dfq
import pandas as pd
import numpy as np


def basic_data_example():
    """Basic data fetching and processing example."""
    print("=== Basic Data Example ===")
    
    # Initialize data fetcher
    fetcher = dfq.data.DataFetcher()
    fetcher.initialize()
    
    # Fetch sample data
    data = fetcher.fetch_stock_data('AAPL', '2023-01-01', '2023-12-31')
    print(f"Fetched {len(data)} rows of data")
    print(data.head())
    
    # Clean data
    cleaner = dfq.data.DataCleaner()
    cleaner.initialize()
    cleaned_data = cleaner.clean_price_data(data)
    print(f"Cleaned data: {len(data)} -> {len(cleaned_data)} rows")
    
    # Validate data
    validator = dfq.data.DataValidator()
    validator.initialize()
    validator.validate_price_data(cleaned_data)
    print("Data validation passed")


def basic_indicators_example():
    """Basic technical indicators example."""
    print("\n=== Basic Indicators Example ===")
    
    # Create sample data
    dates = pd.date_range('2023-01-01', periods=100, freq='D')
    prices = 100 + np.cumsum(np.random.randn(100) * 0.5)
    
    data = pd.DataFrame({
        'date': dates,
        'close': prices,
        'high': prices * 1.02,
        'low': prices * 0.98,
        'open': prices,
        'volume': np.random.randint(1000, 10000, 100)
    })
    
    # Calculate technical indicators
    indicators = dfq.indicators.TechnicalIndicators()
    indicators.initialize()
    
    # Simple Moving Average
    sma_20 = indicators.sma(data['close'], 20)
    print(f"SMA(20) latest value: {sma_20.iloc[-1]:.2f}")
    
    # RSI
    rsi = indicators.rsi(data['close'], 14)
    print(f"RSI(14) latest value: {rsi.iloc[-1]:.2f}")
    
    # MACD
    macd = indicators.macd(data['close'])
    print(f"MACD latest value: {macd['macd'].iloc[-1]:.2f}")


def basic_strategy_example():
    """Basic strategy example."""
    print("\n=== Basic Strategy Example ===")
    
    # Create sample data
    dates = pd.date_range('2023-01-01', periods=100, freq='D')
    prices = 100 + np.cumsum(np.random.randn(100) * 0.5)
    
    data = pd.DataFrame({
        'date': dates,
        'close': prices,
        'high': prices * 1.02,
        'low': prices * 0.98,
        'open': prices,
        'volume': np.random.randint(1000, 10000, 100)
    })
    
    # Create a simple moving average strategy
    class SimpleMAStrategy(dfq.strategy.BaseStrategy):
        def __init__(self, fast_period=10, slow_period=20):
            super().__init__()
            self.fast_period = fast_period
            self.slow_period = slow_period
        
        def generate_signals(self, data):
            # Calculate moving averages
            fast_ma = data['close'].rolling(window=self.fast_period).mean()
            slow_ma = data['close'].rolling(window=self.slow_period).mean()
            
            # Generate signals: 1 for buy, -1 for sell, 0 for hold
            signals = np.where(fast_ma > slow_ma, 1, np.where(fast_ma < slow_ma, -1, 0))
            
            return pd.Series(signals, index=data.index)
    
    # Run strategy
    strategy = SimpleMAStrategy()
    strategy.initialize()
    results = strategy.run(data)
    
    print(f"Strategy: {results['strategy_name']}")
    print(f"Total signals generated: {len(results['signals'])}")
    print(f"Buy signals: {(results['signals'] == 1).sum()}")
    print(f"Sell signals: {(results['signals'] == -1).sum()}")


def basic_backtest_example():
    """Basic backtesting example."""
    print("\n=== Basic Backtest Example ===")
    
    # Create sample data
    dates = pd.date_range('2023-01-01', periods=100, freq='D')
    prices = 100 + np.cumsum(np.random.randn(100) * 0.5)
    
    data = pd.DataFrame({
        'date': dates,
        'close': prices,
        'high': prices * 1.02,
        'low': prices * 0.98,
        'open': prices,
        'volume': np.random.randint(1000, 10000, 100)
    })
    
    # Create strategy
    class SimpleMAStrategy(dfq.strategy.BaseStrategy):
        def __init__(self, fast_period=10, slow_period=20):
            super().__init__()
            self.fast_period = fast_period
            self.slow_period = slow_period
        
        def generate_signals(self, data):
            fast_ma = data['close'].rolling(window=self.fast_period).mean()
            slow_ma = data['close'].rolling(window=self.slow_period).mean()
            signals = np.where(fast_ma > slow_ma, 1, np.where(fast_ma < slow_ma, -1, 0))
            return pd.Series(signals, index=data.index)
    
    # Run backtest
    strategy = SimpleMAStrategy()
    strategy.initialize()
    
    engine = dfq.backtest.BacktestEngine(initial_capital=100000)
    engine.initialize()
    
    results = engine.run_backtest(strategy, data)
    
    print(f"Initial Capital: ${results['initial_capital']:,.2f}")
    print(f"Final Value: ${results['final_value']:,.2f}")
    print(f"Total Return: {results['total_return']:.2%}")
    print(f"Total Trades: {len(results['trades'])}")


def basic_paper_trading_example():
    """Basic paper trading example."""
    print("\n=== Basic Paper Trading Example ===")
    
    # Create sample data
    dates = pd.date_range('2023-01-01', periods=50, freq='D')
    prices = 100 + np.cumsum(np.random.randn(50) * 0.5)
    
    data = pd.DataFrame({
        'date': dates,
        'close': prices,
        'high': prices * 1.02,
        'low': prices * 0.98,
        'open': prices,
        'volume': np.random.randint(1000, 10000, 50)
    })
    
    # Create strategy
    class SimpleMAStrategy(dfq.strategy.BaseStrategy):
        def __init__(self, fast_period=5, slow_period=10):
            super().__init__()
            self.fast_period = fast_period
            self.slow_period = slow_period
        
        def generate_signals(self, data):
            fast_ma = data['close'].rolling(window=self.fast_period).mean()
            slow_ma = data['close'].rolling(window=self.slow_period).mean()
            signals = np.where(fast_ma > slow_ma, 1, np.where(fast_ma < slow_ma, -1, 0))
            return pd.Series(signals, index=data.index)
    
    # Run paper trading
    strategy = SimpleMAStrategy()
    strategy.initialize()
    
    simulator = dfq.trading.PaperTradingSimulator(initial_capital=50000)
    simulator.initialize()
    
    portfolio_summary = simulator.run_strategy(strategy, data)
    
    print(f"Initial Capital: $50,000")
    print(f"Final Value: ${portfolio_summary['total_value']:,.2f}")
    print(f"Total Return: {portfolio_summary['total_return']:.2%}")
    print(f"Final Cash: ${portfolio_summary['cash']:,.2f}")
    print(f"Total Trades: {portfolio_summary['total_trades']}")


if __name__ == "__main__":
    print("DeltaFQ Basic Usage Examples")
    print("=" * 40)
    
    try:
        basic_data_example()
        basic_indicators_example()
        basic_strategy_example()
        basic_backtest_example()
        basic_paper_trading_example()
        
        print("\n" + "=" * 40)
        print("All examples completed successfully!")
        
    except Exception as e:
        print(f"Error running examples: {str(e)}")
        import traceback
        traceback.print_exc()

