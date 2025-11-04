# DeltaFQ

一个全面的Python量化金融库，用于策略开发、回测和实盘交易。

## 功能特性

- **数据管理**: 高效的数据获取、清洗和存储
- **策略框架**: 灵活的策略开发框架
- **回测系统**: 高性能的历史数据回测
- **模拟交易**: 无风险的策略测试模拟交易
- **实盘交易**: 实时交易与券商集成
- **技术指标**: 丰富的技术分析指标库
- **风险管理**: 内置风险控制模块

## 安装

```bash
pip install deltafq
```

## 快速开始

```python
import deltafq as dfq

# 获取市场数据
fetcher = dfq.data.DataFetcher()
fetcher.initialize()
data = fetcher.fetch_data('AAPL', '2023-01-01', '2023-12-31', clean=True)

# 清洗数据（移除NaN行）
cleaner = dfq.data.DataCleaner()
cleaner.initialize()
cleaned_data = cleaner.dropna(data)

validator = dfq.data.DataValidator()
validator.initialize()
validator.validate_price_data(cleaned_data)

# 创建并测试策略
class SimpleMAStrategy(dfq.strategy.BaseStrategy):
    def __init__(self, fast_period=10, slow_period=20):
        super().__init__()
        self.fast_period = fast_period
        self.slow_period = slow_period
    
    def generate_signals(self, data):
        fast_ma = data['close'].rolling(window=self.fast_period).mean()
        slow_ma = data['close'].rolling(window=self.slow_period).mean()
        import numpy as np
        signals = np.where(fast_ma > slow_ma, 1, np.where(fast_ma < slow_ma, -1, 0))
        return pd.Series(signals, index=data.index)

strategy = SimpleMAStrategy()
strategy.initialize()
results = strategy.run(cleaned_data)

# 运行回测
engine = dfq.backtest.BacktestEngine(initial_capital=100000)
engine.initialize()
backtest_results = engine.run_backtest(strategy, cleaned_data)

# 运行模拟交易
simulator = dfq.trading.PaperTradingSimulator(initial_capital=100000)
simulator.initialize()
portfolio_summary = simulator.run_strategy(strategy, cleaned_data)
```

## 文档

- [API参考](docs/api_reference/)
- [教程](docs/tutorials/)
- [示例](examples/)

## 贡献

欢迎贡献！欢迎提交 Pull Request。

## 许可证

本项目采用MIT许可证 - 查看[LICENSE](LICENSE)文件了解详情。

