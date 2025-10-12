"""
Trade execution engine for DeltaFQ.
"""

import pandas as pd
from typing import Dict, List, Optional, Any
from ..core.base import BaseComponent
from ..core.exceptions import TradingError
from .order_manager import OrderManager
from .position_manager import PositionManager


class ExecutionEngine(BaseComponent):
    """Trade execution engine."""
    
    def __init__(self, broker=None, **kwargs):
        """Initialize execution engine."""
        super().__init__(**kwargs)
        self.broker = broker
        self.order_manager = OrderManager()
        self.position_manager = PositionManager()
        self.execution_history = []
    
    def initialize(self) -> bool:
        """Initialize execution engine."""
        self.logger.info("Initializing execution engine")
        
        if self.broker:
            return self.broker.initialize()
        
        return True
    
    def execute_order(self, symbol: str, quantity: int, order_type: str = "market", 
                     price: Optional[float] = None) -> str:
        """Execute an order through the broker."""
        try:
            # Create order
            order_id = self.order_manager.create_order(
                symbol=symbol,
                quantity=quantity,
                order_type=order_type,
                price=price
            )
            
            # Execute through broker
            if self.broker:
                broker_order_id = self.broker.place_order(
                    symbol=symbol,
                    quantity=quantity,
                    order_type=order_type,
                    price=price
                )
                
                # Update order with broker ID
                order = self.order_manager.get_order(order_id)
                if order:
                    order['broker_order_id'] = broker_order_id
                
                self.logger.info(f"Order executed through broker: {order_id} -> {broker_order_id}")
            else:
                # Simulate execution
                current_price = self._get_simulated_price(symbol)
                self._simulate_execution(order_id, current_price)
                self.logger.info(f"Order executed in simulation: {order_id}")
            
            return order_id
            
        except Exception as e:
            raise TradingError(f"Failed to execute order: {str(e)}")
    
    def _simulate_execution(self, order_id: str, execution_price: float):
        """Simulate order execution."""
        order = self.order_manager.get_order(order_id)
        if not order:
            return
        
        # Mark as executed
        self.order_manager.mark_executed(order_id, execution_price)
        
        # Update position
        symbol = order['symbol']
        quantity = order['quantity']
        
        if quantity > 0:  # Buy
            self.position_manager.add_position(symbol, quantity, execution_price)
        else:  # Sell
            self.position_manager.reduce_position(symbol, abs(quantity), execution_price)
        
        # Record execution
        self.execution_history.append({
            'order_id': order_id,
            'symbol': symbol,
            'quantity': quantity,
            'execution_price': execution_price,
            'timestamp': pd.Timestamp.now()
        })
    
    def _get_simulated_price(self, symbol: str) -> float:
        """Get simulated price for symbol."""
        # Simple simulation - in real implementation this would come from market data
        base_prices = {
            'AAPL': 150.0,
            'GOOGL': 2500.0,
            'MSFT': 300.0,
            'TSLA': 200.0
        }
        return base_prices.get(symbol, 100.0)
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """Get execution summary."""
        return {
            'total_orders': len(self.order_manager.get_order_history()),
            'executed_orders': len(self.order_manager.get_executed_orders()),
            'pending_orders': len(self.order_manager.get_pending_orders()),
            'total_positions': len(self.position_manager.get_all_positions()),
            'execution_history': self.execution_history
        }
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order."""
        try:
            # Cancel in order manager
            success = self.order_manager.cancel_order(order_id)
            
            # Cancel with broker if available
            if self.broker and success:
                order = self.order_manager.get_order(order_id)
                if order and 'broker_order_id' in order:
                    self.broker.cancel_order(order['broker_order_id'])
            
            if success:
                self.logger.info(f"Order cancelled: {order_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to cancel order: {str(e)}")
            return False
    
    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """Get order status."""
        order = self.order_manager.get_order(order_id)
        if not order:
            return {}
        
        # Get status from broker if available
        if self.broker and 'broker_order_id' in order:
            broker_status = self.broker.get_order_status(order['broker_order_id'])
            order.update(broker_status)
        
        return order
    
    def sync_with_broker(self) -> bool:
        """Sync orders and positions with broker."""
        if not self.broker:
            return False
        
        try:
            # Sync positions
            broker_positions = self.broker.get_positions()
            # Update position manager with broker positions
            
            # Sync order statuses
            for order_id, order in self.order_manager.orders.items():
                if 'broker_order_id' in order:
                    broker_status = self.broker.get_order_status(order['broker_order_id'])
                    order.update(broker_status)
            
            self.logger.info("Synced with broker")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to sync with broker: {str(e)}")
            return False

