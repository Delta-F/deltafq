"""Minimal LiveEngine demo: set symbol/params -> add_strategy -> run_live."""

import sys
import os
import time

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pandas as pd
from deltafq.live import LiveEngine
from deltafq.strategy.base import BaseStrategy


class Every2BarFlipStrategy(BaseStrategy):
    """Every 2 strategy runs flip signal 1/-1 for quick verification."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._run_count = 0
        self.order_amount = 100000 # 单次买入投入金额

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        self._run_count += 1
        sig = 1 if (self._run_count // 2) % 2 == 0 else -1
        return pd.Series([sig] * len(data), index=data.index)


def main():
    engine = LiveEngine(
        symbol="BTC-USD",
        interval=10.0,
        lookback_bars=50,
        signal_interval="1m",
    )
    engine.set_trade_gateway("paper", initial_capital=1_000_000)
    engine.add_strategy(Every2BarFlipStrategy(name="Every2Flip"))
    engine.run_live()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        engine.stop()

    # print trades and orders
    def _fmt_dt_cols(df):
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = df[col].apply(lambda x: x.strftime("%Y-%m-%d %H:%M:%S") if pd.notna(x) else "")
        return df

    eng = engine._trade_gw._engine if engine._trade_gw else None
    if eng:
        trades = eng.trades
        orders = eng.order_manager.get_order_history()
        if trades:
            df_t = _fmt_dt_cols(pd.DataFrame(trades))
            print("\n=== Trades (DataFrame) ===")
            print(df_t.to_string(float_format="%.2f"))
        if orders:
            df_o = _fmt_dt_cols(pd.DataFrame(orders))
            print("\n=== Orders (DataFrame) ===")
            print(df_o.to_string(float_format="%.2f"))

    # plot K-line & signal (Plotly)
    chart = engine.get_chart_data()
    if chart["candles"]:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        df = pd.DataFrame(chart["candles"]).set_index("date")
        df.index = pd.to_datetime(df.index)
        sig = pd.Series(chart["signals"], index=df.index)
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.75, 0.25],
                            specs=[[{"type": "candlestick"}], [{"type": "scatter"}]])
        fig.add_trace(go.Candlestick(x=df.index, open=df.open, high=df.high, low=df.low, close=df.close), row=1, col=1)
        fig.add_trace(go.Scatter(x=sig.index, y=sig.values, mode="lines", name="Signal", line=dict(dash="dot")), row=2, col=1)
        fig.update_layout(template="plotly_white")
        fig.show()


if __name__ == "__main__":
    main()
