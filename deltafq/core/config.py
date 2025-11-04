"""
Configuration management for DeltaFQ.
"""

import os
from typing import Dict, Any
from pathlib import Path


class Config:
    """Configuration manager for DeltaFQ."""
    
    def __init__(self, config_file: str = None):
        """Initialize configuration."""
        self.config = self._load_default_config()
        if config_file and os.path.exists(config_file):
            self._load_config_file(config_file)
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration."""
        return {
            "data": {
                "cache_dir": "data_cache",
                "default_source": "yahoo"
            },
            "trading": {
                "initial_capital": 1000000,
                "commission": 0.001,
                "slippage": 0.0005
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        }
    
    def _load_config_file(self, config_file: str):
        """Load configuration from file."""
        # Placeholder for config file loading
        pass
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def set(self, key: str, value: Any):
        """Set configuration value."""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value

