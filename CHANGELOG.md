# 更新日志

项目遵循语义化版本，此处简要记录关键变化。

## [1.0.2] - 2026-04-27
### DataGateway 接口补全与深度行情统一
- `DataGateway`：新增 `emit_tick()` 主动分发接口，并将 `get_today_ohlc()` / `get_depths()` 作为统一抽象能力，明确网关最小公开 API
- `MiniQmtDataGateway`：移除 `get_full_tick_dict()`，新增 `get_depths(symbol, levels)`，兼容数组字段与逐档字段两种快照格式，统一返回 `bids/asks` 深度结构
- `YFinanceDataGateway`：新增 `get_depths(symbol, levels)`（基于 `fast_info` 的合成盘口），并整理类注释与方法说明，保持与 DataGateway 抽象一致

### 示例同步
- 示例 `18_miniqmt_trade_demo.py`：下单前改为通过 Tick 回调获取最新价，不再依赖全快照字段直读
- 示例 `20_data_gateway_tpl.py`：新增 DataGateway 公开 API 烟测模板（`get_today_ohlc` / `get_depths` / `emit_tick` / `start` / `subscribe` / `stop`）
- 删除示例 `20_miniqmt_ask_bid.py`（能力已由统一 `get_depths` 与模板示例覆盖）

## [1.0.1] - 2026-04-24
### miniQMT 基于 bid/ask 下单完善
- `MiniQmtDataGateway`：增强 tick 数值兼容逻辑，`_to_f` 现在可处理 `list/tuple` 形式字段（取首值后再转换），降低不同柜台返回格式导致的解析失败风险
- `LiveEngine`：信号翻转下单时明确基于盘口价执行（买单取 `ask`、卖单取 `bid`），无盘口时回退到 `last`，并补充买卖下单日志，便于排查成交偏差

## [1.0.0] - 2026-04-22
### miniQMT 实盘链路完善
- `LiveEngine`：新增 miniQMT 柜台资金/持仓快照读取（`_account_snapshot`），支持策略 `order_quantity`（买卖统一股数上限），并在信号翻转时先判断上一挂单是否终态再决定是否撤单，降低反向误撤/误成交风险
- `LiveEngine`：重构 Tick 处理流程（信号构建、权益记录、下单 sizing、翻转下单拆分），同时增强日志精度（价格四位小数）并在有行情字段时输出 bid/ask
- `TickData`：新增 `bid` / `ask` 字段，支持下游策略与日志感知买一卖一

### 数据与交易适配器
- `MiniQmtDataGateway`：新增 `get_full_tick_dict(symbol)`，并在 poll/push 两种模式下统一补充 bid/ask；同时完善生命周期与 warm-up/退订相关处理
- `MiniQmtTradeGateway`：交易网关实现迁移到 `deltafq/adapters/trade/miniqmt_gateway.py` 并调整导出路径；下单保持限价单与 `lot_size` 对齐，撤单失败时支持按合同号兜底
- `MiniQmtXtTraderClient` 与 `miniqmt_xtdata`：补充接口说明与注释，保持交易查询与历史数据工具语义一致

### 文档与示例
- 新增 `documents/MiniQmtLiveEngine.md`，补充 LiveEngine + miniQMT 的分阶段上线与验证清单
- 更新 `documents/LiveEngine.md`，明确 paper 与 miniQMT 在撮合、账户快照、撤单判定上的差异
- 更新 `documents/MiniQmtTrade.md`，新增 `order_status` 枚举对照表，便于委托终态判断与对账
- 示例 `19_miniqmt_live_engine.py`：新增 LiveEngine + miniQMT 行情/交易联调示例

## [0.9.1] - 2026-04-20
- `BacktestEngine.set_parameters`：`data_source` 未传入时不再默认 `"yahoo"`，保留 `BacktestEngine(..., data_source=...)` 构造时已选数据源，避免 Yahoo 与 miniQMT 混用时被静默切回 yfinance

## [0.9.0] - 2026-04-17
### miniQMT 交易接入
- 交易客户端：新增 `MiniQmtXtTraderClient`，支持连接、下单、撤单、账户/持仓/委托/成交查询
- 交易网关：新增 `MiniQmtTradeGateway`，支持限价单、`lot_size` 对齐与撤单回退
- 注册导出：`TRADE_GATEWAYS` 注册 `miniqmt`，并在 `deltafq.live` 与 `deltafq.adapters.trade` 导出
- 示例 `18_miniqmt_trade_demo.py`：新增 miniQMT 实盘连接、查询、限价下单与批量撤单演示

## [0.8.3] - 2026-04-17
### miniQMT 数据接入
- 数据网关：`MiniQmtDataGateway` 新增 `mode`（`poll` / `push`）与推送清理逻辑
- 示例 `17_miniqmt_live_push.py`：由 `17_qmt_tick_push.py` 更名，演示 miniQMT push 模式分笔订阅
- 示例 `16_fetch_miniqmt_data.py`：简化为历史 K 线拉取与落盘
- 示例 `01_fetch_yahoo_data.py`：补充可选 HTTP/HTTPS 代理说明

