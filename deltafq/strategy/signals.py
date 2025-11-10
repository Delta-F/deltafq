"""Essential signal generation and combination utilities."""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from ..core.base import BaseComponent


class SignalGenerator(BaseComponent):
    """Generate trading signals from precomputed indicators and combine them."""
    
    def initialize(self) -> bool:
        """Initialize signal generator."""
        self.logger.info("Initializing signal generator")
        return True

    def _log_signal_counts(self, label: str, series: pd.Series) -> None:
        """Log the number of buy, sell, and flat signals."""
        buy = int((series == 1).sum())
        sell = int((series == -1).sum())
        flat = int((series == 0).sum())
        self.logger.info(f"{label} signals -> buy={buy}, sell={sell}, flat={flat}")
        
    # --- SMA -----------------------------------------------------------------
    def sma_signals(self, fast_ma: pd.Series, slow_ma: pd.Series) -> pd.Series:
        """Bullish when the fast MA is above the slow MA, bearish when below."""
        if not fast_ma.index.equals(slow_ma.index):
            slow_ma = slow_ma.reindex(fast_ma.index)
        signals = pd.Series(
            np.where(fast_ma > slow_ma, 1, np.where(fast_ma < slow_ma, -1, 0)),
            index=fast_ma.index,
            dtype=int,
        )
        self._log_signal_counts("SMA crossover", signals)
        return signals

    def ma_signals(self, fast_ma: pd.Series, slow_ma: pd.Series) -> pd.Series:
        """Alias for backwards compatibility."""
        return self.sma_signals(fast_ma, slow_ma)

    # --- EMA -----------------------------------------------------------------
    def ema_signals(self, price: pd.Series, ema: pd.Series) -> pd.Series:
        """Bullish when price sits above the EMA, bearish when it falls below."""
        if not price.index.equals(ema.index):
            ema = ema.reindex(price.index)
        signals = pd.Series(
            np.where(price > ema, 1, np.where(price < ema, -1, 0)),
            index=price.index,
            dtype=int,
        )
        self._log_signal_counts("EMA price-vs-ema", signals)
        return signals

    # --- RSI -----------------------------------------------------------------
    def rsi_signals(self, rsi: pd.Series, oversold: float = 30, overbought: float = 70) -> pd.Series:
        """Buy when RSI drops beneath the oversold band, sell when above overbought."""
        signals = pd.Series(
            np.where(rsi < oversold, 1, np.where(rsi > overbought, -1, 0)),
            index=rsi.index,
            dtype=int,
        )
        self._log_signal_counts("RSI", signals)
        return signals

    # --- KDJ -----------------------------------------------------------------
    def kdj_signals(self, kdj: pd.DataFrame) -> pd.Series:
        """Bullish on K crossing above D, bearish on K crossing beneath D."""
        for col in ("k", "d"):
            if col not in kdj:
                raise ValueError("kdj must contain 'k' and 'd' columns")
        signals = pd.Series(
            np.where(kdj["k"] > kdj["d"], 1, np.where(kdj["k"] < kdj["d"], -1, 0)),
            index=kdj.index,
            dtype=int,
        )
        self._log_signal_counts("KDJ K>D", signals)
        return signals

    # --- BOLL ----------------------------------------------------------------
    def boll_signals(self, price: pd.Series, bands: pd.DataFrame, method: str = "cross") -> pd.Series:
        """Bollinger logic: touch or cross of the outer bands triggers entries."""
        if method not in ["touch", "cross", "cross_current"]:
            raise ValueError("Invalid method")
        if not all(col in bands for col in ("upper", "middle", "lower")):
            raise ValueError("bands missing required columns")

        signals = pd.Series(0, index=price.index, dtype=int)

        if method == "touch":
            buy_condition = price <= bands["lower"]
            sell_condition = price >= bands["upper"]
            signals = np.where(buy_condition, 1, np.where(sell_condition, -1, 0))

        elif method == "cross":
            prev_price = price.shift(1)
            prev_bands = bands.shift(1)
            buy_condition = (prev_price <= prev_bands["lower"]) & (price >= bands["lower"])
            sell_condition = (prev_price >= prev_bands["upper"]) & (price <= bands["upper"])
            signals = np.where(buy_condition, 1, np.where(sell_condition, -1, 0))

        elif method == "cross_current":
            prev_price = price.shift(1)
            buy_condition = (prev_price <= bands["lower"]) & (price >= bands["lower"])
            sell_condition = (prev_price >= bands["upper"]) & (price <= bands["upper"])
            signals = np.where(buy_condition, 1, np.where(sell_condition, -1, 0))

        series = pd.Series(signals, index=price.index, dtype=int)
        self._log_signal_counts(f"Boll ({method})", series)
        return series

    # --- OBV -----------------------------------------------------------------
    def obv_signals(self, obv: pd.Series) -> pd.Series:
        """Positive OBV slope hints at buying pressure; negative slope at selling."""
        obv_change = obv.diff().fillna(0)
        signals = pd.Series(
            np.where(obv_change > 0, 1, np.where(obv_change < 0, -1, 0)),
            index=obv.index,
            dtype=int,
        )
        self._log_signal_counts("OBV slope", signals)
        return signals
    
    def combine_signals(
        self,
        signals_dict: Dict[str, pd.Series],
        method: str = 'vote',
        weights: Optional[Dict[str, float]] = None,
        threshold: float = 0.5
    ) -> pd.Series:
        """Combine multiple {-1,0,1} Series using 'vote' | 'weighted' | 'threshold'."""
        if not signals_dict:
            raise ValueError("signals_dict cannot be empty")
        
        signal_names = list(signals_dict.keys())
        first_signal = signals_dict[signal_names[0]]
        index = first_signal.index
        
        for name, signal in signals_dict.items():
            if len(signal) != len(first_signal):
                raise ValueError(f"Signal '{name}' has different length")
            if not signal.index.equals(index):
                signals_dict[name] = signal.reindex(index)
                self.logger.info(f"Aligned signal '{name}' index")
        
        signals_df = pd.DataFrame(signals_dict)
        
        if method == 'vote':
            buy_votes = (signals_df == 1).sum(axis=1)
            sell_votes = (signals_df == -1).sum(axis=1)
            combined = pd.Series(0, index=index, dtype=int)
            combined = np.where(buy_votes > sell_votes, 1, combined)
            combined = np.where(sell_votes > buy_votes, -1, combined)
            
        elif method == 'weighted':
            if weights is None:
                weights = {name: 1.0 / len(signals_dict) for name in signal_names}
            else:
                total_weight = sum(weights.values())
                if total_weight == 0:
                    raise ValueError("Total weight cannot be zero")
                weights = {k: v / total_weight for k, v in weights.items()}
            
            weighted_sum = pd.Series(0.0, index=index)
            for name in signal_names:
                weighted_sum += signals_df[name] * weights.get(name, 0)
            
            combined = pd.Series(0, index=index, dtype=int)
            combined = np.where(weighted_sum > 0.33, 1, combined)
            combined = np.where(weighted_sum < -0.33, -1, combined)
            
        elif method == 'threshold':
            if weights is None:
                weights = {name: 1.0 / len(signals_dict) for name in signal_names}
            else:
                total_weight = sum(weights.values())
                if total_weight == 0:
                    raise ValueError("Total weight cannot be zero")
                weights = {k: v / total_weight for k, v in weights.items()}
            
            weighted_sum = pd.Series(0.0, index=index)
            for name in signal_names:
                weighted_sum += signals_df[name] * weights.get(name, 0)
            
            combined = pd.Series(0, index=index, dtype=int)
            combined = np.where(weighted_sum >= threshold, 1, combined)
            combined = np.where(weighted_sum <= -threshold, -1, combined)
            
        else:
            raise ValueError("Invalid method")
        
        combined_series = pd.Series(combined, index=index, dtype=int)
        self._log_signal_counts(f"Combined ({method})", combined_series)
        return combined_series
