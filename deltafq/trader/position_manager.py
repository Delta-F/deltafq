"""
Position management for DeltaFQ.
"""

from typing import Dict, Optional
from datetime import datetime
from ..core.base import BaseComponent


class PositionManager(BaseComponent):
    """Manage trading positions."""
    
    def __init__(self, **kwargs):
        """Initialize position manager."""
        super().__init__(**kwargs)
        self.positions = {}
    
    def initialize(self) -> bool:
        """Initialize position manager."""
        self.logger.info("Initializing position manager")
        return True
    
    def add_position(self, symbol: str, quantity: int, price: Optional[float] = None) -> bool:
        """Add to existing position or create new position."""
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
        
        self.logger.info(f"Position updated: {symbol} -> {self.positions[symbol]['quantity']}")
        return True
    
    def reduce_position(self, symbol: str, quantity: int, price: Optional[float] = None) -> bool:
        """Reduce existing position."""
        if symbol not in self.positions:
            self.logger.warning(f"No position found for symbol: {symbol}")
            return False
        
        current_quantity = self.positions[symbol]['quantity']
        if current_quantity < quantity:
            self.logger.warning(f"Insufficient position: {symbol}")
            return False
        
        new_quantity = current_quantity - quantity
        
        if new_quantity == 0:
            del self.positions[symbol]
        else:
            self.positions[symbol]['quantity'] = new_quantity
            self.positions[symbol]['updated_at'] = datetime.now()
        
        self.logger.info(f"Position reduced: {symbol} -> {new_quantity}")
        return True
    
    def get_position(self, symbol: str) -> int:
        """Get current position quantity for symbol."""
        return self.positions.get(symbol, {}).get('quantity', 0)
    
    def get_all_positions(self) -> Dict[str, int]:
        """Get all current positions."""
        return {symbol: pos['quantity'] for symbol, pos in self.positions.items()}
    
    def can_sell(self, symbol: str, quantity: int) -> bool:
        """Check if we can sell the specified quantity."""
        return self.get_position(symbol) >= quantity
    
    def close_position(self, symbol: str, price: Optional[float] = None) -> bool:
        """Close entire position for symbol."""
        if symbol not in self.positions:
            return False
        
        quantity = self.positions[symbol]['quantity']
        return self.reduce_position(symbol, quantity, price)
