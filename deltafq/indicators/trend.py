"""趋势类指标"""

import pandas as pd
from typing import Union


def SMA(data: Union[pd.Series, pd.DataFrame], period: int) -> pd.Series:
    """简单移动平均线
    
    Args:
        data: 价格序列
        period: 周期
        
    Returns:
        SMA序列
    """
    return data.rolling(window=period).mean()


def EMA(data: Union[pd.Series, pd.DataFrame], period: int) -> pd.Series:
    """指数移动平均线
    
    Args:
        data: 价格序列
        period: 周期
        
    Returns:
        EMA序列
    """
    return data.ewm(span=period, adjust=False).mean()


def MACD(
    data: pd.Series,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9
) -> pd.DataFrame:
    """MACD指标
    
    Args:
        data: 价格序列
        fast_period: 快线周期
        slow_period: 慢线周期
        signal_period: 信号线周期
        
    Returns:
        包含DIF、DEA、MACD的DataFrame
    """
    fast = EMA(data, fast_period)
    slow = EMA(data, slow_period)
    dif = fast - slow
    dea = EMA(dif, signal_period)
    macd = (dif - dea) * 2
    
    return pd.DataFrame({
        'dif': dif,
        'dea': dea,
        'macd': macd
    })

