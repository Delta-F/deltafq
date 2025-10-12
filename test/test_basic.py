#!/usr/bin/env python3
"""
Comprehensive test suite for DeltaFQ project.
Tests core functionality including config, indicators, strategies, and data handling.
"""

import sys
import os
import unittest
import pandas as pd
import numpy as np

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import deltafq as dfq


class TestDeltaFQCore(unittest.TestCase):
    """Test core DeltaFQ functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = dfq.core.Config()
        self.test_data = self._create_sample_data()
    
    def _create_sample_data(self):
        """Create sample price data for testing."""
        dates = pd.date_range('2023-01-01', periods=50, freq='D')
        prices = 100 + np.cumsum(np.random.randn(50) * 0.5)
        return pd.DataFrame({
            'date': dates,
            'close': prices,
            'high': prices * 1.02,
            'low': prices * 0.98,
            'open': prices,
            'volume': np.random.randint(1000, 10000, 50)
        })
    
    def test_config_management(self):
        """Test configuration management."""
        # Test default config
        self.assertEqual(self.config.get('trading.initial_capital'), 100000)
        self.assertEqual(self.config.get('data.default_source'), 'yahoo')
        
        # Test config modification
        self.config.set('test.value', 42)
        self.assertEqual(self.config.get('test.value'), 42)
        
        # Test non-existent key
        self.assertIsNone(self.config.get('nonexistent.key'))
        self.assertEqual(self.config.get('nonexistent.key', 'default'), 'default')
    
    def test_technical_indicators(self):
        """Test technical indicators calculation."""
        indicators = dfq.indicators.TechnicalIndicators()
        indicators.initialize()
        
        # Test SMA
        sma_20 = indicators.sma(self.test_data['close'], 20)
        self.assertEqual(len(sma_20), len(self.test_data))
        self.assertFalse(sma_20.iloc[:19].notna().any())  # First 19 should be NaN
        
        # Test RSI
        rsi = indicators.rsi(self.test_data['close'], 14)
        self.assertEqual(len(rsi), len(self.test_data))
        # Check RSI values only for non-NaN values
        rsi_valid = rsi.dropna()
        if len(rsi_valid) > 0:
            self.assertTrue((rsi_valid >= 0).all() and (rsi_valid <= 100).all())
        
        # Test MACD
        macd = indicators.macd(self.test_data['close'])
        self.assertIn('macd', macd.columns)
        self.assertIn('signal', macd.columns)
        self.assertIn('histogram', macd.columns)
    
    def test_base_strategy(self):
        """Test base strategy functionality."""
        class TestStrategy(dfq.strategy.BaseStrategy):
            def generate_signals(self, data):
                return pd.Series([1, -1, 0], index=data.index[:3])
        
        strategy = TestStrategy()
        strategy.initialize()
        
        # Test strategy execution
        results = strategy.run(self.test_data)
        self.assertEqual(results['strategy_name'], 'TestStrategy')
        self.assertEqual(len(results['signals']), 3)
        self.assertIn('performance', results)
    
    def test_data_fetcher(self):
        """Test data fetching functionality."""
        fetcher = dfq.data.DataFetcher()
        fetcher.initialize()
        
        # Test data fetching
        data = fetcher.fetch_stock_data('AAPL', '2023-01-01', '2023-01-31')
        self.assertIsInstance(data, pd.DataFrame)
        self.assertIn('close', data.columns)
        self.assertIn('volume', data.columns)
        
        # Test multiple symbols
        data_dict = fetcher.fetch_multiple_symbols(['AAPL', 'GOOGL'], '2023-01-01', '2023-01-31')
        self.assertEqual(len(data_dict), 2)
        self.assertIn('AAPL', data_dict)
        self.assertIn('GOOGL', data_dict)
    
    def test_integration(self):
        """Test integration between components."""
        # Create a simple moving average strategy
        class MAStrategy(dfq.strategy.BaseStrategy):
            def generate_signals(self, data):
                sma_10 = data['close'].rolling(10).mean()
                sma_20 = data['close'].rolling(20).mean()
                signals = pd.Series(0, index=data.index)
                signals[sma_10 > sma_20] = 1
                signals[sma_10 < sma_20] = -1
                return signals
        
        # Test complete workflow
        strategy = MAStrategy()
        strategy.initialize()
        
        results = strategy.run(self.test_data)
        self.assertIsInstance(results['signals'], pd.Series)
        self.assertTrue(results['signals'].isin([-1, 0, 1]).all())


def run_tests():
    """Run all tests and return results."""
    print("Running DeltaFQ Comprehensive Tests")
    print("=" * 40)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDeltaFQCore)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 40)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            error_msg = traceback.split('AssertionError: ')[-1].split('\n')[0]
            print(f"- {test}: {error_msg}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            error_msg = traceback.split('\n')[-2]
            print(f"- {test}: {error_msg}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nOverall result: {'PASSED' if success else 'FAILED'}")
    
    return success


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
