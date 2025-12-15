"""
Parsers for different potentiostat manufacturers.
Currently supports: Gamry
"""

from .gamry import GamryParser, load_gamry_file

__all__ = ['GamryParser', 'load_gamry_file']