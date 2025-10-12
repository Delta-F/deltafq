"""
Data validation for DeltaFQ.
"""

import pandas as pd
from typing import List, Optional
from ..core.base import BaseComponent
from ..core.exceptions import DataError


class DataValidator(BaseComponent):
    """Data validator for ensuring data quality."""
    
    def initialize(self) -> bool:
        """Initialize the data validator."""
        self.logger.info("Initializing data validator")
        return True
    
    def validate_price_data(self, data: pd.DataFrame) -> bool:
        """Validate price data structure and values."""
        required_columns = ['open', 'high', 'low', 'close']
        
        # Check required columns
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            raise DataError(f"Missing required columns: {missing_columns}")
        
        # Check for negative prices
        for col in required_columns:
            if (data[col] <= 0).any():
                raise DataError(f"Found non-positive values in {col} column")
        
        # Check high >= low
        if (data['high'] < data['low']).any():
            raise DataError("Found high < low values")
        
        self.logger.info("Price data validation passed")
        return True
    
    def validate_data_continuity(self, data: pd.DataFrame, date_column: str = 'date') -> bool:
        """Validate data continuity."""
        if date_column not in data.columns:
            raise DataError(f"Date column '{date_column}' not found")
        
        # Check for duplicate dates
        if data[date_column].duplicated().any():
            raise DataError("Found duplicate dates in data")
        
        self.logger.info("Data continuity validation passed")
        return True

