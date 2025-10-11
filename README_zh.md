# DeltaFQ

[![PyPI version](https://badge.fury.io/py/deltafq.svg)](https://badge.fury.io/py/deltafq)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

专业的Python量化交易库，为量化策略开发者和研究人员提供从数据获取到策略回测的完整工具链。

## 特性

- 📊 **多源数据支持** - 统一的数据接口，支持多种数据源
- 📈 **丰富的技术指标** - 内置常用技术指标，支持自定义扩展
- 🎯 **灵活的策略框架** - 简洁的API，快速构建交易策略
- ⚡ **高效的回测引擎** - 向量化计算，快速验证策略效果
- 📉 **全面的风险管理** - 仓位管理、风险控制、绩效分析
- 🔧 **参数优化工具** - 多种优化算法，寻找最佳参数
- 📱 **实盘交易接口** - 统一的交易接口，无缝切换模拟与实盘

## 安装

```bash
pip install deltafq
```

或者安装开发版本：

```bash
git clone https://github.com/Delta-F/deltafq.git
cd deltafq
pip install -e .
```

## 快速开始

### 获取数据

```python
import deltafq as dfq

# 获取股票数据
data = dfq.data.get_stock_daily('000001.SZ', start='2020-01-01', end='2023-12-31')
print(data.head())
```

### 计算技术指标

```python
# 计算移动平均线
data['ma5'] = dfq.indicators.SMA(data['close'], 5)
data['ma20'] = dfq.indicators.SMA(data['close'], 20)

# 计算MACD
macd = dfq.indicators.MACD(data['close'])
data = data.join(macd)
```

### 构建交易策略

```python
class MAStrategy(dfq.strategy.Strategy):
    """双均线策略"""
    
    def on_bar(self, bar):
        if bar.ma5 > bar.ma20:
            self.buy()
        elif bar.ma5 < bar.ma20:
            self.sell()
```

### 运行回测

```python
# 创建回测引擎
engine = dfq.backtest.BacktestEngine(
    initial_cash=100000,
    commission=0.0003
)

# 运行回测
result = engine.run(data, MAStrategy())

# 查看结果
print(result.summary())
result.plot()
```

## 模块说明

- **data** - 数据获取和管理
- **indicators** - 技术指标计算
- **strategy** - 策略开发框架
- **backtest** - 回测引擎
- **risk** - 风险管理
- **performance** - 绩效分析
- **optimization** - 参数优化
- **trade** - 实盘交易接口
- **utils** - 工具函数

## 示例

查看 `examples/` 目录获取更多示例代码：

- `ma_strategy.py` - 双均线策略
- `macd_strategy.py` - MACD策略
- `optimization_example.py` - 参数优化示例

## 文档

- **使用指南**: [docs/GUIDE_zh.md](docs/GUIDE_zh.md) | [English Guide](docs/GUIDE.md)
- **API参考**: [docs/API.md](docs/API.md)
- **开发指南**: [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)
- **更新日志**: [docs/CHANGELOG.md](docs/CHANGELOG.md)

## 依赖

- Python >= 3.8
- pandas >= 1.3.0
- numpy >= 1.21.0

## 开发

```bash
# 克隆仓库
git clone https://github.com/Delta-F/deltafq.git
cd deltafq

# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 代码格式化
black deltafq/

# 类型检查
mypy deltafq/
```

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 贡献

欢迎提交 Issue 和 Pull Request！

## 联系方式

- 项目主页：[https://github.com/Delta-F/deltafq](https://github.com/Delta-F/deltafq)
- PyPI 主页：[https://pypi.org/project/deltafq/](https://pypi.org/project/deltafq/)
- 问题反馈：[https://github.com/Delta-F/deltafq/issues](https://github.com/Delta-F/deltafq/issues)

---

⚠️ **风险提示**：量化交易存在风险，本库仅供学习研究使用，不构成投资建议。实盘交易需谨慎，风险自担。

## 语言支持

本项目支持中英文双语文档：

- **中文**: [README_zh.md](README_zh.md) (当前)
- **English**: [README.md](README.md)
