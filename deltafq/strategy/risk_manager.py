"""
Risk management for DeltaFQ.
"""

from typing import Dict, Any, Optional
from ..core.base import BaseComponent


class RiskManager(BaseComponent):
    """Risk management system."""
    
    def __init__(self, max_position_size: float = 0.1, max_drawdown: float = 0.2, **kwargs):
        """Initialize risk manager."""
        super().__init__(**kwargs)
        self.max_position_size = max_position_size
        self.max_drawdown = max_drawdown
        self.peak_value = 0.0
    
    def initialize(self) -> bool:
        """Initialize risk manager."""
        self.logger.info("Initializing risk manager")
        return True
    
    def check_position_size(self, symbol: str, quantity: float, portfolio_value: float) -> bool:
        """Check if position size is within limits."""
        position_value = abs(quantity) * self._get_current_price(symbol)
        position_ratio = position_value / portfolio_value
        
        if position_ratio > self.max_position_size:
            self.logger.warning(f"Position size exceeds limit: {symbol}")
            return False
        return True
    
    def check_drawdown(self, current_value: float) -> bool:
        """Check if drawdown is within limits."""
        if current_value > self.peak_value:
            self.peak_value = current_value
        
        drawdown = (self.peak_value - current_value) / self.peak_value
        
        if drawdown > self.max_drawdown:
            self.logger.warning(f"Drawdown exceeds limit: {drawdown:.2%}")
            return False
        return True
    
    def _get_current_price(self, symbol: str) -> float:
        """Get current price for symbol (placeholder)."""
        # This would be replaced with actual price fetching
        return 100.0
    
    def get_risk_metrics(self, portfolio_value: float) -> Dict[str, float]:
        """Get current risk metrics."""
        drawdown = 0.0
        if self.peak_value > 0:
            drawdown = (self.peak_value - portfolio_value) / self.peak_value
        
        return {
            'current_drawdown': drawdown,
            'max_drawdown_limit': self.max_drawdown,
            'peak_value': self.peak_value,
            'max_position_size': self.max_position_size
        }

