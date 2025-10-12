"""
Backtesting engine for DeltaFQ.
"""

import pandas as pd
from typing import Dict, Any, Optional
from ..core.base import BaseComponent
from ..core.exceptions import BacktestError


class BacktestEngine(BaseComponent):
    """Backtesting engine for strategy testing."""
    
    def __init__(self, initial_capital: float = 100000, commission: float = 0.001, **kwargs):
        """Initialize backtest engine."""
        super().__init__(**kwargs)
        self.initial_capital = initial_capital
        self.commission = commission
        self.results = None
    
    def initialize(self) -> bool:
        """Initialize backtest engine."""
        self.logger.info(f"Initializing backtest engine with capital: {self.initial_capital}")
        return True
    
    def run_backtest(self, strategy, data: pd.DataFrame) -> Dict[str, Any]:
        """Run backtest for given strategy and data."""
        try:
            self.logger.info("Starting backtest")
            
            # Initialize portfolio
            cash = self.initial_capital
            positions = {}
            trades = []
            
            # Run strategy on data
            for i, (date, row) in enumerate(data.iterrows()):
                # Get signals from strategy
                signals = strategy.generate_signals(data.iloc[:i+1])
                
                if not signals.empty and i > 0:
                    signal = signals.iloc[-1]
                    
                    # Execute trades based on signals
                    if signal != 0:  # Buy or sell signal
                        symbol = 'STOCK'  # Simplified for single asset
                        price = row['close']
                        quantity = int(signal * cash * 0.1 / price)  # Use 10% of cash
                        
                        if quantity > 0 and quantity * price <= cash:
                            # Buy
                            cost = quantity * price * (1 + self.commission)
                            cash -= cost
                            positions[symbol] = positions.get(symbol, 0) + quantity
                            trades.append({
                                'date': date,
                                'symbol': symbol,
                                'quantity': quantity,
                                'price': price,
                                'type': 'buy'
                            })
                        elif quantity < 0 and positions.get(symbol, 0) >= abs(quantity):
                            # Sell
                            quantity = abs(quantity)
                            proceeds = quantity * price * (1 - self.commission)
                            cash += proceeds
                            positions[symbol] -= quantity
                            trades.append({
                                'date': date,
                                'symbol': symbol,
                                'quantity': -quantity,
                                'price': price,
                                'type': 'sell'
                            })
            
            # Calculate final portfolio value
            final_price = data['close'].iloc[-1]
            final_value = cash + sum(positions.values()) * final_price
            
            self.results = {
                'initial_capital': self.initial_capital,
                'final_value': final_value,
                'total_return': (final_value - self.initial_capital) / self.initial_capital,
                'trades': trades,
                'final_positions': positions,
                'final_cash': cash
            }
            
            self.logger.info(f"Backtest completed. Total return: {self.results['total_return']:.2%}")
            return self.results
            
        except Exception as e:
            raise BacktestError(f"Backtest failed: {str(e)}")
    
    def get_results(self) -> Optional[Dict[str, Any]]:
        """Get backtest results."""
        return self.results

