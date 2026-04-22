# 基于 LiveEngine + TradeGateway 运行 miniQMT 实盘策略

> 本文档由 Cursor 计划 `miniqmt-liveengine-run` 同步至仓库 `documents/`。  
> **实现**：`LiveEngine` 已对 miniQMT 交易网关接入柜台资金/可用持仓快照（见 `deltafq/live/engine.py` 中 `_account_snapshot`）；`_on_tick_match` 仅在存在 `_engine`（paper）时撮合。

## 目标

用 `LiveEngine` 作为统一运行器，接入 miniQMT 行情与交易网关，实现策略信号到实盘下单的完整链路，并确保可观测、可回滚、可验证。

## 运行路径（推荐）

- 以 [examples/15_live_engine_tpl.py](../examples/15_live_engine_tpl.py) 为模板，保留 `BaseStrategy` + `LiveEngine` 主体。
- 将网关切换为 miniQMT：
  - `engine.set_data_gateway("miniqmt", interval=5.0, mode="poll")`
  - `engine.set_trade_gateway("miniqmt", userdata_mini_path=..., account_id=..., strategy_name=..., lot_size=100)`
- 更完整说明见 [LiveEngine.md](LiveEngine.md) 第十章。

## 策略与下单约束

- 策略只输出 `{-1,0,1}`，信号来源仍通过 `generate_signals(df)`。
- `LiveEngine` 数量规则（策略层可选属性）：
  - 若设置 **`self.order_quantity`**（正整数，股）：买为 `min(order_quantity, 可买上限)`，卖为 `min(order_quantity, 当前可用仓)`，买卖统一上限。
  - 否则若设置 **`self.order_amount`**：仅按金额限制**买**；**卖**仍为可用仓全平。
  - 两者都未设置：买为可用资金全仓可买，卖为可用仓全平。
  - 两者都设置时，**买**侧以 `order_quantity` 为准（与引擎 docstring 一致）。
- miniQMT 交易侧仅支持限价单，数量按 `lot_size` 对齐（默认 100 股），见 [deltafq/adapters/trade/miniqmt_gateway.py](../deltafq/adapters/trade/miniqmt_gateway.py)。

## 资金与持仓（已实现）

当 `trade_gateway_name="miniqmt"` 时，`LiveEngine` 通过 `MiniQmtTradeGateway.client` 查询柜台资金与可用持仓（`can_use_volume` 优先），用于 `order_quantity` / `order_amount` 折算、卖出数量与净值记录；`PaperTradeGateway` 仍使用内嵌 `ExecutionEngine`。

撮合：仅 `PaperTradeGateway` 在 `_on_tick_match` 中调用 `_engine.on_tick`；`MiniQmtTradeGateway` 无本地撮合链路。

## 分阶段上线步骤

- **连通性**：先跑 [examples/17_miniqmt_live_push.py](../examples/17_miniqmt_live_push.py)，再跑 [examples/18_miniqmt_trade_demo.py](../examples/18_miniqmt_trade_demo.py)。
- **策略联调**：运行 [examples/19_miniqmt_live_engine.py](../examples/19_miniqmt_live_engine.py)（含 `order_quantity`），低风险标的与最小手数。
- **稳定运行**：`run_live()` + `KeyboardInterrupt` 时 `stop()`；委托/成交以 miniQMT 客户端为准。

## 验证清单

- miniQMT 已启动，`xtquant` 可导入，`QMT_USERDATA_MINI` / `QMT_ACCOUNT_ID` 正确。
- tick 持续到达，warmup 不参与策略信号。
- 信号变化触发下单；反向信号前尝试撤销上一挂单。
- 日志中 `cash` / `pos` 与客户端资金、可用持仓一致（同 tick 快照）。

## 关键注意事项

- 信号翻转时会先查上一单是否已终态再决定是否撤单；柜台仍以客户端与 `query_stock_orders` 为准。
- 若需更强健壮性，可后续增加 `order_id` 状态轮询后再撤单；柜台委托状态枚举见 [MiniQmtTrade.md](MiniQmtTrade.md) 第八节。

## 预期运行示例（含 `order_quantity`）

见 [examples/19_miniqmt_live_engine.py](../examples/19_miniqmt_live_engine.py)；运行前将 `symbol`、`MIN_PATH`、`ACCOUNT_ID` 改为本机配置。
