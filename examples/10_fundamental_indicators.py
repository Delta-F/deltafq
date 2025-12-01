"""
Minimal example: test fundamental indicators with DeltaFQ.
"""

import os
import sys

import pandas as pd
import yfinance as yf

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from deltafq.data import DataFetcher
from deltafq.indicators import FundamentalIndicators


def main() -> None:
    symbol = "AAPL"
    
    # Fetch price data
    fetcher = DataFetcher()
    data = fetcher.fetch_data(symbol=symbol, start_date="2024-01-01", end_date="2024-12-31", clean=True)
    price = data["Close"]
    
    # Fetch fundamental data from yfinance
    ticker = yf.Ticker(symbol)
    info = ticker.info
    quarterly_financials = ticker.quarterly_financials
    quarterly_balance = ticker.quarterly_balance_sheet
    
    # Get fundamental data and align with price index
    index = price.index
    
    # EPS TTM
    eps_ttm = pd.Series(info.get('trailingEps', 0), index=index)
    
    # Book Value Per Share
    bvps = pd.Series(info.get('bookValue', 0), index=index)
    
    # Market Cap
    market_cap = pd.Series(info.get('marketCap', 0), index=index)
    
    # Revenue (latest quarter)
    revenue_value = quarterly_financials.loc['Total Revenue'].iloc[0] if not quarterly_financials.empty and 'Total Revenue' in quarterly_financials.index else 0
    revenue = pd.Series(revenue_value, index=index)
    
    # Net Income (latest quarter)
    net_income_value = quarterly_financials.loc['Net Income'].iloc[0] if not quarterly_financials.empty and 'Net Income' in quarterly_financials.index else 0
    net_income = pd.Series(net_income_value, index=index)
    
    # Gross Profit (latest quarter)
    gross_profit_value = quarterly_financials.loc['Gross Profit'].iloc[0] if not quarterly_financials.empty and 'Gross Profit' in quarterly_financials.index else 0
    gross_profit = pd.Series(gross_profit_value, index=index)
    
    # Total Assets (latest quarter)
    total_assets_value = quarterly_balance.loc['Total Assets'].iloc[0] if not quarterly_balance.empty and 'Total Assets' in quarterly_balance.index else 0
    total_assets = pd.Series(total_assets_value, index=index)
    
    # Shareholders Equity (latest quarter)
    equity_fields = ['Stockholders Equity', 'Total Stockholder Equity', 'Shareholders Equity']
    equity_value = 0
    if not quarterly_balance.empty:
        for field in equity_fields:
            if field in quarterly_balance.index:
                equity_value = quarterly_balance.loc[field].iloc[0]
                break
    shareholders_equity = pd.Series(equity_value, index=index)
    
    # Initialize indicators
    indicators = FundamentalIndicators()
    
    # Calculate indicators
    pe = indicators.pe(price, eps_ttm)
    pb = indicators.pb(price, bvps)
    ps = indicators.ps(market_cap, revenue)
    roa = indicators.roa(net_income, total_assets)
    roe = indicators.roe(net_income, shareholders_equity)
    gross_margin = indicators.gross_margin(gross_profit, revenue)
    
    # Print results
    print("Fundamental Indicators:")
    print(f"PE: {pe.iloc[-1]:.2f}")
    print(f"PB: {pb.iloc[-1]:.2f}")
    print(f"PS: {ps.iloc[-1]:.2f}")
    print(f"ROA: {roa.iloc[-1]:.4f}")
    print(f"ROE: {roe.iloc[-1]:.4f}")
    print(f"Gross Margin: {gross_margin.iloc[-1]:.4f}")



if __name__ == "__main__":
    main()
