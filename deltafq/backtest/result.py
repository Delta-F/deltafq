"""回测结果"""

import pandas as pd
from typing import Dict, Any, List


class BacktestResult:
    """回测结果类"""
    
    def __init__(
        self,
        initial_cash: float,
        data: pd.DataFrame,
        signals: List[Dict]
    ):
        self.initial_cash = initial_cash
        self.data = data
        self.signals = signals
        
    def summary(self) -> Dict[str, Any]:
        """生成回测摘要
        
        Returns:
            包含各项指标的字典
        """
        return {
            'initial_cash': self.initial_cash,
            'total_signals': len(self.signals),
            'data_length': len(self.data),
        }
    
    def plot(self) -> None:
        """绘制回测结果"""
        try:
            import matplotlib.pyplot as plt
            plt.figure(figsize=(12, 6))
            plt.plot(self.data['close'])
            plt.title('Price Chart')
            plt.xlabel('Date')
            plt.ylabel('Price')
            plt.grid(True)
            plt.show()
        except ImportError:
            print("需要matplotlib: pip install matplotlib")

