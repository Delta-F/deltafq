"""
Example: fetch fund net value data using DataFetcher.
"""

import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from deltafq.data import DataFetcher


def fetch_watchlist_funds(output_dir: str = "fund_data") -> None:
    """
    Fetch data for watchlist funds and save to CSV files.
    """
    # 自选基金列表
    watchlist_codes = ["050025", "270042", "160119", "510300", "000071", "510880"]
    
    fetcher = DataFetcher()
    
    print("=" * 60)
    print("Fetching watchlist funds data")
    print("=" * 60)
    print(f"Watchlist funds: {', '.join(watchlist_codes)}")
    
    for code in watchlist_codes:
        try:
            data = fetcher.fetch_fund_data(code=code, page=None)
            
            if len(data) > 0:
                # 保存到CSV文件
                csv_filename = f"fund_{code}.csv"
                data.to_csv(csv_filename, index=False, encoding='utf-8-sig')
                print(f"  ✓ Saved {len(data)} records to {csv_filename}")
                print(f"  Date range: {data['净值日期'].min()} to {data['净值日期'].max()}")
            else:
                print(f"  ✗ No data found for fund {code}")
        except Exception as e:
            print(f"  ✗ Error fetching data for fund {code}: {str(e)}")
        print()
    
    print("=" * 60)
    print("All watchlist funds data fetched and saved!")
    print("=" * 60)


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
    print()

    # Example 3: Fetch watchlist funds and save to CSV
    print("=" * 60)
    print("Example 3: Fetch watchlist funds and save to CSV")
    print("=" * 60)
    fetch_watchlist_funds(output_dir="fund_data")


if __name__ == "__main__":
    # main()
    fetch_watchlist_funds()
