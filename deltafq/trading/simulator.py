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
        self.slippage = None
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
    
    def execute_order(self, order_id: str, current_price: float, timestamp: Optional[datetime] = None) -> bool:
        """Execute an order at current price with commission and detailed trade recording.
        If timestamp is provided, it will be used as the trade time; otherwise uses now.
        """
        try:
            order = self.order_manager.get_order(order_id)
            if not order:
                return False
            
            symbol = order['symbol']
            quantity = int(order['quantity'])
            timestamp = timestamp or datetime.now()
            commission_rate = self.commission
            
            if quantity > 0:
                # Buy
                gross_cost = quantity * current_price
                commission_amount = gross_cost * commission_rate
                total_cost = gross_cost + commission_amount
                
                if total_cost <= self.cash:
                    self.cash -= total_cost
                    self.position_manager.add_position(symbol=symbol, quantity=quantity, price=current_price)
                    
                    # record trade
                    self.trades.append({
                        'order_id': order_id,
                        'symbol': symbol,
                        'quantity': quantity,
                        'price': current_price,
                        'type': 'buy',
                        'timestamp': timestamp,
                        'commission': commission_amount,
                        'cost': total_cost
                    })
                    
                    self.order_manager.mark_executed(order_id)
                    self.logger.info(f"Buy executed: {order_id} @{current_price} cost={total_cost} cash={self.cash}")
                    return True
                else:
                    self.logger.info(f"Insufficient cash for buy: need {total_cost}, cash {self.cash}")
                    return False
            else:
                # Sell
                sell_qty = abs(quantity)
                if self.position_manager.can_sell(symbol, sell_qty):
                    gross_revenue = sell_qty * current_price
                    commission_amount = gross_revenue * commission_rate
                    net_revenue = gross_revenue - commission_amount
                    
                    # latest buy cost (full in/full out scenario)
                    buy_cost = self.get_latest_buy_cost(symbol)
                    profit_loss = net_revenue - buy_cost if buy_cost else net_revenue
                    profit_rate = (profit_loss / buy_cost) if buy_cost else 0.0
                    
                    self.position_manager.reduce_position(symbol=symbol, quantity=sell_qty, price=current_price)
                    self.cash += net_revenue
                    
                    self.trades.append({
                        'order_id': order_id,
                        'symbol': symbol,
                        'quantity': sell_qty,
                        'price': current_price,
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
                    self.logger.info(f"Sell executed: {order_id} @{current_price} net={net_revenue} PnL={profit_loss} cash={self.cash}")
                    return True
                else:
                    self.logger.info(f"Insufficient position for sell: {symbol}, need {sell_qty}, have {self.position_manager.get_position(symbol)}")
                    return False
                    
        except Exception as e:
            raise TradingError(f"Failed to execute order: {str(e)}")
    
    def execute_trade(self, symbol: str, quantity: int, price: float, date, commission: float = None) -> bool:
        """Convenience method: place + execute at given price/time. quantity>0 buy; quantity<0 sell."""
        commission = commission if commission is not None else self.commission
        try:
            order_id = self.place_order(symbol=symbol, quantity=quantity, order_type="market", price=price)
            # 使用传入的 date 作为成交时间
            return self.execute_order(order_id=order_id, current_price=price, timestamp=date)
        except Exception as e:
            self.logger.info(f"execute_trade error: {e}")
            return False

    def run_strategy(self, strategy, data: pd.DataFrame, symbol: str = "STOCK") -> Dict[str, Any]:
        """Run a strategy with the simulator."""
        self.logger.info(f"Running strategy: {strategy.name}")
        
        for i, (date, row) in enumerate(data.iterrows()):
            # Generate signals
            signals = strategy.generate_signals(data.iloc[:i+1])
            
            if not signals.empty and i > 0:
                signal = signals.iloc[-1]
                current_price = row['Close']
                
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
        
        return self.get_portfolio_summary({symbol: data['Close'].iloc[-1]})

    def run_signals(self, symbol: str, signals: pd.DataFrame, save_csv: bool = False, price_series: Optional[pd.Series] = None):
        """
        Execute trades based on a precomputed signals DataFrame and compute daily metrics.
        Accepts either:
          - DataFrame with columns 'Signal' (1/-1/0) and 'Close'
          - Series of signals; in this case provide price_series=Close price series

        Returns:
            (trades_df, values_df)
        """
        try:
            # Normalize input to DataFrame with required columns
            if isinstance(signals, pd.Series):
                if price_series is None:
                    raise ValueError("When 'signals' is a Series, you must pass price_series with Close prices")
                df_sig = pd.DataFrame({
                    'Signal': signals.astype(float),
                    'Close': pd.Series(price_series).reindex(signals.index)
                })
            else:
                df_sig = signals.copy()
                if 'Signal' not in df_sig.columns:
                    raise ValueError("Signals DataFrame must contain 'Signal' column")
                if 'Close' not in df_sig.columns:
                    raise ValueError("Signals DataFrame must contain 'Close' column")

            values_records: List[Dict[str, Any]] = []

            for i, (date, row) in enumerate(df_sig.iterrows()):
                signal = int(row['Signal']) if pd.notna(row['Signal']) else 0
                price = float(row['Close'])

                # Apply slippage if configured
                exec_price = price
                if getattr(self, 'slippage', None):
                    if signal == 1:
                        exec_price = price * (1 + float(self.slippage))
                    elif signal == -1:
                        exec_price = price * (1 - float(self.slippage))

                # Execute trades: full-in/full-out
                if signal == 1:
                    max_qty = int(self.cash / (exec_price * (1 + self.commission)))
                    if max_qty > 0:
                        self.execute_trade(symbol=symbol, quantity=max_qty, price=exec_price, date=date)
                elif signal == -1:
                    current_qty = self.position_manager.get_position(symbol)
                    if current_qty > 0:
                        self.execute_trade(symbol=symbol, quantity=-current_qty, price=exec_price, date=date)

                # Daily valuation
                position_qty = self.position_manager.get_position(symbol)
                position_value = position_qty * price
                total_value = position_value + self.cash

                if i == 0:
                    daily_pnl = 0.0
                else:
                    prev_total = values_records[-1]['total_value']
                    daily_pnl = total_value - prev_total

                values_records.append({
                    'date': date,
                    'signal': signal,
                    'price': price,
                    'cash': self.cash,
                    'position': position_qty,
                    'position_value': position_value,
                    'total_value': total_value,
                    'daily_pnl': daily_pnl,
                })

            trades_df = pd.DataFrame(self.trades)
            values_df = pd.DataFrame(values_records)

            if save_csv:
                trades_fn = f"{symbol}_backtest_trades.csv"
                values_fn = f"{symbol}_backtest_values.csv"
                trades_df.to_csv(trades_fn, encoding='utf-8-sig', index=False)
                values_df.to_csv(values_fn, encoding='utf-8-sig', index=False)
                self.logger.info(f"Saved CSV: {trades_fn}, {values_fn}")

            return trades_df, values_df

        except Exception as e:
            self.logger.info(f"run_signals error: {e}")
            return pd.DataFrame(), pd.DataFrame()
    
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

    # --- Helpers ---
    def get_latest_buy_cost(self, symbol: str) -> float:
        """Return the latest total buy cost for the given symbol (full-in/full-out)."""
        for trade in reversed(self.trades):
            if trade.get('symbol') == symbol and trade.get('type') == 'buy':
                if 'cost' in trade:
                    return float(trade['cost'])
                return float(trade.get('quantity', 0)) * float(trade.get('price', 0.0))
        self.logger.info(f"No buy record found for {symbol}")
        return 0.0
