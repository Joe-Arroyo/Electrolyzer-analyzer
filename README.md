# Electrolyzer Analyzer
A Python GUI application for electrochemical characterization of electrolyzers. Unifies data from multiple instruments and measurement techniques into a single interactive analysis environment — replacing fragmented notebook workflows with a cohesive, publication-ready tool.

# Features
## EIS (Electrochemical Impedance Spectroscopy)

Overlay mode: Nyquist + optional Bode plots (magnitude and phase) for multiple datasets
Grid mode: individual Nyquist/Bode subplots per file with alphabetical labels
Nyquist aspect ratio controls: Auto, Equal, or Adjusted (removes blank space)
Frequency markers: annotate specific frequencies on the Nyquist plot
Editable legend names per dataset
Supports up to 20 simultaneous datasets with distinct colors

## Polarization Curves

Automatically detects galvanostatic current steps from chronopotentiometry data
Extracts steady-state voltages by averaging over a configurable trailing window (e.g., last 30 s of each step)
Builds polarization curves (cell voltage vs. current density) across multiple files
Group management: create named groups to compare different experimental conditions side by side
Interactive point selection: click to exclude/include points, with full undo/redo support
Displays raw transient data alongside the polarization curve
CSV export: polarization curve data and/or raw transient data, with optional metadata headers
Plot export: configurable size, DPI (150–1200), and format (PNG, PDF, SVG, TIFF)

## Chronopotentiometry Viewer

Load and visualize raw voltage and/or current vs. time traces
Optional time range filtering
Export as CSV or PNG