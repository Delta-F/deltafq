"""
Paper trading simulator for DeltaFQ.
"""

import pandas as pd
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from ..core.base import BaseComponent
from ..core.exceptions import TradingError
from .order_manager import OrderManager
from .position_manager import PositionManager


class PaperTradingSimulator(BaseComponent):
    """Paper trading simulator for testing strategies."""
    
    def __init__(self, initial_capital: float = 1000000, commission: float = 0.001, 
                 slippage: Optional[float] = None, **kwargs):
        """Initialize paper trading simulator."""
        super().__init__(**kwargs)
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.cash = initial_capital
        self.order_manager = OrderManager()
        self.position_manager = PositionManager()
        self.trades: List[Dict[str, Any]] = []
    
    def initialize(self) -> bool:
        """Initialize simulator and its components."""
        self.logger.info(f"Initializing paper trading simulator with capital: {self.initial_capital}, \
                        commission: {self.commission}, slippage: {self.slippage}")
        return True
    
    def execute_order(self, order_id: str, current_price: float, 
                     timestamp: Optional[datetime] = None) -> bool:
        """Execute an order at current price with commission."""
        try:
            order = self.order_manager.get_order(order_id)
            if not order:
                return False
            
            symbol = order['symbol']
            quantity = int(order['quantity'])
            timestamp = timestamp or datetime.now()
            commission_rate = self.commission
            
            if quantity > 0:
                # Buy order
                return self._execute_buy(symbol, quantity, current_price, timestamp, 
                                       order_id, commission_rate)
            else:
                # Sell order
                return self._execute_sell(symbol, abs(quantity), current_price, timestamp,
                                        order_id, commission_rate)
                    
        except Exception as e:
            raise TradingError(f"Failed to execute order: {str(e)}")
    
    def execute_trade(self, symbol: str, quantity: int, price: float, 
                     timestamp: Optional[Union[datetime, pd.Timestamp]] = None,
                     commission: Optional[float] = None) -> bool:
        """Place and execute a trade in one step. quantity>0 buy, quantity<0 sell."""
        # Store original commission temporarily
        original_commission = self.commission
        if commission is not None:
            self.commission = commission
        
        try:
            order_id = self.order_manager.create_order(
                symbol=symbol, quantity=quantity, order_type="market", price=price
            )
            
            # Convert timestamp if needed
            if timestamp is None:
                exec_timestamp = datetime.now()
            elif isinstance(timestamp, pd.Timestamp):
                exec_timestamp = timestamp.to_pydatetime()
            else:
                exec_timestamp = timestamp
            
            return self.execute_order(order_id=order_id, current_price=price, 
                                    timestamp=exec_timestamp)
        except Exception as e:
            self.logger.warning(f"execute_trade error: {e}")
            return False
        finally:
            # Restore original commission
            self.commission = original_commission
    
    def _execute_buy(self, symbol: str, quantity: int, price: float, 
                    timestamp: datetime, order_id: str, commission_rate: float) -> bool:
        """Execute a buy order."""
        gross_cost = quantity * price
        commission_amount = gross_cost * commission_rate
        total_cost = gross_cost + commission_amount
        
        if total_cost <= self.cash:
            self.cash -= total_cost
            self.position_manager.add_position(symbol=symbol, quantity=quantity, price=price)
            
            # Record trade
            self.trades.append({
                'order_id': order_id,
                'symbol': symbol,
                'quantity': quantity,
                'price': price,
                'type': 'buy',
                'timestamp': timestamp,
                'commission': commission_amount,
                'cost': total_cost
            })
            
            self.order_manager.mark_executed(order_id)
            self.logger.info(f"Buy executed: {order_id} @{price} cost={total_cost:.2f} cash={self.cash:.2f}")
            return True
        else:
            self.logger.warning(f"Insufficient cash for buy: need {total_cost:.2f}, have {self.cash:.2f}")
            return False
    
    def _execute_sell(self, symbol: str, quantity: int, price: float,
                     timestamp: datetime, order_id: str, commission_rate: float) -> bool:
        """Execute a sell order."""
        if not self.position_manager.can_sell(symbol, quantity):
            current_position = self.position_manager.get_position(symbol)
            self.logger.warning(f"Insufficient position for sell: {symbol}, need {quantity}, have {current_position}")
            return False
        
        gross_revenue = quantity * price
        commission_amount = gross_revenue * commission_rate
        net_revenue = gross_revenue - commission_amount
        
        # Calculate profit/loss (full-in/full-out scenario)
        buy_cost = self.get_latest_buy_cost(symbol)
        profit_loss = net_revenue - buy_cost if buy_cost else net_revenue
        profit_rate = (profit_loss / buy_cost) if buy_cost else 0.0
        
        self.position_manager.reduce_position(symbol=symbol, quantity=quantity, price=price)
        self.cash += net_revenue
        
        # Record trade
        self.trades.append({
            'order_id': order_id,
            'symbol': symbol,
            'quantity': quantity,
            'price': price,
            'type': 'sell',
            'timestamp': timestamp,
            'commission': commission_amount,
            'gross_revenue': gross_revenue,
            'net_revenue': net_revenue,
            'buy_cost': buy_cost,
            'profit_loss': profit_loss,
            'profit_rate': profit_rate,
            'profit_rate_pct': f"{profit_rate:.2%}"
        })
        
        self.order_manager.mark_executed(order_id)
        self.logger.info(f"Sell executed: {order_id} @{price} net={net_revenue:.2f} PnL={profit_loss:.2f} cash={self.cash:.2f}")
        return True

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
    
    def get_latest_buy_cost(self, symbol: str) -> float:
        """Get the latest buy cost for a symbol (full-in/full-out)."""
        for trade in reversed(self.trades):
            if trade.get('symbol') == symbol and trade.get('type') == 'buy':
                if 'cost' in trade:
                    return float(trade['cost'])
                return float(trade.get('quantity', 0)) * float(trade.get('price', 0.0))
        
        self.logger.debug(f"No buy record found for {symbol}")
        return 0.0
    