## [0.8.2] - 2026-04-17
- pandas 兼容：`DataCleaner` 与绩效图基准序列不再使用已弃用的 `fillna(method=...)`，改为 `ffill()` / `bfill()`
- 示例 `17_miniqmt_live_push.py`：新增 miniQMT 分笔行情 `subscribe_quote` 推送演示

## [0.8.1] - 2026-04-16
- 文档同步：更新 README（中英文）与 LiveEngine/BacktestEngine 文档，补齐 miniQMT 接入与数据源映射说明

## [0.8.0] - 2026-04-16
### miniQMT 数据源全链路接入
- 数据接入：`DataFetcher(source="miniqmt")` 支持通过 `xtquant.xtdata` 拉取历史 OHLCV，并对齐 yfinance 列名
- 数据网关：新增 `MiniQmtDataGateway` 并注册到 `LiveEngine`，支持订阅、轮询快照与 `miniqmt_warmup` 预热推送
- 引擎联动：`LiveEngine` 按网关自动映射 DataFetcher source，并忽略 warm-up tick 防止误触发策略
- 示例 `16_fetch_miniqmt_data.py`：新增 miniQMT 历史数据拉取、落盘与实时快照演示
- 依赖调整：新增 `xtquant`；`plotly` 与 `TA-Lib` 改为默认安装依赖

## [0.7.9] - 2026-03-06
- PerformanceReporter：总成交额（total_turnover）改为按每笔「|数量|×价格」汇总，买卖两侧均计入，修正原先仅统计 gross_revenue（仅卖出）导致的少计

## [0.7.8] - 2026-03-05
- LiveEngine：运行中录制净值曲线（_values_records），新增 `get_trades_df()`、`get_values_df()`、`calculate_metrics()`，与 BacktestEngine 同 API，可随时计算收益、回撤、夏普等指标
- 示例 `15_live_engine_tpl.py`：退出后打印 Trades / Orders / Values / Metrics，统一分节格式

## [0.7.7] - 2026-03-02
- LiveEngine：仅在实际撤销挂单成功时打印 "Cancelled pending order"，避免订单已成交时误报撤单日志

## [0.7.6] - 2026-03-02
- LiveEngine：信号反转时撤销前一挂单，记录 `_last_pending_order_id`，避免限价单在信号翻转后仍被成交导致方向错误

## [0.7.5] - 2026-02-28
- LiveEngine：缓存 K 线与信号，新增 `get_chart_data()` 供应用层直接获取图表数据，无需重复拉取或计算
- LiveEngine：支持策略设置 `order_amount`（单次买入投入金额），策略 `self.order_amount = 10000` 即可生效，未设置则全仓
- LiveEngine：yfinance end_date 改为次日（exclusive），修复 get_chart_data 1m 数据显示昨日的问题
- TradeGateway：接口新增 `stop()`，Paper 实现 pass，为实盘扩展预留
- 日志：Logger 格式简化为单 `>>>`；Signal/订单/仓位加 ASCII 图标（↑↓✓○x-），run_live 加「开始运行」前缀
- 文档：新增 `documents/LiveEngine.md`、`documents/BacktestEngine.md` 使用说明与架构
- 示例 `15_live_engine_tpl.py`：Plotly K 线+信号图，Trades/Orders 时间到秒、浮点两位小数

## [0.7.4] - 2026-02-27
- LiveEngine：数据不足时使用可用 bars 替代返回 None，修复 1d 周期下每 tick 重复拉取
- LiveEngine：按 lookback_bars 与周期（1d/1wk/1mo）计算请求日期范围，保证 bars 充足
- 统一日志格式：Order pending/filled、Tick、Signal 采用 `Type: details` 结构，便于排查与复盘

## [0.7.3] - 2026-02-25
- 新增 LiveEngine：实盘/模拟入口——用实时数据跑策略并下单，串联数据网关、策略调度与交易网关，与回测同一套策略、不同引擎
- 优化 LiveEngine：网关配置改为独立方法 `set_data_gateway(name, **params)`、`set_trade_gateway(name, **params)`，`set_parameters` 仅保留 symbol/interval/lookback_bars/signal_interval；资金与手续费由 Trade Gateway 决定，可通过 `set_trade_gateway("paper", initial_capital=..., commission=...)` 传入
- 示例：`15_live_engine_tpl.py` 策略改为 Every5BarFlipStrategy（每 2 次运行翻转 1/-1），便于快速触发买卖、验证撮合

## [0.7.2] - 2026-02-21
- DataFetcher：`fetch_data` / `fetch_data_multiple` 新增参数 `interval`（默认 `"1d"`），支持多周期（如 `"1m"`、`"5m"`、`"1h"`、`"1d"`、`"1wk"`、`"1mo"`），兼容原有调用
- 新增示例 `14_auto_trade_demo.py`：基于 DataFetcher 的策略自动化（按 interval 区分 5m/1d 等），拉数据、算信号、存盘、按信号用 ExecutionEngine 模拟交易

