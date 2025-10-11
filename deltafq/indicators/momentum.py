"""动量类指标"""

import pandas as pd


def RSI(data: pd.Series, period: int = 14) -> pd.Series:
    """相对强弱指标
    
    Args:
        data: 价格序列
        period: 周期
        
    Returns:
        RSI序列
    """
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

