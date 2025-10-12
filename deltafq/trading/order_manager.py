"""
Order management system for DeltaFQ.
"""

import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime
from ..core.base import BaseComponent


class OrderManager(BaseComponent):
    """Manage trading orders."""
    
    def __init__(self, **kwargs):
        """Initialize order manager."""
        super().__init__(**kwargs)
        self.orders = {}
        self.order_counter = 0
    
    def initialize(self) -> bool:
        """Initialize order manager."""
        self.logger.info("Initializing order manager")
        return True
    
    def create_order(self, symbol: str, quantity: int, order_type: str = "market", 
                    price: Optional[float] = None, stop_price: Optional[float] = None) -> str:
        """Create a new order."""
        self.order_counter += 1
        order_id = f"ORD_{self.order_counter:06d}"
        
        order = {
            'id': order_id,
            'symbol': symbol,
            'quantity': quantity,
            'order_type': order_type,
            'price': price,
            'stop_price': stop_price,
            'status': 'pending',
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        self.orders[order_id] = order
        self.logger.info(f"Order created: {order_id}")
        return order_id
    
    def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get order by ID."""
        return self.orders.get(order_id)
    
    def update_order_status(self, order_id: str, status: str) -> bool:
        """Update order status."""
        if order_id in self.orders:
            self.orders[order_id]['status'] = status
            self.orders[order_id]['updated_at'] = datetime.now()
            return True
        return False
    
    def mark_executed(self, order_id: str, execution_price: Optional[float] = None) -> bool:
        """Mark order as executed."""
        if order_id in self.orders:
            self.orders[order_id]['status'] = 'executed'
            self.orders[order_id]['execution_price'] = execution_price
            self.orders[order_id]['executed_at'] = datetime.now()
            self.orders[order_id]['updated_at'] = datetime.now()
            return True
        return False
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order."""
        if order_id in self.orders and self.orders[order_id]['status'] == 'pending':
            self.orders[order_id]['status'] = 'cancelled'
            self.orders[order_id]['updated_at'] = datetime.now()
            return True
        return False
    
    def get_orders_by_symbol(self, symbol: str) -> List[Dict[str, Any]]:
        """Get all orders for a symbol."""
        return [order for order in self.orders.values() if order['symbol'] == symbol]
    
    def get_orders_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get all orders with specific status."""
        return [order for order in self.orders.values() if order['status'] == status]
    
    def get_pending_orders(self) -> List[Dict[str, Any]]:
        """Get all pending orders."""
        return self.get_orders_by_status('pending')
    
    def get_executed_orders(self) -> List[Dict[str, Any]]:
        """Get all executed orders."""
        return self.get_orders_by_status('executed')
    
    def get_order_history(self) -> List[Dict[str, Any]]:
        """Get complete order history."""
        return list(self.orders.values())
    
    def cleanup_old_orders(self, days: int = 30) -> int:
        """Clean up old orders."""
        cutoff_date = datetime.now() - pd.Timedelta(days=days)
        old_orders = [
            order_id for order_id, order in self.orders.items()
            if order['created_at'] < cutoff_date and order['status'] in ['executed', 'cancelled']
        ]
        
        for order_id in old_orders:
            del self.orders[order_id]
        
        self.logger.info(f"Cleaned up {len(old_orders)} old orders")
        return len(old_orders)

