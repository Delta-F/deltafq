"""
Paper trading simulator for DeltaFQ.
"""

import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime
from ..core.base import BaseComponent
from ..core.exceptions import TradingError
from .order_manager import OrderManager
from .position_manager import PositionManager


class PaperTradingSimulator(BaseComponent):
    """Paper trading simulator for testing strategies."""
    
    def __init__(self, initial_capital: float = 100000, commission: float = 0.001, **kwargs):
        """Initialize paper trading simulator."""
        super().__init__(**kwargs)
        self.initial_capital = initial_capital
        self.commission = commission
        self.cash = initial_capital
        self.order_manager = OrderManager()
        self.position_manager = PositionManager()
        self.trades = []
    
    def initialize(self) -> bool:
        """Initialize simulator."""
        self.logger.info(f"Initializing paper trading simulator with capital: {self.initial_capital}")
        return True
    
    def place_order(self, symbol: str, quantity: int, order_type: str = "market", 
                   price: Optional[float] = None) -> str:
        """Place an order."""
        try:
            order_id = self.order_manager.create_order(
                symbol=symbol,
                quantity=quantity,
                order_type=order_type,
                price=price
            )
            
            self.logger.info(f"Order placed: {order_id} - {symbol} {quantity} @ {order_type}")
            return order_id
            
        except Exception as e:
            raise TradingError(f"Failed to place order: {str(e)}")
    
    def execute_order(self, order_id: str, current_price: float) -> bool:
        """Execute an order at current price."""
        try:
            order = self.order_manager.get_order(order_id)
            if not order:
                return False
            
            # Calculate cost
            quantity = order['quantity']
            cost = abs(quantity) * current_price * (1 + self.commission)
            
            if quantity > 0:  # Buy order
                if cost <= self.cash:
                    self.cash -= cost
                    self.position_manager.add_position(symbol=order['symbol'], quantity=quantity)
                    self.trades.append({
                        'order_id': order_id,
                        'symbol': order['symbol'],
                        'quantity': quantity,
                        'price': current_price,
                        'type': 'buy',
                        'timestamp': datetime.now()
                    })
                    self.order_manager.mark_executed(order_id)
                    self.logger.info(f"Buy order executed: {order_id}")
                    return True
                else:
                    self.logger.warning(f"Insufficient cash for order: {order_id}")
                    return False
            else:  # Sell order
                if self.position_manager.can_sell(order['symbol'], abs(quantity)):
                    self.cash += abs(quantity) * current_price * (1 - self.commission)
                    self.position_manager.reduce_position(symbol=order['symbol'], quantity=abs(quantity))
                    self.trades.append({
                        'order_id': order_id,
                        'symbol': order['symbol'],
                        'quantity': quantity,
                        'price': current_price,
                        'type': 'sell',
                        'timestamp': datetime.now()
                    })
                    self.order_manager.mark_executed(order_id)
                    self.logger.info(f"Sell order executed: {order_id}")
                    return True
                else:
                    self.logger.warning(f"Insufficient position for order: {order_id}")
                    return False
                    
        except Exception as e:
            raise TradingError(f"Failed to execute order: {str(e)}")
    
    def get_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """Calculate total portfolio value."""
        total_value = self.cash
        positions = self.position_manager.get_all_positions()
        
        for symbol, quantity in positions.items():
            if symbol in current_prices:
                total_value += quantity * current_prices[symbol]
        
        return total_value
    
    def get_portfolio_summary(self, current_prices: Dict[str, float]) -> Dict[str, Any]:
        """Get portfolio summary."""
        total_value = self.get_portfolio_value(current_prices)
        
        return {
            'total_value': total_value,
            'cash': self.cash,
            'positions': self.position_manager.get_all_positions(),
            'total_return': (total_value - self.initial_capital) / self.initial_capital,
            'total_trades': len(self.trades),
            'open_orders': len(self.order_manager.get_pending_orders())
        }
    
    def run_strategy(self, strategy, data: pd.DataFrame, symbol: str = "STOCK") -> Dict[str, Any]:
        """Run a strategy with the simulator."""
        self.logger.info(f"Running strategy: {strategy.name}")
        
        for i, (date, row) in enumerate(data.iterrows()):
            # Generate signals
            signals = strategy.generate_signals(data.iloc[:i+1])
            
            if not signals.empty and i > 0:
                signal = signals.iloc[-1]
                current_price = row['close']
                
                # Execute trades based on signals
                if signal > 0:  # Buy signal
                    quantity = int(self.cash * 0.1 / current_price)  # Use 10% of cash
                    if quantity > 0:
                        order_id = self.place_order(symbol, quantity, "market")
                        self.execute_order(order_id, current_price)
                
                elif signal < 0:  # Sell signal
                    position = self.position_manager.get_position(symbol)
                    if position > 0:
                        quantity = min(position, int(position * 0.5))  # Sell 50% of position
                        order_id = self.place_order(symbol, -quantity, "market")
                        self.execute_order(order_id, current_price)
        
        return self.get_portfolio_summary({symbol: data['close'].iloc[-1]})
