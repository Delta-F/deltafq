# LiveEngine 使用说明与架构文档

LiveEngine 是 DeltaFQ 的策略自动化运行核心，负责将实时行情接入、信号计算、下单执行串联成一条完整链路。

---

## 一、快速开始

```python
from deltafq.live import LiveEngine
from deltafq.strategy.base import BaseStrategy
import pandas as pd

class MyStrategy(BaseStrategy):
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        # 返回 -1 / 0 / 1
        return pd.Series([1] * len(data), index=data.index)

engine = LiveEngine(symbol="BTC-USD", signal_interval="1m", lookback_bars=50)
engine.set_trade_gateway("paper", initial_capital=100000)
engine.add_strategy(MyStrategy())
engine.run_live()
# Ctrl+C 退出时: engine.stop()
```

---

## 二、架构总览

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           LiveEngine 策略自动化链路                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  [DataGateway]  ──Tick──► [EventEngine] ──► [LiveEngine 双 Handler]         │
│  (YFinance)              (事件总线)           ├─ _on_tick_match ──► TradeGW  │
│  poll/推送                                    └─ _on_tick_strategy           │
│       │                                                     │               │
│       │                                                     ▼               │
│       │                                    ┌────────────────────────────────┤
│       │                                    │ 1. 构建数据 (tick 或 fetch bars)│
│       │                                    │ 2. 策略 generate_signals(df)   │
│       │                                    │ 3. 信号变化 → send_order       │
│       │                                    └────────────────────────────────┤
│       │                                                     │               │
│       │                                                     ▼               │
│       │                                    [TradeGateway] ──► [ExecutionEngine]│
│       │                                    (Paper)              order_match │
│       │                                                         position    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 三、初始化与启动流程

| 步骤 | 调用 | 作用 |
|-----|------|------|
| 1 | `LiveEngine(symbol, signal_interval, lookback_bars...)` | 创建引擎，配置标的、K 线周期、回溯根数 |
| 2 | `set_trade_gateway("paper", initial_capital=...)` | 指定交易网关及资金参数 |
| 3 | `add_strategy(MyStrategy())` | 挂载策略 |
| 4 | `run_live()` | 启动实盘链路 |

---

## 四、run_live() 内部流程

```
run_live()
  │
  ├─► _ensure_gateways()
  │     ├─ create_data_gateway("yfinance") → YFinanceDataGateway
  │     ├─ create_trade_gateway("paper")   → PaperTradeGateway (内嵌 ExecutionEngine)
  │     └─ DataFetcher(source="yahoo")     # 非 tick 模式时用于 fetch K 线
  │
  ├─► trade_gw.connect() / data_gw.connect()
  │
  ├─► 注册事件
  │     EventEngine.on(EVENT_TICK, _on_tick_match)    # 先执行：推 tick 给交易引擎
  │     EventEngine.on(EVENT_TICK, _on_tick_strategy) # 后执行：算信号、下单
  │
  ├─► data_gw.set_tick_handler(lambda t: event_engine.emit(EVENT_TICK, t))
  │     # 所有 tick 统一经由 EventEngine 分发
  │
  ├─► data_gw.subscribe([symbol])
  │     # YFinance: _warm_up 拉历史 1m 数据，逐条以 source="yf_warmup" 推送
  │
  └─► data_gw.start()
        # YFinance: 后台线程按 interval 轮询 fast_info，推送 source="yfinance" tick
```

---

## 五、单 Tick 处理链路

每个 tick 进来后，EventEngine 按注册顺序依次调用两个 handler：

### 5.1 _on_tick_match（撮合）

```
Tick → EventEngine.emit(EVENT_TICK, tick)
         │
         └─► _on_tick_match(tick)
               ├─ source != "yf_warmup" → 打日志 (symbol, price, vol, time)
               └─ trade_gw._engine.on_tick(tick)  # ExecutionEngine 撮合挂单
```

### 5.2 _on_tick_strategy（策略与下单）

```
_on_tick_strategy(tick)
  │
  ├─ source == "yf_warmup" ? → return  # 预热数据不参与策略
  ├─ symbol 不匹配 / 无策略 ? → return
  │
  ├─ 构建策略输入数据 (df)
  │     ├─ signal_interval == "tick"
  │     │     └─ 用 _prices / _timestamps 攒够 lookback_bars 根 tick，构 DataFrame
  │     │
  │     └─ signal_interval in ["1m","5m",...]
  │           ├─ 节流：距上次 fetch 不足 refetch_sec → return
  │           └─ _fetch_bars() → DataFetcher(yahoo) 拉最近 lookback_bars 根 K 线
  │
  ├─ strategy.generate_signals(df) → signals
  ├─ 缓存 _cached_bars, _cached_signals（供 get_chart_data）
  │
  ├─ signal = signals.iloc[-1]
  ├─ 计算 action：BUY qty / SELL qty / no_change
  ├─ 打日志：Signal: ↑/↓  signal  [symbol] price cash pos -> action
  │
  └─ 若 signal 相对 _last_signal 变化
        ├─ signal=1 且 _last≤0 → send_order(BUY)
        └─ signal=-1 且 _last≥0 且 position>0 → send_order(SELL)
        → 更新 _last_signal
```

---

## 六、数据流与依赖

| 组件 | 数据来源 | 职责 |
|-----|---------|------|
| **YFinanceDataGateway** | yfinance `fast_info` 轮询 + warm-up 1m 历史 | 产生 Tick，推入 EventEngine |
| **DataFetcher** | yfinance `download` | 拉 K 线供策略使用（非 tick 模式） |
| **EventEngine** | DataGateway 的 tick_handler | 事件分发，保证 match 先于 strategy |
| **BaseStrategy** | LiveEngine 传入的 df | `generate_signals(df)` 输出 1/-1/0 |
| **PaperTradeGateway** | LiveEngine 的 OrderRequest | `send_order` → ExecutionEngine |
| **ExecutionEngine** | Tick + 挂单 | `on_tick` 撮合、更新持仓与资金 |

---

## 七、signal_interval 模式

| signal_interval | 数据来源 | 更新频率 |
|-----------------|----------|----------|
| **tick** | DataGateway 推送的 tick 直接作为 Close | 每个 tick |
| **1m / 5m / 15m / 1h / 1d** | DataFetcher 拉取 K 线 | 按 _REFETCH_SEC 节流（1m=60s, 5m=300s...） |

---

## 八、可选参数

### 8.1 order_amount（策略层）

策略可设置 `self.order_amount = 10000`，指定单次买入投入金额（美元）；未设置则按全仓计算。

### 8.2 get_chart_data()

`engine.get_chart_data()` 返回最近一次策略运行的 K 线和信号，供图表展示，不触发重新拉数或重新计算。

---

## 九、收尾流程

```
stop()
  ├─ data_gw.stop()   # 停止轮询线程
  └─ trade_gw.stop()  # Paper 为 no-op；实盘时可做断开等
```

---

## 十、API 速查

| 方法 | 说明 |
|-----|------|
| `set_parameters(symbol=..., interval=..., lookback_bars=..., signal_interval=...)` | 更新运行参数 |
| `set_data_gateway(name, **params)` | 设置数据网关 |
| `set_trade_gateway(name, **params)` | 设置交易网关 |
| `add_strategy(strategy)` | 挂载策略 |
| `run_live()` | 启动实盘 |
| `stop()` | 停止并释放资源 |
| `get_chart_data()` | 获取缓存的 candles 和 signals |
