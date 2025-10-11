"""波动率类指标"""

import pandas as pd


def BOLL(data: pd.Series, period: int = 20, std_dev: float = 2.0) -> pd.DataFrame:
    """布林带
    
    Args:
        data: 价格序列
        period: 周期
        std_dev: 标准差倍数
        
    Returns:
        包含upper、middle、lower的DataFrame
    """
    middle = data.rolling(window=period).mean()
    std = data.rolling(window=period).std()
    upper = middle + std_dev * std
    lower = middle - std_dev * std
    
    return pd.DataFrame({
        'upper': upper,
        'middle': middle,
        'lower': lower
    })

