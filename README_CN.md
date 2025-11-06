# DeltaFQ

现代化的 Python 量化库：策略研究、回测、模拟/实盘交易与精美报告。

## 特性亮点

- **清晰架构**：`data` → `strategy`（信号）→ `backtest`（执行）→ `performance`（指标）→ `reporter`（文本+图表）
- **执行引擎**：统一下单执行；`Broker` 抽象兼容纸面与实盘
- **技术指标**：`TechnicalIndicators`（SMA/EMA/RSI/KDJ/BOLL/ATR/...）
- **信号模块**：`SignalGenerator`（如 BOLL 的 `touch`/`cross`/`cross_current`）
- **可视化**：默认 Matplotlib；支持 Plotly 生成交互式业绩图
- **报告**：控制台友好报告（中/英）+ 可视化图表

## 安装

```bash
pip install deltafq
```

## 60 秒快速上手（BOLL 策略）

```python
import deltafq as dfq

symbol = 'AAPL'
fetcher = dfq.data.DataFetcher(); indicators = dfq.indicators.TechnicalIndicators()
generator = dfq.strategy.SignalGenerator()
engine = dfq.backtest.BacktestEngine(initial_capital=100000)
perf = dfq.backtest.PerformanceAnalyzer(); reporter = dfq.backtest.BacktestReporter()

data = fetcher.fetch_data(symbol, '2023-01-01', '2023-12-31', clean=True)
bands = indicators.boll(data['Close'], period=20, std_dev=2)
signals = generator.boll_signals(price=data['Close'], bands=bands, method='cross_current')

trades_df, values_df = engine.run_backtest(symbol, signals, data['Close'], strategy_name='BOLL')
values_df, metrics = perf.get_performance_metrics(symbol, trades_df, values_df, engine.initial_capital)

reporter.generate_visual_report(metrics=metrics, values_df=values_df, title=f'{symbol} BOLL 策略', language='zh')
```

## 目录说明

- `deltafq/data`：数据获取、清洗与校验
- `deltafq/indicators`：经典技术指标
- `deltafq/strategy`：信号生成与组合
- `deltafq/backtest`：执行引擎、业绩分析与报告
- `deltafq/charts`：信号与业绩图表（Matplotlib + Plotly 可选）

## 示例

示例位于 `examples/`：
- 指标/信号对比
- BOLL 策略回测与完整报告

## 贡献

欢迎参与完善！提交 Issue 或 Pull Request 即可。

## 许可证

MIT 许可协议，见 [LICENSE](LICENSE)。
