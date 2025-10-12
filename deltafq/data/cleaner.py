"""
Data cleaning utilities for DeltaFQ.
"""

import pandas as pd
from typing import Optional
from ..core.base import BaseComponent


class DataCleaner(BaseComponent):
    """Data cleaning utilities."""
    
    def initialize(self) -> bool:
        """Initialize the data cleaner."""
        self.logger.info("Initializing data cleaner")
        return True
    
    def clean_price_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Clean price data by removing invalid values."""
        # Remove rows with NaN values
        cleaned_data = data.dropna()
        
        # Remove rows with zero or negative prices
        price_columns = ['open', 'high', 'low', 'close']
        for col in price_columns:
            if col in cleaned_data.columns:
                cleaned_data = cleaned_data[cleaned_data[col] > 0]
        
        self.logger.info(f"Cleaned data: {len(data)} -> {len(cleaned_data)} rows")
        return cleaned_data
    
    def fill_missing_data(self, data: pd.DataFrame, method: str = "forward") -> pd.DataFrame:
        """Fill missing data using specified method."""
        if method == "forward":
            return data.fillna(method='ffill')
        elif method == "backward":
            return data.fillna(method='bfill')
        else:
            return data.fillna(0)

