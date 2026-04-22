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
│  (YFinance / miniQMT)    (事件总线)           ├─ _on_tick_match ──► TradeGW  │
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
  │     ├─ create_data_gateway(data_gateway_name)
  │     ├─ create_trade_gateway("paper")   → PaperTradeGateway (内嵌 ExecutionEngine)
  │     └─ DataFetcher(source=fetcher_source_for_data_gateway(data_gateway_name))
  │                                  # 非 tick 模式时用于 fetch K 线
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
  │     # miniQMT: _warm_up 拉历史 1m 数据，逐条以 source="miniqmt_warmup" 推送
  │
  └─► data_gw.start()
        # YFinance: 后台线程按 interval 轮询 fast_info，推送 source="yfinance" tick
        # miniQMT: 后台线程按 interval 轮询 full tick，推送 source="miniqmt" tick
```

---

## 五、单 Tick 处理链路

每个 tick 进来后，EventEngine 按注册顺序依次调用两个 handler：

### 5.1 _on_tick_match（撮合）

```
Tick → EventEngine.emit(EVENT_TICK, tick)
         │
         └─► _on_tick_match(tick)
              ├─ source 不在 {"yf_warmup","miniqmt_warmup"} → 打日志
              └─ 若 trade_gw 含 _engine（paper）→ _engine.on_tick(tick)  # 本地限价撮合
                 （miniqmt 交易网关无 _engine，不在此撮合）
```

### 5.2 _on_tick_strategy（策略与下单）

```
_on_tick_strategy(tick)
  │
  ├─ source in {"yf_warmup","miniqmt_warmup"} ? → return  # 预热数据不参与策略
  ├─ symbol 不匹配 / 无策略 ? → return
  │
  ├─ 构建策略输入数据 (df)
  │     ├─ signal_interval == "tick"
  │     │     └─ 用 _prices / _timestamps 攒够 lookback_bars 根 tick，构 DataFrame
  │     │
  │     └─ signal_interval in ["1m","5m",...]
  │           ├─ 节流：距上次 fetch 不足 refetch_sec → return
  │           └─ _fetch_bars() → DataFetcher(mapped source) 拉最近 lookback_bars 根 K 线
  │
  ├─ strategy.generate_signals(df) → signals
  ├─ 缓存 _cached_bars, _cached_signals（供 get_chart_data）
  │
  ├─ signal = signals.iloc[-1]
  ├─ 计算 action：BUY qty / SELL qty / no_change
  ├─ 打日志：Signal: ↑/↓  signal  [symbol] price cash pos -> action
  │
  └─ 若 signal 相对 _last_signal 变化
        ├─ 若有 _last_pending_order_id → cancel_order（信号反转前撤销挂单，避免方向错误成交）
        ├─ signal=1 且 _last≤0 → send_order(BUY)，记录 order_id
        └─ signal=-1 且 _last≥0 且 position>0 → send_order(SELL)，记录 order_id
        → 更新 _last_signal
