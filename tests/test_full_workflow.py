"""全流程集成测试"""

import pytest
import sys
sys.path.insert(0, '.')

import deltafq as dfq


class SimpleMAStrategy(dfq.strategy.Strategy):
    def __init__(self):
        super().__init__()
        self.position_status = None
    
    def on_bar(self, bar):
        if hasattr(bar, 'ma5') and hasattr(bar, 'ma20'):
            if bar.ma5 > bar.ma20 and self.position_status != 'long':
                self.buy()
                self.position_status = 'long'
            elif bar.ma5 < bar.ma20 and self.position_status != 'short':
                self.sell()
                self.position_status = 'short'


class TestFullWorkflow:
    
    def test_complete_workflow(self):
        print("\n[步骤1] 获取数据...")
        data = dfq.data.get_stock_daily(
            symbol='000001.SZ',
            start='2023-01-01',
            end='2023-12-31'
        )
        
        # 验证数据
        assert data is not None
        assert len(data) > 0
        assert 'close' in data.columns
        print(f"[OK] 数据获取成功: {len(data)} 条记录")
        
        print("\n[步骤2] 计算技术指标...")
        data['ma5'] = dfq.indicators.SMA(data['close'], 5)
        data['ma20'] = dfq.indicators.SMA(data['close'], 20)
        macd = dfq.indicators.MACD(data['close'])
        data = data.join(macd)
        data['rsi'] = dfq.indicators.RSI(data['close'], 14)
        boll = dfq.indicators.BOLL(data['close'], 20)
        data = data.join(boll)
        assert 'ma5' in data.columns
        assert 'ma20' in data.columns
        assert 'dif' in data.columns
        assert 'rsi' in data.columns
        assert 'upper' in data.columns
        print(f"[OK] 技术指标计算完成: {len([c for c in data.columns if c not in ['open','high','low','close','volume']])} 个指标")
        
        print("\n[步骤3] 创建交易策略...")
        strategy = SimpleMAStrategy()
        assert strategy.position == 0
        assert strategy.cash == 100000
        assert len(strategy.signals) == 0
        print("[OK] 策略创建成功: SimpleMAStrategy")
        
        print("\n[步骤4] 配置回测引擎...")
        engine = dfq.backtest.BacktestEngine(
            initial_cash=100000,
            commission=0.0003,
            slippage=0.0
        )
        
        assert engine.initial_cash == 100000
        assert engine.commission == 0.0003
        print("[OK] 回测引擎配置完成")
        
        print("\n[步骤5] 运行回测...")
        result = engine.run(data, strategy)
        assert result is not None
        assert len(strategy.signals) > 0
        print(f"[OK] 回测完成: 产生 {len(strategy.signals)} 个交易信号")
        
        print("\n[步骤6] 分析回测结果...")
        summary = result.summary()
        
        assert 'initial_cash' in summary
        assert 'total_signals' in summary
        assert 'data_length' in summary
        
        print("回测摘要:")
        for key, value in summary.items():
            print(f"  {key}: {value}")
        
        print("\n[步骤7] 计算风险指标...")
        returns = data['close'].pct_change().dropna()
        max_drawdown = dfq.risk.calculate_max_drawdown(returns)
        var_95 = dfq.risk.calculate_var(returns, confidence=0.95)
        print(f"  最大回撤: {max_drawdown:.4f}")
        print(f"  VaR(95%): {var_95:.4f}")
        
        print("\n[步骤8] 计算绩效指标...")
        annual_return = dfq.performance.calculate_annual_return(returns)
        sharpe_ratio = dfq.performance.calculate_sharpe_ratio(returns)
        
        print(f"  年化收益率: {annual_return:.4f}")
        print(f"  夏普比率: {sharpe_ratio:.4f}")
        
        print("\n" + "="*50)
        print("[SUCCESS] 完整流程测试通过!")
        print("="*50)
    
    def test_workflow_with_optimization(self):
        print("\n[额外测试] 参数优化流程...")
        
        def objective_function(params):
            short_period = params['short_period']
            long_period = params['long_period']
            data = dfq.data.get_stock_daily('000001.SZ', '2023-01-01', '2023-06-30')
            data[f'ma{short_period}'] = dfq.indicators.SMA(data['close'], short_period)
            data[f'ma{long_period}'] = dfq.indicators.SMA(data['close'], long_period)
            class OptStrategy(dfq.strategy.Strategy):
                def on_bar(self, bar):
                    ma_short = getattr(bar, f'ma{short_period}', None)
                    ma_long = getattr(bar, f'ma{long_period}', None)
                    if ma_short and ma_long:
                        if ma_short > ma_long:
                            self.buy()
                        elif ma_short < ma_long:
                            self.sell()
            
            engine = dfq.backtest.BacktestEngine()
            result = engine.run(data, OptStrategy())
            return result.summary()['total_signals']
        
        param_grid = {
            'short_period': [5, 10],
            'long_period': [20, 30]
        }
        
        optimizer = dfq.optimization.GridSearchOptimizer()
        best_params = optimizer.optimize(param_grid, objective_function)
        assert best_params is not None
        assert 'short_period' in best_params
        assert 'long_period' in best_params
        print(f"[OK] 参数优化完成")
        print(f"  最佳参数: {best_params}")
        print(f"  测试了 {len(optimizer.results)} 组参数")


if __name__ == '__main__':
    print("=" * 60)
    print("DeltaFQ 完整流程测试")
    print("=" * 60)
    test = TestFullWorkflow()
    test.test_complete_workflow()
    print("\n")
    test.test_workflow_with_optimization()
    print("\n" + "=" * 60)
    print("所有测试完成!")
    print("=" * 60)

