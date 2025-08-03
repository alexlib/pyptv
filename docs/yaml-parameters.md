# YAML Parameters Reference

This guide provides a comprehensive reference for all parameters in PyPTV's YAML configuration system.

## Overview

PyPTV uses a single YAML file to store all experiment parameters. The file is organized into logical sections, each controlling different aspects of the PTV workflow.

## Environment Setup and Testing

PyPTV uses a modern conda environment (`environment.yml`) and separates tests into headless (`tests/`) and GUI (`tests_gui/`) categories. See the README for details.

> **Important**: Always use `num_cams` for camera count. Do not use legacy fields like `n_img`.

## File Structure

```yaml
num_cams: 4  # Global camera count

cal_ori:
  # Calibration parameters
  
criteria:
  # Correspondence criteria
  
detect_plate:
  # Detection parameters
  
dumbbell:
  # Dumbbell tracking parameters
  
examine:
  # Examination settings
  
man_ori:
  # Manual orientation
  
multi_planes:
  # Multi-plane calibration
  
orient:
  # Orientation parameters
  
pft_version:
  # Version settings
  
ptv:
  # Main PTV parameters
  
sequence:
  # Image sequence settings
  
shaking:
  # Shaking correction
  
sortgrid:
  # Grid sorting
  
targ_rec:
  # Target recognition
  
track:
  # Tracking parameters
  
masking:
  # Image masking
  
unsharp_mask:
  # Unsharp mask filter
  
plugins:
  # Plugin configuration
  
man_ori_coordinates:
  # Manual orientation coordinates
```

## Global Parameters

### num_cams
**Type**: Integer  
**Description**: Number of cameras in the system  
**Example**: `num_cams: 4`

> **Important**: This is the master camera count. Do not use `n_img` anywhere in the YAML file.

## Calibration Parameters (cal_ori)

Controls camera calibration and orientation setup.

```yaml
cal_ori:
  chfield: 0                    # Change field flag
  fixp_name: cal/target.txt     # Fixed point file path
  img_cal_name:                 # Calibration image paths
    - cal/cam1.tif
    - cal/cam2.tif
    - cal/cam3.tif
    - cal/cam4.tif
  img_ori:                      # Orientation file paths (auto-generated)
    - cal/cam1.tif.ori
    - cal/cam2.tif.ori
    - cal/cam3.tif.ori
    - cal/cam4.tif.ori
  pair_flag: false              # Pair calibration flag
  tiff_flag: true               # TIFF format flag
  cal_splitter: false           # Splitter calibration mode
```

### Field Descriptions

- **chfield**: Field change flag (0 = no change, 1 = change)
- **fixp_name**: Path to file containing fixed 3D calibration points
- **img_cal_name**: List of calibration image file paths for each camera
- **img_ori**: List of orientation file paths (automatically populated)
- **pair_flag**: Enable pair-wise calibration
- **tiff_flag**: Use TIFF image format
- **cal_splitter**: Enable splitter-based calibration

## Correspondence Criteria (criteria)

Defines criteria for stereo matching and correspondence.

```yaml
criteria:
  X_lay: [-40, 40]             # X layer bounds [min, max]
  Zmax_lay: [25, 25]           # Maximum Z bounds per layer
  Zmin_lay: [-20, -20]         # Minimum Z bounds per layer
  cn: 0.02                     # Correspondence tolerance
  cnx: 0.02                    # X correspondence tolerance
  cny: 0.02                    # Y correspondence tolerance
  corrmin: 33.0                # Minimum correlation value
  csumg: 0.02                  # Sum of grey value tolerance
  eps0: 0.2                    # Initial epsilon value
```

## Detection Parameters (detect_plate)

Controls particle detection on each camera.

```yaml
detect_plate:
  gvth_1: 40                   # Grey value threshold camera 1
  gvth_2: 40                   # Grey value threshold camera 2
  gvth_3: 40                   # Grey value threshold camera 3
  gvth_4: 40                   # Grey value threshold camera 4
  max_npix: 400                # Maximum pixel count
  max_npix_x: 50               # Maximum pixels in X
  max_npix_y: 50               # Maximum pixels in Y
  min_npix: 25                 # Minimum pixel count
  min_npix_x: 5                # Minimum pixels in X
  min_npix_y: 5                # Minimum pixels in Y
  size_cross: 3                # Cross correlation size
  sum_grey: 100                # Minimum sum of grey values
  tol_dis: 500                 # Distance tolerance
```

## PTV Main Parameters (ptv)

Core PTV processing parameters.

```yaml
ptv:
  allcam_flag: false           # All cameras flag
  chfield: 0                   # Change field flag
  hp_flag: true                # High pass filter flag
  img_cal:                     # Calibration images
    - cal/cam1.tif
    - cal/cam2.tif
    - cal/cam3.tif
    - cal/cam4.tif
  img_name:                    # Current frame images
    - img/cam1.10002
    - img/cam2.10002
    - img/cam3.10002
    - img/cam4.10002
  imx: 1280                    # Image width in pixels
  imy: 1024                    # Image height in pixels
  mmp_d: 6.0                   # Glass thickness (mm)
  mmp_n1: 1.0                  # Refractive index air
  mmp_n2: 1.33                 # Refractive index water
  mmp_n3: 1.46                 # Refractive index glass
  pix_x: 0.012                 # Pixel size X (mm)
  pix_y: 0.012                 # Pixel size Y (mm)
  tiff_flag: true              # TIFF format flag
  splitter: false              # Splitter mode flag
```

