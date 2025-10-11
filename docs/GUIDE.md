# DeltaFQ 使用指南

## 安装

### PyPI 安装（推荐）
```bash
pip install deltafq
```

### 源码安装
```bash
git clone https://github.com/Delta-F/deltafq.git
cd deltafq
pip install -e .
```

---

## 快速开始

### 1. 获取数据并计算指标

```python
import deltafq as dfq

# 获取数据
data = dfq.data.get_stock_daily('000001.SZ', start='2023-01-01', end='2023-12-31')

# 计算技术指标
data['ma5'] = dfq.indicators.SMA(data['close'], 5)
data['ma20'] = dfq.indicators.SMA(data['close'], 20)
```

### 2. 创建交易策略

```python
class MyStrategy(dfq.strategy.Strategy):
    """双均线策略"""
    
    def on_bar(self, bar):
        if bar.ma5 > bar.ma20:
            self.buy()
        elif bar.ma5 < bar.ma20:
            self.sell()
```

### 3. 运行回测

```python
# 创建回测引擎
engine = dfq.backtest.BacktestEngine(
    initial_cash=100000,
    commission=0.0003
)

# 运行回测
result = engine.run(data, MyStrategy())

# 查看结果
print(result.summary())
result.plot()  # 需要 matplotlib
```

---

## 核心模块

### 数据模块 (data)
```python
# 获取日线数据
data = dfq.data.get_stock_daily(symbol, start, end)
```

### 技术指标 (indicators)
```python
# 趋势指标
ma = dfq.indicators.SMA(data['close'], 20)
ema = dfq.indicators.EMA(data['close'], 20)
macd = dfq.indicators.MACD(data['close'])

# 动量指标
rsi = dfq.indicators.RSI(data['close'], 14)

# 波动率指标
boll = dfq.indicators.BOLL(data['close'], 20)
```

### 策略框架 (strategy)
```python
class MyStrategy(dfq.strategy.Strategy):
    def on_bar(self, bar):
        # 实现交易逻辑
        pass
```

### 回测引擎 (backtest)
```python
engine = dfq.backtest.BacktestEngine(
    initial_cash=100000,
    commission=0.0003,
    slippage=0.0
)
result = engine.run(data, strategy)
```

### 风险管理 (risk)
```python
# 风险指标
max_dd = dfq.risk.calculate_max_drawdown(returns)
var = dfq.risk.calculate_var(returns, confidence=0.95)
```

### 绩效分析 (performance)
```python
# 绩效指标
annual_return = dfq.performance.calculate_annual_return(returns)
sharpe = dfq.performance.calculate_sharpe_ratio(returns)
```

### 参数优化 (optimization)
```python
optimizer = dfq.optimization.GridSearchOptimizer()
best_params = optimizer.optimize(param_grid, objective_func)
```

---

## 完整示例

查看 [examples/](../examples/) 目录：
- `ma_strategy.py` - 双均线策略
- `macd_strategy.py` - MACD策略
- `optimization_example.py` - 参数优化

运行示例：
```bash
cd examples
python ma_strategy.py
```

---

## 测试

运行完整流程测试：
```bash
python tests/test_full_workflow.py
```

运行所有测试：
```bash
pytest
```

---

## 更多资源

- [API参考](API.md)
- [开发指南](CONTRIBUTING.md)
- [更新日志](CHANGELOG.md)
- [GitHub](https://github.com/Delta-F/deltafq)
- [PyPI](https://pypi.org/project/deltafq/)

---

## 重要提示

1. 当前版本使用模拟数据，适合学习和测试
2. 回测引擎是简化版，实盘交易前需更严格测试
3. 量化交易存在风险，仅供学习研究使用

