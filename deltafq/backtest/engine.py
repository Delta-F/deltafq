"""
Backtesting engine for DeltaFQ.
"""

import pandas as pd
from typing import Dict, Any, Optional, Tuple, List
from ..core.base import BaseComponent
from ..trader.engine import ExecutionEngine
from ..data.storage import DataStorage


class BacktestEngine(BaseComponent):
    """Backtesting engine for DeltaFQ."""
    
    def __init__(self, initial_capital: float = 1000000, commission: float = 0.001, 
                 slippage: Optional[float] = None, storage: Optional[DataStorage] = None,
                 storage_path: str = None, **kwargs):
        """Initialize backtest engine."""
        super().__init__(**kwargs)
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        
        # Create execution engine for paper trading (broker=None)
        self.execution = ExecutionEngine(
            broker=None,
            initial_capital=initial_capital,
            commission=commission,
            **kwargs
        )
        
        # Data storage
        self.storage = storage or DataStorage(base_path=storage_path)
    
    def initialize(self) -> bool:
        """Initialize backtest engine."""
        self.logger.info(f"Initializing backtest engine with capital: {self.initial_capital}, "
                        f"commission: {self.commission}")
        return self.execution.initialize()
    
    def run_backtest(self, symbol: str, signals: pd.Series, price_series: pd.Series,
                   save_csv: bool = False, strategy_name: Optional[str] = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Execute a historical replay for a single symbol.

        Args:
            symbol: Instrument identifier (e.g. ticker).
            signals: Series aligned with `price_series`, containing {-1, 0, 1}.
            price_series: Historical close prices used for fills.
            save_csv: When True, persist trades and equity curve via `DataStorage`.
            strategy_name: Optional strategy label for saved files.

        Returns:
            trades_df: Executed orders recorded by the execution engine.
            values_df: Daily portfolio snapshot with cash, positions, and PnL.
        """
        try:
            # Reset execution engine for new backtest
            self.execution = ExecutionEngine(
                broker=None,
                initial_capital=self.initial_capital,
                commission=self.commission
            )
            self.execution.initialize()
            
            # Normalize input to DataFrame with required columns
            df_sig = pd.DataFrame({
                'Signal': signals,
                'Close': price_series
            })
            
            values_records: List[Dict[str, Any]] = []
            
            for i, (date, row) in enumerate(df_sig.iterrows()):
                signal = row['Signal']
                price = row['Close']
                
                # Process signals and define order parameters
                if signal == 1:  # Buy signal
                    # Calculate maximum quantity based on available cash
                    # Note: ExecutionEngine will handle cash validation
                    max_qty = int(self.execution.cash / (price * (1 + self.commission)))
                    if max_qty > 0:
                        # Execute order through ExecutionEngine
                        self.execution.execute_order(
                            symbol=symbol,
                            quantity=max_qty,
                            order_type="market",
                            price=price,
                            timestamp=date
                        )
                        
                elif signal == -1:  # Sell signal
                    # Get current position
                    current_qty = self.execution.position_manager.get_position(symbol)
                    if current_qty > 0:
                        # Execute order through ExecutionEngine
                        self.execution.execute_order(
                            symbol=symbol,
                            quantity=-current_qty,  # Negative for sell
                            order_type="market",
                            price=price,
                            timestamp=date
                        )
                
                # Calculate daily portfolio metrics from ExecutionEngine
                position_qty = self.execution.position_manager.get_position(symbol)
                position_value = position_qty * price
                total_value = position_value + self.execution.cash
                
                daily_pnl = 0.0 if i == 0 else total_value - values_records[-1]['total_value']
                
                values_records.append({
                    'date': date,
                    'signal': signal,
                    'price': price,
                    'cash': self.execution.cash,
                    'position': position_qty,
                    'position_value': position_value,
                    'total_value': total_value,
                    'daily_pnl': daily_pnl,
                })
            
            # Get trades from ExecutionEngine
            trades_df = pd.DataFrame(self.execution.trades)
            values_df = pd.DataFrame(values_records)
            
            if save_csv:
                self._save_backtest_results(symbol, trades_df, values_df, strategy_name)
            
            return trades_df, values_df
            
        except Exception as e:
            self.logger.error(f"run_backtest error: {e}")
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
