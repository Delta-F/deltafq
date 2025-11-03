"""
Base classes for DeltaFQ components.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict
from .logger import Logger
from .config import Config


class BaseComponent(ABC):
    """Base class for all DeltaFQ components."""
    
    def __init__(self, name: str = None, config: Config = None, **kwargs):
        """Initialize base component."""
        self.name = name or self.__class__.__name__
        self.config = config or Config()
        self.logger = Logger(self.name)
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the component."""
        pass
    
    def cleanup(self):
        """Cleanup resources."""
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """Get component information."""
        return {
            "name": self.name,
            "class": self.__class__.__name__,
            "config": self.config.config
        }

