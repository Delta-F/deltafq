"""DeltaFQ - 专业的Python量化交易库

一个面向量化策略开发者和量化研究人员的完整工具链。
"""

__version__ = "0.1.0"
__author__ = "DeltaFQ Team"

# 导入主要模块
from deltafq import data
from deltafq import indicators
from deltafq import strategy
from deltafq import backtest
from deltafq import risk
from deltafq import performance
from deltafq import optimization
from deltafq import trade
from deltafq import utils

__all__ = [
    "data",
    "indicators",
    "strategy",
    "backtest",
    "risk",
    "performance",
    "optimization",
    "trade",
    "utils",
]

