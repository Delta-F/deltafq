"""DataGateway 公开 API 烟测：改 NAME、SYMBOL。"""
import os
import sys
import threading
from datetime import datetime

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from deltafq.live import create_data_gateway
from deltafq.live.gateways import DataGateway
from deltafq.live.models import TickData

NAME = "miniqmt"  # "yfinance" | "miniqmt"
SYMBOL = "600000.SH" # "AAPL" | "600000.SH"

_LIVE = {"yfinance": ("yfinance",), "miniqmt": ("miniqmt", "miniqmt_push")}


def sec(t: str) -> None:
    print(f"\n--- {t} ---")


def kv(k: str, v: object) -> None:
    print(f"  {k}: {v}")


def print_depths(depths: dict) -> None:
    bids = depths.get("bids") or []
    asks = depths.get("asks") or []
    for row in bids:
        lv = int(row.get("level", 0))
        kv(f"bid{lv}", f"px={row.get('price')} vol={row.get('volume')}")
    for row in asks:
        lv = int(row.get("level", 0))
        kv(f"ask{lv}", f"px={row.get('price')} vol={row.get('volume')}")


if __name__ == "__main__":
    # 创建数据网关（可切换 yfinance / miniqmt）
    gw: DataGateway = create_data_gateway(NAME, interval=5.0)

    sec("inst")
    # 查看网关公开方法列表
    ms = [n for n in sorted(dir(gw)) if not n.startswith("_") and callable(getattr(gw, n, None))]
    kv("methods", ", ".join(ms))
    # 查看实例公开属性（隐藏 logger 具体对象）
    ad = {k: ("<logger>" if k == "logger" else v) for k, v in vars(gw).items() if not k.startswith("_")}
    kv("attrs", ad)

    sec("connect")
    # 建立连接
    assert gw.connect()
    kv("ok", True)

    sec("get_today_ohlc")
    # 获取当日开高低
    kv(SYMBOL, gw.get_today_ohlc(SYMBOL))

    sec("get_depths")
    # 获取盘口深度（一行一档）
    d = gw.get_depths(SYMBOL)
    print_depths(d)

    n_live, done = [0], threading.Event()
    live = _LIVE.get(NAME, ())

    _wu = ("yf_warmup", "miniqmt_warmup")

    def on_tick(t: TickData) -> None:
        if t.symbol != SYMBOL:
            return
        if t.source not in _wu:
            kv("tick", f"{t.source} px={t.price}")
        if live and t.source not in live:
            return
        n_live[0] += 1
        if n_live[0] >= 5: # 5 次后结束
            done.set()

    sec("emit_tick")
    # 注册 Tick 回调
    gw.set_tick_handler(on_tick)
    # 主动触发一次回调，验证分发链路
    gw.emit_tick(TickData(symbol=SYMBOL, price=0.0, timestamp=datetime.utcnow(), source="tpl_emit"))

    sec("live")
    # 启动网关循环（轮询/推送）
    gw.start()
    # 订阅测试标的
    assert gw.subscribe([SYMBOL])
    try:
        done.wait(45.0)
        kv("live_ticks", n_live[0])
    finally:
        # 停止网关并释放资源
        gw.stop()
        kv("stop", True)
