"""
Minimal example: fetch Yahoo Finance data with the local DataFetcher.
"""

import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from deltafq.data import DataFetcher

# 国内用户如遇到 too many requests 或 possibly delisted 错误，需使用代理设置
# proxy = 'http://127.0.0.1:7897' # 具体端口号请查看vpn代理软件
# os.environ['HTTP_PROXY'] = proxy 
# os.environ['HTTPS_PROXY'] = proxy

def main() -> None:
    fetcher = DataFetcher() # default source="yahoo"
    data = fetcher.fetch_data(symbol="AAPL", start_date="2024-01-01", end_date="2024-01-10")
    print(data.head())


if __name__ == "__main__":
    main()

