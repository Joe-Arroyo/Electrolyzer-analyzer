"""
Polarization curve analysis tab
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QFileDialog, QGroupBox, QComboBox, QLineEdit
)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from parsers.gamry import load_gamry_file


class PolarizationTab(QWidget):
    """Tab for polarization curve analysis"""
    
    def __init__(self):
        super().__init__()
        
        self.current_data = None
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI components"""
        
        # Main horizontal layout
        main_layout = QHBoxLayout(self)
        
        # Left panel - Controls
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_panel.setMaximumWidth(300)
        
        # File loading group
        file_group = QGroupBox("📁 Load Data")
        file_layout = QVBoxLayout()
        
        # Instrument selector
        file_layout.addWidget(QLabel("Instrument:"))
        self.instrument_combo = QComboBox()
        self.instrument_combo.addItems([
            "Gamry (.DTA)", 
            "Autolab (.xlsx) - Coming Soon",
            "Riden (.xlsx) - Coming Soon"
        ])
        file_layout.addWidget(self.instrument_combo)
        
        # Load button
        self.load_btn = QPushButton("Open File")
        self.load_btn.clicked.connect(self.load_file)
        self.load_btn.setMinimumHeight(40)
        file_layout.addWidget(self.load_btn)
        
        # File info
        self.file_label = QLabel("No file loaded")
        self.file_label.setWordWrap(True)
        self.file_label.setStyleSheet("padding: 10px; background-color: #f0f0f0; border-radius: 5px;")
        file_layout.addWidget(self.file_label)
        
        file_group.setLayout(file_layout)
        left_layout.addWidget(file_group)
        
        # Metadata group
        metadata_group = QGroupBox("⚙️ Metadata")
        metadata_layout = QVBoxLayout()
        
        metadata_layout.addWidget(QLabel("Electrode Area (cm²):"))
        self.area_input = QLineEdit()
        self.area_input.setPlaceholderText("e.g., 1.0")
        metadata_layout.addWidget(self.area_input)
        
        metadata_layout.addWidget(QLabel("Temperature (°C):"))
        self.temp_input = QLineEdit()
        self.temp_input.setPlaceholderText("e.g., 25")
        metadata_layout.addWidget(self.temp_input)
        
        self.apply_metadata_btn = QPushButton("Apply & Replot")
        self.apply_metadata_btn.clicked.connect(self.apply_metadata)
        self.apply_metadata_btn.setEnabled(False)
        metadata_layout.addWidget(self.apply_metadata_btn)
        
        metadata_group.setLayout(metadata_layout)
        left_layout.addWidget(metadata_group)
        
        # Export group
        export_group = QGroupBox("💾 Export")
        export_layout = QVBoxLayout()
        
        self.export_csv_btn = QPushButton("Save as CSV")
        self.export_csv_btn.clicked.connect(self.export_csv)
        self.export_csv_btn.setEnabled(False)
        export_layout.addWidget(self.export_csv_btn)
        
        self.export_png_btn = QPushButton("Save Plot as PNG")
        self.export_png_btn.clicked.connect(self.export_png)
        self.export_png_btn.setEnabled(False)
        export_layout.addWidget(self.export_png_btn)
        
        export_group.setLayout(export_layout)
        left_layout.addWidget(export_group)
        
        left_layout.addStretch()
        
        # Right panel - Plots
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Create matplotlib figure
        self.figure = Figure(figsize=(10, 8))
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        right_layout.addWidget(self.toolbar)
        right_layout.addWidget(self.canvas)
        
        # Add panels to main layout
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel)
        
        # Initial empty plot
        self.show_empty_plot()
    
    def show_empty_plot(self):
        """Show placeholder when no data is loaded"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.text(0.5, 0.5, 'Load a polarization curve file to display data', 
                ha='center', va='center', fontsize=14, color='gray')
        ax.set_xticks([])
        ax.set_yticks([])
        self.canvas.draw()
    
    def load_file(self):
        """Load polarization data file"""
        
        instrument = self.instrument_combo.currentText()
        
        if "Gamry" in instrument:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Select Gamry Polarization File", "", "DTA Files (*.DTA);;All Files (*)"
            )
            
            if file_path:
                try:
                    # Load with technique forced to 'polarization'
                    self.current_data = load_gamry_file(file_path, technique='polarization')
                    
                    if self.current_data:
                        self.file_label.setText(f"✓ {self.current_data.source_file.name}")
                        
                        # Pre-fill metadata if available
                        if self.current_data.electrode_area:
                            self.area_input.setText(str(self.current_data.electrode_area))
                        if self.current_data.temperature:
                            self.temp_input.setText(str(self.current_data.temperature))
                        
                        self.plot_polarization()
                        
                        # Enable controls
                        self.apply_metadata_btn.setEnabled(True)
                        self.export_csv_btn.setEnabled(True)
                        self.export_png_btn.setEnabled(True)
                    else:
                        self.file_label.setText("❌ Failed to load file")
                        self.show_empty_plot()
                
                except Exception as e:
                    self.file_label.setText(f"❌ Error: {str(e)}")
                    self.show_empty_plot()
        else:
            self.file_label.setText("⚠️ This instrument support coming soon")
    
    def plot_polarization(self):
        """Plot polarization curve (I-V)"""
        
        if self.current_data is None:
            return
        
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # Determine if we should use mA or A
        current_data = self.current_data.current
        current_label = 'Current (A)'
        
        if abs(current_data.max()) < 0.1:  # If max current < 100 mA
            current_data = current_data * 1000  # Convert to mA
            current_label = 'Current (mA)'
        
        # Plot I-V curve
        ax.plot(current_data, self.current_data.voltage, 
                'o-', markersize=4, linewidth=1.5, color='blue')
        ax.set_xlabel(current_label, fontsize=11)
        ax.set_ylabel('Voltage (V)', fontsize=11)
        ax.set_title('Polarization Curve', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        # If electrode area available, add current density axis on top
        if self.current_data.current_density is not None:
            ax2 = ax.twiny()
            cd_data = self.current_data.current_density
            cd_label = 'Current Density (A/cm²)'
            
            if abs(cd_data.max()) < 0.1:
                cd_data = cd_data * 1000
                cd_label = 'Current Density (mA/cm²)'
            
            ax2.plot(cd_data, self.current_data.voltage, alpha=0)  # Invisible
            ax2.set_xlabel(cd_label, fontsize=11, color='red')
            ax2.tick_params(axis='x', labelcolor='red')
        
        self.figure.tight_layout()
        self.canvas.draw()
    
    def apply_metadata(self):
        """Apply metadata changes and replot"""
        
        if self.current_data is None:
            return
        
        # Update electrode area
        area_text = self.area_input.text().strip()
        if area_text:
            try:
                self.current_data.electrode_area = float(area_text)
            except ValueError:
                self.file_label.setText("⚠️ Invalid electrode area")
                return
        
        # Update temperature
        temp_text = self.temp_input.text().strip()
        if temp_text:
            try:
                self.current_data.temperature = float(temp_text)
            except ValueError:
                self.file_label.setText("⚠️ Invalid temperature")
                return
        
        # Replot with updated metadata
        self.plot_polarization()
        self.file_label.setText("✓ Metadata updated")
    
    def export_csv(self):
        """Export data to CSV"""
        
        if self.current_data is None:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save CSV", "", "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            df = self.current_data.to_dataframe()
            df.to_csv(file_path, index=False)
            self.file_label.setText(f"✓ Exported to CSV")
    
    def export_png(self):
        """Export plot to PNG"""
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Plot", "", "PNG Files (*.png);;All Files (*)"
        )
        
        if file_path:
            self.figure.savefig(file_path, dpi=300, bbox_inches='tight')
            self.file_label.setText(f"✓ Plot saved")