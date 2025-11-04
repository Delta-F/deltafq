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
    
    def dropna(self, data: pd.DataFrame) -> pd.DataFrame:
        """Remove rows with NaN values."""
        cleaned_data = data.dropna()
        self.logger.info(f"Dropped NaN rows: {len(data)} -> {len(cleaned_data)} rows")
        return cleaned_data
    
    def fillna(self, data: pd.DataFrame, method: str = "forward") -> pd.DataFrame:
        """Fill missing data using specified method."""
        na_count_before = data.isna().sum().sum()
        
        if method == "forward":
            filled_data = data.fillna(method='ffill')
        elif method == "backward":
            filled_data = data.fillna(method='bfill')
        else:
            filled_data = data.fillna(0)
        
        na_count_after = filled_data.isna().sum().sum()
        self.logger.info(f"Filled NaN: {na_count_before} -> {na_count_after} (method: {method})")
        
        return filled_data

