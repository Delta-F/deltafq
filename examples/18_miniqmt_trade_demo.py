"""Minimal example: miniQMT trade demo - connect → query → limit order/cancel."""

import os
import sys
from time import sleep
import threading

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from deltafq.adapters.data import MiniQmtDataGateway
from deltafq.adapters.trade import MiniQmtTradeGateway
from deltafq.live.models import OrderRequest, TickData

# 配置 miniQMT 环境变量
MIN_PATH = os.environ.get("QMT_USERDATA_MINI", r"D:\国金证券QMT交易端\userdata_mini")
ACCOUNT_ID = os.environ.get("QMT_ACCOUNT_ID", "8886180407")


def connect_broker() -> MiniQmtTradeGateway:
    gw = MiniQmtTradeGateway(userdata_mini_path=MIN_PATH, account_id=ACCOUNT_ID)
    if not gw.connect():
        sys.exit("connect failed")
    return gw


def run_queries(gw: MiniQmtTradeGateway) -> None:
    c = gw.client
    for x in c.query_account_infos() or []:
        print("account_info", x)
    for s in c.query_account_status() or []:
        print(f"account_status id={s.account_id} type={s.account_type} st={s.status}")

    a = c.query_stock_asset()
    if a is None:
        print("asset", None)
    else:
        print(f"asset cash={a.cash} frozen={a.frozen_cash} mv={a.market_value} total={a.total_asset}")

    pos = c.query_stock_positions()
    print(f"positions n={len(pos)}")
    for p in pos:
        print(f"  {p.stock_code} vol={p.volume} can_use={p.can_use_volume}")

    orders = c.query_stock_orders(cancelable_only=False)
    trades = c.query_stock_trades()
    print(f"orders n={len(orders)} (show 5)")
    for o in orders[:5]:
        print(f"  {o.order_id} {o.stock_code} vol={o.order_volume} px={o.price} st={o.order_status}")
    print(f"trades n={len(trades)} (show 5)")
    for t in trades[:5]:
        print(f"  {t.stock_code} px={t.traded_price} vol={t.traded_volume}")


def run_orders(gw: MiniQmtTradeGateway) -> None:
    code = "000001.SZ"
    # 通过 tick 回调获取最新价
    data_gw = MiniQmtDataGateway(interval=1.0, mode="poll")
    if not data_gw.connect():
        raise ValueError("行情网关连接失败")
    done = threading.Event()
    latest = {"price": None}

    def on_tick(tick: TickData) -> None:
        if tick.symbol != code:
            return
        latest["price"] = float(tick.price)
        done.set()

    data_gw.set_tick_handler(on_tick)
    data_gw.start()
    data_gw.subscribe([code])
    ok = done.wait(timeout=5.0)
    data_gw.stop()
    if not ok or latest["price"] is None or latest["price"] <= 0:
        raise ValueError(f"无有效最新价: {code!r}")
    last_f = float(latest["price"])
    
    # 较最新价下调比例
    delta = 0.03
    limit_px = round(last_f * (1 - delta), 2)
    print(f"order {code} last={last_f} limit={limit_px} (-{delta*100}%)")
    oid = gw.send_order(OrderRequest(code, 100, limit_px, "limit"))
    print("send_order", oid)

    # 等待5秒后撤销全部订单
    sleep(5)
    for o in gw.client.query_stock_orders(cancelable_only=True):
        print(f"cancel_order {o.order_id}")
        gw.cancel_order(o.order_id)


if __name__ == "__main__":
    gw = connect_broker()
    try:
        # run_queries(gw)
        run_orders(gw)
    finally:
        gw.stop()
    """
    输出示例：
    ***** xtdata连接成功 2026-04-17 11:31:59*****
    服务信息: {'tag': 'sp3', 'version': '1.0'}
    服务地址: 127.0.0.1:58610
    数据路径: D:\国金证券QMT交易端\bin.x64/../userdata_mini/datadir
    设置xtdata.enable_hello = False可隐藏此消息

    order 000001.SZ last=11.05 limit=10.72 (-3.0%)
    send_order 1098986390
    cancel_order 1098986370
    cancel_order 1098986378
    cancel_order 1098986390
    """
