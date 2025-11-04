"""
Base classes for DeltaFQ components.
"""

from abc import ABC, abstractmethod
from .logger import Logger


class BaseComponent(ABC):
    """Base class for all DeltaFQ components."""
    
    def __init__(self, name: str = None, **kwargs):
        """Initialize base component."""
        self.name = name or self.__class__.__name__
        self.logger = Logger(self.name)
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the component."""
        pass

