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
    
    def get_cache_dir(self) -> Path:
        """Get cache directory path (project root / data_cache)."""
        project_root = self._get_project_root()
        cache_dir_name = self.get("data.cache_dir", "data_cache")
        return project_root / cache_dir_name
    
    def _get_project_root(self) -> Path:
        """Get project root directory by finding setup.py or pyproject.toml."""
        current = Path(__file__).resolve()
        # Go up from deltafq/core/config.py to project root
        # deltafq/core/config.py -> deltafq/core -> deltafq -> project_root
        for parent in current.parents:
            if (parent / "setup.py").exists() or (parent / "pyproject.toml").exists():
                return parent
        # If not found, assume deltafq package is 2 levels up from config.py
        # This should never happen in normal usage, but provides a safe fallback
        return current.parent.parent.parent

