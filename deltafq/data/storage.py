"""
Data storage management for DeltaFQ.
"""

import pandas as pd
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from ..core.base import BaseComponent


class DataStorage(BaseComponent):
    """
    Data storage manager with categorized storage.
    
    Directory structure:
        data_cache/
        ├── price/          # Price data
        │   └── {symbol}/
        ├── backtest/       # Backtest results
        │   └── {symbol}/
        ├── indicators/     # Technical indicators
        └── misc/          # Other data
    """
    
    def __init__(self, base_path: str = None, **kwargs):
        """Initialize data storage."""
        super().__init__(**kwargs)
        
        # Auto-detect project root if base_path not provided
        if base_path is None:
            project_root = self._get_project_root()
            base_path = project_root / "data_cache"
        
        self.base_path = Path(base_path)
        self.logger.info(f"Initializing data storage at: {self.base_path}")
        self._init_directories()
    
    def _get_project_root(self) -> Path:
        """Get project root directory by finding setup.py or pyproject.toml."""
        current = Path(__file__).resolve()
        # Go up from deltafq/data/storage.py to project root
        for parent in current.parents:
            if (parent / "setup.py").exists() or (parent / "pyproject.toml").exists():
                return parent
        # Fallback to current working directory
        return Path.cwd()
    
    def _init_directories(self):
        """Initialize directory structure."""
        self.price_dir = self.base_path / "price"
        self.backtest_dir = self.base_path / "backtest"
        self.indicators_dir = self.base_path / "indicators"
        self.misc_dir = self.base_path / "misc"
        
        # Create directories
        for dir_path in [self.price_dir, self.backtest_dir, 
                        self.indicators_dir, self.misc_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    
    # ============================================================================
    # Price Data Storage
    # ============================================================================
    
    def save_price_data(self, data: pd.DataFrame, symbol: str, 
                       start_date: Optional[str] = None, 
                       end_date: Optional[str] = None) -> Path:
        """Save price data to storage."""
        symbol_dir = self.price_dir / symbol.replace('.', '_')
        symbol_dir.mkdir(exist_ok=True)
        
        # Generate filename
        if start_date and end_date:
            filename = f"{symbol}_{start_date}_{end_date}.csv"
        else:
            filename = f"{symbol}_{datetime.now().strftime('%Y%m%d')}.csv"
        
        filepath = symbol_dir / filename
        data.to_csv(filepath, encoding='utf-8-sig', index=True)
        self.logger.info(f"Saved price data to: {filepath}")
        return filepath
    
    def load_price_data(self, symbol: str, start_date: Optional[str] = None,
                       end_date: Optional[str] = None) -> Optional[pd.DataFrame]:
        """Load price data from storage."""
        symbol_dir = self.price_dir / symbol.replace('.', '_')
        
        if start_date and end_date:
            filename = f"{symbol}_{start_date}_{end_date}.csv"
        else:
            # Try to find the latest file
            files = list(symbol_dir.glob(f"{symbol}_*.csv"))
            if not files:
                self.logger.warning(f"No price data found for {symbol}")
                return None
            filename = sorted(files)[-1].name
        
        filepath = symbol_dir / filename
        if filepath.exists():
            data = pd.read_csv(filepath, index_col=0, parse_dates=True)
            self.logger.info(f"Loaded price data from: {filepath}")
            return data
        return None
    
    # ============================================================================
    # Backtest Data Storage
    # ============================================================================
    
    def save_backtest_results(self, trades_df: pd.DataFrame, 
                             values_df: pd.DataFrame, symbol: str,
                             strategy_name: Optional[str] = None) -> Dict[str, Path]:
        """Save backtest results to storage."""
        symbol_dir = self.backtest_dir / symbol.replace('.', '_')
        symbol_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        strategy_suffix = f"_{strategy_name}" if strategy_name else ""
        
        trades_path = symbol_dir / f"{symbol}_trades{strategy_suffix}_{timestamp}.csv"
        values_path = symbol_dir / f"{symbol}_values{strategy_suffix}_{timestamp}.csv"
        
        trades_df.to_csv(trades_path, encoding='utf-8-sig', index=False)
        values_df.to_csv(values_path, encoding='utf-8-sig', index=False)
        
        self.logger.info(f"Saved backtest results to: {symbol_dir}")
        return {'trades': trades_path, 'values': values_path}
    
    def load_backtest_results(self, symbol: str, strategy_name: Optional[str] = None,
                             latest: bool = True) -> Optional[Dict[str, pd.DataFrame]]:
        """Load backtest results from storage."""
        symbol_dir = self.backtest_dir / symbol.replace('.', '_')
        
        if not symbol_dir.exists():
            self.logger.warning(f"No backtest results found for {symbol}")
            return None
        
        # Find trades and values files
        if strategy_name:
            trades_files = list(symbol_dir.glob(f"{symbol}_trades_{strategy_name}_*.csv"))
            values_files = list(symbol_dir.glob(f"{symbol}_values_{strategy_name}_*.csv"))
        else:
            trades_files = list(symbol_dir.glob(f"{symbol}_trades*.csv"))
            values_files = list(symbol_dir.glob(f"{symbol}_values*.csv"))
        
        if not trades_files or not values_files:
            self.logger.warning(f"No backtest results found for {symbol}")
            return None
        
        if latest:
            trades_file = sorted(trades_files)[-1]
            values_file = sorted(values_files)[-1]
            return {
                'trades': pd.read_csv(trades_file, encoding='utf-8-sig'),
                'values': pd.read_csv(values_file, encoding='utf-8-sig')
            }
        else:
            # Return all files
            return {
                'trades': [pd.read_csv(f, encoding='utf-8-sig') for f in trades_files],
                'values': [pd.read_csv(f, encoding='utf-8-sig') for f in values_files]
            }
    
    # ============================================================================
    # Generic Storage Methods
    # ============================================================================
    
    def save_data(self, data: pd.DataFrame, filename: str, 
                 category: str = "misc", subdir: Optional[str] = None) -> Path:
        """Save data to storage with category."""
        if category == "price":
            target_dir = self.price_dir
        elif category == "backtest":
            target_dir = self.backtest_dir
        elif category == "indicators":
            target_dir = self.indicators_dir
        else:
            target_dir = self.misc_dir
        
        if subdir:
            target_dir = target_dir / subdir
            target_dir.mkdir(parents=True, exist_ok=True)
        
        filepath = target_dir / filename
        data.to_csv(filepath, encoding='utf-8-sig', index=False)
        self.logger.info(f"Saved data to: {filepath}")
        return filepath
    
    def load_data(self, filename: str, category: str = "misc", 
                 subdir: Optional[str] = None) -> Optional[pd.DataFrame]:
        """Load data from storage."""
        if category == "price":
            target_dir = self.price_dir
        elif category == "backtest":
            target_dir = self.backtest_dir
        elif category == "indicators":
            target_dir = self.indicators_dir
        else:
            target_dir = self.misc_dir
        
        if subdir:
            target_dir = target_dir / subdir
        
        filepath = target_dir / filename
        if filepath.exists():
            data = pd.read_csv(filepath, encoding='utf-8-sig')
            self.logger.info(f"Loaded data from: {filepath}")
            return data
        else:
            self.logger.warning(f"File not found: {filepath}")
            return None
    
    # ============================================================================
    # Utility Methods
    # ============================================================================
    
    def list_files(self, category: Optional[str] = None, 
                  subdir: Optional[str] = None) -> list:
        """List all files in storage."""
        if category == "price":
            target_dir = self.price_dir
        elif category == "backtest":
            target_dir = self.backtest_dir
        elif category == "indicators":
            target_dir = self.indicators_dir
        elif category == "misc":
            target_dir = self.misc_dir
        else:
            target_dir = self.base_path
        
        if subdir:
            target_dir = target_dir / subdir
        
        if not target_dir.exists():
            return []
        
        files = []
        for item in target_dir.rglob('*.csv'):
            if item.is_file():
                files.append(str(item.relative_to(self.base_path)))
        return files
    
    def get_storage_info(self) -> Dict[str, Any]:
        """Get storage information."""
        return {
            'base_path': str(self.base_path),
            'price_files': len(list(self.price_dir.rglob('*.csv'))),
            'backtest_files': len(list(self.backtest_dir.rglob('*.csv'))),
            'indicators_files': len(list(self.indicators_dir.rglob('*.csv'))),
            'misc_files': len(list(self.misc_dir.rglob('*.csv'))),
            'total_size_mb': self._calculate_size()
        }
    
    def _calculate_size(self) -> float:
        """Calculate total storage size in MB."""
        total_size = 0
        for file_path in self.base_path.rglob('*'):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        return round(total_size / (1024 * 1024), 2)
