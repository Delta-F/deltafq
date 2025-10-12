"""
Backtest report generation.
"""

import pandas as pd
from typing import Dict, Any, Optional
from ..core.base import BaseComponent


class BacktestReporter(BaseComponent):
    """Generate backtest reports."""
    
    def initialize(self) -> bool:
        """Initialize backtest reporter."""
        self.logger.info("Initializing backtest reporter")
        return True
    
    def generate_summary_report(self, results: Dict[str, Any]) -> str:
        """Generate a summary report."""
        report = f"""
=== Backtest Summary Report ===

Initial Capital: ${results.get('initial_capital', 0):,.2f}
Final Value: ${results.get('final_value', 0):,.2f}
Total Return: {results.get('total_return', 0):.2%}

Trades:
- Total Trades: {len(results.get('trades', []))}
- Final Cash: ${results.get('final_cash', 0):,.2f}
- Final Positions: {results.get('final_positions', {})}

=== End of Report ===
        """
        return report
    
    def generate_detailed_report(self, results: Dict[str, Any], performance_metrics: Dict[str, float]) -> str:
        """Generate detailed report with performance metrics."""
        report = f"""
=== Detailed Backtest Report ===

PORTFOLIO PERFORMANCE
====================
Initial Capital: ${results.get('initial_capital', 0):,.2f}
Final Value: ${results.get('final_value', 0):,.2f}
Total Return: {results.get('total_return', 0):.2%}

PERFORMANCE METRICS
==================
Annualized Return: {performance_metrics.get('annualized_return', 0):.2%}
Volatility: {performance_metrics.get('volatility', 0):.2%}
Sharpe Ratio: {performance_metrics.get('sharpe_ratio', 0):.2f}
Maximum Drawdown: {performance_metrics.get('max_drawdown', 0):.2%}
Calmar Ratio: {performance_metrics.get('calmar_ratio', 0):.2f}

TRADING METRICS
===============
Total Trades: {len(results.get('trades', []))}
Final Cash: ${results.get('final_cash', 0):,.2f}
Final Positions: {results.get('final_positions', {})}

=== End of Detailed Report ===
        """
        return report
    
    def save_report(self, report: str, filename: str) -> bool:
        """Save report to file."""
        try:
            with open(filename, 'w') as f:
                f.write(report)
            self.logger.info(f"Report saved to: {filename}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save report: {str(e)}")
            return False
    
    def export_trades_to_csv(self, trades: list, filename: str) -> bool:
        """Export trades to CSV file."""
        try:
            if trades:
                trade_df = pd.DataFrame(trades)
                trade_df.to_csv(filename, index=False)
                self.logger.info(f"Trades exported to: {filename}")
                return True
            else:
                self.logger.warning("No trades to export")
                return False
        except Exception as e:
            self.logger.error(f"Failed to export trades: {str(e)}")
            return False

