"""Backtest report generation (Markdown/text)."""

from typing import Dict, Any, Optional
from ..core.base import BaseComponent


class BacktestReporter(BaseComponent):
    """Generate backtest reports."""
    
    def initialize(self) -> bool:
        """Initialize reporter."""
        self.logger.info("Init backtest reporter")
        return True
    
    def generate_summary_report(self, metrics: Dict[str, Any], title: Optional[str] = None) -> str:
        """中文摘要报告（控制台友好格式）。"""
        first_trade_date = metrics.get('first_trade_date')
        last_trade_date = metrics.get('last_trade_date')
        total_trading_days = metrics.get('total_trading_days', 0)
        profitable_days = metrics.get('profitable_days', 0)
        losing_days = metrics.get('losing_days', 0)

        start_capital = metrics.get('start_capital', 0.0)
        end_capital = metrics.get('end_capital', 0.0)

        total_return = metrics.get('total_return', 0.0)
        annualized_return = metrics.get('annualized_return', 0.0)
        avg_daily_return = metrics.get('avg_daily_return', 0.0)

        max_drawdown = metrics.get('max_drawdown', 0.0)
        return_std = metrics.get('return_std', 0.0)
        volatility = metrics.get('volatility', 0.0)

        sharpe_ratio = metrics.get('sharpe_ratio', 0.0)
        return_drawdown_ratio = metrics.get('return_drawdown_ratio', 0.0)
        win_rate = metrics.get('win_rate', 0.0)
        profit_loss_ratio = metrics.get('profit_loss_ratio', 0.0)

        total_pnl = metrics.get('total_pnl', 0.0)
        total_commission = metrics.get('total_commission', 0.0)
        total_turnover = metrics.get('total_turnover', 0.0)
        total_trade_count = metrics.get('total_trade_count', 0)

        avg_daily_pnl = metrics.get('avg_daily_pnl', 0.0)
        avg_daily_commission = metrics.get('avg_daily_commission', 0.0)
        avg_daily_turnover = metrics.get('avg_daily_turnover', 0.0)
        avg_daily_trade_count = metrics.get('avg_daily_trade_count', 0.0)

        title_line = f"{title}\n\n" if title else ""
        report = (
            title_line +
            "【日期信息】\n"
            f"  首个交易日: {first_trade_date}\n"
            f"  最后交易日: {last_trade_date}\n"
            f"  总交易日: {total_trading_days}\n"
            f"  盈利交易日: {profitable_days}\n"
            f"  亏损交易日: {losing_days}\n\n"

            "【资金信息】\n"
            f"  起始资金: {start_capital:,.2f}\n"
            f"  结束资金: {end_capital:,.2f}\n\n"

            "【收益指标】\n"
            f"  总收益率: {total_return:.2%}\n"
            f"  年化收益: {annualized_return:.2%}\n"
            f"  日均收益率: {avg_daily_return:.2%}\n\n"

            "【风险指标】\n"
            f"  最大回撤: {max_drawdown:.2%}\n"
            f"  收益标准差: {return_std:.2%}\n"
            f"  波动比率: {volatility:.2%}\n\n"

            "【绩效指标】\n"
            f"  夏普比率: {sharpe_ratio:.2f}\n"
            f"  收益回撤比: {return_drawdown_ratio:.2f}\n"
            f"  交易胜率: {win_rate}\n"
            f"  交易盈亏比: {profit_loss_ratio}\n\n"

            "【交易统计】\n"
            f"  总盈亏: {total_pnl:,.2f}\n"
            f"  总手续费: {total_commission:,.2f}\n"
            f"  总成交额: {total_turnover:,.2f}\n"
            f"  总成交笔数: {total_trade_count}\n\n"

            "【日均统计】\n"
            f"  日均盈亏: {avg_daily_pnl:,.2f}\n"
            f"  日均手续费: {avg_daily_commission:,.2f}\n"
            f"  日均成交额: {avg_daily_turnover:,.2f}\n"
            f"  日均成交笔数: {avg_daily_trade_count:.2f}\n"
        )
        return report

