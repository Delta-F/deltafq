"""Combined performance computation and reporting utilities."""

from __future__ import annotations

from typing import Any, Dict

import math
import sys

import pandas as pd

from ..core.base import BaseComponent
from .metrics import (
    calculate_annualized_return,
    calculate_calmar_ratio,
    calculate_max_drawdown,
    calculate_returns,
    calculate_sharpe_ratio,
    calculate_total_return,
    calculate_volatility,
    compute_cumulative_returns,
    compute_drawdown_series,
)

_EMPTY_TRADE_METRICS = {
    "total_trades": 0,
    "total_pnl": 0.0,
    "win_rate": 0.0,
    "winning_trades": 0,
    "losing_trades": 0,
    "avg_win": 0.0,
    "avg_loss": 0.0,
    "profit_loss_ratio": 0.0,
}

_EMPTY_TRADING_METRICS = {
    "total_commission": 0.0,
    "total_turnover": 0.0,
    "avg_daily_pnl": 0.0,
    "avg_daily_commission": 0.0,
    "avg_daily_turnover": 0.0,
    "avg_daily_trade_count": 0.0,
}


class PerformanceReporter(BaseComponent):
    """Compute backtest metrics and print summary."""

    def initialize(self) -> bool:
        self.logger.info("Initializing performance reporter")
        return True

    def print_summary(
        self,
        symbol: str,
        trades_df: pd.DataFrame,
        values_df: pd.DataFrame,
        title: str | None = None,
        language: str = "zh",
    ) -> None:
        _, metrics = self.compute(symbol, trades_df, values_df)
        texts = _TEXTS_ZH if language == "zh" else _TEXTS_EN
        _ensure_utf8(language)

        print("\n" + "=" * 80)
        header = title or texts["title_default"]
        print(f"  {header}")
        print("=" * 80 + "\n")

        print(texts["date_info"])
        print(f"  {texts['first_trade_date']}: {metrics.get('first_trade_date')}")
        print(f"  {texts['last_trade_date']}: {metrics.get('last_trade_date')}")
        print(f"  {texts['total_trading_days']}: {metrics.get('total_trading_days', 0)}")
        print(f"  {texts['profitable_days']}: {metrics.get('profitable_days', 0)}")
        print(f"  {texts['losing_days']}: {metrics.get('losing_days', 0)}\n")

        print(texts["capital_info"])
        print(f"  {texts['start_capital']}: {metrics.get('start_capital', 0.0):,.2f}")
        end_capital = float(metrics.get("end_capital", 0.0))
        start_capital = float(metrics.get("start_capital", 0.0))
        print(f"  {texts['end_capital']}: {end_capital:,.2f}")
        growth = end_capital - start_capital
        total_return = metrics.get("total_return", 0.0)
        print(f"  {texts['capital_growth']}: {growth:,.2f} ({total_return:.2%})\n")

        print(texts["return_metrics"])
        print(f"  {texts['total_return']}: {total_return:.2%}")
        print(f"  {texts['annualized_return']}: {metrics.get('annualized_return', 0.0):.2%}")
        print(f"  {texts['avg_daily_return']}: {metrics.get('avg_daily_return', 0.0):.2%}\n")

        print(texts["risk_metrics"])
        print(f"  {texts['max_drawdown']}: {metrics.get('max_drawdown', 0.0):.2%}")
        print(f"  {texts['return_std']}: {metrics.get('return_std', 0.0):.2%}")
        print(f"  {texts['volatility']}: {metrics.get('volatility', 0.0):.2%}\n")

        print(texts["performance_metrics"])
        print(f"  {texts['sharpe_ratio']}: {metrics.get('sharpe_ratio', 0.0):.2f}")
        print(f"  {texts['return_drawdown_ratio']}: {metrics.get('return_drawdown_ratio', 0.0):.2f}")
        print(f"  {texts['win_rate']}: {metrics.get('win_rate', 0.0):.2%}")
        print(f"  {texts['profit_loss_ratio']}: {metrics.get('profit_loss_ratio', 0.0):.2f}")
        print(f"  {texts['avg_win']}: {metrics.get('avg_win', 0.0):,.2f}")
        print(f"  {texts['avg_loss']}: {metrics.get('avg_loss', 0.0):,.2f}\n")

        print(texts["trading_stats"])
        print(f"  {texts['total_pnl']}: {metrics.get('total_pnl', 0.0):,.2f}")
        print(f"  {texts['total_commission']}: {metrics.get('total_commission', 0.0):,.2f}")
        print(f"  {texts['total_turnover']}: {metrics.get('total_turnover', 0.0):,.2f}")
        print(f"  {texts['total_trade_count']}: {metrics.get('total_trade_count', 0)}\n")

        print(texts["daily_stats"])
        print(f"  {texts['avg_daily_pnl']}: {metrics.get('avg_daily_pnl', 0.0):,.2f}")
        print(f"  {texts['avg_daily_commission']}: {metrics.get('avg_daily_commission', 0.0):,.2f}")
        print(f"  {texts['avg_daily_turnover']}: {metrics.get('avg_daily_turnover', 0.0):,.2f}")
        print(f"  {texts['avg_daily_trade_count']}: {metrics.get('avg_daily_trade_count', 0.0):.2f}\n")
        print("=" * 80 + "\n")

    def compute(
        self,
        symbol: str,
        trades_df: pd.DataFrame,
        values_df: pd.DataFrame,
    ) -> tuple[pd.DataFrame, Dict[str, Any]]:
        values = values_df.copy()
        trades = trades_df.copy()

        if not values.empty and "date" in values.columns:
            values["date"] = pd.to_datetime(values["date"])
            values = values.set_index("date")

        if "timestamp" in trades.columns:
            trades["timestamp"] = pd.to_datetime(trades["timestamp"])

        values = values.sort_index()
        index = values.index

        equity = values.get("total_value", pd.Series(dtype=float, index=index)).astype(float)
        has_equity = len(equity) > 1

        returns = (
            calculate_returns(equity).reindex(index, fill_value=0.0)
            if has_equity
            else pd.Series(0.0, index=index)
        )

        values["returns"] = returns
        values["cumulative_returns"] = compute_cumulative_returns(returns)
        values["drawdown"] = compute_drawdown_series(returns)

        start_capital = float(equity.iloc[0]) if not equity.empty else 0.0
        end_capital = float(equity.iloc[-1]) if not equity.empty else start_capital

        pnl_series = values.get("daily_pnl", pd.Series(0.0, index=index))
        profitable_days = int((pnl_series > 0).sum())
        losing_days = int((pnl_series < 0).sum())

        total_days = int(len(values))

        avg_daily_return = float(returns.mean())
        return_std = float(returns.std())
        total_return = calculate_total_return(equity) if has_equity else 0.0
        annualized_return = calculate_annualized_return(returns) if has_equity else 0.0
        volatility = calculate_volatility(returns) if has_equity else 0.0
        sharpe_ratio = calculate_sharpe_ratio(returns) if has_equity else 0.0
        max_drawdown = calculate_max_drawdown(equity) if has_equity else 0.0
        calmar_ratio = calculate_calmar_ratio(annualized_return, max_drawdown) if has_equity else float("inf")
        return_drawdown_ratio = (
            calmar_ratio
            if math.isfinite(calmar_ratio)
            else (abs(annualized_return / max_drawdown) if max_drawdown else float("inf"))
        )

        trade_metrics = _calculate_trade_metrics(trades)
        trading_metrics = _calculate_trading_metrics(trades, total_days)

        metrics: Dict[str, Any] = {
            "symbol": symbol,
            "first_trade_date": values.index[0] if not values.empty else None,
            "last_trade_date": values.index[-1] if not values.empty else None,
            "total_trading_days": total_days,
            "profitable_days": profitable_days,
            "losing_days": losing_days,
            "start_capital": start_capital,
            "end_capital": end_capital,
            "total_return": total_return,
            "annualized_return": annualized_return,
            "avg_daily_return": avg_daily_return,
            "max_drawdown": max_drawdown,
            "return_std": return_std,
            "volatility": volatility,
            "sharpe_ratio": sharpe_ratio,
            "return_drawdown_ratio": return_drawdown_ratio,
            "total_pnl": trade_metrics.get("total_pnl", 0.0),
            "avg_win": trade_metrics.get("avg_win", 0.0),
            "avg_loss": trade_metrics.get("avg_loss", 0.0),
            "total_commission": trading_metrics.get("total_commission", 0.0),
            "total_turnover": trading_metrics.get("total_turnover", 0.0),
            "total_trade_count": trade_metrics.get("total_trades", 0),
            "win_rate": trade_metrics.get("win_rate", 0.0),
            "profit_loss_ratio": trade_metrics.get("profit_loss_ratio", 0.0),
            "avg_daily_pnl": trading_metrics.get("avg_daily_pnl", 0.0),
            "avg_daily_commission": trading_metrics.get("avg_daily_commission", 0.0),
            "avg_daily_turnover": trading_metrics.get("avg_daily_turnover", 0.0),
            "avg_daily_trade_count": trading_metrics.get("avg_daily_trade_count", 0.0),
        }

        return values, metrics


