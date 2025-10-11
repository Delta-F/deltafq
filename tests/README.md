# 测试说明

## 快速开始

### 运行完整流程测试
```bash
python tests/test_full_workflow.py
```

### 运行所有测试
```bash
pytest
pytest -v  # 显示详细信息
```

## 测试文件

### test_full_workflow.py - 完整流程测试
展示完整的量化交易流程：数据获取 → 指标计算 → 策略创建 → 回测执行 → 结果分析

### 单元测试
- `test_data.py` - 数据模块测试
- `test_indicators.py` - 技术指标测试
- `test_strategy.py` - 策略框架测试
- `test_backtest.py` - 回测引擎测试

## 快速示例

```python
import deltafq as dfq

data = dfq.data.get_stock_daily('000001.SZ', '2023-01-01', '2023-12-31')
data['ma5'] = dfq.indicators.SMA(data['close'], 5)
data['ma20'] = dfq.indicators.SMA(data['close'], 20)

class MyStrategy(dfq.strategy.Strategy):
    def on_bar(self, bar):
        if bar.ma5 > bar.ma20:
            self.buy()
        elif bar.ma5 < bar.ma20:
            self.sell()

engine = dfq.backtest.BacktestEngine()
result = engine.run(data, MyStrategy())
print(result.summary())
```

## 常见问题

**Q: 测试失败怎么办？**
- 确保已安装依赖: `pip install -r requirements.txt`
- 确保在项目根目录运行
- 检查Python版本 >= 3.8

