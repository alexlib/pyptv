# Running the GUI

Learn how to use the PyPTV graphical user interface for particle tracking analysis.

## Launching PyPTV

### Command Line Launch
```bash
# Activate environment
conda activate pyptv

# Launch GUI from any directory
python -m pyptv.pyptv_gui

# Or from PyPTV source directory
cd pyptv
python -m pyptv.pyptv_gui
```

### From Python Script
```python
from pyptv.pyptv_gui import MainGUI
from pathlib import Path

# Launch with specific experiment
experiment_path = Path("path/to/your/experiment")
gui = MainGUI(experiment_path, Path.cwd())
gui.configure_traits()
```

## GUI Overview

The PyPTV interface consists of several main areas:

### 1. Parameter Tree (Left Panel)
- **Experiment structure** with parameter sets (Run1, Run2, etc.)
- **Right-click menus** for parameter management
- **Expandable sections** showing parameter groups

### 2. Camera Views (Center/Right)
- **Tabbed interface** for multiple cameras
- **Image display** with zoom and pan
- **Overlay graphics** for particles, correspondences, and trajectories

### 3. Control Buttons (Top)
- **Processing buttons** for detection, correspondence, tracking
- **Parameter editing** and calibration access
- **Sequence processing** controls

### 4. Status Bar (Bottom)
- **Progress indicators** during processing
- **File information** and current frame
- **Error messages** and warnings

## Main Workflow

### 1. Load Experiment

**Option A: Load Existing YAML**
```
File → Load Experiment → Select parameters.yaml
```

**Option B: Load Legacy Parameters**
```
File → Load Legacy → Select parameters/ folder
# Automatically converts to YAML format
```

**Option C: Create New Experiment**
```
File → New Experiment → Choose directory
# Creates basic parameter structure
```

### 2. Initialize Parameters

After loading an experiment:

1. **Load images/parameters** button
   - Reads all configuration files
   - Loads calibration data
   - Prepares camera views

2. **Verify setup**:
   - Check parameter tree is populated
   - Ensure camera tabs are visible
   - Confirm calibration images load

### 3. Single Frame Processing

Process one frame to test setup:

1. **Detection**:
   ```
   Click "Detection" button
   → Blue crosses mark detected particles
   ```

2. **Correspondences**:
   ```
   Click "Correspondences" button  
   → Colored lines connect matching particles
   ```

3. **Determination**:
   ```
   Click "Determination" button
   → Calculates 3D positions
   ```

### 4. Sequence Processing

Process multiple frames:

1. **Set frame range** in sequence parameters
2. **Click "Sequence" button**
3. **Monitor progress** in status bar
4. **Check output files** in experiment directory

## Parameter Management

### Editing Parameters

**Method 1: Right-click in Parameter Tree**
```
Right-click parameter set → "Edit Parameters"
→ Opens parameter editing dialog
```

**Method 2: Direct File Editing**
```
Edit parameters.yaml in text editor
→ Reload experiment in GUI
```

**Method 3: Calibration-specific**
```
Calibration → Open Calibration
→ Specialized calibration interface
```

### Parameter Sets

Create multiple parameter configurations:

1. **Add new set**:
   ```
   Right-click in parameter tree → "Add Parameter Set"
   → Enter name (e.g., "HighSpeed", "LowLight")
   ```

2. **Switch between sets**:
   ```
   Right-click parameter set → "Set as Active"
   ```

3. **Copy settings**:
   ```
   Right-click → "Duplicate Parameter Set"
   ```

### Parameter Sections

Key parameter groups:

| Section | Purpose | Key Settings |
|---------|---------|--------------|
| **ptv** | General PTV settings | Image names, camera count, preprocessing |
| **detect_plate** | Particle detection | Gray thresholds, size limits |
| **criteria** | Correspondence matching | Search tolerances, minimum matches |
| **track** | Particle tracking | Velocity limits, trajectory linking |
| **cal_ori** | Calibration | Camera files, calibration images |