def _calculate_trade_metrics(trades_df: pd.DataFrame) -> Dict[str, Any]:
    if trades_df.empty:
        return _EMPTY_TRADE_METRICS.copy()

    pnl_series = trades_df.get("profit_loss")
    if pnl_series is None:
        return _EMPTY_TRADE_METRICS.copy()

    pnl_series = pnl_series.dropna()
    if pnl_series.empty:
        return _EMPTY_TRADE_METRICS.copy()

    total_pnl = float(pnl_series.sum())
    winning = pnl_series[pnl_series > 0]
    losing = pnl_series[pnl_series < 0]
    avg_win = float(winning.mean()) if not winning.empty else 0.0
    avg_loss = float(losing.mean()) if not losing.empty else 0.0
    profit_loss_ratio = float(avg_win / abs(avg_loss)) if avg_loss else (float("inf") if avg_win > 0 else 0.0)

    return {
        "total_trades": int(len(trades_df)),
        "total_pnl": total_pnl,
        "win_rate": float((pnl_series > 0).mean()),
        "winning_trades": int((pnl_series > 0).sum()),
        "losing_trades": int((pnl_series < 0).sum()),
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "profit_loss_ratio": profit_loss_ratio,
    }


def _calculate_trading_metrics(trades_df: pd.DataFrame, total_days: int) -> Dict[str, float]:
    if trades_df.empty:
        return _EMPTY_TRADING_METRICS.copy()

    commission = float(trades_df.get("commission", pd.Series(dtype=float)).sum())
    turnover = float(trades_df.get("gross_revenue", pd.Series(dtype=float)).sum())
    pnl = float(trades_df.get("profit_loss", pd.Series(dtype=float)).sum())
    divisor = total_days or 1

    return {
        "total_commission": commission,
        "total_turnover": turnover,
        "avg_daily_pnl": pnl / divisor,
        "avg_daily_commission": commission / divisor,
        "avg_daily_turnover": turnover / divisor,
        "avg_daily_trade_count": len(trades_df) / divisor,
    }


