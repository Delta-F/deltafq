"""
Backtesting engine for DeltaFQ.
"""

import pandas as pd
from typing import Dict, Any, Optional, Tuple, List
from ..core.base import BaseComponent
from ..data import DataFetcher, DataStorage
from ..strategy.base import BaseStrategy
from ..trader.engine import ExecutionEngine
from .performance import PerformanceReporter
from ..charts.performance import PerformanceChart
from abc import ABC


class BacktestEngine(BaseComponent, ABC):
    """Backtesting engine for DeltaFQ."""
    
    def __init__(self, initial_capital: float = 1000000, commission: float = 0.001, 
                 slippage: float = 0.001, data_source: str = "yahoo", **kwargs):
        """Initialize backtest engine."""
        super().__init__(**kwargs)
        self.logger.info("Initializing backtest engine")
        # initialize parameters
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.data_source = data_source
        # initialize components
        self.data_fetcher = DataFetcher(source=self.data_source)
        self.storage = DataStorage()
        self.reporter = PerformanceReporter()
        self.chart = PerformanceChart()
        # initialize execution engine
        self.execution = ExecutionEngine(
            broker=None, 
            initial_capital=self.initial_capital, 
            commission=self.commission
        )
        # initialize variables
        self.symbol = None
        self.start_date = None
        self.end_date = None
        self.benchmark = None
        self.data = None
        self.strategy = None
        self.signals = None
        self.price_series = None
        self.trades_df = pd.DataFrame()
        self.values_df = pd.DataFrame()
        
    def set_parameters(self, symbol: str, start_date: str, end_date: str, benchmark: str, 
                      data_source: Optional[str] = None, initial_capital: Optional[float] = None, 
                      commission: Optional[float] = None, slippage: Optional[float] = None) -> None:
        """Set backtest parameters."""
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date
        self.benchmark = benchmark
        
        self.initial_capital = initial_capital if initial_capital is not None else self.initial_capital
        self.commission = commission if commission is not None else self.commission
        self.slippage = slippage if slippage is not None else self.slippage
        self.execution = ExecutionEngine(broker=None, initial_capital=self.initial_capital, commission=self.commission)

        self.data_source = data_source if data_source is not None else self.data_source
        self.data_fetcher = DataFetcher(source=self.data_source)
    
    def load_data(self) -> pd.DataFrame:
        """Load data via data fetcher."""
        self.data = self.data_fetcher.fetch_data(self.symbol, self.start_date, self.end_date, clean=True)
        return self.data
    
    def add_strategy(self, strategy: BaseStrategy) -> None:
        """Add a strategy to the backtest engine."""
        self.strategy = strategy
        self.strategy.run(self.data)
        self.signals = self.strategy.signals
        self.price_series = self.data['Close']
    
    def run_backtest(self, symbol: Optional[str] = None, signals: Optional[pd.Series] = None, price_series: Optional[pd.Series] = None,
                   save_csv: bool = False, strategy_name: Optional[str] = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Execute a historical replay for a single symbol."""
        if symbol is None and self.symbol is None:
            raise ValueError("Symbol must be set. Call set_parameters() first.")
        if signals is None and self.signals is None:
            raise ValueError("Signals must be set. Call add_strategy() first.")
        
        # Initialize empty DataFrames in case of error
        self.trades_df = pd.DataFrame()
        self.values_df = pd.DataFrame()
        
        try:            
            symbol = symbol if symbol is not None else self.symbol
            signals = signals if signals is not None else self.signals
            price_series = price_series if price_series is not None else self.price_series
            strategy_name = strategy_name if strategy_name is not None else self.strategy.name
            
            df_sig = pd.DataFrame({'Signal': signals, 'Close': price_series})
            values_records: List[Dict[str, Any]] = []
            
            for i, (date, row) in enumerate(df_sig.iterrows()):
                signal = row['Signal']
                price = row['Close']
                
                if signal == 1:
                    max_qty = int(self.execution.cash / (price * (1 + self.commission)))
                    if max_qty > 0:
                        self.execution.execute_order(
                            symbol=symbol,
                            quantity=max_qty,
                            order_type="limit",
                            price=price,
                            timestamp=date
                        )
                        
                elif signal == -1:
                    current_qty = self.execution.position_manager.get_position(symbol)
                    if current_qty > 0:
                        self.execution.execute_order(
                            symbol=symbol,
                            quantity=-current_qty,
                            order_type="limit",
                            price=price,
                            timestamp=date
                        )
                
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
            
            self.trades_df = pd.DataFrame(self.execution.trades)
            self.values_df = pd.DataFrame(values_records)
            
            if save_csv:
                self.save_backtest_results()
            
            return self.trades_df, self.values_df
            
        except Exception as e:
            self.logger.error(f"run_backtest error: {e}")
            return self.trades_df, self.values_df
    
    def calculate_metrics(self) -> Tuple[pd.DataFrame, Dict[str, float]]:
        """Calculate backtest metrics, such as return, volatility, sharpe ratio, etc."""
        self.values_metrics, self.metrics = self.reporter.compute(self.symbol, self.trades_df, self.values_df)
        return self.values_metrics, self.metrics
    
    def show_report(self) -> None:
        """Show backtest summary report."""
        self.reporter.print_summary(symbol=self.symbol, trades_df=self.trades_df, values_df=self.values_df)
        
    def show_chart(self, use_plotly: bool = False) -> None:
        """Show backtest performance chart."""
        benchmark_data = self.data_fetcher.fetch_data(self.benchmark, self.start_date, self.end_date, clean=True)
        self.chart.plot_backtest_charts(values_df=self.values_df, benchmark_close=benchmark_data['Close'], use_plotly=use_plotly)
    
    def save_backtest_results(self) -> None:
        """Save backtest results to csv files."""
        self.storage.save_backtest_results(trades_df=self.trades_df, values_df=self.values_df, symbol=self.symbol, strategy_name=self.strategy.name)
