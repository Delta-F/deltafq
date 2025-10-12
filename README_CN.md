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
data = dfq.data.fetch_stock_data('AAPL', start='2023-01-01')

# 创建并测试策略
strategy = dfq.strategy.MovingAverageStrategy(fast_period=10, slow_period=20)
results = dfq.backtest.run_backtest(strategy, data)

# 运行模拟交易
simulator = dfq.trading.PaperTradingSimulator(initial_capital=100000)
simulator.run_strategy(strategy, data)
```

## 文档

- [API参考](docs/api_reference/)
- [教程](docs/tutorials/)
- [示例](examples/)

## 贡献

请阅读我们的[贡献指南](CONTRIBUTING.md)了解行为准则和提交拉取请求的流程。

## 许可证

本项目采用MIT许可证 - 查看[LICENSE](LICENSE)文件了解详情。

