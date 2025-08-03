# Parameter Migration Guide

This guide helps you migrate from older PyPTV parameter formats to the current YAML-based system.

## Overview

PyPTV has undergone significant improvements in its parameter management system. This guide will help you understand and migrate to the current format.

## Environment Setup and Testing

PyPTV uses a modern conda environment (`environment.yml`) and separates tests into headless (`tests/`) and GUI (`tests_gui/`) categories. See the README for details.

> **Important**: Always use `num_cams` for camera count. Do not use legacy fields like `n_img`.

## Current YAML Structure

The current parameter system uses a single YAML file with the following top-level structure:

```yaml
num_cams: 4  # Number of cameras (global setting)

cal_ori:
  # Calibration and orientation parameters
  
criteria:
  # Tracking criteria parameters
  
detect_plate:
  # Detection parameters
  
ptv:
  # Main PTV processing parameters
  
sequence:
  # Image sequence parameters
  
track:
  # Tracking algorithm parameters
  
plugins:
  # Plugin configuration
```

## Key Changes from Legacy Formats

### 1. Camera Count Management

**Old system:** Used `n_img` in various parameter sections
**New system:** Uses single global `num_cams` field

```yaml
# ✅ Correct - current format
num_cams: 4

# ❌ Incorrect - legacy format
ptv:
  n_img: 4
```

### 2. Parameter Organization

Parameters are now organized into logical groups rather than scattered across multiple files.

### 3. Manual Orientation Format

The `man_ori` section now uses a flattened array format:

```yaml
man_ori:
  nr: [3, 5, 72, 73, 3, 5, 72, 73, 1, 5, 71, 73, 1, 5, 71, 73]
```

## Migration Steps

### From Old PyPTV Installations

1. **Backup your existing parameters**
   ```bash
   cp -r your_project/parameters your_project/parameters_backup
   ```

2. **Use the GUI to load and save parameters**
   - Open PyPTV GUI
   - Load your old parameter files
   - Save as new YAML format using "Save Parameters"

3. **Verify the migration**
   - Check that `num_cams` is set correctly at the top level
   - Ensure no `n_img` fields remain in the YAML
   - Test calibration and tracking workflows

### Step-by-step: Migrating from Parameter Directories to YAML

**1. Locate your legacy parameter files:**
   - Typical files: `ptv_par.txt`, `criterium.txt`, `detect_plate.txt`, `track.txt`, etc.
   - These are usually in a `parameters/` or project root directory.

**2. Open PyPTV GUI:**
   - Launch with `python -m pyptv.pyptv_gui`
   - Use `File → Load Legacy` to select your old parameter directory.

**3. Save as YAML:**
   - After loading, use `File → Save Parameters` to export all settings to a single YAML file (e.g., `parameters_Run1.yaml`).

**4. Check and edit YAML:**
   - Open the YAML file in a text editor.
   - Ensure `num_cams` is present and correct.
   - Update any file paths to be relative to your experiment directory.
   - Remove any legacy fields (e.g., `n_img`).

**5. Validate in GUI:**
   - Reload the YAML in the GUI and check that all dialogs open and parameters are correct.

**6. Use the YAML in Python:**
   - You can now use the YAML file for all PyPTV workflows, including headless and batch processing.

#### Using YAML Parameters in Python

You can load and use YAML parameters in Python via two main interfaces:

**A. Using the `Experiment` class:**
```python
from pyptv.experiment import Experiment
exp = Experiment('parameters_Run1.yaml')
# Access parameters:
print(exp.cpar)  # ControlParams object
print(exp.spar)  # SequenceParams object
print(exp.vpar)  # VolumeParams object
print(exp.tpar)  # TargetParams object
print(exp.cals)  # List of Calibration objects
```

**B. Using the `ParameterManager` directly:**
```python
from pyptv.parameter_manager import ParameterManager
pm = ParameterManager('parameters_Run1.yaml')
# Access raw parameter dictionary:
params = pm.parameters
num_cams = pm.num_cams
# Use helper functions to populate objects:
from pyptv.ptv import _populate_cpar, _populate_spar
cpar = _populate_cpar(params['ptv'], num_cams)
spar = _populate_spar(params['sequence'], num_cams)


**Tip:** For most workflows, use the `Experiment` class for convenience. For advanced or custom workflows, use `ParameterManager` and the population functions.

**Summary:**
- Migrate all legacy parameter files to a single YAML using the GUI.
- Always use `num_cams` for camera count.
- Use the YAML file in Python via `Experiment` or `ParameterManager`.
### From Manual Parameter Files

If you have manually created parameter files:

1. Start with the test_cavity example as a template
2. Copy the structure from `tests/test_cavity/parameters_Run1.yaml`
3. Update paths and values to match your experiment

## Common Migration Issues

### Issue 1: Multiple Camera Count Fields

**Problem:** Old files may have `n_img` in multiple sections
**Solution:** Remove all `n_img` fields and use only the global `num_cams`

### Issue 2: Incorrect File Paths

**Problem:** Relative paths may not work with new structure
**Solution:** Use paths relative to your experiment directory

### Issue 3: Missing Parameter Groups

**Problem:** New YAML structure requires all parameter groups
**Solution:** Use the test_cavity example to ensure all sections are present

## Validation

After migration, validate your parameters:

1. Load the YAML file in PyPTV GUI
2. Check the "Edit Parameters" dialogs work correctly
3. Run a test calibration to ensure all parameters are read properly
4. Verify tracking parameters are applied correctly

## Example Migration

From this legacy structure:
```
project/
├── ptv_par.txt
├── criterium.txt
├── detect_plate.txt
└── track.txt
```

To this modern structure:
```
project/
├── parameters_Run1.yaml
├── cal/
│   ├── cam1.tif
│   └── ...
└── img/
    ├── cam1.10001
    └── ...
```

## Getting Help

If you encounter issues during migration:

1. Check the test_cavity example for reference
2. Use the PyPTV GUI parameter editors to understand the expected format
3. Consult the [YAML Parameters Guide](yaml-parameters.md) for detailed field descriptions
4. Ask for help on the PyPTV community forums or GitHub issues

## See Also

- [YAML Parameters Guide](yaml-parameters.md)
- [Quick Start Guide](quick-start.md)
- [Test Cavity Example](examples.md#test-cavity)
