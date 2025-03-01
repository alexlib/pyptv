# PyPTV User Guide

## Introduction

PyPTV is a Python-based graphical user interface for the OpenPTV library, designed for Particle Tracking Velocimetry analysis. This document provides guidance on using the modernized interface, which includes new features for parameter management, 3D visualization, and improved workflow.

## Getting Started

### Installation

```bash
# Install dependencies
pip install numpy

# Install PyPTV
python -m pip install pyptv --index-url https://pypi.fury.io/pyptv --extra-index-url https://pypi.org/simple
```

### Launching the Application

```bash
# Launch the GUI
python -m pyptv.pyptv_gui

# Or use the command-line interface
python -m pyptv.cli
```

## Modern Interface Overview

The PyPTV interface has been modernized with the following key improvements:

1. **YAML Parameter System**: A more readable and maintainable parameter management system
2. **Interactive 3D Visualization**: Advanced visualization of particle trajectories
3. **Improved Camera Views**: Enhanced controls for image visualization
4. **Parameter Dialog**: Form-based parameter editing with validation

## YAML Parameter System

### Benefits of YAML Parameters

- Human-readable format
- Type validation
- Default values
- Automatic conversion from legacy formats

### Editing Parameters

1. Open the parameter dialog from the menu: **Parameters > Edit Parameters**
2. Parameters are organized by category
3. Modified parameters are highlighted
4. Click **Save** to apply changes

### Parameter Files

Parameter files are stored with a `.yaml` extension in the `parameters/` directory of your project:

- `ptv.yaml`: Main PTV parameters
- `calibration.yaml`: Camera calibration parameters
- `detection.yaml`: Particle detection parameters
- `tracking.yaml`: Tracking parameters

## 3D Visualization

The new 3D visualization tool provides interactive exploration of particle trajectories.

### Accessing the Visualization Tool

Open the visualization dialog from:
- The menu: **View > 3D Visualization**
- The toolbar: Click the 3D visualization icon

### Visualization Features

- **Rotation**: Click and drag to rotate the view
- **Zoom**: Scroll wheel to zoom in/out
- **Pan**: Right-click and drag to pan
- **Color Options**: 
  - Color by velocity magnitude
  - Color by frame number
  - Solid color
- **Trajectory Filtering**:
  - Show/hide specific trajectories
  - Filter by length
  - Filter by velocity
- **Export Options**:
  - Export as image (.png)
  - Export as 3D model (.obj)
  - Export data (.csv)

### Keyboard Shortcuts

- **R**: Reset view
- **S**: Take screenshot
- **C**: Change color scheme
- **F**: Show/hide frame number
- **V**: Show/hide velocity vectors

## Camera View Improvements

### Enhanced Controls

- **Zoom**: Scroll wheel or use the zoom slider
- **Pan**: Right-click and drag or use arrow keys
- **Brightness/Contrast**: Adjust using sliders in the sidebar
- **Overlays**: Toggle particle markers, calibration points, and coordinate axes

### Selection Tools

- **Select Points**: Click to select individual particles
- **Rectangle Selection**: Shift+drag to select multiple particles
- **Point Information**: View coordinates and intensity values

## Working with Projects

### Project Structure

A typical PyPTV project contains:

```
my_experiment/
├── cal/              # Calibration images and data
├── img/              # Experimental images
├── parameters/       # Parameter files (YAML)
├── res/              # Results
└── masking.json      # Optional camera mask definitions
```

### Workflow Example

1. **Setup Project**:
   - Create directory structure
   - Import calibration and experimental images

2. **Calibration**:
   - Load calibration images
   - Detect calibration points
   - Optimize camera parameters

3. **Particle Detection**:
   - Configure detection parameters
   - Run detection on image sequence
   - Verify detection results

4. **Tracking**:
   - Set tracking parameters
   - Run tracking algorithm
   - Visualize and analyze trajectories

## Plugin System

PyPTV supports plugins to extend functionality without modifying the core application.

### Using Plugins

1. Copy `sequence_plugins.txt` and `tracking_plugins.txt` to your working folder
2. Copy the `plugins/` directory to your working folder
3. Select plugins from the menu: **Plugins > Choose**
4. Run your workflow: **Init > Sequence > Tracking**

### Available Plugins

- **Denis Sequence**: Standard sequence processing
- **Contour Sequence**: Contour-based detection
- **Rembg Sequence**: Background removal (requires `pip install rembg[cpu]`)
- **Denis Tracker**: Standard tracking algorithm

## Migrating from Legacy UI

If you're familiar with the previous PyPTV interface, here's what changed:

1. Parameters are now stored in YAML format but are automatically converted from legacy formats
2. The main workflow remains the same, but with improved user interface
3. New visualization tools provide more insights without changing the core functionality
4. All legacy project files remain compatible

## Troubleshooting

### Common Issues

- **Parameter File Issues**: If parameters don't load, check file permissions and format
- **Visualization Problems**: Ensure your graphics drivers are up to date
- **Plugin Errors**: Verify that required dependencies are installed
- **Image Loading Errors**: Check that images are in a supported format (TIF, PNG, JPG)

### Getting Help

- Documentation: http://openptv-python.readthedocs.io
- Mailing List: openptv@googlegroups.com
- Issue Tracker: https://github.com/alexlib/pyptv/issues