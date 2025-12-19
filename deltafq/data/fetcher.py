"""
Data fetching interfaces for DeltaFQ.
"""

import pandas as pd
import yfinance as yf
import requests
import re
import time
from typing import List, Optional, Dict, Any
from io import StringIO
from bs4 import BeautifulSoup
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
        return {symbol: self.fetch_data(symbol, start_date, end_date, clean) for symbol in symbols}
    
    def fetch_fund(self, fund_code: str, max_page: Optional[int] = None) -> pd.DataFrame:
        """Fetch fund historical net value data from EastMoney."""
        fund_code = str(fund_code).zfill(6)
        self.logger.info(f"Fetching fund data for {fund_code}")
        
        try:
            def _get_url(page: int) -> str:
                return f'https://fundf10.eastmoney.com/F10DataApi.aspx?type=lsjz&per=20&code={fund_code}&page={page}'
            
            def _extract_html(s: str) -> str:
                start = s.find('content:"') + 9
                return s[start:s.find('",records:', start)]
            
            def _parse_page(content: str) -> pd.DataFrame:
                apidata = content.split('var apidata=')[1].strip().rstrip(';')
                html = _extract_html(apidata)
                table = BeautifulSoup(html, 'html.parser').find('table')
                return pd.read_html(StringIO(str(table)))[0]
            
            # Get total pages and first page data
            content = requests.get(_get_url(1), timeout=30).text
            apidata = content.split('var apidata=')[1].strip().rstrip(';')
            total_pages = int(re.search(r'pages:(\d+)', apidata).group(1))
            pages_to_fetch = min(max_page, total_pages) if max_page else total_pages
            
            # Fetch all pages (reuse first page data)
            dfs = [_parse_page(content)]
            for page in range(2, pages_to_fetch + 1):
                self.logger.debug(f"Fetching {fund_code} page {page}/{pages_to_fetch}")
                dfs.append(_parse_page(requests.get(_get_url(page), timeout=30).text))
                time.sleep(0.2)
            
            # Merge and clean data
            result = pd.concat(dfs, ignore_index=True)
            result = result.drop_duplicates(subset=['净值日期'], keep='first')
            result['净值日期'] = pd.to_datetime(result['净值日期'], errors='coerce')
            result = result.sort_values('净值日期', ascending=True)
            
            self.logger.info(f"Successfully fetched {len(result)} records for fund {fund_code}")
            return result
            
        except Exception as e:
            raise RuntimeError(f"Failed to fetch fund data for {fund_code}: {str(e)}") from e


