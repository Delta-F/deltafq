"""
Data storage management for DeltaFQ.
"""

import pandas as pd
import os
from pathlib import Path
from typing import Optional
from ..core.base import BaseComponent


class DataStorage(BaseComponent):
    """Data storage manager."""
    
    def __init__(self, storage_path: str = "./data_cache", **kwargs):
        """Initialize data storage."""
        super().__init__(**kwargs)
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
    
    def initialize(self) -> bool:
        """Initialize the data storage."""
        self.logger.info(f"Initializing data storage at: {self.storage_path}")
        return True
    
    def save_data(self, data: pd.DataFrame, filename: str) -> bool:
        """Save data to storage."""
        try:
            filepath = self.storage_path / filename
            data.to_csv(filepath, index=False)
            self.logger.info(f"Saved data to: {filepath}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save data: {str(e)}")
            return False
    
    def load_data(self, filename: str) -> Optional[pd.DataFrame]:
        """Load data from storage."""
        try:
            filepath = self.storage_path / filename
            if filepath.exists():
                data = pd.read_csv(filepath)
                self.logger.info(f"Loaded data from: {filepath}")
                return data
            else:
                self.logger.warning(f"File not found: {filepath}")
                return None
        except Exception as e:
            self.logger.error(f"Failed to load data: {str(e)}")
            return None
    
    def list_files(self) -> list:
        """List all files in storage."""
        return [f.name for f in self.storage_path.iterdir() if f.is_file()]

