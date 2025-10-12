"""
Position management for DeltaFQ.
"""

from typing import Dict, Optional, Any
from datetime import datetime
from ..core.base import BaseComponent


class PositionManager(BaseComponent):
    """Manage trading positions."""
    
    def __init__(self, **kwargs):
        """Initialize position manager."""
        super().__init__(**kwargs)
        self.positions = {}
        self.position_history = []
    
    def initialize(self) -> bool:
        """Initialize position manager."""
        self.logger.info("Initializing position manager")
        return True
    
    def add_position(self, symbol: str, quantity: int, price: Optional[float] = None) -> bool:
        """Add to existing position or create new position."""
        try:
            if symbol in self.positions:
                # Update existing position
                current_quantity = self.positions[symbol]['quantity']
                current_avg_price = self.positions[symbol]['avg_price']
                
                new_quantity = current_quantity + quantity
                if price:
                    new_avg_price = ((current_quantity * current_avg_price) + (quantity * price)) / new_quantity
                else:
                    new_avg_price = current_avg_price
                
                self.positions[symbol]['quantity'] = new_quantity
                self.positions[symbol]['avg_price'] = new_avg_price
                self.positions[symbol]['updated_at'] = datetime.now()
            else:
                # Create new position
                self.positions[symbol] = {
                    'symbol': symbol,
                    'quantity': quantity,
                    'avg_price': price or 0.0,
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                }
            
            # Record in history
            self.position_history.append({
                'symbol': symbol,
                'quantity': quantity,
                'price': price,
                'action': 'add',
                'timestamp': datetime.now()
            })
            
            self.logger.info(f"Position updated: {symbol} -> {self.positions[symbol]['quantity']}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add position: {str(e)}")
            return False
    
    def reduce_position(self, symbol: str, quantity: int, price: Optional[float] = None) -> bool:
        """Reduce existing position."""
        try:
            if symbol not in self.positions:
                self.logger.warning(f"No position found for symbol: {symbol}")
                return False
            
            current_quantity = self.positions[symbol]['quantity']
            if current_quantity < quantity:
                self.logger.warning(f"Insufficient position: {symbol}")
                return False
            
            new_quantity = current_quantity - quantity
            
            if new_quantity == 0:
                # Close position
                del self.positions[symbol]
            else:
                # Update position
                self.positions[symbol]['quantity'] = new_quantity
                self.positions[symbol]['updated_at'] = datetime.now()
            
            # Record in history
            self.position_history.append({
                'symbol': symbol,
                'quantity': -quantity,
                'price': price,
                'action': 'reduce',
                'timestamp': datetime.now()
            })
            
            self.logger.info(f"Position reduced: {symbol} -> {new_quantity}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to reduce position: {str(e)}")
            return False
    
    def get_position(self, symbol: str) -> int:
        """Get current position quantity for symbol."""
        return self.positions.get(symbol, {}).get('quantity', 0)
    
    def get_all_positions(self) -> Dict[str, int]:
        """Get all current positions."""
        return {symbol: pos['quantity'] for symbol, pos in self.positions.items()}
    
    def get_position_details(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get detailed position information."""
        return self.positions.get(symbol)
    
    def get_all_position_details(self) -> Dict[str, Dict[str, Any]]:
        """Get all position details."""
        return dict(self.positions)
    
    def can_sell(self, symbol: str, quantity: int) -> bool:
        """Check if we can sell the specified quantity."""
        current_position = self.get_position(symbol)
        return current_position >= quantity
    
    def get_position_value(self, symbol: str, current_price: float) -> float:
        """Calculate position value at current price."""
        quantity = self.get_position(symbol)
        return quantity * current_price
    
    def get_total_position_value(self, current_prices: Dict[str, float]) -> float:
        """Calculate total position value."""
        total_value = 0.0
        for symbol, position in self.positions.items():
            if symbol in current_prices:
                total_value += position['quantity'] * current_prices[symbol]
        return total_value
    
    def close_position(self, symbol: str, price: Optional[float] = None) -> bool:
        """Close entire position for symbol."""
        if symbol not in self.positions:
            return False
        
        quantity = self.positions[symbol]['quantity']
        return self.reduce_position(symbol, quantity, price)
    
    def close_all_positions(self, current_prices: Dict[str, float]) -> Dict[str, bool]:
        """Close all positions."""
        results = {}
        symbols = list(self.positions.keys())
        
        for symbol in symbols:
            results[symbol] = self.close_position(symbol, current_prices.get(symbol))
        
        return results

