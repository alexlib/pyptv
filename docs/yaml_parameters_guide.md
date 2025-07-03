# PyPTV YAML Parameters Guide

*Updated for PyPTV 2025 - Modern YAML-based Parameter System*

## Table of Contents
- [Overview](#overview)
- [YAML Parameter File Structure](#yaml-parameter-file-structure)
- [Converting Legacy Parameters](#converting-legacy-parameters)
- [Creating New Parameter Sets](#creating-new-parameter-sets)
- [Parameter Sections Reference](#parameter-sections-reference)
- [Migration Examples](#migration-examples)
- [Troubleshooting](#troubleshooting)

## Overview

PyPTV has transitioned from the legacy `.par` file system to a modern, unified YAML-based parameter format. This new system provides:

- **Single File Configuration**: All parameters in one `parameters.yaml` file
- **Human-Readable Format**: Easy to edit, version control, and share
- **Complete Parameter Sets**: Includes tracking plugins and manual orientation data
- **Backward Compatibility**: Tools to convert to/from legacy format when needed

### Key Benefits

✅ **Simplified Management**: One file instead of multiple `.par` files  
✅ **Version Control Friendly**: Text-based format works well with Git  
✅ **Easy Editing**: Standard YAML syntax with comments and structure  
✅ **Complete Configuration**: Includes plugins, manual orientation, and all parameters  
✅ **Portable**: Copy one file to share complete parameter sets  

## YAML Parameter File Structure

A typical `parameters.yaml` file contains several main sections:

```yaml
# PyPTV Parameters File
# Generated from legacy parameters on 2025-07-03

# Global settings
n_cam: 4                    # Number of cameras

# Core parameter sections
detect_plate:
  gv_threshold_1: 80
  gv_threshold_2: 40
  gv_threshold_3: 20
  # ... more detection parameters

man_ori:
  n_img: 4
  name_img:
    - "cam1.tif"
    - "cam2.tif"
    - "cam3.tif"
    - "cam4.tif"
  # ... manual orientation parameters

orient:
  point_precision: 0.02
  angle_precision: 0.1
  # ... orientation parameters

# Plugin configuration
plugins:
  available_tracking:
    - "default"
    - "rembg_contour"
  selected_tracking: "default"
  available_sequence:
    - "default"
  selected_sequence: "default"

# Manual orientation coordinates (if present)
man_ori_coordinates:
  camera_0:
    point_1: {x: 100.5, y: 200.3}
    point_2: {x: 150.2, y: 250.8}
    # ... more points
  # ... more cameras
```

### File Naming Convention

- **Standard**: `parameters.yaml` - Place in your experiment directory
- **Variants**: `parameters_highspeed.yaml`, `parameters_test.yaml` etc.
- **Legacy Backup**: `parameters_backup/` folder with original `.par` files

## Converting Legacy Parameters

PyPTV includes a powerful conversion utility to migrate from legacy `.par` files to the new YAML format.

### Command Line Conversion

```bash
# Convert legacy parameters folder to YAML
python -m pyptv.parameter_util legacy-to-yaml ./path/to/parameters/

# Convert to specific output file
python -m pyptv.parameter_util legacy-to-yaml ./parameters/ --output my_params.yaml

# Convert without creating backup
python -m pyptv.parameter_util legacy-to-yaml ./parameters/ --no-backup
```

### Python API Conversion

```python
from pyptv.parameter_util import legacy_to_yaml, yaml_to_legacy

# Convert legacy to YAML
yaml_file = legacy_to_yaml("./test_cavity/parameters/", "experiment.yaml")

# Convert YAML back to legacy (if needed)
legacy_dir = yaml_to_legacy("experiment.yaml", "legacy_output/")
```

### What Gets Converted

The conversion process handles:

- **All `.par` files**: `ptv.par`, `detect_plate.par`, `man_ori.par`, etc.
- **`plugins.json`**: Tracking and sequence plugin configuration
- **`man_ori.dat`**: Manual orientation coordinate data
- **Directory structure**: Maintains organization and relationships

### Legacy Folder Structure (Before)

```
experiment/
├── parameters/
│   ├── ptv.par
│   ├── detect_plate.par
│   ├── man_ori.par
│   ├── orient.par
│   ├── track.par
│   ├── plugins.json
│   └── man_ori.dat
├── img/
└── cal/
```

### YAML Structure (After)

```
experiment/
├── parameters.yaml         # Single unified file
├── parameters_backup/      # Backup of original files
├── img/
└── cal/
```

## Creating New Parameter Sets

### From Scratch

Create a new `parameters.yaml` with basic structure:

```yaml
# Minimal PyPTV Parameters
n_cam: 2

detect_plate:
  gv_threshold_1: 80
  gv_threshold_2: 40
  gv_threshold_3: 20

man_ori:
  n_img: 2
  name_img:
    - "cam1.tif"
    - "cam2.tif"

plugins:
  selected_tracking: "default"
  selected_sequence: "default"
```

### From Existing Configuration

```bash
# Copy and modify existing parameters
cp parameters.yaml parameters_new_experiment.yaml

# Edit the new file for your specific needs
# Change camera names, thresholds, etc.
```

### Using PyPTV GUI

1. Load existing `parameters.yaml`
2. Adjust parameters through the GUI
3. Save to new YAML file
4. GUI automatically maintains YAML format

## Parameter Sections Reference

### Core Sections

| Section | Purpose | Key Parameters |
|---------|---------|----------------|
| `detect_plate` | Particle detection settings | `gv_threshold_1/2/3`, `tolerable_discontinuity` |
| `man_ori` | Manual orientation setup | `n_img`, `name_img`, image file paths |
| `orient` | Automatic orientation | `point_precision`, `angle_precision` |
| `track` | Particle tracking | `dvxmin/max`, `dvymin/max`, `dvzmin/max` |
| `ptv` | General PTV settings | Camera and processing parameters |

### Special Sections

| Section | Purpose | Notes |
|---------|---------|-------|
| `plugins` | Plugin configuration | Tracking and sequence plugins |
| `man_ori_coordinates` | Manual orientation points | Camera calibration coordinates |
| `n_cam` | Global camera count | Used throughout the system |

### Detection Parameters (`detect_plate`)

```yaml
detect_plate:
  gv_threshold_1: 80        # Primary detection threshold
  gv_threshold_2: 40        # Secondary threshold
  gv_threshold_3: 20        # Tertiary threshold
  tolerable_discontinuity: 2 # Allowable pixel gaps
  min_npix: 1               # Minimum particle size
  max_npix: 100             # Maximum particle size
```

### Tracking Parameters (`track`)

```yaml
track:
  dvxmin: -100.0           # Minimum X velocity
  dvxmax: 100.0            # Maximum X velocity
  dvymin: -100.0           # Minimum Y velocity
  dvymax: 100.0            # Maximum Y velocity
  dvzmin: -100.0           # Minimum Z velocity
  dvzmax: 100.0            # Maximum Z velocity
  angle: 1.0               # Search angle tolerance
```

### Plugin Configuration

```yaml
plugins:
  available_tracking:       # Available tracking plugins
    - "default"
    - "rembg_contour"
    - "custom_plugin"
  selected_tracking: "default"  # Currently selected
  available_sequence:       # Available sequence plugins
    - "default"
  selected_sequence: "default"
```

## Migration Examples

### Example 1: Simple 2-Camera Setup

**Legacy files:**
```
parameters/
├── ptv.par
├── detect_plate.par
└── man_ori.par
```

**Command:**
```bash
python -m pyptv.parameter_util legacy-to-yaml ./parameters/
```

**Result:** `parameters.yaml` with all settings unified

### Example 2: Complex 4-Camera with Plugins

**Legacy files:**
```
parameters/
├── ptv.par
├── detect_plate.par
├── man_ori.par
├── orient.par
├── track.par
├── plugins.json
└── man_ori.dat
```

**Conversion:**
```python
from pyptv.parameter_util import legacy_to_yaml

# Convert with custom output name
yaml_file = legacy_to_yaml(
    "./complex_experiment/parameters/",
    "./complex_experiment/config.yaml",
    backup_legacy=True
)
```

### Example 3: Round-Trip Conversion

```python
# Start with legacy parameters
yaml_file = legacy_to_yaml("./legacy_params/")

# Modify YAML as needed
# ... edit parameters.yaml ...

# Convert back to legacy format (for older PyPTV versions)
legacy_dir = yaml_to_legacy("parameters.yaml", "./legacy_output/")
```

## Working with YAML Parameters

### Loading in PyPTV

```python
from pyptv.parameter_manager import ParameterManager

# Load YAML parameters
manager = ParameterManager()
manager.from_yaml("parameters.yaml")

# Access parameters
detection_params = manager.get_parameter('detect_plate')
n_cameras = manager.get_n_cam()
```

### Editing YAML Files

YAML files can be edited with any text editor:

```yaml
# Comments are preserved and encouraged
detect_plate:
  gv_threshold_1: 85      # Increased for better detection
  gv_threshold_2: 45      # Secondary threshold
  
# You can add your own comments
man_ori:
  n_img: 4
  name_img:
    - "cam1_001.tif"      # Updated filename
    - "cam2_001.tif"
    - "cam3_001.tif" 
    - "cam4_001.tif"
```

### Version Control Best Practices

```bash
# Track parameter changes
git add parameters.yaml
git commit -m "Adjusted detection thresholds for better particle detection"

# Create parameter branches
git checkout -b high_speed_params
# ... modify parameters.yaml for high-speed experiments
git commit -m "High-speed experiment parameters"
```

## Troubleshooting

### Common Issues

**Q: Conversion fails with "No .par files found"**  
A: Ensure you're pointing to the `parameters/` folder, not the parent directory.

```bash
# Wrong:
python -m pyptv.parameter_util legacy-to-yaml ./experiment/

# Correct:
python -m pyptv.parameter_util legacy-to-yaml ./experiment/parameters/
```

**Q: YAML file is very large**  
A: This is normal. YAML includes all parameters explicitly for completeness.

**Q: Some parameters seem to be missing**  
A: Check that all required `.par` files exist in the legacy directory.

**Q: Plugin settings not preserved**  
A: Ensure `plugins.json` exists in the parameters folder before conversion.

### Validation

```python
# Validate YAML parameters
from pyptv.parameter_manager import ParameterManager

try:
    manager = ParameterManager()
    manager.from_yaml("parameters.yaml")
    print("✅ YAML parameters are valid")
except Exception as e:
    print(f"❌ YAML validation failed: {e}")
```

### Recovery

If you need to recover legacy format:

```bash
# Convert YAML back to legacy .par files
python -m pyptv.parameter_util yaml-to-legacy parameters.yaml recovered_legacy/
```

## Best Practices

### 1. Use Descriptive Names
```yaml
# Good
detect_plate:
  gv_threshold_1: 80  # High contrast particles

# Better with comments
detect_plate:
  gv_threshold_1: 80  # Primary threshold for bright particles
  gv_threshold_2: 40  # Secondary for dimmer particles
```

### 2. Version Your Parameters
```bash
parameters_v1.yaml          # Initial setup
parameters_v2_tuned.yaml    # After optimization
parameters_final.yaml       # Production settings
```

### 3. Backup Before Major Changes
```bash
cp parameters.yaml parameters_backup_$(date +%Y%m%d).yaml
```

### 4. Use Consistent Formatting
- Keep indentation consistent (2 or 4 spaces)
- Add comments for non-obvious values
- Group related parameters together

## Advanced Usage

### Programmatic Parameter Generation

```python
from pyptv.parameter_manager import ParameterManager

# Create parameters programmatically
manager = ParameterManager()
manager.set_n_cam(4)

# Set detection parameters
manager.set_parameter('detect_plate', {
    'gv_threshold_1': 80,
    'gv_threshold_2': 40,
    'gv_threshold_3': 20
})

# Save to YAML
manager.to_yaml("generated_parameters.yaml")
```

### Parameter Templates

Create template files for common setups:

```yaml
# template_2cam.yaml
n_cam: 2
detect_plate:
  gv_threshold_1: 80
  gv_threshold_2: 40
man_ori:
  n_img: 2
  name_img: ["cam1.tif", "cam2.tif"]
```

```bash
# Use template
cp template_2cam.yaml my_experiment_parameters.yaml
# ... customize for your specific experiment
```

## Summary

The YAML parameter system modernizes PyPTV configuration management:

- **Unified Configuration**: Single `parameters.yaml` file
- **Easy Migration**: Convert legacy `.par` files seamlessly  
- **Better Workflow**: Version control, sharing, and editing simplified
- **Backward Compatible**: Convert back to legacy format when needed

Start by converting your existing parameters:

```bash
python -m pyptv.parameter_util legacy-to-yaml ./your_experiment/parameters/
```

Then enjoy the benefits of modern, unified parameter management in PyPTV!
