"""
Live data feed management for real-time trading.
"""

import pandas as pd
from typing import Dict, List, Callable, Optional, Any
from datetime import datetime
from ..core.base import BaseComponent
from ..core.exceptions import TradingError


class LiveDataFeed(BaseComponent):
    """Manages real-time market data feeds."""
    
    def __init__(self, **kwargs):
        """Initialize live data feed."""
        super().__init__(**kwargs)
        self.subscribers = {}
        self.data_callbacks = []
        self.is_running = False
        self.last_prices = {}
        self.logger.info("Initializing live data feed")
    
    def subscribe(self, symbols: List[str], callback: Optional[Callable] = None) -> bool:
        """Subscribe to live data for given symbols."""
        try:
            for symbol in symbols:
                if symbol not in self.subscribers:
                    self.subscribers[symbol] = []
                
                if callback:
                    self.subscribers[symbol].append(callback)
                
                self.logger.info(f"Subscribed to {symbol}")
            
            return True
            
        except Exception as e:
            raise TradingError(f"Failed to subscribe to symbols: {str(e)}")
    
    def unsubscribe(self, symbols: List[str]) -> bool:
        """Unsubscribe from live data."""
        try:
            for symbol in symbols:
                if symbol in self.subscribers:
                    del self.subscribers[symbol]
                    self.logger.info(f"Unsubscribed from {symbol}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to unsubscribe: {str(e)}")
            return False
    
    def add_data_callback(self, callback: Callable) -> bool:
        """Add a general data callback."""
        self.data_callbacks.append(callback)
        return True
    
    def start_feed(self) -> bool:
        """Start the live data feed."""
        try:
            self.is_running = True
            self.logger.info("Live data feed started")
            
            # In a real implementation, this would start the actual data feed
            # For now, we'll simulate with periodic updates
            self._simulate_data_feed()
            
            return True
            
        except Exception as e:
            self.is_running = False
            raise TradingError(f"Failed to start data feed: {str(e)}")
    
    def stop_feed(self) -> bool:
        """Stop the live data feed."""
        try:
            self.is_running = False
            self.logger.info("Live data feed stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop data feed: {str(e)}")
            return False
    
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """Get latest price for a symbol."""
        return self.last_prices.get(symbol)
    
    def get_latest_prices(self, symbols: List[str]) -> Dict[str, float]:
        """Get latest prices for multiple symbols."""
        return {symbol: self.last_prices.get(symbol) for symbol in symbols if symbol in self.last_prices}
    
    def _simulate_data_feed(self):
        """Simulate live data feed for testing."""
        import time
        import random
        
        base_prices = {
            'AAPL': 150.0,
            'GOOGL': 2500.0,
            'MSFT': 300.0,
            'TSLA': 200.0
        }
        
        while self.is_running:
            for symbol in self.subscribers.keys():
                if symbol in base_prices:
                    # Simulate price movement
                    current_price = self.last_prices.get(symbol, base_prices[symbol])
                    change = random.uniform(-0.02, 0.02)  # ±2% change
                    new_price = current_price * (1 + change)
                    
                    self.last_prices[symbol] = new_price
                    
                    # Create data point
                    data_point = {
                        'symbol': symbol,
                        'price': new_price,
                        'timestamp': datetime.now(),
                        'volume': random.randint(1000, 10000)
                    }
                    
                    # Notify subscribers
                    self._notify_subscribers(symbol, data_point)
            
            time.sleep(1)  # Update every second
    
    def _notify_subscribers(self, symbol: str, data_point: Dict[str, Any]):
        """Notify subscribers of new data."""
        try:
            # Notify symbol-specific subscribers
            if symbol in self.subscribers:
                for callback in self.subscribers[symbol]:
                    callback(data_point)
            
            # Notify general data callbacks
            for callback in self.data_callbacks:
                callback(data_point)
                
        except Exception as e:
            self.logger.error(f"Error notifying subscribers: {str(e)}")
    
    def get_feed_status(self) -> Dict[str, Any]:
        """Get feed status information."""
        return {
            'is_running': self.is_running,
            'subscribed_symbols': list(self.subscribers.keys()),
            'total_subscribers': sum(len(callbacks) for callbacks in self.subscribers.values()),
            'data_callbacks': len(self.data_callbacks),
            'latest_prices': dict(self.last_prices)
        }

