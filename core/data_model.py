"""
Core data model for electrolyzer characterization data.
Provides a unified format for data from different instruments.
"""

from dataclasses import dataclass, field
from typing import Optional, Literal
import pandas as pd
from pathlib import Path


@dataclass
class ElectrolyzerData:
    """
    Unified data structure for electrochemical measurements.
    
    This class standardizes data from different instruments (Gamry, Autolab, Riden)
    into a common format for analysis and visualization.
    """
    
    # Required fields
    technique: Literal["polarization", "eis", "chronopotentiometry"]
    instrument: str  # Source instrument (gamry, autolab, riden)
    
    # Time series data (pandas Series for easy manipulation)
    time: pd.Series
    voltage: pd.Series  # Cell voltage in Volts
    current: pd.Series  # Current in Amperes
    
    # EIS-specific data (None for polarization curves)
    frequency: Optional[pd.Series] = None  # Hz
    z_real: Optional[pd.Series] = None      # Real impedance (Ohms)
    z_imag: Optional[pd.Series] = None      # Imaginary impedance (Ohms)
    
    # Metadata (editable by user)
    electrode_area: Optional[float] = None  # cm²
    temperature: Optional[float] = None      # °C
    
    # File information
    source_file: Optional[Path] = None
    
    # Flexible storage for additional metadata
    metadata: dict = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate data after initialization."""
        # Ensure Series have same length
        if self.technique == "polarization" or self.technique == "chronopotentiometry":
            if self.time is not None and self.voltage is not None and self.current is not None:
                lengths = [len(self.time), len(self.voltage), len(self.current)]
                if len(set(lengths)) != 1:
                    raise ValueError("Time, voltage, and current must have same length")
        
        elif self.technique == "eis":
            if self.frequency is None or self.z_real is None or self.z_imag is None:
                raise ValueError("EIS data requires frequency, z_real, and z_imag")
            lengths = [len(self.frequency), len(self.z_real), len(self.z_imag)]
            if len(set(lengths)) != 1:
                raise ValueError("EIS data series must have same length")
    
    @property
    def current_density(self) -> Optional[pd.Series]:
        """Calculate current density if electrode area is available."""
        if self.electrode_area is not None and self.electrode_area > 0:
            return self.current / self.electrode_area  # A/cm²
        return None
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert to pandas DataFrame for easy export."""
        if self.technique == "polarization" or self.technique == "chronopotentiometry":
            df = pd.DataFrame({
                'Time (s)': self.time,
                'Voltage (V)': self.voltage,
                'Current (A)': self.current
            })
            if self.current_density is not None:
                df['Current Density (A/cm2)'] = self.current_density
            return df
        
        elif self.technique == "eis":
            df = pd.DataFrame({
                'Frequency (Hz)': self.frequency,
                'Z_real (Ohm)': self.z_real,
                'Z_imag (Ohm)': self.z_imag
            })
            return df
        
        else:
            # Fallback for unknown technique
            return pd.DataFrame()
    
    def summary(self) -> str:
        """Return a human-readable summary of the data."""
        lines = [
            f"Technique: {self.technique}",
            f"Instrument: {self.instrument}",
        ]
        
        # Add data points count
        if self.technique in ['polarization', 'chronopotentiometry'] and self.time is not None:
            lines.append(f"Data points: {len(self.time)}")
        elif self.technique == 'eis' and self.frequency is not None:
            lines.append(f"Data points: {len(self.frequency)}")
        
        if self.electrode_area:
            lines.append(f"Electrode area: {self.electrode_area} cm²")
        if self.temperature:
            lines.append(f"Temperature: {self.temperature} °C")
        if self.source_file:
            lines.append(f"Source: {self.source_file.name}")
        
        return "\n".join(lines)