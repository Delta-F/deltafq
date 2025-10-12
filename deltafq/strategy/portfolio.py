"""
Portfolio management for DeltaFQ.
"""

import pandas as pd
from typing import Dict, List, Optional
from ..core.base import BaseComponent


class Portfolio(BaseComponent):
    """Portfolio management system."""
    
    def __init__(self, initial_capital: float = 100000, **kwargs):
        """Initialize portfolio."""
        super().__init__(**kwargs)
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions = {}
        self.trades = []
    
    def initialize(self) -> bool:
        """Initialize portfolio."""
        self.logger.info(f"Initializing portfolio with capital: {self.initial_capital}")
        return True
    
    def get_position(self, symbol: str) -> float:
        """Get current position for symbol."""
        return self.positions.get(symbol, 0.0)
    
    def get_portfolio_value(self, prices: Dict[str, float]) -> float:
        """Calculate total portfolio value."""
        total_value = self.cash
        for symbol, quantity in self.positions.items():
            if symbol in prices:
                total_value += quantity * prices[symbol]
        return total_value
    
    def execute_trade(self, symbol: str, quantity: int, price: float, commission: float = 0.001):
        """Execute a trade."""
        cost = quantity * price * (1 + commission)
        
        if quantity > 0:  # Buy
            if cost <= self.cash:
                self.cash -= cost
                self.positions[symbol] = self.positions.get(symbol, 0) + quantity
                self.trades.append({
                    'symbol': symbol,
                    'quantity': quantity,
                    'price': price,
                    'type': 'buy',
                    'timestamp': pd.Timestamp.now()
                })
                self.logger.info(f"Bought {quantity} shares of {symbol} at {price}")
            else:
                self.logger.warning(f"Insufficient cash for trade: {symbol}")
        else:  # Sell
            quantity = abs(quantity)
            if self.positions.get(symbol, 0) >= quantity:
                self.cash += quantity * price * (1 - commission)
                self.positions[symbol] -= quantity
                self.trades.append({
                    'symbol': symbol,
                    'quantity': -quantity,
                    'price': price,
                    'type': 'sell',
                    'timestamp': pd.Timestamp.now()
                })
                self.logger.info(f"Sold {quantity} shares of {symbol} at {price}")
            else:
                self.logger.warning(f"Insufficient position for trade: {symbol}")
    
    def get_portfolio_summary(self, prices: Dict[str, float]) -> Dict[str, float]:
        """Get portfolio summary."""
        total_value = self.get_portfolio_value(prices)
        return {
            'total_value': total_value,
            'cash': self.cash,
            'total_return': (total_value - self.initial_capital) / self.initial_capital,
            'positions': dict(self.positions)
        }

