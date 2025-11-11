"""
Data fetching interfaces for DeltaFQ.
"""

import pandas as pd
import yfinance as yf
from typing import List, Optional
from ..core.base import BaseComponent
from ..core.exceptions import DataError
from .cleaner import DataCleaner
import warnings
warnings.filterwarnings('ignore')


class DataFetcher(BaseComponent):
    """Data fetcher for various sources."""
    
    def __init__(self, source: str = "yahoo", **kwargs):
        """Initialize data fetcher."""
        super().__init__(**kwargs)
        self.source = source
        self.cleaner = None
    
    def initialize(self) -> bool:
        """Initialize the data fetcher."""
        self.logger.info(f"Initializing data fetcher with source: {self.source}")
        return True
    
    def _ensure_cleaner(self):
        """Lazy initialization of cleaner."""
        if self.cleaner is None:
            self.cleaner = DataCleaner()
            # self.cleaner.initialize()
    
    def fetch_data(self, symbol: str, start_date: str, end_date: str = None, clean: bool = False) -> pd.DataFrame:
        """Fetch stock data for given symbol."""
        try:
            self.logger.info(f"Fetching data for {symbol} from {start_date} to {end_date}")
            
            data = yf.download(symbol, start=start_date, end=end_date, progress=False)
            data = data.droplevel(level=1, axis=1)  # Drop the multi-index level
            
            if clean:
                self._ensure_cleaner()
                data = self.cleaner.dropna(data)
                
            return data
        except Exception as e:
            raise DataError(f"Failed to fetch data for {symbol}: {str(e)}")
    
    def fetch_data_multiple(self, symbols: List[str], start_date: str, end_date: str = None, clean: bool = False) -> dict:
        """Fetch data for multiple symbols."""
        data_dict = {}
        for symbol in symbols:
            data_dict[symbol] = self.fetch_data(symbol, start_date, end_date, clean)
        return data_dict


