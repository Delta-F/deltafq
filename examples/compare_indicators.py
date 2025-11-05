"""
Compare TechnicalIndicators and TalibIndicators calculation results.
"""

import sys
import os

# Add project root to sys.path to use local DeltaFQ modules.
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pandas as pd
import numpy as np
from deltafq.data.fetcher import DataFetcher
from deltafq.indicators import TechnicalIndicators, TalibIndicators
import warnings
warnings.filterwarnings('ignore')


def compare_results(series1: pd.Series, series2: pd.Series, name: str):
    """Compare two series and show statistics."""
    # Align indices
    aligned1, aligned2 = series1.align(series2, join='inner')
    
    # Remove NaN values for comparison
    mask = aligned1.notna() & aligned2.notna()
    aligned1 = aligned1[mask]
    aligned2 = aligned2[mask]
    
    # Calculate differences
    diff = aligned1 - aligned2
    abs_diff = np.abs(diff)
    rel_diff = (abs_diff / np.abs(aligned2)) * 100
    
    print(f"\n{name} Comparison:")
    print(f"  Valid values: {len(aligned1)}")
    print(f"  Mean difference: {diff.mean():.6f}")
    print(f"  Max absolute difference: {abs_diff.max():.6f}")
    print(f"  Mean relative difference: {rel_diff.mean():.4f}%")
    print(f"  Max relative difference: {rel_diff.max():.4f}%")
    
    # Show first few differences
    print(f"  First 5 differences:")
    for i in range(min(5, len(diff))):
        print(f"    [{aligned1.index[i]}] Custom: {aligned1.iloc[i]:.6f}, TA-Lib: {aligned2.iloc[i]:.6f}, Diff: {diff.iloc[i]:.6f}")


def compare_dataframes(df1: pd.DataFrame, df2: pd.DataFrame, name: str):
    """Compare two dataframes column by column."""
    for col in df1.columns:
        if col in df2.columns:
            compare_results(df1[col], df2[col], f"{name} - {col}")


def main():
    print("=" * 60)
    print("Technical Indicators Comparison: Custom vs TA-Lib")
    print("=" * 60)
    
    # Initialize components
    fetcher = DataFetcher()
    custom_indicators = TechnicalIndicators()
    talib_indicators = TalibIndicators()
    
    # Fetch sample data
    print("\nFetching data...")
    symbol = 'AAPL'
    start_date = '2024-10-01'
    end_date = '2024-12-31'
    
    data = fetcher.fetch_data(symbol, start_date, end_date, clean=True)
    
    # Extract price series
    close = data['Close']
    high = data['High']
    low = data['Low']
    volume = data['Volume']
    
    print("\n" + "=" * 60)
    print("Calculating Indicators (TA-Lib Compatible Methods)...")
    print("=" * 60)
    
    # 1. SMA
    print("\n1. SMA (Simple Moving Average)")
    sma_custom = custom_indicators.sma(close, period=20)
    sma_talib = talib_indicators.sma(close, period=20)
    compare_results(sma_custom, sma_talib, "SMA(20)")
    
    # 2. EMA (TA-Lib compatible)
    print("\n2. EMA (Exponential Moving Average) - TA-Lib Method")
    ema_custom = custom_indicators.ema(close, period=12, method='talib')
    ema_talib = talib_indicators.ema(close, period=12)
    compare_results(ema_custom, ema_talib, "EMA(12) - TA-Lib Method")
    
    # 3. RSI (TA-Lib compatible: RMA method)
    print("\n3. RSI (Relative Strength Index) - TA-Lib Method (RMA)")
    rsi_custom = custom_indicators.rsi(close, period=14, method='rma')
    rsi_talib = talib_indicators.rsi(close, period=14)
    compare_results(rsi_custom, rsi_talib, "RSI(14) - TA-Lib Method")
    
    # 4. KDJ (TA-Lib compatible: SMA method)
    print("\n4. KDJ (Stochastic Oscillator) - TA-Lib Method (SMA)")
    kdj_custom = custom_indicators.kdj(high, low, close, n=9, m1=3, m2=3, method='sma')
    kdj_talib = talib_indicators.kdj(high, low, close, n=9, m1=3, m2=3)
    compare_dataframes(kdj_custom, kdj_talib, "KDJ - TA-Lib Method")
    
    # 5. BOLL (TA-Lib compatible: population std)
    print("\n5. BOLL (Bollinger Bands) - TA-Lib Method (Population Std)")
    boll_custom = custom_indicators.boll(close, period=20, std_dev=2, method='population')
    boll_talib = talib_indicators.boll(close, period=20, std_dev=2)
    compare_dataframes(boll_custom, boll_talib, "BOLL - TA-Lib Method")
    
    # 6. ATR (TA-Lib compatible: RMA method)
    print("\n6. ATR (Average True Range) - TA-Lib Method (RMA)")
    atr_custom = custom_indicators.atr(high, low, close, period=14, method='rma')
    atr_talib = talib_indicators.atr(high, low, close, period=14)
    compare_results(atr_custom, atr_talib, "ATR(14) - TA-Lib Method")
    
    # 7. OBV
    print("\n7. OBV (On-Balance Volume)")
    obv_custom = custom_indicators.obv(close, volume)
    obv_talib = talib_indicators.obv(close, volume)
    compare_results(obv_custom, obv_talib, "OBV")
    
    print("\n" + "=" * 60)
    print("Comparison Complete!")   
    print("=" * 60)


if __name__ == "__main__":
    main()

