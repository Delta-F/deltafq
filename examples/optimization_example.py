"""参数优化示例

使用网格搜索寻找双均线策略的最佳参数组合。
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import deltafq as dfq


def objective_function(params):
    """目标函数"""
    short_window = params['short_window']
    long_window = params['long_window']
    
    data = dfq.data.get_stock_daily('000001.SZ', start='2020-01-01', end='2023-12-31')
    data[f'ma{short_window}'] = dfq.indicators.SMA(data['close'], short_window)
    data[f'ma{long_window}'] = dfq.indicators.SMA(data['close'], long_window)
    
    class MAStrategy(dfq.strategy.Strategy):
        def on_bar(self, bar):
            ma_short = getattr(bar, f'ma{short_window}', None)
            ma_long = getattr(bar, f'ma{long_window}', None)
            if ma_short and ma_long:
                if ma_short > ma_long:
                    self.buy()
                elif ma_short < ma_long:
                    self.sell()
    
    engine = dfq.backtest.BacktestEngine()
    result = engine.run(data, MAStrategy())
    return result.summary()['total_signals']


def main():
    print("开始参数优化...")
    
    param_grid = {
        'short_window': [5, 10, 15],
        'long_window': [20, 30, 60],
    }
    
    optimizer = dfq.optimization.GridSearchOptimizer()
    best_params = optimizer.optimize(param_grid, objective_function)
    
    print("\n优化完成!")
    print("-" * 50)
    print(f"最佳参数: {best_params}")
    print(f"\n所有结果:")
    for result in optimizer.results:
        print(f"参数: {result['params']}, 得分: {result['score']}")


if __name__ == '__main__':
    main()

