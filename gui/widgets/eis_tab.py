"""
EIS (Electrochemical Impedance Spectroscopy) analysis tab
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QFileDialog, QGroupBox, QComboBox, QLineEdit, QSplitter
)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import numpy as np

from parsers.gamry import load_gamry_file


class EISTab(QWidget):
    """Tab for EIS analysis"""
    
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
        self.instrument_combo.addItems(["Gamry (.DTA)", "Autolab (.xlsx) - Coming Soon"])
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
        
        # Frequency filter group
        filter_group = QGroupBox("🔧 Frequency Filter")
        filter_layout = QVBoxLayout()
        
        filter_layout.addWidget(QLabel("Min Frequency (Hz):"))
        self.freq_min = QLineEdit()
        self.freq_min.setPlaceholderText("e.g., 0.1")
        filter_layout.addWidget(self.freq_min)
        
        filter_layout.addWidget(QLabel("Max Frequency (Hz):"))
        self.freq_max = QLineEdit()
        self.freq_max.setPlaceholderText("e.g., 100000")
        filter_layout.addWidget(self.freq_max)
        
        self.apply_filter_btn = QPushButton("Apply Filter")
        self.apply_filter_btn.clicked.connect(self.apply_filter)
        self.apply_filter_btn.setEnabled(False)
        filter_layout.addWidget(self.apply_filter_btn)
        
        filter_group.setLayout(filter_layout)
        left_layout.addWidget(filter_group)
        
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
        ax.text(0.5, 0.5, 'Load an EIS file to display data', 
                ha='center', va='center', fontsize=14, color='gray')
        ax.set_xticks([])
        ax.set_yticks([])
        self.canvas.draw()
    
    def load_file(self):
        """Load EIS data file"""
        
        instrument = self.instrument_combo.currentText()
        
        if "Gamry" in instrument:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Select Gamry EIS File", "", "DTA Files (*.DTA);;All Files (*)"
            )
            
            if file_path:
                try:
                    # Load with technique forced to 'eis'
                    self.current_data = load_gamry_file(file_path, technique='eis')
                    
                    if self.current_data and self.current_data.technique == 'eis':
                        self.file_label.setText(f"✓ {self.current_data.source_file.name}")
                        self.plot_eis()
                        
                        # Enable controls
                        self.apply_filter_btn.setEnabled(True)
                        self.export_csv_btn.setEnabled(True)
                        self.export_png_btn.setEnabled(True)
                    else:
                        self.file_label.setText("❌ Not an EIS file")
                        self.show_empty_plot()
                
                except Exception as e:
                    self.file_label.setText(f"❌ Error: {str(e)}")
                    self.show_empty_plot()
        else:
            self.file_label.setText("⚠️ Autolab support coming soon")
    
    def plot_eis(self):
        """Plot EIS data (Nyquist and Bode)"""
        
        if self.current_data is None:
            return
        
        self.figure.clear()
        
        # Create two subplots
        ax1 = self.figure.add_subplot(211)
        ax2 = self.figure.add_subplot(212)
        
        # Nyquist plot
        ax1.plot(self.current_data.z_real, -self.current_data.z_imag, 
                'o-', markersize=4, linewidth=1, color='blue')
        ax1.set_xlabel('Z_real (Ω)', fontsize=11)
        ax1.set_ylabel('-Z_imag (Ω)', fontsize=11)
        ax1.set_title('Nyquist Plot', fontsize=12, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.axis('equal')
        
        # Bode plot (magnitude)
        z_mod = np.sqrt(self.current_data.z_real**2 + self.current_data.z_imag**2)
        ax2.semilogx(self.current_data.frequency, z_mod, 
                    'o-', markersize=4, linewidth=1, color='red')
        ax2.set_xlabel('Frequency (Hz)', fontsize=11)
        ax2.set_ylabel('|Z| (Ω)', fontsize=11)
        ax2.set_title('Bode Plot - Magnitude', fontsize=12, fontweight='bold')
        ax2.grid(True, alpha=0.3, which='both')
        
        self.figure.tight_layout()
        self.canvas.draw()
    
    def apply_filter(self):
        """Apply frequency filter"""
        # TODO: Implement frequency filtering
        pass
    
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