"""
EIS (Electrochemical Impedance Spectroscopy) analysis tab
Enhanced with batch plotting, phase analysis, and grid view with drag & drop,
frequency markers, and flexible aspect ratio modes
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QFileDialog, QGroupBox, QComboBox, QLineEdit, QListWidget,
    QCheckBox, QListWidgetItem, QRadioButton, QButtonGroup, QSpinBox,
    QScrollArea, QDialog, QFormLayout, QDialogButtonBox
)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
import string

from parsers.gamry import load_gamry_file


class EISTab(QWidget):
    """Tab for EIS analysis with batch plotting and grid view support"""
    
    def __init__(self):
        super().__init__()
        
        self.loaded_files = {}  # Dictionary: filename -> data
        self.display_names = {}  # Dictionary: filename -> custom display name
        self.colors = plt.cm.tab20(np.linspace(0, 1, 20))  # 20 distinct colors
        
        self.init_ui()
    
    def _calculate_subplot_position(self, file_idx, n_cols, show_both, is_bode=False):
        """
        Calculate matplotlib subplot position for grid layout.
        
        Args:
            file_idx: Index of the file (0, 1, 2, ...)
            n_cols: Number of columns in grid
            show_both: If True, each file gets 2 rows (Nyquist + Bode)
            is_bode: If show_both=True, specifies whether this is the Bode subplot
            
        Returns:
            int: Subplot position (1-indexed for matplotlib)
        """
        row = file_idx // n_cols
        col = file_idx % n_cols
        
        if show_both:
            if is_bode:
                return (row * 2 + 1) * n_cols + col + 1
            else:
                return row * 2 * n_cols + col + 1
        else:
            return row * n_cols + col + 1
    
    def _parse_frequency_markers(self, text_input):
        """
        Parse frequency marker input from text field
        
        Args:
            text_input: String like "0.1, 10, 1000" or "0.1,10,1000"
            
        Returns:
            List of float frequencies, or empty list if invalid
        """
        if not text_input or not text_input.strip():
            return []
        
        try:
            # Split by comma and convert to floats
            freqs = [float(f.strip()) for f in text_input.split(',') if f.strip()]
            return freqs
        except ValueError:
            return []
    
    def _add_frequency_markers(self, ax, z_real, z_imag, freq, marker_freqs):
        """
        Add frequency annotations to Nyquist plot with arrows
        
        Args:
            ax: Matplotlib axis
            z_real: Real impedance array (pandas Series or numpy array)
            z_imag: Imaginary impedance array
            freq: Frequency array
            marker_freqs: List of frequencies to mark (Hz)
        """
        if not marker_freqs:
            return
        
        # Convert to numpy arrays if needed
        z_real = np.array(z_real)
        z_imag = np.array(z_imag)
        freq = np.array(freq)
        
        for f in marker_freqs:
            # Find closest data point to desired frequency
            idx = np.argmin(np.abs(freq - f))
            actual_f = freq[idx]
            
            # Format frequency nicely
            if actual_f >= 1000:
                label = f'{actual_f/1000:.1f} kHz'
            elif actual_f >= 1:
                label = f'{actual_f:.1f} Hz'
            else:
                label = f'{actual_f*1000:.1f} mHz'
            
            # Add annotation with arrow
            ax.annotate(
                label,
                xy=(z_real[idx], -z_imag[idx]),     # Point to mark
                xytext=(15, 15),                     # Offset for text (pixels)
                textcoords='offset points',
                fontsize=7,
                color='darkred',
                arrowprops=dict(arrowstyle='->', color='darkred', lw=1.5, connectionstyle='arc3,rad=0.3')
            )
    
    def _get_aspect_mode(self):
        """
        Get current aspect ratio mode
        
        Returns:
            str: 'auto', 'equal', or 'adjusted'
        """
        if self.aspect_auto_radio.isChecked():
            return 'auto'
        elif self.aspect_equal_radio.isChecked():
            return 'equal'
        else:  # adjusted
            return 'adjusted'
    
    def init_ui(self):
        """Initialize UI components"""
        
        # Main horizontal layout
        main_layout = QHBoxLayout(self)
        
        # Left panel - Controls (with scroll area)
        left_panel_container = QScrollArea()
        left_panel_container.setWidgetResizable(True)
        left_panel_container.setMaximumWidth(320)
        
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_panel_container.setWidget(left_panel)
        
        # File loading group
        file_group = QGroupBox("📁 Load Data")
        file_layout = QVBoxLayout()
        
        # Instrument selector
        file_layout.addWidget(QLabel("Instrument:"))
        self.instrument_combo = QComboBox()
        self.instrument_combo.addItems([
            "Gamry (.DTA)", 
            "Autolab ASCII (.txt)",
            "Autolab Excel (.xlsx)"
        ])
        file_layout.addWidget(self.instrument_combo)
        
        # Load button
        self.load_btn = QPushButton("Load File(s)")
        self.load_btn.clicked.connect(self.load_files)
        self.load_btn.setMinimumHeight(40)
        file_layout.addWidget(self.load_btn)
        
        # File list with drag & drop
        file_layout.addWidget(QLabel("Loaded Files: (drag to reorder)"))
        self.file_list = QListWidget()
        self.file_list.setMaximumHeight(150)
        self.file_list.setDragDropMode(QListWidget.InternalMove)  # Enable drag & drop
        self.file_list.itemChanged.connect(self.update_plot)
        file_layout.addWidget(self.file_list)
        
        # Clear and remove buttons
        list_btn_layout = QHBoxLayout()
        self.remove_btn = QPushButton("Remove Selected")
        self.remove_btn.clicked.connect(self.remove_selected_files)
        list_btn_layout.addWidget(self.remove_btn)
        
        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.clicked.connect(self.clear_all_files)
        list_btn_layout.addWidget(self.clear_btn)
        file_layout.addLayout(list_btn_layout)
        
        # Edit names button
        self.edit_names_btn = QPushButton("Edit Legend Names")
        self.edit_names_btn.clicked.connect(self.edit_legend_names)
        self.edit_names_btn.setEnabled(False)
        file_layout.addWidget(self.edit_names_btn)
        
        # Status label
        self.status_label = QLabel("No files loaded")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("padding: 8px; background-color: #f0f0f0; border-radius: 5px;")
        file_layout.addWidget(self.status_label)
        
        file_group.setLayout(file_layout)
        left_layout.addWidget(file_group)
        
        # Plot options group
        plot_group = QGroupBox("🎨 Plot Options")
        plot_layout = QVBoxLayout()
        
        # Aspect ratio options
        plot_layout.addWidget(QLabel("Nyquist Aspect Ratio:"))
        self.aspect_auto_radio = QRadioButton("Auto (may distort circles)")
        self.aspect_equal_radio = QRadioButton("Equal (same scale both axes)")
        self.aspect_adjusted_radio = QRadioButton("Adjusted (removes blank space)")
        self.aspect_auto_radio.setChecked(True)
        self.aspect_auto_radio.toggled.connect(self.update_plot)
        self.aspect_equal_radio.toggled.connect(self.update_plot)
        self.aspect_adjusted_radio.toggled.connect(self.update_plot)
        
        plot_layout.addWidget(self.aspect_auto_radio)
        plot_layout.addWidget(self.aspect_equal_radio)
        plot_layout.addWidget(self.aspect_adjusted_radio)
        
        # Overlay mode settings
        self.overlay_settings_widget = QWidget()
        overlay_settings_layout = QVBoxLayout(self.overlay_settings_widget)
        overlay_settings_layout.setContentsMargins(20, 5, 0, 5)  # Indent
        
        overlay_settings_layout.addWidget(QLabel("Overlay Options:"))
        self.show_bode_checkbox = QCheckBox("Show Bode plots")
        self.show_bode_checkbox.setChecked(True)
        self.show_bode_checkbox.stateChanged.connect(self.update_plot)
        overlay_settings_layout.addWidget(self.show_bode_checkbox)
        
        self.show_overlay_titles_checkbox = QCheckBox("Show plot titles")
        self.show_overlay_titles_checkbox.setChecked(True)
        self.show_overlay_titles_checkbox.stateChanged.connect(self.update_plot)
        overlay_settings_layout.addWidget(self.show_overlay_titles_checkbox)
        
        # Frequency markers for overlay
        overlay_settings_layout.addWidget(QLabel("Frequency Markers (Hz):"))
        self.freq_markers_input = QLineEdit()
        self.freq_markers_input.setPlaceholderText("e.g., 0.1, 10, 1000")
        self.freq_markers_input.textChanged.connect(self.update_plot)
        overlay_settings_layout.addWidget(self.freq_markers_input)
        
        plot_layout.addWidget(self.overlay_settings_widget)
        
        # Display mode selection
        plot_layout.addWidget(QLabel("Display Mode:"))
        self.overlay_radio = QRadioButton("Overlay (compare all files)")
        self.grid_radio = QRadioButton("Grid View (individual plots)")
        self.overlay_radio.setChecked(True)
        self.overlay_radio.toggled.connect(self.toggle_display_mode)
        
        # Add button group to ensure mutual exclusivity
        self.display_mode_group = QButtonGroup(self)
        self.display_mode_group.addButton(self.overlay_radio)
        self.display_mode_group.addButton(self.grid_radio)
        
        plot_layout.addWidget(self.overlay_radio)
        plot_layout.addWidget(self.grid_radio)
        
        # Grid view settings (initially hidden)
        self.grid_settings_widget = QWidget()
        grid_settings_layout = QVBoxLayout(self.grid_settings_widget)
        grid_settings_layout.setContentsMargins(20, 5, 0, 5)  # Indent
        
        # Plot type for each cell
        grid_settings_layout.addWidget(QLabel("Show per file:"))
        self.grid_nyquist_radio = QRadioButton("Nyquist only")
        self.grid_bode_radio = QRadioButton("Bode only")
        self.grid_both_radio = QRadioButton("Both (stacked)")
        self.grid_both_radio.setChecked(True)  # Make "Both" the default
        
        # Connect to auto-update
        self.grid_nyquist_radio.toggled.connect(self.update_plot)
        self.grid_bode_radio.toggled.connect(self.update_plot)
        self.grid_both_radio.toggled.connect(self.update_plot)
        
        grid_settings_layout.addWidget(self.grid_nyquist_radio)
        grid_settings_layout.addWidget(self.grid_bode_radio)
        grid_settings_layout.addWidget(self.grid_both_radio)
        
        # Show titles checkbox
        self.show_titles_checkbox = QCheckBox("Show titles")
        self.show_titles_checkbox.setChecked(True)
        self.show_titles_checkbox.stateChanged.connect(self.update_plot)
        grid_settings_layout.addWidget(self.show_titles_checkbox)
        
        # Spacing control
        spacing_layout = QHBoxLayout()
        spacing_layout.addWidget(QLabel("Spacing:"))
        self.spacing_combo = QComboBox()
        self.spacing_combo.addItems(["Tight", "Normal", "Loose"])
        self.spacing_combo.setCurrentIndex(1)  # Default to Normal
        self.spacing_combo.currentIndexChanged.connect(self.update_plot)
        spacing_layout.addWidget(self.spacing_combo)
        spacing_layout.addStretch()
        grid_settings_layout.addLayout(spacing_layout)
        
        # Frequency markers for grid
        grid_settings_layout.addWidget(QLabel("Frequency Markers (Hz):"))
        self.grid_freq_markers_input = QLineEdit()
        self.grid_freq_markers_input.setPlaceholderText("e.g., 0.1, 10, 1000")
        self.grid_freq_markers_input.textChanged.connect(self.update_plot)
        grid_settings_layout.addWidget(self.grid_freq_markers_input)
        
        self.grid_settings_widget.setVisible(False)  # Hidden by default
        plot_layout.addWidget(self.grid_settings_widget)
        
        plot_group.setLayout(plot_layout)
        left_layout.addWidget(plot_group)
        
        # Export group
        export_group = QGroupBox("💾 Export")
        export_layout = QVBoxLayout()
        
        self.export_csv_btn = QPushButton("Save Data as CSV")
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
        
        # Create matplotlib figure (will adjust dynamically)
        self.figure = Figure(figsize=(10, 10))
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        right_layout.addWidget(self.toolbar)
        right_layout.addWidget(self.canvas)
        
        # Add panels to main layout
        main_layout.addWidget(left_panel_container)
        main_layout.addWidget(right_panel)
        
        # Initial empty plot
        self.show_empty_plot()
    
    def show_empty_plot(self):
        """Show placeholder when no data is loaded"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.text(0.5, 0.5, 'Load EIS file(s) to display data', 
                ha='center', va='center', fontsize=14, color='gray')
        ax.set_xticks([])
        ax.set_yticks([])
        self.canvas.draw()
    
    def toggle_display_mode(self):
        """Show/hide settings based on display mode"""
        is_grid = self.grid_radio.isChecked()
        self.grid_settings_widget.setVisible(is_grid)
        self.overlay_settings_widget.setVisible(not is_grid)
        
        # Trigger update when switching to grid view
        if is_grid and len(self.loaded_files) > 0:
            self.update_plot()
    
    def load_files(self):
        """Load one or multiple EIS files"""
        
        instrument = self.instrument_combo.currentText()
        
        if "Gamry" in instrument:
            file_paths, _ = QFileDialog.getOpenFileNames(
                self, "Select Gamry EIS File(s)", "", "DTA Files (*.DTA);;All Files (*)"
            )
            
            if file_paths:
                for file_path in file_paths:
                    self.load_file(file_path, instrument_type='gamry')
        
        elif "ASCII" in instrument:
            file_paths, _ = QFileDialog.getOpenFileNames(
                self, "Select Autolab ASCII File(s)", "", "Text Files (*.txt);;All Files (*)"
            )
            
            if file_paths:
                for file_path in file_paths:
                    self.load_file(file_path, instrument_type='autolab_ascii')
        
        elif "Excel" in instrument:
            file_paths, _ = QFileDialog.getOpenFileNames(
                self, "Select Autolab Excel File(s)", "", "Excel Files (*.xlsx *.xls);;All Files (*)"
            )
            
            if file_paths:
                for file_path in file_paths:
                    self.load_file(file_path, instrument_type='autolab_excel')
    
    def load_file(self, file_path, instrument_type='gamry'):
        """Load a single file and add to list"""
        
        try:
            # Load based on instrument type
            if instrument_type == 'gamry':
                from parsers.gamry import load_gamry_file
                data = load_gamry_file(file_path, technique='eis')
            elif instrument_type == 'autolab_ascii':
                from parsers.autolab import load_autolab_ascii
                data = load_autolab_ascii(file_path)
            elif instrument_type == 'autolab_excel':
                from parsers.autolab import load_autolab_excel
                data = load_autolab_excel(file_path)
            else:
                self.status_label.setText(f"❌ Unknown instrument type: {instrument_type}")
                return
            
            if data and data.technique == 'eis':
                filename = data.source_file.name
                
                # Add to dictionary
                self.loaded_files[filename] = data
                self.display_names[filename] = filename.replace('.DTA', '').replace('.txt', '').replace('.xlsx', '')
                
                # Add to list widget with checkbox
                item = QListWidgetItem(filename)
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Checked)
                self.file_list.addItem(item)
                
                # Update status
                self.update_status()
                
                # Enable controls
                self.export_csv_btn.setEnabled(True)
                self.export_png_btn.setEnabled(True)
                self.edit_names_btn.setEnabled(True)
                
                # Plot
                self.update_plot()
            else:
                self.status_label.setText(f"❌ Not an EIS file: {file_path}")
        
        except Exception as e:
            self.status_label.setText(f"❌ Error loading {file_path}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def remove_selected_files(self):
        """Remove selected files from list"""
        
        for item in self.file_list.selectedItems():
            filename = item.text()
            if filename in self.loaded_files:
                del self.loaded_files[filename]
                del self.display_names[filename]
            self.file_list.takeItem(self.file_list.row(item))
        
        self.update_status()
        
        if len(self.loaded_files) == 0:
            self.show_empty_plot()
            self.edit_names_btn.setEnabled(False)
        else:
            self.update_plot()
    
    def clear_all_files(self):
        """Clear all loaded files"""
        
        self.loaded_files.clear()
        self.display_names.clear()
        self.file_list.clear()
        self.update_status()
        self.show_empty_plot()
        
        # Disable controls
        self.export_csv_btn.setEnabled(False)
        self.export_png_btn.setEnabled(False)
        self.edit_names_btn.setEnabled(False)
    
    def edit_legend_names(self):
        """Open dialog to edit display names for legend"""
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Legend Names")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        form_layout = QFormLayout()
        
        # Create text input for each file
        name_inputs = {}
        for filename in self.loaded_files.keys():
            label = QLabel(f"{filename}:")
            line_edit = QLineEdit(self.display_names[filename])
            form_layout.addRow(label, line_edit)
            name_inputs[filename] = line_edit
        
        layout.addLayout(form_layout)
        
        # OK/Cancel buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        # Show dialog
        if dialog.exec_():
            # Update display names
            for filename, line_edit in name_inputs.items():
                self.display_names[filename] = line_edit.text()
            
            # Replot with new names
            self.update_plot()
            self.status_label.setText("✓ Legend names updated")
    
    def update_status(self):
        """Update status label"""
        
        count = len(self.loaded_files)
        if count == 0:
            self.status_label.setText("No files loaded")
        elif count == 1:
            self.status_label.setText(f"✓ 1 file loaded")
        else:
            self.status_label.setText(f"✓ {count} files loaded")
    
    def update_plot(self):
        """Update plot based on display mode"""
        
        if len(self.loaded_files) == 0:
            return
        
        if self.overlay_radio.isChecked():
            self.plot_overlay()
        else:
            self.plot_grid()
    
    def plot_overlay(self):
        """Plot all checked EIS files overlaid"""
        
        self.figure.clear()
        
        # Suppress matplotlib warnings
        import warnings
        warnings.filterwarnings('ignore', message='Attempt to set non-positive xlim')
        warnings.filterwarnings('ignore', message='Ignoring fixed .* limits')
        
        # Check if we should show Bode plots
        show_bode = self.show_bode_checkbox.isChecked()
        show_titles = self.show_overlay_titles_checkbox.isChecked()
        
        # Always create 2-subplot layout for consistent sizing
        ax1 = self.figure.add_subplot(211)  # Nyquist (top)
        ax2 = self.figure.add_subplot(212)  # Bode (bottom)
        ax3 = ax2.twinx()  # Bode phase
        
        # Collect data for aspect ratio calculation
        all_zreal = []
        all_zimag = []
        
        # Plot each checked file
        color_idx = 0
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            if item.checkState() == Qt.Checked:
                filename = item.text()
                data = self.loaded_files[filename]
                color = self.colors[color_idx % len(self.colors)]
                
                # Collect data for limits
                all_zreal.extend(data.z_real.values)
                all_zimag.extend(data.z_imag.values)
                
                # Nyquist plot
                ax1.plot(data.z_real, -data.z_imag, 
                        'o', markersize=5, color=color, label=self.display_names[filename])
                
                # Bode plots (only if enabled)
                if show_bode:
                    # Bode magnitude (left y-axis)
                    z_mod = np.sqrt(data.z_real**2 + data.z_imag**2)
                    ax2.semilogx(data.frequency, z_mod, 
                                'o-', markersize=5, linewidth=1, color=color, 
                                label=self.display_names[filename])
                    
                    # Bode phase (right y-axis) - dashed line
                    phase = np.arctan2(-data.z_imag, data.z_real) * 180 / np.pi
                    ax3.semilogx(data.frequency, phase,
                                'o--', markersize=5, markerfacecolor='None', 
                                linewidth=1, color=color, alpha=0.7)
                
                color_idx += 1
        
        # Nyquist formatting
        ax1.set_xlabel('Z_real (Ω)', fontsize=10)
        ax1.set_ylabel('-Z_imag (Ω)', fontsize=10)
        if show_titles:
            ax1.set_title('Nyquist Plot', fontsize=11, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.legend(fontsize=8, loc='best')
        
        # Add frequency markers for all checked files
        marker_freqs = self._parse_frequency_markers(self.freq_markers_input.text())
        if marker_freqs:
            for i in range(self.file_list.count()):
                item = self.file_list.item(i)
                if item.checkState() == Qt.Checked:
                    filename = item.text()
                    data = self.loaded_files[filename]
                    self._add_frequency_markers(ax1, data.z_real, data.z_imag, data.frequency, marker_freqs)
        
        # Bode plot formatting (only if enabled)
        if show_bode:
            ax2.set_xlabel('Frequency (Hz)', fontsize=10)
            ax2.set_ylabel('|Z| (Ω)', fontsize=10, color='blue')
            ax2.tick_params(axis='y', labelcolor='blue')
            if show_titles:
                ax2.set_title('Bode Plot - Magnitude & Phase', fontsize=11, fontweight='bold')
            ax2.grid(True, alpha=0.3, which='both')
            
            # Phase axis formatting
            ax3.set_ylabel('Phase (°)', fontsize=10, color='red')
            ax3.tick_params(axis='y', labelcolor='red')
        else:
            # Hide Bode subplot but show it's intentionally hidden
            ax2.text(0.5, 0.5, '(Bode plot hidden)', 
                     transform=ax2.transAxes, ha='center', va='center',
                     fontsize=11, color='gray', style='italic')
            ax2.set_xticks([])
            ax2.set_yticks([])
            ax3.set_visible(False)
        
        # Apply aspect ratio ONLY to Nyquist
        aspect_mode = self._get_aspect_mode()
        
        # Apply layout adjustments FIRST, before setting aspect
        self.figure.subplots_adjust(left=0.12, right=0.88, bottom=0.08, top=0.95, hspace=0.3)
        
        if aspect_mode == 'equal':
            # Same scale on both axes (traditional locked aspect)
            max_zreal = max(all_zreal) if all_zreal else 1
            max_zimag = max([-z for z in all_zimag]) if all_zimag else 1
            max_val = max(max_zreal, max_zimag) * 1.05
            
            ax1.set_xlim(0, max_val)
            ax1.set_ylim(0, max_val)
            ax1.set_aspect('equal', adjustable='box')
            
        elif aspect_mode == 'adjusted':
            # Lock aspect but allow different axis scales
            # Set aspect AFTER subplots_adjust to avoid conflicts
            ax1.set_aspect('equal', adjustable='datalim')
            
        else:  # 'auto'
            # matplotlib handles it automatically, start from 0
            ax1.set_xlim(left=0)
            ax1.set_ylim(bottom=0)
        
        self.canvas.draw()
    
    def plot_grid(self):
        """Plot checked files in grid layout with simplified 2-row structure"""
        
        self.figure.clear()
        
        # Suppress matplotlib warnings
        import warnings
        warnings.filterwarnings('ignore', message='Ignoring fixed .* limits')
        
        # Get checked files in list order
        checked_files = []
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            if item.checkState() == Qt.Checked:
                filename = item.text()
                checked_files.append((filename, self.loaded_files[filename]))
        
        if not checked_files:
            self.show_empty_plot()
            return
        
        # Calculate global limits for Nyquist (used in 'equal' mode)
        all_zreal = []
        all_zimag = []
        for filename, data in checked_files:
            all_zreal.extend(data.z_real.values)
            all_zimag.extend(data.z_imag.values)
        
        max_zreal = max(all_zreal) if all_zreal else 1
        max_zimag = max([-z for z in all_zimag]) if all_zimag else 1
        global_max = max(max_zreal, max_zimag) * 1.05
        
        # Grid settings
        n_files = len(checked_files)
        show_titles = self.show_titles_checkbox.isChecked()
        
        # Determine which plots to show
        show_nyquist = self.grid_nyquist_radio.isChecked() or self.grid_both_radio.isChecked()
        show_bode = self.grid_bode_radio.isChecked() or self.grid_both_radio.isChecked()
        
        # Get aspect mode
        aspect_mode = self._get_aspect_mode()
        
        # Always use 2 rows for consistent sizing (don't let plots expand when one is hidden)
        n_rows = 2
        
        # Store Nyquist axes for applying 'adjusted' aspect later
        nyquist_axes = []
        
        # Plot each file
        for idx, (filename, data) in enumerate(checked_files):
            # Letter label
            letter = string.ascii_lowercase[idx] if idx < 26 else f"({idx})"
            
            # Nyquist plot (Row 0)
            if show_nyquist:
                plot_pos = idx + 1  # Row 0, columns 0 to n_files-1
                ax_nyq = self.figure.add_subplot(n_rows, n_files, plot_pos)
                nyquist_axes.append(ax_nyq)  # Store reference
                
                ax_nyq.plot(data.z_real, -data.z_imag, 'o', markersize=4, color='blue')
                ax_nyq.set_xlabel('Z_real (Ω)', fontsize=8)
                ax_nyq.set_ylabel('-Z_imag (Ω)', fontsize=8)
                ax_nyq.grid(True, alpha=0.3)
                ax_nyq.tick_params(labelsize=7)
                
                # Add label in upper-left corner
                if show_titles:
                    label_text = f"({letter}) {self.display_names[filename]}"
                else:
                    label_text = f"({letter})"
                
                ax_nyq.text(0.02, 0.98, label_text, transform=ax_nyq.transAxes,
                            fontsize=9, verticalalignment='top', horizontalalignment='left')
                
                # Add frequency markers
                marker_freqs = self._parse_frequency_markers(self.grid_freq_markers_input.text())
                if marker_freqs:
                    self._add_frequency_markers(ax_nyq, data.z_real, data.z_imag, data.frequency, marker_freqs)
                
                # Apply aspect ratio ONLY to Nyquist (will be finalized after subplots_adjust)
                if aspect_mode == 'equal':
                    ax_nyq.set_xlim(0, global_max)
                    ax_nyq.set_ylim(0, global_max)
                    ax_nyq.set_aspect('equal', adjustable='box')
                elif aspect_mode == 'auto':
                    ax_nyq.set_xlim(left=0)
                    ax_nyq.set_ylim(bottom=0)
                # 'adjusted' mode will be applied after subplots_adjust
                
            else:
                # Create empty placeholder for Nyquist row
                plot_pos = idx + 1
                ax_empty = self.figure.add_subplot(n_rows, n_files, plot_pos)
                ax_empty.text(0.5, 0.5, '(Nyquist hidden)', 
                            transform=ax_empty.transAxes, ha='center', va='center',
                            fontsize=9, color='gray', style='italic')
                ax_empty.set_xticks([])
                ax_empty.set_yticks([])
            
            # Bode plot (Row 1) - No aspect ratio applied
            if show_bode:
                plot_pos = n_files + idx + 1  # Row 1, columns 0 to n_files-1
                ax_bode = self.figure.add_subplot(n_rows, n_files, plot_pos)
                ax_phase = ax_bode.twinx()
                
                z_mod = np.sqrt(data.z_real**2 + data.z_imag**2)
                phase = np.arctan2(-data.z_imag, data.z_real) * 180 / np.pi
                
                ax_bode.semilogx(data.frequency, z_mod, 'o-', markersize=3, linewidth=1, color='blue')
                ax_phase.semilogx(data.frequency, phase, 'o--', markersize=3, linewidth=1, 
                                color='red', alpha=0.7, markerfacecolor='None')
                
                ax_bode.set_xlabel('Frequency (Hz)', fontsize=8)
                ax_bode.set_ylabel('|Z| (Ω)', fontsize=8, color='blue')
                ax_bode.tick_params(axis='y', labelcolor='blue', labelsize=7)
                ax_bode.tick_params(axis='x', labelsize=7)
                ax_bode.grid(True, alpha=0.3, which='both')
                
                ax_phase.set_ylabel('Phase (°)', fontsize=8, color='red')
                ax_phase.tick_params(axis='y', labelcolor='red', labelsize=7)
                
                # Add label only if Nyquist is not shown
                if not show_nyquist:
                    if show_titles:
                        label_text = f"({letter}) {self.display_names[filename]}"
                    else:
                        label_text = f"({letter})"
                    
                    ax_bode.text(0.02, 0.98, label_text, transform=ax_bode.transAxes,
                                fontsize=9, verticalalignment='top', horizontalalignment='left')
            else:
                # Create empty placeholder for Bode row
                plot_pos = n_files + idx + 1
                ax_empty = self.figure.add_subplot(n_rows, n_files, plot_pos)
                ax_empty.text(0.5, 0.5, '(Bode hidden)', 
                            transform=ax_empty.transAxes, ha='center', va='center',
                            fontsize=9, color='gray', style='italic')
                ax_empty.set_xticks([])
                ax_empty.set_yticks([])
        
        # Get spacing preference
        spacing = self.spacing_combo.currentText()
        
        # Define spacing values
        if spacing == "Tight":
            h_space = 0.15
            w_space = 0.15
            margins = {'left': 0.06, 'right': 0.97, 'bottom': 0.05, 'top': 0.97}
        elif spacing == "Loose":
            h_space = 0.40
            w_space = 0.30
            margins = {'left': 0.08, 'right': 0.95, 'bottom': 0.07, 'top': 0.95}
        else:  # Normal
            h_space = 0.25
            w_space = 0.20
            margins = {'left': 0.07, 'right': 0.96, 'bottom': 0.06, 'top': 0.96}
        
        # Apply spacing FIRST
        self.figure.subplots_adjust(
            left=margins['left'], 
            right=margins['right'], 
            bottom=margins['bottom'], 
            top=margins['top'], 
            hspace=h_space,
            wspace=w_space
        )
        
        # THEN apply 'adjusted' aspect ratios ONLY to stored Nyquist axes
        if aspect_mode == 'adjusted' and nyquist_axes:
            for ax_nyq in nyquist_axes:
                ax_nyq.set_aspect('equal', adjustable='datalim')
        
        self.canvas.draw_idle()
        self.canvas.flush_events()
    
    def export_csv(self):
        """Export all data to CSV"""
        
        if len(self.loaded_files) == 0:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save CSV", "", "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            import pandas as pd
            
            # Combine all data
            all_data = []
            for filename, data in self.loaded_files.items():
                df = data.to_dataframe()
                df['Filename'] = filename
                all_data.append(df)
            
            combined_df = pd.concat(all_data, ignore_index=True)
            combined_df.to_csv(file_path, index=False)
            self.status_label.setText(f"✓ Exported {len(self.loaded_files)} files to CSV")
    
    def export_png(self):
        """Export plot to PNG"""
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Plot", "", "PNG Files (*.png);;All Files (*)"
        )
        
        if file_path:
            self.figure.savefig(file_path, dpi=300, bbox_inches='tight')
            self.status_label.setText(f"✓ Plot saved to PNG")