## Sequence Parameters (sequence)

Defines image sequence for processing.

```yaml
sequence:
  base_name:                   # Base filename patterns
    - img/cam1.%d
    - img/cam2.%d
    - img/cam3.%d
    - img/cam4.%d
  first: 10001                 # First frame number
  last: 10004                  # Last frame number
```

## Tracking Parameters (track)

Controls particle tracking algorithm.

```yaml
track:
  angle: 100.0                 # Maximum angle change (degrees)
  dacc: 2.8                    # Acceleration tolerance
  dvxmax: 15.5                 # Maximum velocity X
  dvxmin: -15.5                # Minimum velocity X
  dvymax: 15.5                 # Maximum velocity Y
  dvymin: -15.5                # Minimum velocity Y
  dvzmax: 15.5                 # Maximum velocity Z
  dvzmin: -15.5                # Minimum velocity Z
  flagNewParticles: true       # Allow new particles
```

## Target Recognition (targ_rec)

Parameters for target/particle recognition.

```yaml
targ_rec:
  cr_sz: 2                     # Cross size
  disco: 100                   # Discontinuity threshold
  gvthres:                     # Grey value thresholds per camera
    - 9
    - 9
    - 9
    - 11
  nnmax: 500                   # Maximum neighbors
  nnmin: 4                     # Minimum neighbors
  nxmax: 100                   # Maximum X extent
  nxmin: 2                     # Minimum X extent
  nymax: 100                   # Maximum Y extent
  nymin: 2                     # Minimum Y extent
  sumg_min: 150                # Minimum sum of grey values
```

## Plugin Configuration (plugins)

Manages available and selected plugins.

```yaml
plugins:
  available_tracking:          # Available tracking plugins
    - default
    - ext_tracker_splitter
  available_sequence:          # Available sequence plugins
    - default
    - ext_sequence_rembg
    - ext_sequence_contour
  selected_tracking: default   # Selected tracking plugin
  selected_sequence: default   # Selected sequence plugin
```

## Manual Orientation (man_ori)

Manual orientation setup for calibration.

```yaml
man_ori:
  nr: [3, 5, 72, 73, 3, 5, 72, 73, 1, 5, 71, 73, 1, 5, 71, 73]
```

The `nr` array contains point IDs for manual orientation, flattened across all cameras.

## Manual Orientation Coordinates (man_ori_coordinates)

Pixel coordinates for manual orientation points.

```yaml
man_ori_coordinates:
  camera_0:
    point_1: {x: 1009.0, y: 608.0}
    point_2: {x: 979.0, y: 335.0}
    point_3: {x: 246.0, y: 620.0}
    point_4: {x: 235.0, y: 344.0}
  camera_1:
    point_1: {x: 1002.0, y: 609.0}
    # ... more points
```

## Optional Parameters

### Masking (masking)

Image masking configuration.

```yaml
masking:
  mask_flag: false             # Enable masking
  mask_base_name: ''           # Mask file base name
```

### Unsharp Mask (unsharp_mask)

Unsharp mask filter settings.

```yaml
unsharp_mask:
  flag: false                  # Enable unsharp mask
  size: 3                      # Kernel size
  strength: 1.0                # Filter strength
```

### Dumbbell Tracking (dumbbell)

Specialized dumbbell particle tracking.

```yaml
dumbbell:
  dumbbell_eps: 3.0           # Epsilon parameter
  dumbbell_gradient_descent: 0.05  # Gradient descent step
  dumbbell_niter: 500         # Number of iterations
  dumbbell_penalty_weight: 1.0 # Penalty weight
  dumbbell_scale: 25.0        # Scale factor
  dumbbell_step: 1            # Step size
```

## Common Parameter Patterns

### Camera-Specific Arrays

Many parameters are arrays with one value per camera:

```yaml
# For 4 cameras, provide 4 values
gvthres: [9, 9, 9, 11]
img_cal_name:
  - cal/cam1.tif
  - cal/cam2.tif
  - cal/cam3.tif
  - cal/cam4.tif
```

### File Paths

Use paths relative to the parameter file location:

```yaml
# Correct - relative paths
fixp_name: cal/target.txt
img_name:
  - img/cam1.10002

# Avoid - absolute paths (not portable)
# fixp_name: /full/path/to/target.txt
```

### Boolean Flags

Use lowercase true/false:

```yaml
tiff_flag: true
pair_flag: false
```

## Validation

To validate your parameter file:

1. Load it in the PyPTV GUI
2. Check that all parameter dialogs open without errors
3. Verify camera count matches your hardware
4. Ensure all file paths exist and are accessible

## Migration Notes

When migrating from older formats:

- Remove any `n_img` fields - use only `num_cams`
- Ensure all camera arrays have exactly `num_cams` elements
- Flatten `man_ori.nr` array if it was nested
- Convert boolean values to lowercase

## See Also

- [Parameter Migration Guide](parameter-migration.md)
- [Calibration Guide](calibration.md)
- [Quick Start Guide](quick-start.md)
