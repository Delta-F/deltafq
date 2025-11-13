"""
Trade execution engine for DeltaFQ.
"""

import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime
from ..core.base import BaseComponent
from ..core.exceptions import TradingError
from .order_manager import OrderManager
from .position_manager import PositionManager


class ExecutionEngine(BaseComponent):
    """
    Trade execution engine for real-time trading.
    Supports paper trading (broker=None) and live trading (broker=Broker).
    Paper trading manages cash internally. Live trading uses broker for account info.
    """
    
    def __init__(self, broker=None, initial_capital: Optional[float] = None,
                 commission: float = 0.001, **kwargs):
        """
        Initialize execution engine.
        Args:
            broker: Broker for live trading. None for paper trading.
            initial_capital: Initial capital for paper trading. Defaults to 1000000.
            commission: Commission rate for paper trading. Defaults to 0.001.
        """
        super().__init__(**kwargs)
        self.broker = broker
        self.order_manager = OrderManager()
        self.position_manager = PositionManager()
        
        # Paper trading mode: manage cash internally
        if broker is None:
            self.initial_capital = initial_capital if initial_capital is not None else 1000000
            self.cash = self.initial_capital
            self.commission = commission
            self.trades: List[Dict[str, Any]] = []
            self.is_paper_trading = True
        else:
            # Live trading mode: get account info from broker
            self.cash = None
            self.commission = None
            self.trades = []
            self.is_paper_trading = False
    
    def initialize(self) -> bool:
        """Initialize execution engine."""
        if self.is_paper_trading:
            self.logger.info(f"Initializing paper trading execution engine with capital: {self.initial_capital}")
        else:
            self.logger.info("Initializing live trading execution engine")
        
        if self.broker:
            return self.broker.initialize()
        
        return True
    
    def execute_order(self, symbol: str, quantity: int, order_type: str = "limit", 
                     price: Optional[float] = None, timestamp: Optional[datetime] = None) -> str:
        """Execute an order. Default is limit order (price required)."""
        try:
            # Validate price for limit orders
            if order_type == "limit" and price is None:
                raise TradingError("Price is required for limit orders")
            
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
                
                self.logger.info(f"Order executed - broker: {order_id} -> {broker_order_id}, date: {timestamp.date()}, price: {price}, quantity: {quantity}")
            else:
                self._execute_paper_trade(order_id, price, timestamp)
                self.logger.info(f"Order executed - paper trading: {order_id}, date: {timestamp.date()}, price: {price}, quantity: {quantity}")
            
            return order_id
            
        except Exception as e:
            raise TradingError(f"Failed to execute order: {str(e)}")
    
    def _execute_paper_trade(self, order_id: str, execution_price: float, timestamp: Optional[datetime] = None):
        """Execute paper trading with cash management."""
        order = self.order_manager.get_order(order_id)
        if not order:
            return
        
        symbol = order['symbol']
        quantity = order['quantity']
        timestamp = timestamp or datetime.now()
        
        if quantity > 0:  # Buy
            gross_cost = quantity * execution_price
            commission_amount = gross_cost * self.commission
            total_cost = gross_cost + commission_amount
            
            if total_cost <= self.cash:
                self.cash -= total_cost
                self.position_manager.add_position(symbol, quantity, execution_price)
                self.order_manager.mark_executed(order_id, execution_price)
                
                # Record trade (unified record with full details)
                self.trades.append({
                    'order_id': order_id,
                    'symbol': symbol,
                    'quantity': quantity,
                    'price': execution_price,
                    'type': 'buy',
                    'timestamp': timestamp,
                    'commission': commission_amount,
                    'cost': total_cost
                })
            else:
                self.logger.warning(f"Insufficient cash for buy: need {total_cost:.2f}, have {self.cash:.2f}")
                self.order_manager.cancel_order(order_id)
        else:  # Sell
            quantity = abs(quantity)
            if self.position_manager.can_sell(symbol, quantity):
                gross_revenue = quantity * execution_price
                commission_amount = gross_revenue * self.commission
                net_revenue = gross_revenue - commission_amount
                
                # Calculate profit/loss
                buy_cost = self._get_latest_buy_cost(symbol)
                profit_loss = net_revenue - buy_cost if buy_cost else net_revenue
                
                self.position_manager.reduce_position(symbol, quantity, execution_price)
                self.cash += net_revenue
                self.order_manager.mark_executed(order_id, execution_price)
                
                # Record trade (unified record with full details)
                self.trades.append({
                    'order_id': order_id,
                    'symbol': symbol,
                    'quantity': quantity,
                    'price': execution_price,
                    'type': 'sell',
                    'timestamp': timestamp,
                    'commission': commission_amount,
                    'gross_revenue': gross_revenue,
                    'net_revenue': net_revenue,
                    'buy_cost': buy_cost,
                    'profit_loss': profit_loss
                })
            else:
                self.logger.warning(f"Insufficient position for sell: {symbol}, need {quantity}")
                self.order_manager.cancel_order(order_id)
    
    def _get_latest_buy_cost(self, symbol: str) -> float:
        """Get the latest buy cost for a symbol (for PnL calculation)."""
        for trade in reversed(self.trades):
            if trade.get('symbol') == symbol and trade.get('type') == 'buy':
                return float(trade.get('cost', 0.0))
        return 0.0

