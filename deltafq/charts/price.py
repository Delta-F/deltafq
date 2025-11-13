"""Minimal price chart helper (Matplotlib or Plotly)."""
from typing import Dict, Optional, Union

import matplotlib.pyplot as plt
import pandas as pd

from ..core.base import BaseComponent


class PriceChart(BaseComponent):
    def __init__(self, **kwargs):
        """Initialize the price chart."""
        super().__init__(**kwargs)
        self.logger.info("Initializing price chart")

    def plot_prices(
        self,
        data: Union[pd.DataFrame, Dict[str, pd.DataFrame]],
        price_column: Optional[str] = "Close",
        normalize: Optional[bool] = True,
        title: Optional[str] = None,
        use_plotly: Optional[bool] = False,
    ) -> None:
        series_map = self._collect(data, price_column, normalize)
        ylabel = "Normalized Price" if normalize else "Price"
        title = title or ("Normalized Price Comparison" if len(series_map) > 1 else "Price Chart")

        if use_plotly:
            import plotly.graph_objects as go

            fig = go.Figure()
            for label, series in series_map.items():
                fig.add_trace(go.Scatter(x=series.index, y=series.values, mode="lines", name=label))
            fig.update_layout(title=title, xaxis_title="Date", yaxis_title=ylabel, template="plotly_white")
            fig.show()
            return

        fig, ax = plt.subplots(figsize=(12, 6))
        for label, series in series_map.items():
            ax.plot(series.index, series.values, label=label)
        ax.set_xlabel("Date")
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

    def _collect(
        self,
        data: Union[pd.DataFrame, Dict[str, pd.DataFrame]],
        price_column: str,
        normalize: bool,
    ) -> Dict[str, pd.Series]:
        def prep(frame: pd.DataFrame) -> pd.Series:
            series = frame[price_column]
            if normalize:
                series = series / series.iloc[0]
            return series

        if isinstance(data, pd.DataFrame):
            return {price_column: prep(data)}
        return {name: prep(df) for name, df in data.items()}
