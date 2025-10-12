"""
Custom exceptions for DeltaFQ.
"""


class DeltaFQError(Exception):
    """Base exception for DeltaFQ."""
    pass


class DataError(DeltaFQError):
    """Exception raised for data-related errors."""
    pass


class TradingError(DeltaFQError):
    """Exception raised for trading-related errors."""
    pass


class BacktestError(DeltaFQError):
    """Exception raised for backtesting errors."""
    pass


class StrategyError(DeltaFQError):
    """Exception raised for strategy-related errors."""
    pass


class IndicatorError(DeltaFQError):
    """Exception raised for indicator calculation errors."""
    pass

