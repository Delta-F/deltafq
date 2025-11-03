"""
Signal generator for trading strategies.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
from ..core.base import BaseComponent


class SignalGenerator(BaseComponent):
    """Generate trading signals from market data."""
    
    def initialize(self) -> bool:
        """Initialize signal generator."""
        self.logger.info("Initializing signal generator")
        return True
    
    def moving_average_crossover(self, data: pd.DataFrame, fast_period: int = 10, slow_period: int = 20) -> pd.Series:
        """Generate signals based on moving average crossover."""
        if 'Close' not in data.columns:
            raise ValueError("Data must contain 'Close' column")
        
        # Calculate moving averages
        fast_ma = data['Close'].rolling(window=fast_period).mean()
        slow_ma = data['Close'].rolling(window=slow_period).mean()
        
        # Generate signals: 1 for buy, -1 for sell, 0 for hold
        signals = np.where(fast_ma > slow_ma, 1, np.where(fast_ma < slow_ma, -1, 0))
        
        self.logger.info(f"Generated MA crossover signals: {fast_period}/{slow_period}")
        return pd.Series(signals, index=data.index)
    
    def rsi_signals(self, data: pd.DataFrame, period: int = 14, oversold: float = 30, overbought: float = 70) -> pd.Series:
        """Generate signals based on RSI."""
        if 'Close' not in data.columns:
            raise ValueError("Data must contain 'Close' column")
        
        # Calculate RSI (simplified)
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # Generate signals
        signals = np.where(rsi < oversold, 1, np.where(rsi > overbought, -1, 0))
        
        self.logger.info(f"Generated RSI signals: period={period}")
        return pd.Series(signals, index=data.index)
    
    def bollinger_bands_signals(self, 
                                data: pd.DataFrame, 
                                period: int = 20, 
                                std_dev: float = 2,
                                method: str = 'touch',
                                bands: Optional[pd.DataFrame] = None) -> pd.Series:
        """
        Generate trading signals based on Bollinger Bands.
        
        Bollinger Bands consist of upper, middle (SMA), and lower bands. Common signal strategies:
        - 'touch': Buy when price touches/breaks lower band, sell when touches upper band
        - 'breakout': Buy on breakout above upper band, sell on breakdown below lower band
        - 'mean_reversion': Buy when price touches lower band and bounces, sell when touches upper and falls
        - 'cross': Buy when price crosses up the lower band; sell when price crosses down the upper band
        
        Args:
            data: DataFrame with 'Close' column containing price data.
            period: Number of periods for Bollinger Bands calculation. Default is 20.
            std_dev: Standard deviation multiplier for band width. Default is 2.
            method: Signal generation method. Options:
                - 'touch': Price-based signals when touching bands
                - 'breakout': Trend-following signals on breakouts
                - 'mean_reversion': Mean reversion signals on bounces
                Default is 'touch'.
            bands: Optional precomputed Bollinger Bands DataFrame with columns
                {'upper','middle','lower'} aligned to data.index. If provided,
                the function will use it directly and skip internal computation.
        
        Returns:
            A pandas Series with signals:
            - 1: Buy signal
            - -1: Sell signal
            - 0: Hold/no signal
        
        Example:
            >>> signals = generator.bollinger_bands_signals(data, period=20, method='touch')
            >>> buy_signals = signals[signals == 1]
        """
        from ..indicators.technical import TechnicalIndicators
        
        if 'Close' not in data.columns:
            raise ValueError("Data must contain 'Close' column")
        
        if method not in ['touch', 'breakout', 'mean_reversion', 'cross']:
            raise ValueError(f"Invalid method '{method}'. Must be one of: 'touch', 'breakout', 'mean_reversion'")
        
        # Calculate or use precomputed Bollinger Bands
        if bands is None:
            indicators = TechnicalIndicators()
            bands = indicators.bollinger_bands(data['Close'], period=period, std_dev=std_dev)
        else:
            # Basic validation
            required_cols = {'upper', 'middle', 'lower'}
            missing = required_cols - set(bands.columns)
            if missing:
                raise ValueError(f"Precomputed bands missing columns: {missing}")
            if not bands.index.equals(data.index):
                bands = bands.reindex(data.index)
        
        price = data['Close']
        signals = pd.Series(0, index=data.index, dtype=int)
        
        if method == 'touch':
            # Buy when price touches or breaks below lower band, sell when touches or breaks above upper band
            buy_condition = price <= bands['lower']
            sell_condition = price >= bands['upper']
            signals = np.where(buy_condition, 1, np.where(sell_condition, -1, 0))
        
        elif method == 'breakout':
            # Trend-following: Buy on breakout above upper band, sell on breakdown below lower band
            # This assumes continuation of trend
            buy_condition = price > bands['upper']
            sell_condition = price < bands['lower']
            signals = np.where(buy_condition, 1, np.where(sell_condition, -1, 0))
        
        elif method == 'mean_reversion':
            # Mean reversion strategy: Buy when price touches lower band and starts bouncing,
            # sell when price touches upper band and starts falling
            # Buy: price touches lower band and price is rising (bounce back)
            price_change = price.diff()
            buy_signal = (price <= bands['lower']) & (price_change > 0)
            # Sell: price touches upper band and price is falling (pull back)
            sell_signal = (price >= bands['upper']) & (price_change < 0)
            signals = np.where(buy_signal, 1, np.where(sell_signal, -1, 0))

        elif method == 'cross':
            # Cross confirmation strategy: require a band boundary crossover between prev and current
            prev_price = price.shift(1)
            buy_condition = (prev_price <= bands['lower']) & (price >= bands['lower'])
            sell_condition = (prev_price >= bands['upper']) & (price <= bands['upper'])
            signals = np.where(buy_condition, 1, np.where(sell_condition, -1, 0))
        
        self.logger.info(f"Generated Bollinger Bands signals: period={period}, std_dev={std_dev}, method={method}")
        return pd.Series(signals, index=data.index, dtype=int)
    
    def combine_signals(
        self,
        signals_dict: Dict[str, pd.Series],
        method: str = 'vote',
        weights: Optional[Dict[str, float]] = None,
        threshold: float = 0.5
    ) -> pd.Series:
        """
        Combine multiple signal Series into a single composite signal.
        
        This method allows combining signals from different indicators using various
        combination strategies, enabling multi-factor decision making. It's useful
        when you want to combine signals that have already been generated separately,
        including custom signals from external sources.
        
        Key Features:
        - Combines any signal Series (from this class or custom signals)
        - Supports multiple combination strategies
        - Allows fine-grained control over weights
        - Useful for experimentation and testing different combinations
        
        Args:
            signals_dict: Dictionary mapping signal names to signal Series.
                         All Series must have the same index and length.
                         Example: {'ma_signal': ma_series, 'rsi_signal': rsi_series, 'custom': custom_series}
            method: Combination method:
                - 'vote': Majority voting - most common signal (buy/sell/hold) wins
                - 'weighted': Weighted sum - sum of weighted signals, normalize to -1/0/1
                - 'and': Logical AND - all signals must agree (most conservative)
                - 'or': Logical OR - any signal triggers (most aggressive)
                - 'threshold': Weighted sum must exceed threshold to trigger
            weights: Dictionary of weights for each signal name.
                    Required for 'weighted' and 'threshold' methods.
                    Defaults to equal weights if not provided.
            threshold: Threshold value for 'threshold' method (default: 0.5).
                      Signal is triggered if weighted sum >= threshold
    
        Returns:
            A pandas Series with combined signals:
            - 1: Buy signal
            - -1: Sell signal  
            - 0: Hold/no signal
        
        Example:
            >>> # Generate individual signals
            >>> ma_signal = generator.moving_average_crossover(data)
            >>> rsi_signal = generator.rsi_signals(data)
            >>> bb_signal = generator.bollinger_bands_signals(data)
            >>> 
            >>> # Majority voting (most common signal wins)
            >>> combined = generator.combine_signals(
            ...     {'MA': ma_signal, 'RSI': rsi_signal, 'BB': bb_signal},
            ...     method='vote'
            ... )
            >>> 
            >>> # Weighted combination (MA权重60%，RSI权重40%)
            >>> combined = generator.combine_signals(
            ...     {'MA': ma_signal, 'RSI': rsi_signal},
            ...     method='weighted',
            ...     weights={'MA': 0.6, 'RSI': 0.4}
            ... )
            >>> 
            >>> # Conservative strategy (所有信号必须一致)
            >>> combined = generator.combine_signals(
            ...     {'MA': ma_signal, 'RSI': rsi_signal, 'BB': bb_signal},
            ...     method='and'
            ... )
        """
        if not signals_dict:
            raise ValueError("signals_dict cannot be empty")
        
        # Validate all signals have same index
        signal_names = list(signals_dict.keys())
        first_signal = signals_dict[signal_names[0]]
        index = first_signal.index
        
        for name, signal in signals_dict.items():
            if len(signal) != len(first_signal):
                raise ValueError(f"Signal '{name}' has different length")
            if not signal.index.equals(index):
                signals_dict[name] = signal.reindex(index)
                self.logger.info(f"Aligned signal '{name}' index")
        
        # Convert to DataFrame for easier manipulation
        signals_df = pd.DataFrame(signals_dict)
        
        if method == 'vote':
            # Majority voting: most common signal wins
            # Count buy (1), sell (-1), hold (0) votes
            buy_votes = (signals_df == 1).sum(axis=1)
            sell_votes = (signals_df == -1).sum(axis=1)
            hold_votes = (signals_df == 0).sum(axis=1)
            
            # Determine winner
            combined = pd.Series(0, index=index, dtype=int)
            combined = np.where(buy_votes > sell_votes, 1, combined)
            combined = np.where(sell_votes > buy_votes, -1, combined)
            # If tie or all hold, stay at 0
            
        elif method == 'weighted':
            # Weighted sum of signals
            if weights is None:
                weights = {name: 1.0 / len(signals_dict) for name in signal_names}
            else:
                # Normalize weights to sum to 1
                total_weight = sum(weights.values())
                if total_weight == 0:
                    raise ValueError("Total weight cannot be zero")
                weights = {k: v / total_weight for k, v in weights.items()}
            
            # Calculate weighted sum
            weighted_sum = pd.Series(0.0, index=index)
            for name in signal_names:
                weighted_sum += signals_df[name] * weights.get(name, 0)
            
            # Convert to -1, 0, 1 based on weighted sum
            # Use threshold of 0.33 to avoid too sensitive triggers
            combined = pd.Series(0, index=index, dtype=int)
            combined = np.where(weighted_sum > 0.33, 1, combined)  # Positive threshold
            combined = np.where(weighted_sum < -0.33, -1, combined)  # Negative threshold
            
        elif method == 'and':
            # Logical AND: all signals must agree
            buy_all = (signals_df == 1).all(axis=1)
            sell_all = (signals_df == -1).all(axis=1)
            combined = pd.Series(0, index=index, dtype=int)
            combined = np.where(buy_all, 1, combined)
            combined = np.where(sell_all, -1, combined)
            
        elif method == 'or':
            # Logical OR: any signal triggers
            buy_any = (signals_df == 1).any(axis=1)
            sell_any = (signals_df == -1).any(axis=1)
            combined = pd.Series(0, index=index, dtype=int)
            combined = np.where(buy_any, 1, combined)
            combined = np.where(sell_any, -1, combined)
            # If both buy and sell exist, prioritize sell (more conservative)
            both = buy_any & sell_any
            combined = np.where(both, -1, combined)
            
        elif method == 'threshold':
            # Weighted sum must exceed threshold
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
            raise ValueError(f"Invalid method '{method}'. Must be one of: 'vote', 'weighted', 'and', 'or', 'threshold'")
        
        self.logger.info(f"Combined {len(signals_dict)} signals using method '{method}'")
        return pd.Series(combined, index=index, dtype=int)
    
    def multi_factor_signals(
        self,
        data: pd.DataFrame,
        factors: List[Dict[str, Any]],
        combination_method: str = 'vote',
        weights: Optional[List[float]] = None
    ) -> pd.Series:
        """
        Generate signals using multiple factors/indicators in a single call.
        
        This is a convenience method that generates multiple signals internally
        and combines them using the specified method. It's designed for quick
        prototyping and when you want to define all factors in one configuration.
        
        Key Features:
        - One-call generation and combination
        - Configuration-based approach (easier to save/load strategies)
        - Supports all predefined factor types
        - Ideal for rapid experimentation
        
        Args:
            data: DataFrame with 'Close' column containing price data.
            factors: List of factor configurations. Each dict should contain:
                - 'type': Signal type - one of:
                    * 'ma_crossover': Moving average crossover
                    * 'rsi': RSI-based signals
                    * 'bollinger': Bollinger Bands signals
                - 'params': Dictionary of parameters for that signal type
                  For 'ma_crossover': {'fast_period': 10, 'slow_period': 20}
                  For 'rsi': {'period': 14, 'oversold': 30, 'overbought': 70}
                  For 'bollinger': {'period': 20, 'std_dev': 2, 'method': 'touch'}
            combination_method: How to combine signals:
                - 'vote': Majority voting (default)
                - 'weighted': Weighted sum
                - 'and': All must agree
                - 'or': Any triggers
            weights: Optional list of weights for each factor (in same order).
                    Only used for 'weighted' combination method.
                    Defaults to equal weights if not provided.
    
        Returns:
            Combined signal Series
    
        Example:
            >>> # Define multiple factors in one configuration
            >>> factors = [
            ...     {'type': 'ma_crossover', 'params': {'fast_period': 10, 'slow_period': 20}},
            ...     {'type': 'rsi', 'params': {'period': 14, 'oversold': 30, 'overbought': 70}},
            ...     {'type': 'bollinger', 'params': {'period': 20, 'method': 'touch'}}
            ... ]
            >>> 
            >>> # Generate combined signals with majority voting
            >>> signals = generator.multi_factor_signals(data, factors, combination_method='vote')
            >>> 
            >>> # Or with weighted combination
            >>> signals = generator.multi_factor_signals(
            ...     data, factors, 
            ...     combination_method='weighted',
            ...     weights=[0.5, 0.3, 0.2]
            ... )
        """
        if not factors:
            raise ValueError("factors list cannot be empty")
        
        generated_signals = {}
        
        for i, factor in enumerate(factors):
            factor_type = factor.get('type')
            params = factor.get('params', {})
            
            if factor_type == 'ma_crossover':
                signal = self.moving_average_crossover(
                    data,
                    fast_period=params.get('fast_period', 10),
                    slow_period=params.get('slow_period', 20)
                )
                generated_signals[f'MA_{i}'] = signal
                
            elif factor_type == 'rsi':
                signal = self.rsi_signals(
                    data,
                    period=params.get('period', 14),
                    oversold=params.get('oversold', 30),
                    overbought=params.get('overbought', 70)
                )
                generated_signals[f'RSI_{i}'] = signal
                
            elif factor_type == 'bollinger':
                signal = self.bollinger_bands_signals(
                    data,
                    period=params.get('period', 20),
                    std_dev=params.get('std_dev', 2),
                    method=params.get('method', 'touch')
                )
                generated_signals[f'BB_{i}'] = signal
                
            else:
                raise ValueError(f"Unknown factor type '{factor_type}'. Must be one of: 'ma_crossover', 'rsi', 'bollinger'")
        
        # Combine signals
        if weights and len(weights) == len(factors):
            weights_dict = {name: weights[i] for i, name in enumerate(generated_signals.keys())}
        else:
            weights_dict = None
        
        combined = self.combine_signals(
            generated_signals,
            method=combination_method,
            weights=weights_dict
        )
        
        self.logger.info(f"Generated multi-factor signals with {len(factors)} factors using '{combination_method}' method")
        return combined