_TEXTS_ZH = {
    "title_default": "策略回测报告",
    "date_info": "【日期信息】",
    "first_trade_date": "首个交易日",
    "last_trade_date": "最后交易日",
    "total_trading_days": "总交易日",
    "profitable_days": "盈利交易日",
    "losing_days": "亏损交易日",
    "capital_info": "【资金信息】",
    "start_capital": "起始资金",
    "end_capital": "结束资金",
    "capital_growth": "资金增长",
    "return_metrics": "【收益指标】",
    "total_return": "总收益率",
    "annualized_return": "年化收益",
    "avg_daily_return": "日均收益率",
    "risk_metrics": "【风险指标】",
    "max_drawdown": "最大回撤",
    "return_std": "收益标准差",
    "volatility": "波动率",
    "performance_metrics": "【绩效指标】",
    "sharpe_ratio": "夏普比率",
    "return_drawdown_ratio": "收益回撤比",
    "win_rate": "交易胜率",
    "profit_loss_ratio": "盈亏比",
    "avg_win": "平均盈利",
    "avg_loss": "平均亏损",
    "trading_stats": "【交易统计】",
    "total_pnl": "总盈亏",
    "total_commission": "总手续费",
    "total_turnover": "总成交额",
    "total_trade_count": "总成交笔数",
    "daily_stats": "【日均统计】",
    "avg_daily_pnl": "日均盈亏",
    "avg_daily_commission": "日均手续费",
    "avg_daily_turnover": "日均成交额",
    "avg_daily_trade_count": "日均成交笔数",
}


_TEXTS_EN = {
    "title_default": "Backtest Report",
    "date_info": "[Date Information]",
    "first_trade_date": "First Trading Date",
    "last_trade_date": "Last Trading Date",
    "total_trading_days": "Total Trading Days",
    "profitable_days": "Profitable Days",
    "losing_days": "Losing Days",
    "capital_info": "[Capital Information]",
    "start_capital": "Start Capital",
    "end_capital": "End Capital",
    "capital_growth": "Capital Growth",
    "return_metrics": "[Return Metrics]",
    "total_return": "Total Return",
    "annualized_return": "Annualized Return",
    "avg_daily_return": "Average Daily Return",
    "risk_metrics": "[Risk Metrics]",
    "max_drawdown": "Max Drawdown",
    "return_std": "Return Std Dev",
    "volatility": "Volatility",
    "performance_metrics": "[Performance Metrics]",
    "sharpe_ratio": "Sharpe Ratio",
    "return_drawdown_ratio": "Return/Drawdown Ratio",
    "win_rate": "Win Rate",
    "profit_loss_ratio": "Profit/Loss Ratio",
    "avg_win": "Avg Win",
    "avg_loss": "Avg Loss",
    "trading_stats": "[Trading Statistics]",
    "total_pnl": "Total P&L",
    "total_commission": "Total Commission",
    "total_turnover": "Total Turnover",
    "total_trade_count": "Total Trades",
    "daily_stats": "[Daily Statistics]",
    "avg_daily_pnl": "Avg Daily P&L",
    "avg_daily_commission": "Avg Daily Commission",
    "avg_daily_turnover": "Avg Daily Turnover",
    "avg_daily_trade_count": "Avg Daily Trades",
}


__all__ = ["PerformanceReporter"]


def _ensure_utf8(language: str) -> None:
    if language == "zh":
        encoding = getattr(sys.stdout, "encoding", "") or ""
        if encoding.lower() != "utf-8":
            try:
                sys.stdout.reconfigure(encoding="utf-8")
            except AttributeError:
                pass

