"""
Backtesting engine for DeltaFQ.
"""

import pandas as pd
from typing import Dict, Any, Optional, Tuple, List
from ..core.base import BaseComponent
from ..trading.simulator import PaperTradingSimulator
from ..data.storage import DataStorage


class BacktestEngine(BaseComponent):
    """Backtesting engine for strategy testing."""
    
    def __init__(self, initial_capital: float = 1000000, commission: float = 0.001, 
                 slippage: Optional[float] = None, storage: Optional[DataStorage] = None,
                 storage_path: str = None, **kwargs):
        """Initialize backtest engine."""
        super().__init__(**kwargs)
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.results = None
        # Use PaperTradingSimulator for trade execution
        self.simulator = PaperTradingSimulator(
            initial_capital=initial_capital,
            commission=commission,
            slippage=slippage
        )
        # Data storage
        self.storage = storage or DataStorage(base_path=storage_path)
    
    def initialize(self) -> bool:
        """Initialize backtest engine."""
        self.logger.info(f"Initializing backtest engine with capital: {self.initial_capital}")
        self.simulator.initialize()
        self.storage.initialize()
        return True
    
   
    def run_backtest(self, symbol: str, signals: pd.Series, price_series: pd.Series,
                   save_csv: bool = False, strategy_name: Optional[str] = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Execute trades based on precomputed signals. 
        Returns (trades_df, values_df).
        
        Example:
            >>> engine = BacktestEngine(initial_capital=100000)
            >>> trades_df, values_df = engine.run_signals(
            ...     symbol='AAPL',
            ...     signals=signals,  # Series with 1/-1/0
            ...     price_series=data['Close']
            ... )
        """
        try:
            # Normalize input to DataFrame with required columns
            df_sig = pd.DataFrame({
                'Signal': signals,
                'Close': price_series
            })
            
            values_records: List[Dict[str, Any]] = []
            
            for i, (date, row) in enumerate(df_sig.iterrows()):
                signal = row['Signal']
                price = row['Close']
                
                # Execute trades: full-in/full-out strategy
                if signal == 1:
                    # Buy: use all available cash
                    max_qty = int(self.simulator.cash / (price * (1 + self.commission)))
                    if max_qty > 0:
                        self.simulator.execute_trade(symbol=symbol, quantity=max_qty, 
                                                     price=price, timestamp=date)
                elif signal == -1:
                    # Sell: sell entire position
                    current_qty = self.simulator.position_manager.get_position(symbol)
                    if current_qty > 0:
                        self.simulator.execute_trade(symbol=symbol, quantity=-current_qty, 
                                                     price=price, timestamp=date)
                
                # Calculate daily portfolio metrics
                position_qty = self.simulator.position_manager.get_position(symbol)
                position_value = position_qty * price
                total_value = position_value + self.simulator.cash
                
                daily_pnl = 0.0 if i == 0 else total_value - values_records[-1]['total_value']
                
                values_records.append({
                    'date': date,
                    'signal': signal,
                    'price': price,
                    'cash': self.simulator.cash,
                    'position': position_qty,
                    'position_value': position_value,
                    'total_value': total_value,
                    'daily_pnl': daily_pnl,
                })
            
            trades_df = pd.DataFrame(self.simulator.trades)
            values_df = pd.DataFrame(values_records)
            
            if save_csv:
                self._save_backtest_results(symbol, trades_df, values_df, strategy_name)
            
            return trades_df, values_df
            
        except Exception as e:
            self.logger.error(f"run_signals error: {e}")
            return pd.DataFrame(), pd.DataFrame()
    
    def _save_backtest_results(self, symbol: str, trades_df: pd.DataFrame, 
                              values_df: pd.DataFrame, strategy_name: Optional[str] = None) -> None:
        """Save backtest results using DataStorage."""
        paths = self.storage.save_backtest_results(
            trades_df=trades_df,
            values_df=values_df,
            symbol=symbol,
            strategy_name=strategy_name
        )
        self.logger.info(f"Saved backtest results: {paths}")
