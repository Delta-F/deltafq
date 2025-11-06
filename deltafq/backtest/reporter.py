"""Backtest report generation (Markdown/text)."""

import pandas as pd
import sys
from typing import Dict, Any, Optional
from ..core.base import BaseComponent
from ..charts.performance import PerformanceChart


class BacktestReporter(BaseComponent):
    """Generate backtest reports."""
    
    def __init__(self, **kwargs):
        """Initialize reporter."""
        super().__init__(**kwargs)
        self.chart = PerformanceChart()
    
    def initialize(self) -> bool:
        """Initialize reporter."""
        self.logger.info("Init backtest reporter")
        self.chart.initialize()
        return True
    
    def generate_summary_report(
        self, 
        metrics: Dict[str, Any], 
        title: Optional[str] = None,
        language: str = 'zh'
    ) -> None:
        """Print strategy report (console-friendly format).
        
        Args:
            metrics: Dictionary containing backtest metrics
            title: Optional report title
            language: Language for output ('zh' for Chinese, 'en' for English). Default is 'zh'
        """
        # Ensure UTF-8 encoding for Chinese output
        if language == 'zh':
            if sys.stdout.encoding != 'utf-8':
                try:
                    sys.stdout.reconfigure(encoding='utf-8')
                except AttributeError:
                    # Python < 3.7 doesn't have reconfigure
                    pass
        
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

        # Language-specific text
        if language == 'zh':
            texts = {
                'title_default': '策略回测报告',
                'date_info': '【日期信息】',
                'first_trade_date': '首个交易日',
                'last_trade_date': '最后交易日',
                'total_trading_days': '总交易日',
                'profitable_days': '盈利交易日',
                'losing_days': '亏损交易日',
                'capital_info': '【资金信息】',
                'start_capital': '起始资金',
                'end_capital': '结束资金',
                'capital_growth': '资金增长',
                'return_metrics': '【收益指标】',
                'total_return': '总收益率',
                'annualized_return': '年化收益',
                'avg_daily_return': '日均收益率',
                'risk_metrics': '【风险指标】',
                'max_drawdown': '最大回撤',
                'return_std': '收益标准差',
                'volatility': '波动比率',
                'performance_metrics': '【绩效指标】',
                'sharpe_ratio': '夏普比率',
                'return_drawdown_ratio': '收益回撤比',
                'win_rate': '交易胜率',
                'profit_loss_ratio': '交易盈亏比',
                'trading_stats': '【交易统计】',
                'total_pnl': '总盈亏',
                'total_commission': '总手续费',
                'total_turnover': '总成交额',
                'total_trade_count': '总成交笔数',
                'daily_stats': '【日均统计】',
                'avg_daily_pnl': '日均盈亏',
                'avg_daily_commission': '日均手续费',
                'avg_daily_turnover': '日均成交额',
                'avg_daily_trade_count': '日均成交笔数'
            }
        else:  # English
            texts = {
                'title_default': 'Backtest Report',
                'date_info': '[Date Information]',
                'first_trade_date': 'First Trading Date',
                'last_trade_date': 'Last Trading Date',
                'total_trading_days': 'Total Trading Days',
                'profitable_days': 'Profitable Days',
                'losing_days': 'Losing Days',
                'capital_info': '[Capital Information]',
                'start_capital': 'Start Capital',
                'end_capital': 'End Capital',
                'capital_growth': 'Capital Growth',
                'return_metrics': '[Return Metrics]',
                'total_return': 'Total Return',
                'annualized_return': 'Annualized Return',
                'avg_daily_return': 'Average Daily Return',
                'risk_metrics': '[Risk Metrics]',
                'max_drawdown': 'Max Drawdown',
                'return_std': 'Return Std Dev',
                'volatility': 'Volatility',
                'performance_metrics': '[Performance Metrics]',
                'sharpe_ratio': 'Sharpe Ratio',
                'return_drawdown_ratio': 'Return/Drawdown Ratio',
                'win_rate': 'Win Rate',
                'profit_loss_ratio': 'Profit/Loss Ratio',
                'trading_stats': '[Trading Statistics]',
                'total_pnl': 'Total P&L',
                'total_commission': 'Total Commission',
                'total_turnover': 'Total Turnover',
                'total_trade_count': 'Total Trades',
                'daily_stats': '[Daily Statistics]',
                'avg_daily_pnl': 'Avg Daily P&L',
                'avg_daily_commission': 'Avg Daily Commission',
                'avg_daily_turnover': 'Avg Daily Turnover',
                'avg_daily_trade_count': 'Avg Daily Trades'
            }

        # Print report
        print("\n" + "=" * 80)
        if title:
            print(f"  {title}")
            print("=" * 80)
        else:
            print(f"  {texts['title_default']}")
            print("=" * 80)
        print()
        
        print(texts['date_info'])
        print(f"  {texts['first_trade_date']}: {first_trade_date}")
        print(f"  {texts['last_trade_date']}: {last_trade_date}")
        print(f"  {texts['total_trading_days']}: {total_trading_days}")
        print(f"  {texts['profitable_days']}: {profitable_days}")
        print(f"  {texts['losing_days']}: {losing_days}")
        print()

        print(texts['capital_info'])
        print(f"  {texts['start_capital']}: {start_capital:,.2f}")
        print(f"  {texts['end_capital']}: {end_capital:,.2f}")
        print(f"  {texts['capital_growth']}: {end_capital - start_capital:,.2f} ({total_return:.2%})")
        print()

        print(texts['return_metrics'])
        print(f"  {texts['total_return']}: {total_return:.2%}")
        print(f"  {texts['annualized_return']}: {annualized_return:.2%}")
        print(f"  {texts['avg_daily_return']}: {avg_daily_return:.2%}")
        print()

        print(texts['risk_metrics'])
        print(f"  {texts['max_drawdown']}: {max_drawdown:.2%}")
        print(f"  {texts['return_std']}: {return_std:.2%}")
        print(f"  {texts['volatility']}: {volatility:.2%}")
        print()

        print(texts['performance_metrics'])
        print(f"  {texts['sharpe_ratio']}: {sharpe_ratio:.2f}")
        print(f"  {texts['return_drawdown_ratio']}: {return_drawdown_ratio:.2f}")
        print(f"  {texts['win_rate']}: {win_rate:.2%}")
        print(f"  {texts['profit_loss_ratio']}: {profit_loss_ratio:.2f}")
        print()

        print(texts['trading_stats'])
        print(f"  {texts['total_pnl']}: {total_pnl:,.2f}")
        print(f"  {texts['total_commission']}: {total_commission:,.2f}")
        print(f"  {texts['total_turnover']}: {total_turnover:,.2f}")
        print(f"  {texts['total_trade_count']}: {total_trade_count}")
        print()

        print(texts['daily_stats'])
        print(f"  {texts['avg_daily_pnl']}: {avg_daily_pnl:,.2f}")
        print(f"  {texts['avg_daily_commission']}: {avg_daily_commission:,.2f}")
        print(f"  {texts['avg_daily_turnover']}: {avg_daily_turnover:,.2f}")
        print(f"  {texts['avg_daily_trade_count']}: {avg_daily_trade_count:.2f}")
        print()
        print("=" * 80)
        print()
    
    def generate_visual_report(
        self,
        metrics: Dict[str, Any],
        values_df: pd.DataFrame,
        benchmark_close: Optional[pd.Series] = None,
        title: Optional[str] = None,
        language: str = 'zh',
        show: bool = True,
        save_path: Optional[str] = None,
        use_plotly: bool = False
    ) -> None:
        """Generate complete visual report (including text report and charts).
        
        Args:
            metrics: Dictionary containing backtest metrics
            values_df: DataFrame with backtest values
            benchmark_close: Optional benchmark price series
            title: Optional report title
            language: Language for output ('zh' for Chinese, 'en' for English). Default is 'zh'
            show: Whether to display the chart
            save_path: Optional path to save the chart
        """
        # Print text report
        self.generate_summary_report(metrics, title, language)
        
        # Generate visualization charts
        chart_title = title if title else ('策略回测报告' if language == 'zh' else 'Backtest Report')
        self.chart.plot_backtest_charts(
            values_df=values_df,
            benchmark_close=benchmark_close,
            title=chart_title,
            show=show,
            save_path=save_path,
            use_plotly=use_plotly
        )
