"""
Chronopotentiometry analysis tab
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QFileDialog, QGroupBox, QComboBox, QLineEdit, QCheckBox, QButtonGroup, QRadioButton
)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from parsers.gamry import load_gamry_file


class ChronopotentiometryTab(QWidget):
    """Tab for chronopotentiometry analysis"""
    
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
        left_panel.setMaximumWidth(400)
        
        # File loading group
        file_group = QGroupBox("📁 Load Data")
        file_layout = QVBoxLayout()
        
        # Instrument selector
        file_layout.addWidget(QLabel("Instrument:"))
        self.instrument_combo = QComboBox()
        self.instrument_combo.addItems([
            "Gamry (.DTA)", 
            "Autolab (.xlsx) - Coming Soon"
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
        
        # Time filter group
        filter_group = QGroupBox("⏱️ Time Filter")
        filter_layout = QVBoxLayout()
        
        self.enable_filter = QCheckBox("Enable time filtering")
        filter_layout.addWidget(self.enable_filter)
        
        filter_layout.addWidget(QLabel("Min Time (s):"))
        self.time_min = QLineEdit()
        self.time_min.setPlaceholderText("e.g., 0")
        self.time_min.setEnabled(False)
        filter_layout.addWidget(self.time_min)
        
        filter_layout.addWidget(QLabel("Max Time (s):"))
        self.time_max = QLineEdit()
        self.time_max.setPlaceholderText("e.g., 1000")
        self.time_max.setEnabled(False)
        filter_layout.addWidget(self.time_max)
        
        self.apply_filter_btn = QPushButton("Apply Filter")
        self.apply_filter_btn.clicked.connect(self.apply_filter)
        self.apply_filter_btn.setEnabled(False)
        filter_layout.addWidget(self.apply_filter_btn)
        
        # Connect checkbox to enable/disable inputs
        self.enable_filter.stateChanged.connect(self.toggle_filter)
        
        filter_group.setLayout(filter_layout)
        left_layout.addWidget(filter_group)
        
        # Plot selection group
        plot_group = QGroupBox("📊 Plot Selection")
        plot_layout = QVBoxLayout()
        
        self.plot_voltage_radio = QRadioButton("Voltage vs Time")
        self.plot_current_radio = QRadioButton("Current vs Time")
        self.plot_both_radio = QRadioButton("Both (2 subplots)")
        self.plot_both_radio.setChecked(True)
        
        plot_layout.addWidget(self.plot_voltage_radio)
        plot_layout.addWidget(self.plot_current_radio)
        plot_layout.addWidget(self.plot_both_radio)
        
        self.replot_btn = QPushButton("Update Plot")
        self.replot_btn.clicked.connect(self.update_plot)
        self.replot_btn.setEnabled(False)
        plot_layout.addWidget(self.replot_btn)
        
        plot_group.setLayout(plot_layout)
        left_layout.addWidget(plot_group)
        
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
        ax.text(0.5, 0.5, 'Load a chronopotentiometry file to display data', 
                ha='center', va='center', fontsize=14, color='gray')
        ax.set_xticks([])
        ax.set_yticks([])
        self.canvas.draw()
    
    def toggle_filter(self, state):
        """Enable/disable time filter inputs"""
        enabled = state == Qt.Checked
        self.time_min.setEnabled(enabled)
        self.time_max.setEnabled(enabled)
    
    def load_file(self):
        """Load chronopotentiometry data file"""
        
        instrument = self.instrument_combo.currentText()
        
        if "Gamry" in instrument:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Select Gamry Chronopotentiometry File", "", "DTA Files (*.DTA);;All Files (*)"
            )
            
            if file_path:
                try:
                    # Load with technique forced to 'chronopotentiometry'
                    self.current_data = load_gamry_file(file_path, technique='chronopotentiometry')
                    
                    if self.current_data:
                        self.file_label.setText(f"✓ {self.current_data.source_file.name}")
                        
                        self.plot_chronopotentiometry()
                        
                        # Enable controls
                        self.apply_filter_btn.setEnabled(True)
                        self.replot_btn.setEnabled(True)
                        self.export_csv_btn.setEnabled(True)
                        self.export_png_btn.setEnabled(True)
                    else:
                        self.file_label.setText("❌ Failed to load file")
                        self.show_empty_plot()
                
                except Exception as e:
                    self.file_label.setText(f"❌ Error: {str(e)}")
                    self.show_empty_plot()
        else:
            self.file_label.setText("⚠️ Autolab support coming soon")
    
    def get_filtered_data(self):
        """Get data with time filter applied if enabled"""
        
        if self.current_data is None:
            return None
        
        data = self.current_data
        
        # Apply time filter if enabled
        if self.enable_filter.isChecked():
            try:
                t_min = float(self.time_min.text()) if self.time_min.text() else data.time.min()
                t_max = float(self.time_max.text()) if self.time_max.text() else data.time.max()
                
                mask = (data.time >= t_min) & (data.time <= t_max)
                
                # Create filtered data (simple approach)
                # In real implementation, you might want to create a new ElectrolyzerData object
                return {
                    'time': data.time[mask],
                    'voltage': data.voltage[mask],
                    'current': data.current[mask]
                }
            except ValueError:
                return {
                    'time': data.time,
                    'voltage': data.voltage,
                    'current': data.current
                }
        
        return {
            'time': data.time,
            'voltage': data.voltage,
            'current': data.current
        }
    
    def plot_chronopotentiometry(self):
        """Plot chronopotentiometry data"""
        
        data = self.get_filtered_data()
        if data is None:
            return
        
        self.figure.clear()
        
        if self.plot_both_radio.isChecked():
            # Two subplots
            ax1 = self.figure.add_subplot(211)
            ax2 = self.figure.add_subplot(212)
            
            # Voltage plot
            ax1.plot(data['time'], data['voltage'], linewidth=1.5, color='blue')
            ax1.set_ylabel('Voltage (V)', fontsize=11)
            ax1.set_title('Voltage vs Time', fontsize=12, fontweight='bold')
            ax1.grid(True, alpha=0.3)
            
            # Current plot
            ax2.plot(data['time'], data['current'], linewidth=1.5, color='red')
            ax2.set_xlabel('Time (s)', fontsize=11)
            ax2.set_ylabel('Current (A)', fontsize=11)
            ax2.set_title('Current vs Time', fontsize=12, fontweight='bold')
            ax2.grid(True, alpha=0.3)
            
        elif self.plot_voltage_radio.isChecked():
            # Voltage only
            ax = self.figure.add_subplot(111)
            ax.plot(data['time'], data['voltage'], linewidth=1.5, color='blue')
            ax.set_xlabel('Time (s)', fontsize=11)
            ax.set_ylabel('Voltage (V)', fontsize=11)
            ax.set_title('Voltage vs Time', fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3)
            
        elif self.plot_current_radio.isChecked():
            # Current only
            ax = self.figure.add_subplot(111)
            ax.plot(data['time'], data['current'], linewidth=1.5, color='red')
            ax.set_xlabel('Time (s)', fontsize=11)
            ax.set_ylabel('Current (A)', fontsize=11)
            ax.set_title('Current vs Time', fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3)
        
        self.figure.tight_layout()
        self.canvas.draw()
    
    def apply_filter(self):
        """Apply time filter and replot"""
        self.plot_chronopotentiometry()
    
    def update_plot(self):
        """Update plot based on selection"""
        self.plot_chronopotentiometry()
    
    def export_csv(self):
        """Export data to CSV"""
        
        if self.current_data is None:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save CSV", "", "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            data = self.get_filtered_data()
            import pandas as pd
            df = pd.DataFrame(data)
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