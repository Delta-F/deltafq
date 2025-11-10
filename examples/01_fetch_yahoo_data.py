"""
Minimal example: fetch Yahoo Finance data with the local DataFetcher.
"""

import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from deltafq.data import DataFetcher


def main() -> None:
    fetcher = DataFetcher(source="yahoo")
    data = fetcher.fetch_data(symbol="AAPL", start_date="2024-01-01", end_date="2024-01-10")
    print(data.head())


if __name__ == "__main__":
    main()

