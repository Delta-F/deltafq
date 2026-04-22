# miniQMT 实盘交易接口接入说明

本文说明 DeltaFQ 中 miniQMT 交易网关的接入方式、参数和常见注意事项。

---

## 一、组件关系

- `MiniQmtXtTraderClient`：对 `xtquant.xttrader` 的薄封装，负责连接、账号订阅、下单、撤单、查询
- `MiniQmtTradeGateway`：对齐 `TradeGateway` 接口，供 `LiveEngine` 统一调用

---

## 二、前置条件

- 本机已安装并可导入 `xtquant`
- 本机已启动 miniQMT 终端
- 已知 `userdata_mini` 目录与资金账号

可选环境变量：

- `QMT_USERDATA_MINI`
- `QMT_ACCOUNT_ID`

---

## 三、在 LiveEngine 中接入

```python
from deltafq.live import LiveEngine

engine = LiveEngine(symbol="000001.SZ", signal_interval="1m", lookback_bars=100)
engine.set_data_gateway("miniqmt", interval=3.0, mode="poll")
engine.set_trade_gateway(
    "miniqmt",
    userdata_mini_path=r"D:\券商QMT\userdata_mini",
    account_id="1234567890",
    strategy_name="deltafq",
    order_remark="",
    lot_size=100,
)
```

---

## 四、参数说明（Trade Gateway）

- `userdata_mini_path`: miniQMT 用户数据目录（可从环境变量读取）
- `account_id`: 资金账号（可从环境变量读取）
- `session_id`: 会话 ID；不传时自动生成随机整数
- `strategy_name`: 下单策略名，透传到柜台
- `order_remark`: 委托备注，透传到柜台
- `lot_size`: 手数对齐，默认 100（A 股整手）

---

## 五、当前行为与限制

- 当前仅支持 `order_type="limit"`
- `quantity` 必须非 0；会按 `lot_size` 向下对齐
- `send_order` 返回字符串 `order_id`
- `cancel_order` 先按本地委托号撤单，失败时回退按 `order_sysid` 撤单

---

## 六、查询接口（通过 client）

可通过 `gateway.client` 访问柜台查询：

- `query_account_infos()`
- `query_account_status()`
- `query_stock_asset()`
- `query_stock_positions()`
- `query_stock_position(stock_code)`
- `query_stock_orders(cancelable_only=False)`
- `query_stock_trades()`

---

## 七、示例脚本

参考：`examples/18_miniqmt_trade_demo.py`

脚本覆盖流程：

- 连接与账号查询
- 读取最新价后发限价单
- 查询可撤委托并批量撤单

---

## 八、委托状态 order_status

`query_stock_orders` 等返回的委托对象上常见字段 `order_status`，取值与 `xtquant.xtconstant` 中枚举一致（以下为官方文档常用对照，便于对账与判断终态）。

| 枚举变量名 | 值 | 含义 |
| :--- | :---: | :--- |
| `xtconstant.ORDER_UNREPORTED` | 48 | 未报 |
| `xtconstant.ORDER_WAIT_REPORTING` | 49 | 待报 |
| `xtconstant.ORDER_REPORTED` | 50 | 已报 |
| `xtconstant.ORDER_REPORTED_CANCEL` | 51 | 已报待撤 |
| `xtconstant.ORDER_PARTSUCC_CANCEL` | 52 | 部成待撤 |
| `xtconstant.ORDER_PART_CANCEL` | 53 | 部撤（部分成交，剩余已撤） |
| `xtconstant.ORDER_CANCELED` | 54 | 已撤 |
| `xtconstant.ORDER_PART_SUCC` | 55 | 部成（部分成交，剩余待成交） |
| `xtconstant.ORDER_SUCCEEDED` | 56 | 已成 |
| `xtconstant.ORDER_JUNK` | 57 | 废单 |
| `xtconstant.ORDER_UNKNOWN` | 255 | 未知 |

**用途简述**：判断是否需要再发撤单（例如已成 `56` 则不必撤）、区分废单与已撤、与 miniQMT 客户端委托列表核对。`LiveEngine` 当前仍以撤单接口返回码与本地 `_last_pending_order_id` 为主，若要做严谨终态同步，可基于上表轮询 `query_stock_orders`。
