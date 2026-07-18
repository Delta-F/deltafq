"""
baostock 历史 K 线适配。

对外
    fetch_baostock_bars    拉取并返回标准 OHLCV DataFrame
    to_bs_code             标的转 baostock 格式（sh./sz.）
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

import pandas as pd

# yfinance 风格 → baostock frequency
_FREQ = {
    "1d": "d", "1wk": "w", "1mo": "m",
    "5m": "5", "15m": "15", "30m": "30", "60m": "60", "1h": "60",
}


def to_bs_code(symbol: str) -> str:
    """600000.SH / 000001.SZ → sh.600000 / sz.000001；已是 baostock 格式则原样返回。"""
    s = symbol.strip()
    u = s.upper()
    if u.endswith(".SH"):
        return "sh." + s.split(".")[0]
    if u.endswith(".SZ"):
        return "sz." + s.split(".")[0]
    return s.lower() if s[:3].lower() in ("sh.", "sz.") else s


def fetch_baostock_bars(
    symbol: str,
    start_date: str,
    end_date: Optional[str] = None,
    interval: str = "1d",
    adjustflag: str = "3",
) -> pd.DataFrame:
    """拉取历史 K 线，返回 Open/High/Low/Close/Volume。end_date 排他（与 yahoo 一致）。"""
    import baostock as bs  # type: ignore

    freq = _FREQ.get((interval or "1d").strip().lower(), (interval or "1d").strip().lower())
    # baostock end 为包含，故排他结束日减一天
    end = ""
    if end_date:
        end = (datetime.strptime(end_date.replace("-", "")[:8], "%Y%m%d") - timedelta(days=1)).strftime("%Y-%m-%d")

    fields = "date,time,open,high,low,close,volume" if freq in ("5", "15", "30", "60") else "date,open,high,low,close,volume"
    bs.login()
    try:
        rs = bs.query_history_k_data_plus(
            to_bs_code(symbol), fields,
            start_date=start_date[:10], end_date=end,
            frequency=freq, adjustflag=str(adjustflag),
        )
        rows = []
        while rs.error_code == "0" and rs.next():
            rows.append(rs.get_row_data())
        if not rows:
            return pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])

        raw = pd.DataFrame(rows, columns=rs.fields)
        # 分钟线用 time（YYYYMMDDHHmmssSSS），日线用 date
        idx = (
            pd.to_datetime(raw["time"].str[:14], format="%Y%m%d%H%M%S")
            if "time" in raw.columns else pd.to_datetime(raw["date"])
        )
        return pd.DataFrame(
            {
                "Open": pd.to_numeric(raw["open"]).to_numpy(),
                "High": pd.to_numeric(raw["high"]).to_numpy(),
                "Low": pd.to_numeric(raw["low"]).to_numpy(),
                "Close": pd.to_numeric(raw["close"]).to_numpy(),
                "Volume": pd.to_numeric(raw["volume"]).to_numpy(),
            },
            index=pd.DatetimeIndex(idx),
        ).sort_index()
    finally:
        bs.logout()
