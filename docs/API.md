# DeltaFQ API 参考

## 数据模块 (deltafq.data)

### get_stock_daily

```python
def get_stock_daily(
    symbol: str,
    start: str,
    end: str,
    source: str = "mock"
) -> pd.DataFrame
```

获取股票日线数据。

**参数：**
- `symbol`: 股票代码
- `start`: 开始日期 (YYYY-MM-DD)
- `end`: 结束日期 (YYYY-MM-DD)
- `source`: 数据源，默认为 "mock"

**返回：**
- DataFrame，包含 open, high, low, close, volume 列

---

## 技术指标模块 (deltafq.indicators)

### SMA - 简单移动平均

```python
def SMA(data: pd.Series, period: int) -> pd.Series
```

计算简单移动平均线。

### EMA - 指数移动平均

```python
def EMA(data: pd.Series, period: int) -> pd.Series
```

计算指数移动平均线。

### MACD

```python
def MACD(
    data: pd.Series,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9
) -> pd.DataFrame
```

计算MACD指标。

**返回：**
- DataFrame，包含 dif, dea, macd 列

### RSI

```python
def RSI(data: pd.Series, period: int = 14) -> pd.Series
```

计算相对强弱指标。

### BOLL - 布林带

```python
def BOLL(
    data: pd.Series,
    period: int = 20,
    std_dev: float = 2.0
) -> pd.DataFrame
```

计算布林带指标。

**返回：**
- DataFrame，包含 upper, middle, lower 列

---

## 策略模块 (deltafq.strategy)

### Strategy

```python
class Strategy(ABC)
```

策略抽象基类。

**属性：**
- `position`: 当前持仓
- `cash`: 当前资金
- `signals`: 信号列表

**方法：**

#### on_bar

```python
@abstractmethod
def on_bar(self, bar: pd.Series) -> None
```

处理每根K线，需要子类实现。

#### buy

```python
def buy(self, size: float = 1.0) -> None
```

发出买入信号。

#### sell

```python
def sell(self, size: float = 1.0) -> None
```

发出卖出信号。

---

## 回测模块 (deltafq.backtest)

### BacktestEngine

```python
class BacktestEngine
```

回测引擎。

**初始化参数：**
- `initial_cash`: 初始资金，默认100000
- `commission`: 手续费率，默认0.0003
- `slippage`: 滑点，默认0.0

**方法：**

#### run

```python
def run(
    self,
    data: pd.DataFrame,
    strategy: Strategy
) -> BacktestResult
```

运行回测。

### BacktestResult

```python
class BacktestResult
```

回测结果类。

**方法：**

#### summary

```python
def summary() -> Dict[str, Any]
```

返回回测摘要信息。

#### plot

```python
def plot() -> None
```

绘制回测结果图表。

---

## 风险管理模块 (deltafq.risk)

### PositionManager

```python
class PositionManager
```

仓位管理器。

#### calculate_size

```python
def calculate_size(
    self,
    signal: str,
    cash: float,
    price: float,
    method: str = "fixed"
) -> float
```

计算交易数量。

### calculate_max_drawdown

```python
def calculate_max_drawdown(returns: pd.Series) -> float
```

计算最大回撤。

### calculate_var

```python
def calculate_var(
    returns: pd.Series,
    confidence: float = 0.95
) -> float
```

计算VaR（风险价值）。

---

## 绩效分析模块 (deltafq.performance)

### calculate_annual_return

```python
def calculate_annual_return(returns: pd.Series) -> float
```

计算年化收益率。

### calculate_sharpe_ratio

```python
def calculate_sharpe_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.03
) -> float
```

计算夏普比率。

---

## 优化模块 (deltafq.optimization)

### GridSearchOptimizer

```python
class GridSearchOptimizer
```

网格搜索优化器。

#### optimize

```python
def optimize(
    self,
    param_grid: Dict[str, List[Any]],
    objective_func: Callable
) -> Dict[str, Any]
```

执行参数优化，返回最优参数组合。

---

## 交易模块 (deltafq.trade)

### Broker

```python
class Broker(ABC)
```

券商接口抽象基类。

**方法：**

#### submit_order

```python
@abstractmethod
def submit_order(
    self,
    symbol: str,
    action: str,
    quantity: float,
    order_type: str = "market"
) -> str
```

提交订单。

#### get_position

```python
@abstractmethod
def get_position() -> List[Dict[str, Any]]
```

获取持仓信息。

#### get_account

```python
@abstractmethod
def get_account() -> Dict[str, Any]
```

获取账户信息。

---

## 工具模块 (deltafq.utils)

### is_trading_day

```python
def is_trading_day(date: datetime) -> bool
```

判断是否为交易日。

### get_trading_dates

```python
def get_trading_dates(start: str, end: str) -> List[datetime]
```

获取指定范围内的交易日列表。

