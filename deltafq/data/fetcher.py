"""
Data fetching interfaces for DeltaFQ.
"""

import pandas as pd
import yfinance as yf
from typing import List, Optional, Dict, Any
from ..core.base import BaseComponent
from .cleaner import DataCleaner
import warnings
warnings.filterwarnings('ignore')


class DataFetcher(BaseComponent):
    """Data fetcher for various sources."""
    
    def __init__(self, source: str = "yahoo", **kwargs: Any) -> None:
        """Initialize data fetcher."""
        super().__init__(**kwargs)
        self.source = source
        self.cleaner = None
        self.logger.info(f"Initializing data fetcher with source: {self.source}")
    
    def _ensure_cleaner(self) -> None:
        """Lazy initialization of cleaner."""
        if self.cleaner is None:
            self.cleaner = DataCleaner()
    
    def fetch_data(self, symbol: str, start_date: str, end_date: Optional[str] = None, clean: bool = False) -> pd.DataFrame:
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
            raise RuntimeError(f"Failed to fetch data for {symbol}: {str(e)}") from e
    
    def fetch_data_multiple(self, symbols: List[str], start_date: str, end_date: Optional[str] = None, clean: bool = False) -> Dict[str, pd.DataFrame]:
        """Fetch data for multiple symbols."""
        data_dict = {}
        for symbol in symbols:
            data_dict[symbol] = self.fetch_data(symbol, start_date, end_date, clean)
        return data_dict