## Camera Views

### Navigation
- **Zoom**: Mouse wheel or zoom tools
- **Pan**: Click and drag
- **Reset view**: Right-click → "Reset zoom"

### Overlays
- **Blue crosses**: Detected particles
- **Colored lines**: Correspondences between cameras
- **Numbers**: Particle IDs or point numbers
- **Trajectories**: Particle paths over time

### Camera-specific Operations
- **Right-click particle**: Delete detection
- **Left-click**: Add manual detection (in calibration mode)
- **Tab switching**: Move between camera views

## Processing Controls

### Detection Settings
```
detect_plate:
  gvth_1: 80     # Primary detection threshold
  gvth_2: 40     # Secondary threshold
  min_npix: 5    # Minimum particle size
  max_npix: 100  # Maximum particle size
```

### Correspondence Settings
```
criteria:
  eps0: 0.2      # Search radius (mm)
  corrmin: 2     # Minimum cameras for correspondence
  cn: 0.02       # Additional tolerance
```

### Tracking Settings
```
track:
  dvxmin: -50.0  # Velocity limits (mm/frame)
  dvxmax: 50.0
  dvymin: -50.0
  dvymax: 50.0
```

## File Management

### Input Files
- **Image sequences**: `img/cam1.XXXXX`, `img/cam2.XXXXX`, etc.
- **Calibration images**: `cal/cam1.tif`, `cal/cam2.tif`, etc.
- **Parameter file**: `parameters.yaml`

### Output Files
- **Detection results**: `cam1_targets`, `cam2_targets`, etc.
- **3D positions**: `rt_is.XXXXX` files
- **Tracking data**: `ptv_is.XXXXX` files
- **Calibration**: Updated `.ori` and `.addpar` files

## Advanced Features

### Plugin Integration
```
Right-click parameter tree → "Configure Plugins"
→ Select tracking and sequence plugins
```

### Batch Processing
```python
# Script for multiple experiments
for experiment in experiment_list:
    gui.load_experiment(experiment)
    gui.process_sequence()
    gui.export_results()
```

### Custom Visualization
```python
# Add custom overlays
def custom_overlay(camera_view, data):
    camera_view.plot_custom_data(data)
```

## Troubleshooting

### Common Issues

**"Images not found"**
- Check file paths in parameters.yaml
- Verify image naming convention
- Ensure correct working directory

**"Calibration errors"**
- Open calibration GUI to debug
- Check .ori and .addpar files exist
- Verify calibration target coordinates

**"No particles detected"**
- Adjust detection thresholds
- Check image contrast and quality
- Try preprocessing options

**"Poor correspondences"**
- Improve calibration accuracy
- Adjust search tolerances
- Check camera synchronization

### Performance Tips

- **Memory usage**: Close unused camera tabs
- **Processing speed**: Reduce image resolution if possible
- **Disk I/O**: Use SSD for image sequences
- **Parallel processing**: Enable multi-threading in plugins

### Debugging Mode

Enable verbose output:
```bash
python -m pyptv.pyptv_gui --debug
```

Check log files:
```bash
tail -f pyptv.log
```

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Ctrl+O` | Open experiment |
| `Ctrl+S` | Save parameters |
| `F5` | Refresh/reload |
| `Space` | Process next frame |
| `Esc` | Cancel current operation |

## Best Practices

### Workflow Organization
1. **Test single frame** before sequence processing
2. **Save parameter changes** before major operations
3. **Back up original parameters** before modifications
4. **Use descriptive parameter set names**

### Data Management
- Keep experiment folders organized
- Use consistent naming conventions
- Document parameter changes
- Archive completed experiments

### Quality Control
- Regularly check calibration accuracy
- Monitor particle detection quality
- Validate tracking results
- Compare with expected physical behavior

---

**Next**: Learn about [Camera Calibration](calibration.md) or [Parameter Migration](parameter-migration.md)
