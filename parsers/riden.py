"""
Riden RD6006 power supply file parser
Supports Excel format (.xlsx) for chronopotentiometry data
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional
import sys

# Add parent directory to path to import core modules
sys.path.append(str(Path(__file__).parent.parent))
from core.data_model import ElectrolyzerData


class RidenParser:
    """Parser for Riden RD6006 Excel files"""
    
    @staticmethod
    def read_xlsx(filepath: str) -> Optional[pd.DataFrame]:
        """
        Read Riden RD6006 Excel files and return clean pandas DataFrame.
        
        Parameters:
        -----------
        filepath : str
            Path to the .xlsx file
        
        Returns:
        --------
        pandas.DataFrame or None
            Electrochemical data with columns: Time, Voltage, Current
        """
        
        try:
            filepath = Path(filepath)
            
            if not filepath.exists():
                print(f"❌ File not found: {filepath}")
                return None
            
            # Read Excel file
            df = pd.read_excel(filepath, sheet_name=0)
            
            print(f"✓ Loaded {filepath.name}")
            print(f"  Shape: {df.shape[0]} points, {df.shape[1]} columns")
            print(f"  Columns: {list(df.columns)}")
            
            # Identify required columns
            time_col = None
            voltage_col = None
            current_col = None
            
            for col in df.columns:
                col_lower = col.lower().strip()  # Add strip() to handle whitespace
                
                if 'time' in col_lower and 'read' in col_lower:
                    time_col = col
                elif 'voltage' in col_lower and 'output' in col_lower:
                    voltage_col = col
                elif 'current' in col_lower and 'output' in col_lower:
                    current_col = col
            
            if not all([time_col, voltage_col, current_col]):
                print(f"❌ Missing required columns")
                print(f"  Found - Time: {time_col}, Voltage: {voltage_col}, Current: {current_col}")
                return None
            
            print(f"  Mapped columns:")
            print(f"    Time: {time_col}")
            print(f"    Voltage: {voltage_col}")
            print(f"    Current: {current_col}")
            
            # Convert timestamp to elapsed seconds
            df[time_col] = pd.to_datetime(df[time_col])
            time_start = df[time_col].iloc[0]
            df['Time_s'] = (df[time_col] - time_start).dt.total_seconds()
            
            # Ensure voltage and current are numeric
            df[voltage_col] = pd.to_numeric(df[voltage_col], errors='coerce')
            df[current_col] = pd.to_numeric(df[current_col], errors='coerce')
            
            # Remove any NaN values
            valid_mask = ~(df['Time_s'].isna() | df[voltage_col].isna() | df[current_col].isna())
            df = df[valid_mask].reset_index(drop=True)
            
            # Create clean output DataFrame
            clean_df = pd.DataFrame({
                'Time': df['Time_s'],
                'Voltage': df[voltage_col],
                'Current': df[current_col]
            })
            
            print(f"  Data range:")
            print(f"    Time: 0 - {clean_df['Time'].max():.1f} s")
            print(f"    Voltage: {clean_df['Voltage'].min():.3f} - {clean_df['Voltage'].max():.3f} V")
            print(f"    Current: {clean_df['Current'].min():.3f} - {clean_df['Current'].max():.3f} A")
            
            return clean_df
            
        except Exception as e:
            print(f"❌ Error reading {filepath}")
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def detect_technique(df: pd.DataFrame) -> str:
        """
        Detect if the data is chronopotentiometry (current steps)
        
        Parameters:
        -----------
        df : pd.DataFrame
            Data read from Riden file
        
        Returns:
        --------
        str : 'chronopotentiometry' or 'unknown'
        """
        # Riden RD6006 files are typically used for chronopotentiometry
        # Check if there are distinct current steps
        
        if 'Current' not in df.columns:
            return 'unknown'
        
        current = df['Current'].values
        
        # Check for variation in current (steps)
        current_range = current.max() - current.min()
        
        if current_range > 0.001:  # More than 1 mA variation
            return 'chronopotentiometry'
        else:
            return 'unknown'
    
    @staticmethod
    def to_electrolyzer_data(filepath: str, technique: str = None) -> Optional[ElectrolyzerData]:
        """
        Read Riden file and convert to unified ElectrolyzerData format
        
        Parameters:
        -----------
        filepath : str
            Path to .xlsx file
        technique : str, optional
            Force a specific technique ('chronopotentiometry')
            If None, auto-detect
        
        Returns:
        --------
        ElectrolyzerData or None
        """
        # Read the raw data
        df = RidenParser.read_xlsx(filepath)
        if df is None:
            return None
        
        # Detect or use provided technique
        if technique is None:
            technique = RidenParser.detect_technique(df)
        
        if technique == 'chronopotentiometry':
            return RidenParser._parse_chronopotentiometry(df, filepath)
        else:
            print(f"❌ Unknown technique type: {technique}")
            return None
    
    @staticmethod
    def _parse_chronopotentiometry(df: pd.DataFrame, filepath: str) -> ElectrolyzerData:
        """Parse chronopotentiometry data"""
        
        # Create ElectrolyzerData object
        return ElectrolyzerData(
            technique='chronopotentiometry',
            instrument='riden',
            time=pd.Series(df['Time'].values, name='Time'),
            voltage=pd.Series(df['Voltage'].values, name='Voltage'),
            current=pd.Series(df['Current'].values, name='Current'),
            source_file=Path(filepath)
        )


# Convenience function
def load_riden_file(filepath: str, technique: str = None) -> Optional[ElectrolyzerData]:
    """
    Quick function to load a Riden RD6006 file
    
    Usage:
        data = load_riden_file('my_experiment.xlsx')
        data = load_riden_file('my_experiment.xlsx', technique='chronopotentiometry')
    """
    return RidenParser.to_electrolyzer_data(filepath, technique)