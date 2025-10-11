"""绩效指标计算"""

import pandas as pd
import numpy as np


def calculate_annual_return(returns: pd.Series) -> float:
    """计算年化收益率
    
    Args:
        returns: 收益率序列
        
    Returns:
        年化收益率
    """
    total_return = (1 + returns).prod() - 1
    n_years = len(returns) / 252
    annual_return = (1 + total_return) ** (1 / n_years) - 1
    return annual_return


def calculate_sharpe_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.03
) -> float:
    """计算夏普比率
    
    Args:
        returns: 收益率序列
        risk_free_rate: 无风险利率
        
    Returns:
        夏普比率
    """
    excess_returns = returns - risk_free_rate / 252
    return np.sqrt(252) * excess_returns.mean() / excess_returns.std()

