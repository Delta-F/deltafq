"""
Minimal example: fetch fund historical data from EastMoney.
"""

import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from deltafq.data import DataFetcher


def main() -> None:
    fetcher = DataFetcher()
    
    # Test fetching fund data (limit to 3 pages for quick test)
    fund_code = "000001"
    print(f"Fetching fund data for {fund_code} (max 3 pages)...")
    fund_data = fetcher.fetch_fund(fund_code=fund_code, max_page=2)
    
    print(f"\nTotal records: {len(fund_data)}")
    print("\nFirst 10 records:")
    print(fund_data.head(10))
    print("\nLast 10 records:")
    print(fund_data.tail(10))
    print("\nData info:")
    print(fund_data.info())
    print("\nData columns:")
    print(fund_data.columns.tolist())


if __name__ == "__main__":
    main()

