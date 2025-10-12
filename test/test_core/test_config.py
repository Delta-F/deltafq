"""
Tests for configuration management.
"""

import unittest
from deltafq.core.config import Config


class TestConfig(unittest.TestCase):
    """Test configuration management."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = Config()
    
    def test_default_config(self):
        """Test default configuration loading."""
        self.assertIsNotNone(self.config.config)
        self.assertIn('data', self.config.config)
        self.assertIn('trading', self.config.config)
        self.assertIn('logging', self.config.config)
    
    def test_get_config_value(self):
        """Test getting configuration values."""
        cache_dir = self.config.get('data.cache_dir')
        self.assertEqual(cache_dir, './data_cache')
        
        initial_capital = self.config.get('trading.initial_capital')
        self.assertEqual(initial_capital, 100000)
    
    def test_set_config_value(self):
        """Test setting configuration values."""
        self.config.set('test.value', 42)
        self.assertEqual(self.config.get('test.value'), 42)
        
        self.config.set('data.cache_dir', '/new/cache')
        self.assertEqual(self.config.get('data.cache_dir'), '/new/cache')
    
    def test_get_nonexistent_value(self):
        """Test getting non-existent configuration values."""
        value = self.config.get('nonexistent.key')
        self.assertIsNone(value)
        
        default_value = self.config.get('nonexistent.key', 'default')
        self.assertEqual(default_value, 'default')


if __name__ == '__main__':
    unittest.main()

