"""
Historical OHLCV via miniQMT / xtquant.

Requires a running miniQMT terminal, the ``xtquant`` package, and xt-style symbols (e.g. ``000001.SZ``).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

import pandas as pd

# yfinance-style interval -> xtdata ``period``; omitted keys pass through if already valid.
_PERIOD_ALIASES = {
    "2m": "1m",
    "1h": "60m",
    "5d": "1d",
    "1wk": "1w",
    "1mo": "1mon",
}
_XT_PERIODS = frozenset({"1m", "5m", "15m", "30m", "60m", "1d", "1w", "1mon"})

_OHLCV_FIELDS = ("open", "high", "low", "close", "volume")
_OHLCV_COLUMNS = ("Open", "High", "Low", "Close", "Volume")


def import_xtdata() -> Any:
    try:
        from xtquant import xtdata  # type: ignore
    except ImportError as e:
        raise ImportError(
            "miniQMT requires xtquant (pip install xtquant). Ensure miniQMT is running when using xtdata."
        ) from e
    return xtdata


def interval_to_xt_period(interval: str) -> str:
    m = (interval or "1d").strip().lower()
    p = _PERIOD_ALIASES.get(m, m)
    if p not in _XT_PERIODS:
        raise ValueError(f"Unsupported interval: {interval!r}")
    return p


def _compact_date(s: str) -> str:
    return s.replace("-", "")[:8]


def _end_exclusive_to_xt(end_date: Optional[str]) -> str:
    """Map yfinance-style exclusive end_date to xt end string (day after last bar)."""
    if not end_date:
        return ""
    ymd = _compact_date(end_date)
    try:
        return (datetime.strptime(ymd, "%Y%m%d") + pd.Timedelta(days=1)).strftime("%Y%m%d")
    except ValueError:
        return ymd


def fetch_miniqmt_bars(
    symbol: str,
    start_date: str,
    end_date: Optional[str] = None,
    interval: str = "1d",
    dividend_type: str = "none",
) -> pd.DataFrame:
    """OHLCV columns aligned with yfinance: Open/High/Low/Close/Volume."""
    xtdata = import_xtdata()
    period = interval_to_xt_period(interval)
    t0 = _compact_date(start_date)
    t1 = _end_exclusive_to_xt(end_date) if end_date else ""

    xtdata.download_history_data(symbol, period, t0, t1)

    fields = ["time", *_OHLCV_FIELDS]
    bars = xtdata.get_market_data(
        field_list=fields,
        stock_list=[symbol],
        period=period,
        start_time=t0,
        end_time=t1,
        count=-1,
        dividend_type=dividend_type,
        fill_data=True,
    )

    loc = bars["time"].loc[symbol].values
    idx = pd.DatetimeIndex(pd.to_datetime(loc, unit="ms"))
    data = {col: bars[f].loc[symbol].values for f, col in zip(_OHLCV_FIELDS, _OHLCV_COLUMNS)}
    return pd.DataFrame(data, index=idx).sort_index()
