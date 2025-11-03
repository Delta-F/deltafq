"""
Data fetching interfaces for DeltaFQ.
"""

import pandas as pd
import yfinance as yf
from typing import List, Optional
from ..core.base import BaseComponent
from ..core.exceptions import DataError
from .cleaner import DataCleaner


class DataFetcher(BaseComponent):
    """Data fetcher for various sources."""
    
    def __init__(self, source: str = "yahoo", auto_clean: bool = False, **kwargs):
        """Initialize data fetcher."""
        super().__init__(**kwargs)
        self.source = source
        self.auto_clean = auto_clean
        if auto_clean:
            self.cleaner = DataCleaner(**kwargs)
    
    def initialize(self) -> bool:
        """Initialize the data fetcher."""
        self.logger.info(f"Initializing data fetcher with source: {self.source}")
        if self.auto_clean and hasattr(self, 'cleaner'):
            self.cleaner.initialize()
        return True
    
    def fetch_stock_data(self, symbol: str, start_date: str, end_date: str = None, clean: Optional[bool] = None) -> pd.DataFrame:
        """Fetch stock data for given symbol."""
        try:
            self.logger.info(f"Fetching data for {symbol} from {start_date} to {end_date}")
            
            data = yf.download(symbol, start=start_date, end=end_date, progress=False)
            data = data.droplevel(level=1, axis=1)  # Drop the multi-index level
            
            # 判断是否需要清洗
            should_clean = clean if clean is not None else self.auto_clean
            if should_clean:
                if not hasattr(self, 'cleaner'):
                    self.cleaner = DataCleaner()
                    self.cleaner.initialize()
                data = self.cleaner.clean_price_data(data)
                
            return data
        except Exception as e:
            raise DataError(f"Failed to fetch data for {symbol}: {str(e)}")
    
    def fetch_multiple_symbols(self, symbols: List[str], start_date: str, end_date: str = None, clean: Optional[bool] = None) -> dict:
        """Fetch data for multiple symbols."""
        data_dict = {}
        for symbol in symbols:
            data_dict[symbol] = self.fetch_stock_data(symbol, start_date, end_date, clean)
        return data_dict


