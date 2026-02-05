"""
Parser modules for electrochemical data files
"""

from .gamry import load_gamry_file
from .autolab import (
    load_autolab_chronopotentiometry_ascii,
    load_autolab_chronopotentiometry_excel
)
from .riden import load_riden_file
from .custom_csv import load_custom_csv

__all__ = [
    'load_gamry_file',
    'load_autolab_chronopotentiometry_ascii',
    'load_autolab_chronopotentiometry_excel',
    'load_riden_file',
    'load_custom_csv'
]