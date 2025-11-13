"""Performance visualization utilities."""

from typing import Optional

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ..core.base import BaseComponent

try:  # pragma: no cover - optional dependency
    from scipy.stats import gaussian_kde
except ImportError:  # pragma: no cover
    gaussian_kde = None


class PerformanceChart(BaseComponent):
    """Visualize backtest performance with stacked panels."""

    def __init__(self, **kwargs):
        """Initialize performance chart."""
        super().__init__(**kwargs)
        self.logger.info("Initializing performance chart")

    def plot_backtest_charts(
        self,
        values_df: pd.DataFrame,
        benchmark_close: Optional[pd.Series] = None,
        title: Optional[str] = None,
        save_path: Optional[str] = None,
        use_plotly: bool = False,
    ) -> None:
        plt.rcParams["font.sans-serif"] = [
            "Microsoft YaHei",
            "SimHei",
            "Heiti TC",
            "Arial Unicode MS",
            "DejaVu Sans",
        ]
        plt.rcParams["axes.unicode_minus"] = False

        df = values_df.copy()
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
            df = df.set_index("date")
        df.index = pd.to_datetime(df.index)

        if "total_value" not in df.columns:
            raise KeyError("values_df must contain 'total_value'")

        if "returns" not in df.columns:
            df["returns"] = df["total_value"].pct_change().fillna(0.0)

        has_price = "price" in df.columns
        if not df.empty:
            date_text = f"{df.index.min().date()} — {df.index.max().date()}"
        else:
            date_text = "no data"

        # Pre-compute series used by both matplotlib and plotly paths
        strategy_nv = df["total_value"] / df["total_value"].iloc[0]
        drawdown = (df["total_value"].expanding().max() - df["total_value"]) / df["total_value"].expanding().max() * -100
        returns_pct = df["returns"] * 100
        price_norm = df["price"].astype(float) / df["price"].iloc[0] if has_price else None
        bench_norm_price = None
        bench_norm_nv = None
        if benchmark_close is not None:
            bench_series = pd.Series(benchmark_close).astype(float)
            bench_series.index = pd.to_datetime(bench_series.index)
            bench_series = bench_series.sort_index().reindex(df.index).fillna(method="ffill").dropna()
            if not bench_series.empty:
                bench_returns = bench_series.pct_change().fillna(0.0)
                bench_nv = (1 + bench_returns).cumprod()
                bench_norm_nv = bench_nv / bench_nv.iloc[0]
                if has_price:
                    bench_norm_price = bench_series / bench_series.iloc[0]

        if use_plotly:
            try:
                import plotly.graph_objects as go
                from plotly.subplots import make_subplots
            except ImportError as exc:  # pragma: no cover
                self.logger.info(f"Plotly not available ({exc}); falling back to Matplotlib")
            else:
                rows = 5
                fig = make_subplots(
                    rows=rows,
                    cols=1,
                    shared_xaxes=True,
                    vertical_spacing=0.04,
                    specs=[[{"type": "scatter"}]] * rows,
                    row_heights=[0.18, 0.22, 0.2, 0.2, 0.2],
                )

                if has_price and price_norm is not None:
                    fig.add_trace(
                        go.Scatter(x=df.index, y=price_norm, name="策略收盘价", line=dict(color="#2E86AB", width=1.5)),
                        row=1,
                        col=1,
                    )
                    if bench_norm_price is not None:
                        fig.add_trace(
                            go.Scatter(
                                x=bench_norm_price.index,
                                y=bench_norm_price.values,
                                name="基准收盘价",
                                line=dict(color="#E63946", width=1.5, dash="dash"),
                            ),
                            row=1,
                            col=1,
                        )
                fig.add_trace(
                    go.Scatter(x=df.index, y=strategy_nv, name="策略净值", line=dict(color="#2E86AB", width=2)),
                    row=2,
                    col=1,
                )
                if bench_norm_nv is not None:
                    fig.add_trace(
                        go.Scatter(
                            x=bench_norm_nv.index,
                            y=bench_norm_nv.values,
                            name="基准净值",
                            line=dict(color="#E63946", width=2, dash="dash"),
                        ),
                        row=2,
                        col=1,
                    )
                fig.add_trace(
                    go.Scatter(
                        x=df.index,
                        y=drawdown,
                        name="回撤",
                        fill="tozeroy",
                        line=dict(color="#C1121F"),
                        fillcolor="rgba(242,66,54,0.4)",
                    ),
                    row=3,
                    col=1,
                )
                fig.add_trace(
                    go.Bar(x=df.index, y=returns_pct, name="每日盈亏", marker_color=np.where(returns_pct >= 0, "#ef4444", "#22c55e")),
                    row=4,
                    col=1,
                )
                returns_for_dist = returns_pct[returns_pct != 0]
                if len(returns_for_dist) > 1:
                    if gaussian_kde is not None:
                        kde = gaussian_kde(returns_for_dist)
                        kde.set_bandwidth(kde.factor * 0.5)
                        x_range = np.linspace(returns_for_dist.min(), returns_for_dist.max(), 300)
                        density = kde(x_range)
                        bin_width = x_range[1] - x_range[0]
                        frequency = density * bin_width * len(returns_for_dist)
                        fig.add_trace(
                            go.Scatter(
                                x=x_range,
                                y=frequency,
                                name="盈亏分布",
                                fill="tozeroy",
                                line=dict(color="#8B6F5E"),
                                fillcolor="rgba(107,76,63,0.6)",
                            ),
                            row=5,
                            col=1,
                        )
                    else:
                        fig.add_trace(
                            go.Histogram(x=returns_for_dist, name="盈亏分布", nbinsx=40, marker_color="#6B4C3F"),
                            row=5,
                            col=1,
                        )
                else:
                    fig.add_trace(
                        go.Histogram(x=returns_pct, name="盈亏分布", nbinsx=10, marker_color="#6B4C3F"),
                        row=5,
                        col=1,
                    )

                fig.update_xaxes(title_text="日期", row=5, col=1)
                fig.update_yaxes(title_text="价格(归一化)", row=1, col=1)
                fig.update_yaxes(title_text="净值", row=2, col=1)
                fig.update_yaxes(title_text="回撤 (%)", row=3, col=1)
                fig.update_yaxes(title_text="收益率 (%)", row=4, col=1)
                fig.update_yaxes(title_text="频数", row=5, col=1)

                base_title = title or "策略表现分析"
                fig.update_layout(
                    title=f"{base_title}<br><sup>{date_text}</sup>",
                    template="plotly_white",
                    showlegend=True,
                )

                if save_path:
                    html_path = save_path if str(save_path).lower().endswith(".html") else f"{save_path}.html"
                    fig.write_html(html_path, include_plotlyjs="cdn")
                    self.logger.info(f"Chart saved to {html_path}")
                else:
                    fig.show()
                return

        # ------------------------------ Matplotlib branch ------------------------------
        n_panels = 5 if has_price else 4
        fig, axes = plt.subplots(n_panels, 1, figsize=(16, 14 if has_price else 12))
        base_title = title or "策略表现分析"
        fig.suptitle(f"{base_title} | {date_text}", fontsize=16, y=0.995)

        idx = 0
        if has_price and price_norm is not None:
            self._plot_price_compare(ax=axes[idx], df=df, benchmark_close=benchmark_close, price_norm=price_norm, bench_norm=bench_norm_price)
            idx += 1

        self._plot_net_value(ax=axes[idx], df=df, strategy_nv=strategy_nv, bench_norm=bench_norm_nv)
        self._plot_drawdown(ax=axes[idx + 1], drawdown=drawdown)
        self._plot_daily_returns(ax=axes[idx + 2], returns_pct=returns_pct)
        self._plot_return_distribution(ax=axes[idx + 3], returns_pct=returns_pct)

        for ax in axes[:-1]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right")

        plt.tight_layout(rect=[0, 0, 1, 0.97])

        if save_path:
            fig.savefig(save_path, dpi=300, bbox_inches="tight")
            self.logger.info(f"Chart saved to {save_path}")
        else:
            plt.show()

    # ------------------------------------------------------------------
    # Individual panels (Matplotlib)
    # ------------------------------------------------------------------

    def _plot_price_compare(
        self,
        ax: plt.Axes,
        df: pd.DataFrame,
        benchmark_close: Optional[pd.Series],
        price_norm: pd.Series,
        bench_norm: Optional[pd.Series],
    ) -> None:
        ax.plot(df.index, price_norm, linewidth=1.5, color="#2E86AB", label="策略收盘价")

        if bench_norm is not None:
            ax.plot(bench_norm.index, bench_norm.values, linewidth=1.5, color="#E63946", linestyle="--", label="基准收盘价")
            ax.legend()

        ax.set_title("价格对比", fontsize=14)
        ax.set_xlabel("日期", fontsize=11)
        ax.set_ylabel("价格(归一化)", fontsize=11)
        ax.grid(True, alpha=0.3, linestyle="--")

    def _plot_net_value(
        self,
        ax: plt.Axes,
        df: pd.DataFrame,
        strategy_nv: pd.Series,
        bench_norm: Optional[pd.Series],
    ) -> None:
        ax.plot(df.index, strategy_nv, linewidth=2, color="#2E86AB", label="策略净值")

        if bench_norm is not None:
            ax.plot(bench_norm.index, bench_norm.values, linewidth=2, color="#E63946", linestyle="--", label="基准净值")
            ax.legend()

        ax.set_title("账户净值", fontsize=14)
        ax.set_xlabel("日期", fontsize=11)
        ax.set_ylabel("净值(起始=1)", fontsize=11)
        ax.grid(True, alpha=0.3, linestyle="--")

    def _plot_drawdown(self, ax: plt.Axes, drawdown: pd.Series) -> None:
        ax.fill_between(drawdown.index, drawdown, 0, color="#F24236", alpha=0.5)
        ax.plot(drawdown.index, drawdown, color="#C1121F", linewidth=1.5)
        ax.set_title("净值回撤", fontsize=14)
        ax.set_xlabel("日期", fontsize=11)
        ax.set_ylabel("回撤 (%)", fontsize=11)
        ax.grid(True, alpha=0.3, linestyle="--")

    def _plot_daily_returns(self, ax: plt.Axes, returns_pct: pd.Series) -> None:
        colors = ["#ef4444" if x >= 0 else "#22c55e" for x in returns_pct]
        ax.bar(returns_pct.index, returns_pct, color=colors, alpha=0.7, width=0.8)
        ax.axhline(y=0, color="black", linewidth=0.5)

        max_return = abs(returns_pct.max()) if returns_pct.max() != 0 else 1
        min_return = abs(returns_pct.min()) if returns_pct.min() != 0 else 1
        y_max = max(max_return, min_return) * 1.1
        ax.set_ylim(-y_max, y_max)

        ax.set_title("每日盈亏", fontsize=14)
        ax.set_xlabel("日期", fontsize=11)
        ax.set_ylabel("收益率 (%)", fontsize=11)
        ax.grid(True, alpha=0.3, linestyle="--", axis="y")

    def _plot_return_distribution(self, ax: plt.Axes, returns_pct: pd.Series) -> None:
        returns_for_dist = returns_pct[returns_pct != 0]
        ax.set_title("盈亏分布（已交易日期）", fontsize=14)
        ax.set_xlabel("盈亏值 (%)", fontsize=11)
        ax.set_ylabel("频数", fontsize=11)
        ax.grid(True, alpha=0.3, linestyle="--", axis="y")

        if len(returns_for_dist) < 2:
            return

        if gaussian_kde is None:
            ax.hist(returns_for_dist, bins=40, color="#6B4C3F", alpha=0.7, edgecolor="white")
            ax.axvline(x=0, color="gray", linestyle="--", linewidth=1, alpha=0.7)
            return

        kde = gaussian_kde(returns_for_dist)
        kde.set_bandwidth(kde.factor * 0.5)
        x_range = np.linspace(returns_for_dist.min(), returns_for_dist.max(), 300)
        density = kde(x_range)
        bin_width = x_range[1] - x_range[0]
        frequency = density * bin_width * len(returns_for_dist)

        ax.fill_between(x_range, 0, frequency, color="#6B4C3F", alpha=0.7)
        ax.plot(x_range, frequency, color="#8B6F5E", linewidth=2)
        ax.axvline(x=0, color="gray", linestyle="--", linewidth=1, alpha=0.7)

