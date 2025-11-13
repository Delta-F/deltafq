# 更新日志

项目遵循语义化版本，此处简要记录关键变化。

## [0.4.3] - 2025-01-XX
- 重构 `BaseComponent`：将 `initialize()` 方法从抽象方法改为可选方法，提供默认实现
- 优化组件初始化：删除所有仅记录日志的 `initialize()` 方法，将日志输出移到 `__init__` 中
- 重构 `BacktestEngine`：将初始化逻辑从 `initialize()` 移到 `__init__`，支持在创建时传入参数
- 修复未平仓持仓计算：修复回测结束时如果最后一笔是买入而非卖出平仓，未平仓持仓的浮动盈亏未计入 `total_pnl` 的问题

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

