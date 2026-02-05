"""
Parser modules for electrochemical data files
"""

from .gamry import load_gamry_file
from .autolab import (
    load_autolab_file, 
    load_autolab_ascii, 
    load_autolab_excel,
    load_autolab_chronopotentiometry_ascii,
    load_autolab_chronopotentiometry_excel
)

__all__ = [
    'load_gamry_file',
    'load_autolab_file',
    'load_autolab_ascii',
    'load_autolab_excel',
    'load_autolab_chronopotentiometry_ascii',
    'load_autolab_chronopotentiometry_excel'
]