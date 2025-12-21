"""
Example: fetch fund net value data using DataFetcher.
"""

import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from deltafq.data import DataFetcher


def main() -> None:
    fetcher = DataFetcher()
    
    # Example 1: Fetch a single page
    print("=" * 60)
    print("Example 1: Fetch single page data")
    print("=" * 60)
    data_single = fetcher.fetch_fund_data(code="018956", page=1)
    print(f"Fetched {len(data_single)} records from page 1")
    print(data_single.head())
    print()

    # Example 2: Fetch all pages (this may take some time)
    print("=" * 60)
    print("Example 2: Fetch all pages data")
    print("=" * 60)
    print("Note: This will fetch all pages, which may take some time...")
    data_all = fetcher.fetch_fund_data(code="018956", page=None)
    print(f"Fetched {len(data_all)} records in total")
    print(f"Date range: {data_all['净值日期'].min()} to {data_all['净值日期'].max()}")
    print(data_all.head())
    print(data_all.tail())


if __name__ == "__main__":
    main()