## [0.7.0] - 2026-02-03
- 本地模拟交易：ExecutionEngine 支持 `match_on_tick`，限价单挂单后由 `on_tick` 按行情撮合
- 统一成交结算入口：`_execute_paper_trade` 重命名为 `_on_trade`，负责资金与仓位更新
- PaperTradeGateway 迁至 `paper_gateway.py`，默认 `match_on_tick=True`，与回测（立即成交）区分
- 事件驱动示例：新增 `13_local_sim_trading.py`，EventEngine 消费行情、完全依赖 Tick 流取价与下单
- YFinanceDataGateway 新增 `get_last_price(symbol)`，便于按网关取当前价

## [0.6.5] - 2026-02-02
- 修复实时数据不更新问题：移除 Ticker 对象缓存，每次轮询创建新实例确保获取最新 price 和 volume

## [0.6.4] - 2026-02-02
- 新增 `YFinanceDataGateway.get_today_ohlc()` 方法，支持获取当日开盘、最高、最低价格
- 优化 yfinance 网关性能：复用 Ticker 对象缓存，减少重复创建开销
- 更新示例：`12_yfinance_live_push.py` 添加 `get_today_ohlc` 调用示例

## [0.6.3] - 2026-01-29
- 统一时区标准：yfinance 数据网关全面转向 Naive UTC，解决美股与加密货币跨零点数据缺失问题

## [0.6.2] - 2026-01-26
- 增强 yfinance 行情预加载逻辑，支持获取当日历史分钟线数据
- 实现自动时区转换，确保历史数据与实时行情的时间对齐

## [0.6.1] - 2026-01-26
- 引入 yfinance `fast_info` 实时行情接口与推送机制
- 优化实盘模块架构，实现网关与事件引擎的标准化对接
- 更新文档，明确工业级量化闭环工作流定位与接口集成状态

## [0.6.0] - 2026-01-20
- 精简实时交易模块结构，引入可插拔网关与适配器目录
- 新增 Akshare A 股实时行情示例

## [0.5.2] - 2025-12-19
- 新增基金历史净值数据获取功能：`DataFetcher.fetch_fund()`，支持从东方财富获取基金数据
- 新增基金数据获取示例：`11_fetch_fund_data.py`

## [0.5.1] - 2025-12-01
- 增加基本面因子计算与相关示例（如 `10_fundamental_indicators.py`）；为策略和分析提供更多财报指标支持

## [0.5.0] - 2025-11-14
- 删除 /test, core/Exception.py 等相关配置和依赖（用户通过脚本实现测试）
- 新增多因子策略示例：`09_multi_factor_strategy.ipynb`
- 新增策略模板示例： `08_deltafq_template.ipynb`

## [0.4.3] - 2025-11-13
- 重构 `BacktestEngine`：提供策略全流程快速调用方法，实现开箱即用
- 修复未平仓持仓计算：修复回测结束时如果最后一笔是买入而非卖出平仓，未平仓持仓的浮动盈亏未计入 `total_pnl` 的问题
- 重构 `BaseComponent`：将 `initialize()` 方法从抽象方法改为可选方法，提供默认实现
- 优化组件初始化：删除所有仅记录日志的 `initialize()` 方法，将日志输出移到 `__init__` 中

## [0.4.2] - 2025-11-12
- `BaseStrategy.generate_signals` 统一输出 `Series`，与信号生成器保持一致。
- 优化策略执行与 Plotly 相关日志，兼顾兼容性和易读性。

## [0.4.1] - 2025-11-10
- 新增快速回测示例：`05_backtest_report.py`、`05_backtest_charts.py`、`06_baseStrategy_backtestEngine.py`。
- 图表配色统一为“红买绿卖”，盈亏显示风格一致。
- 精简核心模块公开接口并同步完善文档。

## [0.3.1] - 2025-11-07
- 增补示例，覆盖基础策略执行、图表预览与快速历史数据获取。
- 性能图支持 Plotly 导出，图表模块 API 与配色规则统一。
- `PerformanceReporter` 内建指标计算，移除旧数据类；优化 `DataFetcher` 描述与文档。
- 弃用 `deltafq/backtest/reporter.py`，收益分布与基准对比更清晰。

## [0.3.0] - 2025-11-06
- 信号与绩效图表新增基准叠加、Plotly 支持及更多展示面板。
- 策略信号加入布林带 `cross_current`，示例与 README 同步调整。
- 新增安装可选项（`viz`、`talib`）及版本文件 `VERSION`。
- 回测引擎拆分执行模块，绩效统计更精简，报告支持中英文。
- 移除 Seaborn 依赖。

---

0.3.0 之前的版本属于内部迭代。***