```

---

## 六、数据流与依赖

| 组件 | 数据来源 | 职责 |
|-----|---------|------|
| **YFinanceDataGateway** | yfinance `fast_info` 轮询 + warm-up 1m 历史 | 产生 Tick，推入 EventEngine |
| **MiniQmtDataGateway** | xtquant `get_full_tick` 轮询 + warm-up 1m 历史 | 产生 Tick，推入 EventEngine |
| **DataFetcher** | yfinance `download` / xtquant `xtdata` | 拉 K 线供策略使用（非 tick 模式） |
| **EventEngine** | DataGateway 的 tick_handler | 事件分发，保证 match 先于 strategy |
| **BaseStrategy** | LiveEngine 传入的 df | `generate_signals(df)` 输出 1/-1/0 |
| **PaperTradeGateway** | LiveEngine 的 OrderRequest | `send_order` → ExecutionEngine；`_on_tick_match` 撮合挂单 |
| **MiniQmtTradeGateway** | LiveEngine 的 OrderRequest | 透传到 miniQMT 柜台（限价下单/撤单）；资金/持仓由 `LiveEngine._account_snapshot` 读 `client` |
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

策略可设置 `self.order_amount = 10000`，指定单次买入投入金额（与账户币种一致）；未设置则买入按可用资金全仓可买。若同时设置了 `order_quantity`，买入股数以 `order_quantity` 为准。

### 8.2 order_quantity（策略层）

策略可设置 `self.order_quantity = 100`（正整数，单位：股），则单次买入为 `min(order_quantity, 资金可买上限)`，单次卖出为 `min(order_quantity, 当前持仓可用数量)`，买卖统一股数上限。未设置时卖出为全仓可用；买入规则见 8.1。

### 8.3 get_chart_data()

`engine.get_chart_data()` 返回最近一次策略运行的 K 线和信号，供图表展示，不触发重新拉数或重新计算。

### 8.4 撤单逻辑

信号反转（buy↔sell）时，LiveEngine 会先处理上一笔 `_last_pending_order_id`：**若检测到委托已终态**（paper：`executed` / `cancelled`；miniQMT：`order_status` 为部撤/已撤/已成/废单，或当日查询列表中已无该 `order_id`），则**不再调用撤单**，仅清空本地 pending；否则调用 `cancel_order`。限价单在 `match_on_tick` 模式下会挂单等待撮合，若信号快速翻转而未撤单，可能导致方向错误的成交；记录 `_last_pending_order_id` 可避免此问题。

### 8.5 运行中指标（与回测同 API）

每次策略评估（有信号时）会录制一行净值：`date`、`total_value`、`cash`、`position`、`position_value`、`daily_pnl` 等，与回测 `values_records` 结构一致。

- **`get_trades_df()`**：返回成交明细 DataFrame（与 ExecutionEngine.trades 一致）。
- **`get_values_df()`**：返回录制的净值序列 DataFrame，按 date 去重、排序。
- **`calculate_metrics()`**：调用 PerformanceReporter，返回 `(values_metrics, metrics)`，与 BacktestEngine.calculate_metrics() 相同，可得到 total_return、max_drawdown、sharpe_ratio 等。运行中或 stop() 后均可调用。

---

## 九、收尾流程

```
stop()
  ├─ data_gw.stop()   # 停止轮询线程
  └─ trade_gw.stop()  # Paper 为 no-op；实盘时可做断开等
```

---

## 十、miniQMT 实盘网关接入

### 10.1 前置条件

- 本机启动 miniQMT 终端
- Python 环境已安装并可导入 `xtquant`
- 配置 `QMT_USERDATA_MINI` 与 `QMT_ACCOUNT_ID`（或在代码中显式传参）

### 10.2 代码示例

```python
engine = LiveEngine(symbol="000001.SZ", signal_interval="1m")
engine.set_data_gateway("miniqmt", interval=3.0, mode="poll")
engine.set_trade_gateway(
    "miniqmt",
    userdata_mini_path=r"D:\券商QMT\userdata_mini",
    account_id="1234567890",
    lot_size=100,
)
```

### 10.3 当前约束

- 当前仅支持 `order_type="limit"`
- 下单数量按 `lot_size` 对齐（默认 100 股）
- 撤单优先按本地委托号，失败时回退到合同号撤单

---

## 十一、API 速查

| 方法 | 说明 |
|-----|------|
| `set_parameters(symbol=..., interval=..., lookback_bars=..., signal_interval=...)` | 更新运行参数 |
| `set_data_gateway(name, **params)` | 设置数据网关 |
| `set_trade_gateway(name, **params)` | 设置交易网关 |
| `add_strategy(strategy)` | 挂载策略 |
| `run_live()` | 启动实盘 |
| `stop()` | 停止并释放资源 |
| `get_chart_data()` | 获取缓存的 candles 和 signals |
| `get_trades_df()` | 成交明细 DataFrame |
| `get_values_df()` | 净值序列 DataFrame |
| `calculate_metrics()` | 计算绩效指标，返回 (values_metrics, metrics) |
