"""
miniQMT 历史 K 线数据工具（xtdata）。

对外
    import_xtdata          导入 xtdata，缺依赖时报错
    interval_to_xt_period  周期名转换并校验
    fetch_miniqmt_bars     拉取并返回标准 OHLCV DataFrame

私有
    _compact_date          日期字符串转紧凑 yyyyMMdd
    _end_exclusive_to_xt   把排他结束日转成 xt 结束日（加一天）
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

import pandas as pd

# yfinance 风格周期映射到 xt 周期；未命中的键若本身合法可直接透传。
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
    """导入 xtdata；未安装 xtquant 时给出明确错误提示。"""
    try:
        from xtquant import xtdata  # type: ignore
    except ImportError as e:
        raise ImportError(
            "miniQMT requires xtquant (pip install xtquant). Ensure miniQMT is running when using xtdata."
        ) from e
    return xtdata


def interval_to_xt_period(interval: str) -> str:
    """把输入周期转为 xt 周期并校验合法性。"""
    m = (interval or "1d").strip().lower()
    p = _PERIOD_ALIASES.get(m, m)
    if p not in _XT_PERIODS:
        raise ValueError(f"Unsupported interval: {interval!r}")
    return p


def _compact_date(s: str) -> str:
    """去掉连字符，仅保留前 8 位日期。"""
    return s.replace("-", "")[:8]


def _end_exclusive_to_xt(end_date: Optional[str]) -> str:
    """把排他 end_date 转成 xt 结束日字符串；默认加 1 天。"""
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
    """拉取历史 K 线并返回 Open/High/Low/Close/Volume 列。"""
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
