"""时间相关工具函数"""

import pandas as pd
from datetime import datetime
from typing import List


def is_trading_day(date: datetime) -> bool:
    """判断是否为交易日
    
    Args:
        date: 日期
        
    Returns:
        是否为交易日
    """
    return date.weekday() < 5


def get_trading_dates(start: str, end: str) -> List[datetime]:
    """获取交易日列表
    
    Args:
        start: 开始日期
        end: 结束日期
        
    Returns:
        交易日列表
    """
    dates = pd.date_range(start=start, end=end, freq='B')
    return dates.tolist()

