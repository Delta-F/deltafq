"""网格搜索优化器"""

from typing import Dict, List, Any, Callable
import itertools


class GridSearchOptimizer:
    """网格搜索参数优化器"""
    
    def __init__(self):
        self.results = []
        
    def optimize(
        self,
        param_grid: Dict[str, List[Any]],
        objective_func: Callable
    ) -> Dict[str, Any]:
        """执行网格搜索
        
        Args:
            param_grid: 参数网格
            objective_func: 目标函数
            
        Returns:
            最优参数组合
        """
        keys = param_grid.keys()
        values = param_grid.values()
        best_score = float('-inf')
        best_params = None
        
        for combination in itertools.product(*values):
            params = dict(zip(keys, combination))
            score = objective_func(params)
            self.results.append({'params': params, 'score': score})
            if score > best_score:
                best_score = score
                best_params = params
        
        return best_params

