"""
Local simulation trading example.

- Event-driven: gateway -> EventEngine(EVENT_TICK) -> execution engine.on_tick + print.
- Price from tick stream only: wait for first live tick, then send limit order.
- PaperTradeGateway (match_on_tick=True): limit orders match in on_tick.
"""

import sys
import os
import time
import threading

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from deltafq.live.event_engine import EventEngine, EVENT_TICK
from deltafq.live.gateway_registry import create_data_gateway, create_trade_gateway
from deltafq.live.models import OrderRequest


def main():
    symbol = "000001.SS"
    last_tick_price = {}
    first_live_tick = threading.Event()

    # 1. Event engine + gateways
    event_engine = EventEngine()
    data_gw = create_data_gateway("yfinance", interval=10.0)
    trade_gw = create_trade_gateway("paper", initial_capital=100_000.0, commission=0.001)

    if not trade_gw.connect() or not data_gw.connect():
        print("Connect failed.")
        return

    # 2. EVENT_TICK handlers: match orders + update price & print live
    def on_tick_match(tick):
        trade_gw._engine.on_tick(tick)

    def on_tick_print(tick):
        if getattr(tick, "source", None) != "yf_warmup":
            last_tick_price[tick.symbol] = tick.price
            first_live_tick.set()
            ts = tick.timestamp.strftime("%H:%M:%S") if tick.timestamp else ""
            print(f"[Live] {tick.symbol} -> {tick.price} | Vol: {tick.volume or '-'} @ {ts}")

    event_engine.on(EVENT_TICK, on_tick_match)
    event_engine.on(EVENT_TICK, on_tick_print)
    data_gw.set_tick_handler(lambda t: event_engine.emit(EVENT_TICK, t))

    # 3. Subscribe & start (ticks flow via EventEngine)
    data_gw.subscribe([symbol])
    data_gw.start()

    # 4. Wait for first live tick, then send order (price from tick stream only)
    if not first_live_tick.wait(timeout=60):
        print("No live tick in 60s, exit.")
        data_gw.stop()
        return
    last = last_tick_price.get(symbol, 150.0)
    limit_price = round(last + 0.5, 2)
    req = OrderRequest(symbol=symbol, quantity=10, price=limit_price, order_type="limit")
    order_id = trade_gw.send_order(req)
    print(f"Order submitted: {order_id} | {symbol} buy 10 @ {limit_price} (pending until tick matches)")

    # 5. Run a while (only print when a new trade appears)
    printed_trade_count = 0
    try:
        for _ in range(35):
            time.sleep(1)
            trades = trade_gw._engine.trades
            if len(trades) > printed_trade_count:
                for t in trades[printed_trade_count:]:
                    print(f"  -> Filled: {t['type']} {t['symbol']} qty={t['quantity']} @ {t['price']}")
                printed_trade_count = len(trades)
    except KeyboardInterrupt:
        pass

    data_gw.stop()
    print("\n--- Summary ---")
    print("Positions:", trade_gw._engine.position_manager.get_all_positions())
    print("Cash:", round(trade_gw._engine.cash, 2))
    print("Trades:", len(trade_gw._engine.trades))


if __name__ == "__main__":
    main()
