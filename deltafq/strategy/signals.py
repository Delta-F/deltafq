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
    
    def ma_signals(self, fast_ma: pd.Series, slow_ma: pd.Series) -> pd.Series:
        """MA crossover using precomputed MAs: 1 if fast>slow, -1 if fast<slow, else 0."""
        if not fast_ma.index.equals(slow_ma.index):
            slow_ma = slow_ma.reindex(fast_ma.index)
        signals = np.where(fast_ma > slow_ma, 1, np.where(fast_ma < slow_ma, -1, 0))
        self.logger.info("Generated MA crossover signals from precomputed MAs")
        return pd.Series(signals, index=fast_ma.index, dtype=int)
    
    def rsi_signals(self, rsi: pd.Series, oversold: float = 30, overbought: float = 70) -> pd.Series:
        """RSI-based signals from precomputed RSI Series."""
        signals = np.where(rsi < oversold, 1, np.where(rsi > overbought, -1, 0))
        self.logger.info("Generated RSI signals from precomputed RSI")
        return pd.Series(signals, index=rsi.index, dtype=int)
    
    def boll_signals(
        self,
        price: pd.Series,
        bands: pd.DataFrame,
        method: str = 'cross',
    ) -> pd.Series:
        """Boll-based signals from precomputed bands: 'touch'|'cross'|'cross_current'."""
        if method not in ['touch', 'cross', 'cross_current']:
            raise ValueError("Invalid method")
        required_cols = {'upper', 'middle', 'lower'}
        missing = required_cols - set(bands.columns)
        if missing:
            raise ValueError("bands missing required columns")
        if not bands.index.equals(price.index):
            bands = bands.reindex(price.index)
        signals = pd.Series(0, index=price.index, dtype=int)
        
        if method == 'touch':
            buy_condition = price <= bands['lower']
            sell_condition = price >= bands['upper']
            signals = np.where(buy_condition, 1, np.where(sell_condition, -1, 0))
        
        elif method == 'cross':
            prev_price = price.shift(1)
            prev_bands = bands.shift(1)
            buy_condition = (prev_price <= prev_bands['lower']) & (price >= bands['lower'])
            sell_condition = (prev_price >= prev_bands['upper']) & (price <= bands['upper'])
            signals = np.where(buy_condition, 1, np.where(sell_condition, -1, 0))

        elif method == 'cross_current':
            prev_price = price.shift(1)
            buy_condition = (prev_price <= bands['lower']) & (price >= bands['lower'])
            sell_condition = (prev_price >= bands['upper']) & (price <= bands['upper'])
            signals = np.where(buy_condition, 1, np.where(sell_condition, -1, 0))
        
        self.logger.info(f"Generated Boll signals: method={method}")
        return pd.Series(signals, index=price.index, dtype=int)
    
    def combine_signals(
        self,
        signals_dict: Dict[str, pd.Series],
        method: str = 'vote',
        weights: Optional[Dict[str, float]] = None,
        threshold: float = 0.5
    ) -> pd.Series:
        """Combine multiple {-1,0,1} Series using 'vote' | 'weighted' | 'and' | 'or' | 'threshold'."""
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
            
        elif method == 'and':
            buy_all = (signals_df == 1).all(axis=1)
            sell_all = (signals_df == -1).all(axis=1)
            combined = pd.Series(0, index=index, dtype=int)
            combined = np.where(buy_all, 1, combined)
            combined = np.where(sell_all, -1, combined)
            
        elif method == 'or':
            buy_any = (signals_df == 1).any(axis=1)
            sell_any = (signals_df == -1).any(axis=1)
            combined = pd.Series(0, index=index, dtype=int)
            combined = np.where(buy_any, 1, combined)
            combined = np.where(sell_any, -1, combined)
            both = buy_any & sell_any
            combined = np.where(both, -1, combined)
            
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
        
        self.logger.info(f"Combined {len(signals_dict)} signals using method '{method}'")
        return pd.Series(combined, index=index, dtype=int)
