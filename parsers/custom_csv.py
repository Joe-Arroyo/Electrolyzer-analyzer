"""
Custom CSV parser for chronopotentiometry data
Format: voltage, current, power, timestamp
Instruments: NiWatts, custom data loggers, or any CSV with V,I,P,t format
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional
import sys

# Add parent directory to path to import core modules
sys.path.append(str(Path(__file__).parent.parent))
from core.data_model import ElectrolyzerData


def load_custom_csv(filepath: str) -> Optional[ElectrolyzerData]:
    """
    Load custom CSV chronopotentiometry file with format: voltage, current, power, timestamp
    
    Parameters:
    -----------
    filepath : str or Path
        Path to the CSV file
    
    Returns:
    --------
    ElectrolyzerData or None
        Data object with technique='chronopotentiometry' and instrument='custom_csv'
    
    File Format:
    -----------
    CSV with no header, 4 columns:
    - Column 1: Voltage (V)
    - Column 2: Current (A)
    - Column 3: Power (W)
    - Column 4: Timestamp (DD/MM/YYYY HH:MM:SS)
    
    Example:
    -------
    1.7400,0.0100,0.0174,3/12/2025 12:40:57
    1.7400,0.0100,0.0174,3/12/2025 12:40:58
    """
    
    filepath = Path(filepath)
    
    if not filepath.exists():
        print(f"❌ File not found: {filepath}")
        return None
    
    try:
        # Read CSV file (no headers)
        df = pd.read_csv(
            filepath,
            header=None,  # No header row
            names=['voltage', 'current', 'power', 'timestamp'],
            encoding='utf-8',
            on_bad_lines='skip'
        )
        
        # Handle European decimal format if present (defensive coding)
        for col in ['voltage', 'current', 'power']:
            if df[col].dtype == 'object':  # If read as string
                df[col] = df[col].astype(str).str.replace(',', '.')
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Parse timestamps and convert to relative time in seconds
        try:
            # Try parsing format: DD/MM/YYYY HH:MM:SS (your file format)
            df['datetime'] = pd.to_datetime(
                df['timestamp'], 
                format='%d/%m/%Y %H:%M:%S', 
                errors='coerce'
            )
            
            # If that fails, try auto-detection
            if df['datetime'].isna().all():
                df['datetime'] = pd.to_datetime(df['timestamp'], errors='coerce')
            
            # Calculate relative time in seconds from start
            if not df['datetime'].isna().all():
                start_time = df['datetime'].iloc[0]
                df['time'] = (df['datetime'] - start_time).dt.total_seconds()
                timestamp_ok = True
            else:
                # Fallback: assume 1 second per row
                df['time'] = np.arange(len(df), dtype=float)
                timestamp_ok = False
                print("  ⚠️  Could not parse timestamps, using row indices (1s intervals)")
        
        except Exception as e:
            print(f"  ⚠️  Timestamp parsing failed: {e}")
            df['time'] = np.arange(len(df), dtype=float)
            timestamp_ok = False
        
        # Remove any rows with NaN in critical columns
        before_cleanup = len(df)
        df = df.dropna(subset=['voltage', 'current', 'time'])
        after_cleanup = len(df)
        
        if after_cleanup < before_cleanup:
            print(f"  ℹ️  Removed {before_cleanup - after_cleanup} rows with invalid data")
        
        if len(df) == 0:
            print(f"❌ No valid data in {filepath.name}")
            return None
        
        # Create ElectrolyzerData object
        data = ElectrolyzerData(
            technique='chronopotentiometry',
            instrument='custom_csv',
            time=pd.Series(df['time'].values, name='time'),
            voltage=pd.Series(df['voltage'].values, name='voltage'),
            current=pd.Series(df['current'].values, name='current'),
            source_file=filepath
        )
        
        # Store additional metadata
        data.metadata['power'] = df['power'].values
        data.metadata['has_timestamps'] = timestamp_ok
        if timestamp_ok:
            data.metadata['start_time'] = df['datetime'].iloc[0]
        
        # Print summary
        print(f"✓ Loaded {filepath.name}")
        print(f"  Shape: {len(df)} points")
        print(f"  Time range: {df['time'].min():.1f} - {df['time'].max():.1f} s")
        print(f"  Voltage range: {df['voltage'].min():.3f} - {df['voltage'].max():.3f} V")
        print(f"  Current range: {df['current'].min():.4f} - {df['current'].max():.4f} A")
        
        return data
        
    except Exception as e:
        print(f"❌ Error reading {filepath.name}")
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
        return None