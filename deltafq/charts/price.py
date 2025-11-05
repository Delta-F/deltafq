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