# 开发指南

## 项目结构

```
deltafq/
├── README.md              # 项目说明
├── LICENSE                # MIT许可证
├── pyproject.toml         # 项目配置
├── setup.py               # 安装脚本
├── requirements.txt       # 依赖列表
├── MANIFEST.in            # 打包配置
├── .gitignore             # Git配置
│
├── deltafq/               # 核心代码包
│   ├── data/             # 数据模块
│   ├── indicators/       # 技术指标
│   ├── strategy/         # 策略框架
│   ├── backtest/         # 回测引擎
│   ├── risk/             # 风险管理
│   ├── performance/      # 绩效分析
│   ├── optimization/     # 参数优化
│   ├── trade/            # 交易接口
│   └── utils/            # 工具函数
│
├── docs/                  # 文档
├── examples/              # 示例代码
└── tests/                 # 测试代码
```

## 开发环境设置

### 1. 克隆仓库
```bash
git clone https://github.com/Delta-F/deltafq.git
cd deltafq
```

### 2. 安装开发依赖
```bash
# 安装包（开发模式）
pip install -e .

# 安装开发工具
pip install -e ".[dev]"
```

### 3. 运行测试
```bash
# 运行所有测试
pytest

# 带覆盖率
pytest --cov=deltafq

# 运行特定测试
pytest tests/test_full_workflow.py -v
```

## 核心架构

### 1. 数据层 (data/)
- `base.py` - 数据源抽象基类
- `loader.py` - 数据加载器

**扩展示例**：添加新数据源
```python
from deltafq.data.base import DataSource

class MyDataSource(DataSource):
    def get_data(self, symbol, start_date, end_date, **kwargs):
        # 实现数据获取逻辑
        return dataframe
```

### 2. 指标层 (indicators/)
- `trend.py` - 趋势指标
- `momentum.py` - 动量指标
- `volatility.py` - 波动率指标

**扩展示例**：添加新指标
```python
def MY_INDICATOR(data: pd.Series, period: int) -> pd.Series:
    """我的自定义指标"""
    return data.rolling(period).mean()  # 示例
```

### 3. 策略层 (strategy/)
- `base.py` - 策略抽象基类

**扩展示例**：创建策略
```python
from deltafq.strategy import Strategy

class MyStrategy(Strategy):
    def on_bar(self, bar):
        # 实现交易逻辑
        if condition:
            self.buy()
```

### 4. 回测层 (backtest/)
- `engine.py` - 回测引擎
- `result.py` - 结果分析

### 5. 分析层
- `risk/` - 风险管理
- `performance/` - 绩效分析
- `optimization/` - 参数优化

## 代码规范

### Python 风格
- 遵循 PEP 8
- 使用类型注解
- 添加文档字符串

```python
def my_function(param: str, value: int = 10) -> float:
    """函数简短描述
    
    Args:
        param: 参数说明
        value: 参数说明，默认10
        
    Returns:
        返回值说明
    """
    return result
```

### 测试要求
- 新功能必须有测试
- 保持测试覆盖率 > 80%
- 使用 pytest

```python
def test_my_feature():
    """测试我的功能"""
    result = my_function("test")
    assert result == expected_value
```

## 发布流程

### 1. 更新版本号
编辑 `deltafq/__init__.py` 和 `pyproject.toml`：
```python
__version__ = "0.2.0"
```

### 2. 更新 CHANGELOG.md
记录本次更新内容。

### 3. 构建包
```bash
pip install build twine
python -m build
```

### 4. 测试包
```bash
twine check dist/*
```

### 5. 上传到 PyPI
```bash
# 测试环境（可选）
twine upload --repository testpypi dist/*

# 正式环境
twine upload dist/*
```

## 开发路线图

### 短期目标
- [ ] 集成真实数据源（Tushare/AKShare）
- [ ] 完善回测引擎交易逻辑
- [ ] 添加更多技术指标
- [ ] 改进可视化功能

### 中期目标
- [ ] 事件驱动回测引擎
- [ ] 更多优化算法
- [ ] 实盘交易接口实现
- [ ] 完善风险管理模块

### 长期目标
- [ ] 多策略组合管理
- [ ] Web界面
- [ ] 分布式回测
- [ ] 机器学习策略支持

## 贡献指南

### 提交 Pull Request
1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 报告问题
使用 [GitHub Issues](https://github.com/Delta-F/deltafq/issues) 报告：
- Bug
- 功能请求
- 文档改进

### 代码审查
- 所有 PR 需要通过测试
- 代码风格检查
- 至少一位维护者审核

## 技术栈

- **语言**: Python 3.8+
- **核心库**: pandas, numpy
- **可选库**: matplotlib (绘图)
- **测试**: pytest
- **代码质量**: black, flake8, mypy
- **构建**: build, twine

## 最佳实践

### 1. 性能优化
- 优先使用向量化操作
- 避免循环处理大数据
- 考虑使用 numba 加速

### 2. 内存管理
- 及时释放大对象
- 使用生成器处理大数据
- 注意 DataFrame 拷贝

### 3. 错误处理
- 提供清晰的错误信息
- 验证输入参数
- 记录关键操作

## 联系方式

- [GitHub](https://github.com/Delta-F/deltafq)
- [PyPI](https://pypi.org/project/deltafq/)
- [Issues](https://github.com/Delta-F/deltafq/issues)

---

感谢你对 DeltaFQ 的贡献！

