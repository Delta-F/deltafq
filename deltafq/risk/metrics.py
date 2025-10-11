"""风险指标计算"""

import pandas as pd
import numpy as np


def calculate_max_drawdown(returns: pd.Series) -> float:
    """计算最大回撤
    
    Args:
        returns: 收益率序列
        
    Returns:
        最大回撤值
    """
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.expanding().max()
    drawdown = (cumulative - running_max) / running_max
    return drawdown.min()


def calculate_var(returns: pd.Series, confidence: float = 0.95) -> float:
    """计算VaR (Value at Risk)
    
    Args:
        returns: 收益率序列
        confidence: 置信度
        
    Returns:
        VaR值
    """
    return returns.quantile(1 - confidence)

