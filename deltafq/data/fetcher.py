"""
Data fetching interfaces for DeltaFQ.
"""

import pandas as pd
import yfinance as yf
import re
import requests
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
    
    def fetch_fund_data(self, code: str, page: Optional[int] = None) -> pd.DataFrame:
        """Fetch fund net value data from East Money API."""
        base_url = "https://fundf10.eastmoney.com/F10DataApi.aspx"
        base_params = {"type": "lsjz", "per": 20, "code": code}
        
        # Internal function to fetch a single page
        def _get_page(p: int) -> pd.DataFrame:
            params = {**base_params, "page": p}
            resp = requests.get(base_url, params=params)
            self.logger.info(f"Fetching page {p} for fund {code}")
            match = re.search(r'content:"([^"]+)"', resp.text, re.DOTALL)
            if not match:
                raise ValueError(f"Unable to parse API response (page={p})")
            html_content = match.group(1).replace('\\r\\n', '\n').replace('\\"', '"')
            dfs = pd.read_html(html_content)
            return dfs[0] if dfs else pd.DataFrame()
        
        try:
            # If page is None, fetch all pages
            if page is None:
                # First, get page 1 to determine total pages
                params = {**base_params, "page": 1}
                resp = requests.get(base_url, params=params)
                match = re.search(r'pages:(\d+)', resp.text)
                max_pages = int(match.group(1)) if match else 1
                
                self.logger.info(f"Fetching all pages for fund {code} (total pages: {max_pages})")
                
                # Fetch all pages
                all_dfs = [_get_page(p) for p in range(1, max_pages + 1)]
                result = pd.concat(all_dfs, ignore_index=True)
                self.logger.info(f"Fetched {len(result)} records from {max_pages} pages")
                return result
            
            # Fetch specified page
            self.logger.info(f"Fetching page {page} for fund {code}")
            return _get_page(page)
        except Exception as e:
            raise RuntimeError(f"Failed to fetch fund data for {code}: {str(e)}") from e

