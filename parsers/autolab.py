"""
Autolab file parser for EIS data
Supports both ASCII (.txt) and Excel (.xlsx) formats
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add parent directory to path to import core modules
sys.path.append(str(Path(__file__).parent.parent))
from core.data_model import ElectrolyzerData


def load_autolab_ascii(file_path):
    """
    Load Autolab ASCII EIS file (.txt)
    
    Args:
        file_path: Path to .txt file
        
    Returns:
        ElectrolyzerData object or None if parsing fails
    """
    try:
        file_path = Path(file_path)
        
        # Read data using pandas with proper settings for Autolab format
        # Autolab uses semicolon separator and comma as decimal
        df = pd.read_csv(
            file_path,
            sep=';',           # Semicolon-separated
            decimal=',',       # Comma as decimal separator
            encoding='utf-8'
        )
        
        # Clean column names (remove whitespace, make lowercase)
        df.columns = df.columns.str.strip().str.lower()
        
        print(f"Available columns: {list(df.columns)}")
        
        # Try to identify columns
        # Autolab format: frequency (hz), z' (ω), -z'' (ω)
        
        freq_col = None
        zreal_col = None
        zimag_col = None
        
        for col in df.columns:
            col_lower = col.lower()
            
            # Frequency
            if 'frequency' in col_lower:
                freq_col = col
            
            # Z' is real impedance (look for z' but NOT -z'')
            elif "z'" in col_lower and "-z''" not in col_lower:
                zreal_col = col
            
            # -Z'' is negative imaginary (look for -z'')
            elif "-z''" in col_lower:
                zimag_col = col
        
        if not all([freq_col, zreal_col, zimag_col]):
            print(f"Could not identify required columns in {file_path}")
            print(f"Found - Freq: {freq_col}, Zreal: {zreal_col}, Zimag: {zimag_col}")
            return None
        
        print(f"Matched columns - Freq: {freq_col}, Zreal: {zreal_col}, Zimag: {zimag_col}")
        
        # Remove any NaN values
        valid_mask = ~(df[freq_col].isna() | df[zreal_col].isna() | df[zimag_col].isna())
        
        # Extract data
        freq_data = df[freq_col][valid_mask].reset_index(drop=True)
        zreal_data = df[zreal_col][valid_mask].reset_index(drop=True)
        zimag_data = df[zimag_col][valid_mask].reset_index(drop=True)
        
        # Autolab exports -Z'', but we store positive imaginary
        # So negate the column to get positive imaginary
        zimag_data = -zimag_data
        
        # Create time series (just an index, like Gamry does for EIS)
        time_series = pd.Series(range(len(freq_data)), name='index')
        
        # Create ElectrolyzerData object (matching Gamry's EIS pattern)
        data = ElectrolyzerData(
            technique='eis',
            instrument='autolab',
            time=time_series,
            voltage=pd.Series([0] * len(freq_data)),  # EIS doesn't have voltage series
            current=pd.Series([0] * len(freq_data)),  # EIS doesn't have current series
            frequency=freq_data,
            z_real=zreal_data,
            z_imag=zimag_data,
            source_file=file_path
        )
        
        print(f"✓ Loaded Autolab ASCII: {file_path.name}")
        print(f"  Shape: {len(data.frequency)} points")
        print(f"  Frequency range: {data.frequency.min():.3f} - {data.frequency.max():.3f} Hz")
        print(f"  Z_real range: {data.z_real.min():.3f} - {data.z_real.max():.3f} Ω")
        print(f"  Z_imag range: {data.z_imag.min():.3f} - {data.z_imag.max():.3f} Ω")
        
        return data
        
    except Exception as e:
        print(f"Error loading Autolab ASCII file {file_path}: {e}")
        import traceback
        traceback.print_exc()
        return None


def load_autolab_excel(file_path):
    """
    Load Autolab Excel EIS file (.xlsx)
    
    Args:
        file_path: Path to .xlsx file
        
    Returns:
        ElectrolyzerData object or None if parsing fails
    """
    try:
        file_path = Path(file_path)
        
        # Try to read the Excel file
        # Autolab often puts data in the first sheet
        df = pd.read_excel(file_path, sheet_name=0)
        
        # Clean column names (remove whitespace, make lowercase)
        df.columns = df.columns.str.strip().str.lower()
        
        print(f"Available columns: {list(df.columns)}")
        
        # Try to identify columns
        freq_col = None
        zreal_col = None
        zimag_col = None
        
        for col in df.columns:
            col_lower = col.lower()
            
            # Frequency
            if 'frequency' in col_lower:
                freq_col = col
            
            # Z' is real impedance (look for z' but NOT -z'')
            elif "z'" in col_lower and "-z''" not in col_lower:
                zreal_col = col
            
            # -Z'' is negative imaginary (look for -z'')
            elif "-z''" in col_lower:
                zimag_col = col
        
        if not all([freq_col, zreal_col, zimag_col]):
            print(f"Could not identify required columns in {file_path}")
            print(f"Found - Freq: {freq_col}, Zreal: {zreal_col}, Zimag: {zimag_col}")
            return None
        
        print(f"Matched columns - Freq: {freq_col}, Zreal: {zreal_col}, Zimag: {zimag_col}")
        
        # Remove any NaN values
        valid_mask = ~(df[freq_col].isna() | df[zreal_col].isna() | df[zimag_col].isna())
        
        # Extract data
        freq_data = df[freq_col][valid_mask].reset_index(drop=True)
        zreal_data = df[zreal_col][valid_mask].reset_index(drop=True)
        zimag_data = df[zimag_col][valid_mask].reset_index(drop=True)
        
        # Autolab exports -Z'', but we store positive imaginary
        # So negate the column to get positive imaginary
        zimag_data = -zimag_data
        
        # Create time series (just an index, like Gamry does for EIS)
        time_series = pd.Series(range(len(freq_data)), name='index')
        
        # Create ElectrolyzerData object (matching Gamry's EIS pattern)
        data = ElectrolyzerData(
            technique='eis',
            instrument='autolab',
            time=time_series,
            voltage=pd.Series([0] * len(freq_data)),  # EIS doesn't have voltage series
            current=pd.Series([0] * len(freq_data)),  # EIS doesn't have current series
            frequency=freq_data,
            z_real=zreal_data,
            z_imag=zimag_data,
            source_file=file_path
        )
        
        print(f"✓ Loaded Autolab Excel: {file_path.name}")
        print(f"  Shape: {len(data.frequency)} points")
        print(f"  Frequency range: {data.frequency.min():.3f} - {data.frequency.max():.3f} Hz")
        print(f"  Z_real range: {data.z_real.min():.3f} - {data.z_real.max():.3f} Ω")
        print(f"  Z_imag range: {data.z_imag.min():.3f} - {data.z_imag.max():.3f} Ω")
        
        return data
        
    except Exception as e:
        print(f"Error loading Autolab Excel file {file_path}: {e}")
        import traceback
        traceback.print_exc()
        return None


def load_autolab_file(file_path, file_type='auto'):
    """
    Load Autolab file (auto-detect or specify type)
    
    Args:
        file_path: Path to Autolab file
        file_type: 'auto', 'ascii', or 'excel'
        
    Returns:
        ElectrolyzerData object or None if parsing fails
    """
    file_path = Path(file_path)
    
    if file_type == 'auto':
        # Auto-detect based on extension
        if file_path.suffix.lower() == '.txt':
            return load_autolab_ascii(file_path)
        elif file_path.suffix.lower() in ['.xlsx', '.xls']:
            return load_autolab_excel(file_path)
        else:
            print(f"Unknown file type: {file_path.suffix}")
            return None
    elif file_type == 'ascii':
        return load_autolab_ascii(file_path)
    elif file_type == 'excel':
        return load_autolab_excel(file_path)
    else:
        print(f"Unknown file_type: {file_type}")
        return None