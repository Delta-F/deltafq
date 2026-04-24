"""需 miniQMT 已启动：五档盘口来自 get_full_tick 快照。"""
import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from deltafq.adapters.data import MiniQmtDataGateway


def depth5(symbol: str) -> dict:
    """经 MiniQmtDataGateway 拉全快照；五档在 askPrice/bidPrice 与 askVol/bidVol。"""
    gw = MiniQmtDataGateway(interval=3.0)
    if not gw.connect():
        return {}
    return gw.get_full_tick_dict(symbol)


if __name__ == "__main__":
    sym = "600000.SH"
    t = depth5(sym)
    if not t:
        print("无数据（检查 miniQMT / connect）")
    else:
        print(t["timetag"], t["lastPrice"])
        print("卖", list(zip(t["askPrice"], t["askVol"])))
        print("买", list(zip(t["bidPrice"], t["bidVol"])))
