# BacktestEngine 使用说明与架构文档

BacktestEngine 是 DeltaFQ 的策略回测核心，基于历史 K 线数据逐日回放信号、模拟下单，并计算绩效指标与图表。

---

## 一、快速开始

```python
from deltafq.backtest import BacktestEngine
from deltafq.strategy.base import BaseStrategy
import pandas as pd

class SimpleMAStrategy(BaseStrategy):
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        fast = data["Close"].rolling(10).mean()
        slow = data["Close"].rolling(30).mean()
        return pd.Series(1, index=data.index).where(fast > slow, -1)

engine = BacktestEngine()
engine.set_parameters(symbol="AAPL", start_date="2024-01-01", end_date="2024-06-30", benchmark="SPY")
engine.load_data()
engine.add_strategy(SimpleMAStrategy())
engine.run_backtest()
engine.calculate_metrics()
engine.show_report()
engine.show_chart(use_plotly=True)
```

---

## 二、架构总览

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        BacktestEngine 回测链路                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  [DataFetcher]  ──历史数据──► [BacktestEngine]                               │
│  (yahoo)                        │                                           │
│                                 ├─ load_data()   → 拉取 OHLC                 │
│                                 ├─ add_strategy()→ strategy.run(data)        │
│                                 │                  → signals                 │
│                                 └─ run_backtest()                            │
│                                        │                                     │
│                                        ▼                                     │
│                                   逐日循环 (date, signal, price)              │
│                                        │                                     │
│                                        ├─ signal=1  → execute_order(BUY)     │
│                                        ├─ signal=-1 → execute_order(SELL)    │
│                                        └─ 记录 values_records                │
│                                        │                                     │
│                                        ▼                                     │
│  [ExecutionEngine]  ◄── execute_order  (match_on_tick=False, 立即成交)       │
│  (Paper)                OrderManager / PositionManager                       │
│                                        │                                     │
│                                        ▼                                     │
│  [PerformanceReporter]  ◄── trades_df, values_df  → 计算收益、回撤、夏普等   │
│  [PerformanceChart]     ◄── values_df             → 净值曲线、回撤图         │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 三、初始化与启动流程

| 步骤 | 调用 | 作用 |
|-----|------|------|
| 1 | `BacktestEngine(initial_capital, commission, slippage, data_source)` | 创建引擎，配置资金、费率、数据源 |
| 2 | `set_parameters(symbol, start_date, end_date, benchmark...)` | 设置标的、回测区间、基准 |
| 3 | `load_data()` | 通过 DataFetcher 拉取历史数据 |
| 4 | `add_strategy(strategy)` | 挂载策略并运行，得到 signals |
| 5 | `run_backtest()` | 逐日回放，执行模拟交易 |
| 6 | `calculate_metrics()` | 计算绩效指标 |
| 7 | `show_report()` / `show_chart()` | 输出报告与图表 |

---

## 四、run_backtest() 内部流程

```
run_backtest()
  │
  ├─ 构造 df_sig = DataFrame{Signal, Close}，按 date 迭代
  │
  └─ for each (date, signal, price):
        │
        ├─ signal == 1
        │     └─ max_qty = int(cash / (price * (1 + commission)))
        │     └─ if max_qty > 0: execute_order(symbol, max_qty, limit, price, date)
        │
        ├─ signal == -1
        │     └─ current_qty = position_manager.get_position(symbol)
        │     └─ if current_qty > 0: execute_order(symbol, -current_qty, limit, price, date)
        │
        ├─ 计算 position_value, total_value, daily_pnl
        │
        └─ 追加 values_records
  │
  └─ trades_df = execution.trades
       values_df = values_records
```

---

## 五、执行引擎与回测差异

| 模式 | ExecutionEngine | 成交方式 | 撤单 |
|-----|-----------------|----------|------|
| **回测** | `match_on_tick=False`（默认） | 限价单立即成交，用当日 Close 价 | 无挂单，无需撤单 |
| **实盘/模拟** | `match_on_tick=True` | 挂单等待 tick 撮合 | LiveEngine 信号反转时撤销前一挂单 |

BacktestEngine 内部创建的 ExecutionEngine 未显式传 `match_on_tick`，使用默认 `False`，即回测时下单即成交。

---

## 六、数据流与依赖

| 组件 | 数据来源 | 职责 |
|-----|---------|------|
| **DataFetcher** | yahoo / 其他 | 拉取历史 OHLC |
| **DataStorage** | 本地路径 | 缓存与保存回测结果 |
| **BaseStrategy** | engine.data | `run(data)` → `generate_signals()` → signals |
| **ExecutionEngine** | BacktestEngine 调用 | 模拟下单、持仓、资金 |
| **PerformanceReporter** | trades_df, values_df | 计算收益、回撤、夏普等 |
| **PerformanceChart** | values_df | 绘制净值、回撤、收益分布等 |

---

## 七、run_backtest 可选参数

```python
engine.run_backtest(
    symbol=None,        # 覆盖 set_parameters 的 symbol
    signals=None,       # 覆盖 add_strategy 产生的 signals
    price_series=None,  # 覆盖 data['Close']
    save_csv=False,     # 是否立即保存结果
    strategy_name=None  # 保存时的策略名
)
```

可直接传入 `signals` 与 `price_series`，跳过 `add_strategy`，用于快速验证信号序列。

---

## 八、输出与存储

### 8.1 trades_df

记录每笔成交：order_id, symbol, quantity, price, type, timestamp, commission, cost, gross_revenue, net_revenue, buy_cost, profit_loss 等。

### 8.2 values_df

逐日记录：date, signal, price, cash, position, position_value, total_value, daily_pnl。

### 8.3 metrics

由 PerformanceReporter 计算：total_return, annualized_return, max_drawdown, sharpe_ratio, calmar_ratio, win_rate 等。

### 8.4 save_backtest_results()

将 trades_df、values_df 保存为 CSV，路径由 DataStorage 配置。

---

## 九、API 速查

| 方法 | 说明 |
|-----|------|
| `set_parameters(symbol, start_date, end_date=None, benchmark=None, ...)` | 设置回测参数 |
| `load_data()` | 拉取历史数据 |
| `add_strategy(strategy)` | 挂载策略并生成 signals |
| `run_backtest(...)` | 执行回测 |
| `calculate_metrics()` | 计算绩效指标 |
| `show_report()` | 打印摘要报告 |
| `show_chart(use_plotly=True)` | 展示绩效图表 |
| `save_backtest_results()` | 保存结果到 CSV |
