# DeltaFQ

现代化的 Python 量化库：策略研究、回测、模拟/实盘交易与精简报告。

## 特性亮点

- **清晰架构**：`data` → `strategy`（信号）→ `backtest`（执行与指标）
- **执行引擎**：统一下单执行；`Broker` 抽象兼容纸面与实盘
- **技术指标**：`TechnicalIndicators`（SMA/EMA/RSI/KDJ/BOLL/ATR/...）
- **信号模块**：`SignalGenerator`（如 BOLL 的 `touch`/`cross`/`cross_current`）
- **文字报告**：`PerformanceReporter` 提供中/英控制台摘要
- **可视化**：`PerformanceChart` 支持 Matplotlib 与 Plotly（可选）

## 安装

```bash
pip install deltafq
```

## 60 秒快速上手（BOLL 策略）

```python
import deltafq as dfq

symbol = "AAPL"
fetcher = dfq.data.DataFetcher()
indicators = dfq.indicators.TechnicalIndicators()
generator = dfq.strategy.SignalGenerator()
engine = dfq.backtest.BacktestEngine(initial_capital=100_000)
reporter = dfq.backtest.PerformanceReporter()
chart = dfq.charts.PerformanceChart()

data = fetcher.fetch_data(symbol, "2023-01-01", "2023-12-31", clean=True)
bands = indicators.boll(data["Close"], period=20, std_dev=2)
signals = generator.boll_signals(price=data["Close"], bands=bands, method="cross_current")

trades_df, values_df = engine.run_backtest(symbol, signals, data["Close"], strategy_name="BOLL")

# 控制台报告（支持中文/英文）
reporter.print_summary(
    symbol=symbol,
    trades_df=trades_df,
    values_df=values_df,
    title=f"{symbol} BOLL 策略",
    language="zh",
)

# 可选的业绩可视化（默认 Matplotlib；use_plotly=True 开启交互式图表）
chart.plot_backtest_charts(values_df=values_df, benchmark_close=data["Close"], title=f"{symbol} BOLL 策略")
```

## 目录说明

- `deltafq/data`：数据获取、清洗与校验
- `deltafq/indicators`：经典技术指标
- `deltafq/strategy`：信号生成与 `BaseStrategy` 框架
- `deltafq/backtest`：执行引擎与业绩摘要
- `deltafq/charts`：信号与业绩图表（Matplotlib + Plotly 可选）

## 示例

示例位于 `examples/`：

- `04_backtest_result.py`：BOLL 策略回测，输出文字与图表
- `05_visualize_charts.py`：独立可视化演示
- `06_base_strategy`：演示基于 `BaseStrategy` 的均线交叉策略

## 贡献

欢迎参与完善！提交 Issue 或 Pull Request 即可。

## 许可证

MIT 许可协议，见 [LICENSE](LICENSE)。
