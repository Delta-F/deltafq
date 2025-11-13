"""Minimal signal chart helper."""

from typing import Dict, Optional

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ..core.base import BaseComponent


class SignalChart(BaseComponent):
    def __init__(self, **kwargs):
        """Initialize the signal chart."""
        super().__init__(**kwargs)
        self.logger.info("Initializing signal chart")

    def plot_boll_signals(
        self,
        data: pd.DataFrame,
        bands: Dict[str, pd.Series],
        signals: pd.Series,
        title: Optional[str] = None,
        use_plotly: bool = False,
    ) -> None:
        required = {"Open", "High", "Low", "Close"}
        if not required.issubset(data.columns):
            raise ValueError(f"data must contain columns: {required}")

        frame = data.copy()
        frame.index = pd.to_datetime(frame.index)
        signals = signals.reindex(frame.index)

        upper = bands.get("upper", pd.Series(index=frame.index)).reindex(frame.index)
        middle = bands.get("middle", pd.Series(index=frame.index)).reindex(frame.index)
        lower = bands.get("lower", pd.Series(index=frame.index)).reindex(frame.index)

        if use_plotly:
            try:
                import plotly.graph_objects as go
                from plotly.subplots import make_subplots
            except ImportError as exc:  # pragma: no cover
                self.logger.info(f"Plotly not available ({exc}); falling back to Matplotlib")
            else:
                fig = make_subplots(
                    rows=2,
                    cols=1,
                    shared_xaxes=True,
                    row_heights=[0.78, 0.22],
                    specs=[[{"type": "candlestick"}], [{"type": "scatter"}]],
                )
                fig.add_trace(
                    go.Candlestick(
                        x=frame.index,
                        open=frame["Open"],
                        high=frame["High"],
                        low=frame["Low"],
                        close=frame["Close"],
                        name="Price",
                        increasing_line_color="#ef4444",
                        decreasing_line_color="#22c55e",
                    ),
                    row=1,
                    col=1,
                )
                for name, series, color in (
                    ("Upper", upper, "#2563eb"),
                    ("Middle", middle, "#7c3aed"),
                    ("Lower", lower, "#0ea5e9"),
                ):
                    fig.add_trace(
                        go.Scatter(x=series.index, y=series.values, mode="lines", name=name, line=dict(color=color)),
                        row=1,
                        col=1,
                    )
                buy_mask = signals == 1
                sell_mask = signals == -1
                fig.add_trace(
                    go.Scatter(
                        x=signals.index[buy_mask],
                        y=frame.loc[buy_mask, "Close"],
                        mode="markers",
                        name="Buy",
                        marker=dict(symbol="triangle-up", size=12, color="#ef4444"),
                    ),
                    row=1,
                    col=1,
                )
                fig.add_trace(
                    go.Scatter(
                        x=signals.index[sell_mask],
                        y=frame.loc[sell_mask, "Close"],
                        mode="markers",
                        name="Sell",
                        marker=dict(symbol="triangle-down", size=12, color="#22c55e"),
                    ),
                    row=1,
                    col=1,
                )
                fig.add_trace(
                    go.Scatter(
                        x=signals.index,
                        y=signals.values,
                        name="Signal",
                        mode="lines",
                        line=dict(color="#6b7280", dash="dot"),
                        showlegend=False,
                    ),
                    row=2,
                    col=1,
                )
                fig.update_xaxes(title_text="Date", row=2, col=1)
                fig.update_yaxes(title_text="Price", row=1, col=1)
                fig.update_yaxes(
                    title_text="Signal",
                    row=2,
                    col=1,
                    tickvals=[-1, 0, 1],
                    ticktext=["Sell", "Hold", "Buy"],
                    range=[-1.5, 1.5],
                )
                fig.update_layout(
                    title=title or "Bollinger Signal Chart",
                    template="plotly_white",
                    showlegend=True,
                )
                fig.show()
                return

        fig, (ax_price, ax_signal) = plt.subplots(2, 1, figsize=(12, 6), sharex=True, gridspec_kw={"height_ratios": [4, 1]})
        self._plot_candles(ax_price, frame)
        ax_price.plot(upper.index, upper.values, color="#2563eb", linewidth=1.2, label="Upper", zorder=2)
        ax_price.plot(middle.index, middle.values, color="#7c3aed", linewidth=1.0, linestyle="--", label="Middle", zorder=2)
        ax_price.plot(lower.index, lower.values, color="#0ea5e9", linewidth=1.2, label="Lower", zorder=2)
        self._plot_markers(ax_price, frame["Close"], signals)

        ax_price.set_title(title or "Bollinger Signal Chart", fontsize=14)
        ax_price.set_ylabel("Price")
        ax_price.grid(True, alpha=0.2, color="#d1d5db")
        handles, labels = ax_price.get_legend_handles_labels()
        unique = dict(zip(labels, handles))
        ax_price.legend(unique.values(), unique.keys(), frameon=False, loc="upper left")

        ax_signal.plot(signals.index, signals.values, color="#6b7280", linewidth=1.0, linestyle=":")
        ax_signal.set_ylabel("Signal")
        ax_signal.set_xlabel("Date")
        ax_signal.set_yticks([-1, 0, 1])
        ax_signal.set_yticklabels(["Sell", "Hold", "Buy"])
        ax_signal.grid(True, alpha=0.2, color="#d1d5db")

        for ax in (ax_price, ax_signal):
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right")
        plt.tight_layout()
        plt.show()

    def _plot_candles(self, ax: plt.Axes, frame: pd.DataFrame) -> None:
        x = mdates.date2num(frame.index.to_pydatetime())
        for xi, row in zip(x, frame[["Open", "High", "Low", "Close"]].itertuples(index=False)):
            o, h, l, c = row
            color = "#ef4444" if c >= o else "#22c55e"
            ax.vlines(xi, l, h, color="#6b7280", linewidth=0.8)
            ax.add_patch(
                plt.Rectangle(
                    (xi - 0.2, min(o, c)),
                    0.4,
                    abs(c - o) or 0.2,
                    facecolor=color,
                    edgecolor=color,
                    alpha=0.85,
                )
            )
        ax.xaxis_date()

    def _plot_markers(self, ax: plt.Axes, price: pd.Series, signals: pd.Series) -> None:
        buy = signals == 1
        sell = signals == -1
        ax.scatter(price.index[buy], price[buy], marker="^", color="#ef4444", edgecolors="white", linewidths=0.6, s=140, label="Buy", zorder=3)
        ax.scatter(price.index[sell], price[sell], marker="v", color="#22c55e", edgecolors="white", linewidths=0.6, s=140, label="Sell", zorder=3)
