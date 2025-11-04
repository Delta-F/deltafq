"""
Price comparison charts for DeltaFQ.
"""

import pandas as pd
import matplotlib.pyplot as plt
from typing import Optional, Dict, Union
from ..core.base import BaseComponent


class PriceChart(BaseComponent):
    """Chart class for price comparison visualization."""
    
    def initialize(self) -> bool:
        """Initialize the price chart component."""
        self.logger.info("Initializing price chart")
        # Set default style
        plt.style.use('seaborn-v0_8-darkgrid' if 'seaborn-v0_8-darkgrid' in plt.style.available else 'default')
        return True
    
    def plot_prices(
        self, 
        data: Union[pd.DataFrame, Dict[str, pd.DataFrame]], 
        price_column: str = 'Close',
        normalize: bool = False,
        base_value: float = 100.0,
        title: Optional[str] = None,
        figsize: tuple = (12, 6),
        show: bool = True,
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Plot price comparison chart.
        
        Args:
            data: DataFrame with price data or dict of DataFrames for multiple symbols.
                 If dict, symbols will be extracted from dict keys automatically.
            price_column: Column name for price (default: 'Close')
            normalize: Whether to normalize prices to start at base_value (default: False)
            base_value: Base value for normalization (default: 100.0, only used when normalize=True)
            title: Chart title
            figsize: Figure size tuple (width, height)
            show: Whether to display the chart
            save_path: Optional path to save the chart
            
        Returns:
            matplotlib Figure object
        """
        try:
            chart_type = "normalized price comparison" if normalize else "price comparison"
            self.logger.info(f"Generating {chart_type} chart")
            
            fig, ax = plt.subplots(figsize=figsize)
            
            # Handle single DataFrame
            if isinstance(data, pd.DataFrame):
                if price_column not in data.columns:
                    raise ValueError(f"Column '{price_column}' not found in data")
                
                price_data = data[price_column]
                
                if normalize:
                    price_data = (price_data / price_data.iloc[0]) * base_value
                    label = 'Normalized Price'
                    ylabel = f'Normalized Price (Base={base_value})'
                else:
                    label = 'Price'
                    ylabel = 'Price'
                
                ax.plot(price_data.index, price_data.values, label=label, linewidth=1.5)
                
                if not title:
                    if normalize:
                        title = f"Normalized Price Chart - {price_column.title()}"
                    else:
                        title = f"Price Chart - {price_column.title()}"
            
            # Handle multiple DataFrames (dict)
            elif isinstance(data, dict):
                symbols = list(data.keys())
                
                # Set ylabel based on normalize flag
                if normalize:
                    ylabel = f'Normalized Price (Base={base_value})'
                else:
                    ylabel = 'Price'
                
                for symbol in symbols:
                    df = data[symbol]
                    if price_column not in df.columns:
                        self.logger.warning(f"Column '{price_column}' not found for {symbol}, skipping")
                        continue
                    
                    price_data = df[price_column]
                    
                    if normalize:
                        price_data = (price_data / price_data.iloc[0]) * base_value
                    
                    ax.plot(price_data.index, price_data.values, label=symbol, linewidth=1.5)
                
                if not title:
                    if normalize:
                        title = "Normalized Price Comparison Chart"
                    else:
                        title = "Price Comparison Chart"
            
            else:
                raise ValueError("Data must be a pandas DataFrame or dict of DataFrames")
            
            ax.set_xlabel('Date', fontsize=10)
            ax.set_ylabel(ylabel, fontsize=10)
            ax.set_title(title, fontsize=12, fontweight='bold')
            ax.legend(loc='best')
            ax.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                self.logger.info(f"Chart saved to {save_path}")
            
            if show:
                plt.show()
            
            return fig
            
        except Exception as e:
            self.logger.info(f"Error generating price chart: {str(e)}")
            raise
    
    def plot_signals(
        self,
        data: pd.DataFrame,
        signals: pd.Series,
        indicators: Optional[Dict[str, pd.Series]] = None,
        price_column: str = 'Close',
        title: Optional[str] = None,
        figsize: tuple = (14, 8),
        show: bool = True,
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Plot price chart with technical indicators and trading signals.
        
        Args:
            data: DataFrame with price data
            signals: Series with trading signals (1=buy, -1=sell, 0=hold)
            indicators: Dictionary of indicator Series to plot (e.g., {'SMA20': sma_series, 'BB_upper': bb_upper})
            price_column: Column name for price (default: 'Close')
            title: Chart title
            figsize: Figure size tuple (width, height)
            show: Whether to display the chart
            save_path: Optional path to save the chart
            
        Returns:
            matplotlib Figure object
            
        Example:
            >>> # Plot with Bollinger Bands and signals
            >>> bands = indicators.bollinger_bands(data['Close'])
            >>> signals = generator.bollinger_bands_signals(data)
            >>> chart.plot_signals(
            ...     data=data,
            ...     signals=signals,
            ...     indicators={'BB_upper': bands['upper'], 
            ...                 'BB_middle': bands['middle'],
            ...                 'BB_lower': bands['lower']}
            ... )
        """
        try:
            self.logger.info("Generating signal chart with price and indicators")
            
            if price_column not in data.columns:
                raise ValueError(f"Column '{price_column}' not found in data")
            
            if len(data) != len(signals):
                raise ValueError("Data and signals must have the same length")
            
            if not data.index.equals(signals.index):
                # Align indices if they don't match
                signals = signals.reindex(data.index)
                self.logger.info("Aligned signal indices with data indices")
            
            # Create figure with subplots
            # Main plot for price and indicators, secondary plot for signal timeline
            fig, axes = plt.subplots(2, 1, figsize=figsize, height_ratios=[3, 1])
            ax_price = axes[0]
            ax_indicator = axes[1]
            
            price_data = data[price_column]
            
            # Plot price
            ax_price.plot(price_data.index, price_data.values, 
                         label='Price', linewidth=1.5, color='black', alpha=0.8)
            
            # Plot indicators on price chart
            if indicators:
                colors = plt.cm.tab10(range(len(indicators)))
                for i, (name, indicator_series) in enumerate(indicators.items()):
                    if len(indicator_series) != len(data):
                        # Try to align indices
                        indicator_series = indicator_series.reindex(data.index)
                    
                    ax_price.plot(indicator_series.index, indicator_series.values,
                                 label=name, linewidth=1.2, alpha=0.7, 
                                 color=colors[i % len(colors)])
            
            # Plot buy signals (green upward arrow)
            buy_signals = signals == 1
            if buy_signals.any():
                buy_dates = price_data.index[buy_signals]
                buy_prices = price_data[buy_signals]
                ax_price.scatter(buy_dates, buy_prices, 
                               marker='^', s=100, color='green', 
                               label='Buy Signal', zorder=5, alpha=0.8)
                # Add small upward arrows
                for date, price in zip(buy_dates, buy_prices):
                    ax_price.annotate('', xy=(date, price), 
                                    xytext=(date, price * 0.98),
                                    arrowprops=dict(arrowstyle='->', 
                                                  color='green', lw=1.5))
            
            # Plot sell signals (red downward arrow)
            sell_signals = signals == -1
            if sell_signals.any():
                sell_dates = price_data.index[sell_signals]
                sell_prices = price_data[sell_signals]
                ax_price.scatter(sell_dates, sell_prices, 
                               marker='v', s=100, color='red', 
                               label='Sell Signal', zorder=5, alpha=0.8)
                # Add small downward arrows
                for date, price in zip(sell_dates, sell_prices):
                    ax_price.annotate('', xy=(date, price), 
                                    xytext=(date, price * 1.02),
                                    arrowprops=dict(arrowstyle='->', 
                                                  color='red', lw=1.5))
            
            ax_price.set_xlabel('Date', fontsize=10)
            ax_price.set_ylabel('Price', fontsize=10)
            if not title:
                title = f"Trading Signals Chart - {price_column}"
            ax_price.set_title(title, fontsize=12, fontweight='bold')
            ax_price.legend(loc='best', fontsize=9)
            ax_price.grid(True, alpha=0.3)
            ax_price.tick_params(axis='x', rotation=45)
            
            # Plot signal timeline on separate axis
            signal_values = signals.astype(float)
            signal_values[signal_values == 0] = None
            ax_indicator.plot(signal_values.index, signal_values.values,
                            marker='o', markersize=3, linestyle='-', linewidth=0.5, alpha=0.5)
            ax_indicator.axhline(y=0, color='gray', linestyle='--', linewidth=0.5, alpha=0.5)
            ax_indicator.fill_between(signal_values.index, 0, signal_values.values,
                                    where=(signal_values > 0), 
                                    color='green', alpha=0.2, label='Buy Zone')
            ax_indicator.fill_between(signal_values.index, 0, signal_values.values,
                                    where=(signal_values < 0), 
                                    color='red', alpha=0.2, label='Sell Zone')
            ax_indicator.set_xlabel('Date', fontsize=9)
            ax_indicator.set_ylabel('Signal', fontsize=9)
            ax_indicator.set_title('Signal Timeline', fontsize=10)
            ax_indicator.set_ylim(-1.5, 1.5)
            ax_indicator.set_yticks([-1, 0, 1])
            ax_indicator.set_yticklabels(['Sell', 'Hold', 'Buy'])
            ax_indicator.grid(True, alpha=0.3)
            ax_indicator.tick_params(axis='x', rotation=45)
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                self.logger.info(f"Chart saved to {save_path}")
            
            if show:
                plt.show()
            
            return fig
            
        except Exception as e:
            self.logger.info(f"Error generating signal chart: {str(e)}")
            raise

