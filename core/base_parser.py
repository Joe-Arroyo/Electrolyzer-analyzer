"""
Base parser interface for instrument data files.
All instrument parsers should inherit from this.
"""

from abc import ABC, abstractmethod
from typing import Optional
from core.data_model import ElectrolyzerData


class BaseParser(ABC):
    """Abstract base class for all instrument parsers"""
    
    @property
    @abstractmethod
    def instrument_name(self) -> str:
        """Return instrument identifier"""
        pass
    
    @property
    @abstractmethod
    def supported_techniques(self) -> list:
        """Which techniques this parser handles"""
        pass
    
    @abstractmethod
    def can_parse(self, filepath: str) -> bool:
        """Check if this parser can handle the file"""
        pass
    
    @abstractmethod
    def parse(self, filepath: str) -> Optional[ElectrolyzerData]:
        """Parse file to unified format"""
        pass