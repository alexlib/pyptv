# Calibration Guide

This guide covers camera calibration in PyPTV, from basic concepts to advanced techniques.

## Overview

Camera calibration is the process of determining the intrinsic and extrinsic parameters of your camera system. This is essential for accurate 3D particle tracking.

## Environment Setup and Testing

PyPTV uses a modern conda environment (`environment.yml`) and separates tests into headless (`tests/`) and GUI (`tests_gui/`) categories. See the README for details.

## Prerequisites

Before starting calibration:

1. **Calibration Target**: You need a calibration target with known 3D coordinates
2. **Camera Images**: High-quality images of the calibration target from all cameras
3. **Parameter File**: A properly configured YAML parameter file

## Basic Calibration Workflow

### 1. Prepare Calibration Images

Place calibration images in your `cal/` directory:

```
your_experiment/
├── parameters_Run1.yaml
├── cal/
│   ├── cam1.tif
│   ├── cam2.tif
│   ├── cam3.tif
│   ├── cam4.tif
│   └── target_coordinates.txt
└── img/
    └── ...
```

### 2. Configure Calibration Parameters

In your YAML file, set up the calibration section:

```yaml
num_cams: 4

cal_ori:
  chfield: 0
  fixp_name: cal/target_coordinates.txt
  img_cal_name:
    - cal/cam1.tif
    - cal/cam2.tif
    - cal/cam3.tif
    - cal/cam4.tif
  img_ori: []  # Will be filled during calibration
  pair_flag: false
  tiff_flag: true
  cal_splitter: false
```

### 3. Define Target Coordinates

Create a target coordinate file (`cal/target_coordinates.txt`) with known 3D points:

```
# point_id   X      Y      Z
1          -25.0  -25.0   0.0
2           25.0  -25.0   0.0
3           25.0   25.0   0.0
4          -25.0   25.0   0.0
```

### 4. Run Calibration in GUI

1. **Open PyPTV GUI**
   ```bash
   python -m pyptv
   ```

2. **Load Your Experiment**
   - File → Open Experiment
   - Select your parameter YAML file

3. **Open Calibration Window**
   - Tools → Calibration
   - Or click the "Calibration" button

4. **Detect Calibration Points**
   - Click "Detect points" for each camera
   - Verify detection quality in the image display
   - Manually correct points if needed

5. **Manual Orientation (if needed)**
   - Click "Manual orient" if automatic detection fails
   - Manually click on known calibration points
   - Follow the on-screen prompts

6. **Run Calibration**
   - Click "Calibration" to calculate camera parameters
   - Check the calibration residuals in the output

7. **Save Results**
   - Calibration parameters are automatically saved to `.ori` files
   - Updated parameters are saved to your YAML file

## Advanced Calibration Features

### Dumbbell Calibration Parameters

PyPTV supports dumbbell-based calibration to refine camera extrinsics. The dumbbell length is specified in millimeters.

Key parameters in the `dumbbell` section:

- `dumbbell_scale`: Expected dumbbell length (mm). Measure the physical dumbbell length and enter it here.
- `dumbbell_penalty_weight`: Weight of the length constraint relative to ray convergence. Start at 0.1-1.0 and increase only if length drift is visible.
- `dumbbell_eps`: Frame filter threshold (mm). Frames with reconstructed length deviating by more than this are excluded. Typical range: 3-10.
- `dumbbell_step`: Frame stride. Use 1 for full data; increase to 2-5 to speed up or reduce correlated frames.
- `dumbbell_fixed_camera`: Camera index to fix (1-based). Set to 0 for automatic selection (most valid detections).
- `dumbbell_niter`: Legacy parameter (not used by the current least-squares solver).
- `dumbbell_gradient_descent`: Legacy parameter (not used by the current least-squares solver).

Suggested starting values:

```yaml
dumbbell:
  dumbbell_scale: 25.0
  dumbbell_penalty_weight: 0.5
  dumbbell_eps: 5.0
  dumbbell_step: 1
  dumbbell_fixed_camera: 0
```

Tuning tips:

- If many frames are filtered, increase `dumbbell_eps`.
- If the length drifts but convergence is stable, increase `dumbbell_penalty_weight`.
- If optimization becomes unstable or flat, reduce `dumbbell_penalty_weight` and remove outlier frames.

### Multi-Plane Calibration

For improved accuracy with large measurement volumes:

```yaml
multi_planes:
  n_planes: 3
  plane_name:
    - img/calib_a_cam
    - img/calib_b_cam
    - img/calib_c_cam
```

### Calibration with Splitter

For splitter-based stereo systems:

```yaml
cal_ori:
  cal_splitter: true
  # Additional splitter-specific parameters
```

### Manual Orientation Points

You can specify manual orientation points in the YAML:

```yaml
man_ori:
  nr: [3, 5, 72, 73, 3, 5, 72, 73, 1, 5, 71, 73, 1, 5, 71, 73]

man_ori_coordinates:
  camera_0:
    point_1: {x: 1009.0, y: 608.0}
    point_2: {x: 979.0, y: 335.0}
    # ... more points
  camera_1:
    point_1: {x: 1002.0, y: 609.0}
    # ... more points
```

## Calibration Quality Assessment

### Residual Analysis

Good calibration typically shows:
- **RMS residuals < 0.5 pixels** for each camera
- **Consistent residuals** across all cameras
- **No systematic patterns** in residual distribution

### Visual Inspection

Check calibration quality by:
1. Examining the 3D visualization of calibrated cameras
2. Verifying that detected points align with known target geometry
3. Testing 3D reconstruction with known test points

## Troubleshooting Calibration Issues

### Common Problems

**Problem**: Points not detected automatically
**Solution**: 
- Adjust detection parameters in `detect_plate` section
- Use manual point picking
- Improve image quality/contrast

**Problem**: High calibration residuals
**Solution**:
- Check target coordinate file accuracy
- Verify image quality and focus
- Ensure stable camera mounting
- Re-examine manual point selections

**Problem**: Inconsistent results between cameras
**Solution**:
- Check that all cameras use the same coordinate system
- Verify synchronization between cameras
- Examine individual camera calibrations

### Detection Parameters

Fine-tune detection in the `detect_plate` section:

```yaml
detect_plate:
  gvth_1: 40      # Threshold for camera 1
  gvth_2: 40      # Threshold for camera 2
  gvth_3: 40      # Threshold for camera 3
  gvth_4: 40      # Threshold for camera 4
  min_npix: 25    # Minimum pixel count
  max_npix: 400   # Maximum pixel count
  size_cross: 3   # Cross correlation size
  sum_grey: 100   # Minimum sum of grey values
  tol_dis: 500    # Distance tolerance
```

## Best Practices

### Target Design
- Use high-contrast markers (black dots on white background)
- Ensure markers are clearly visible from all camera angles
- Include sufficient markers for robust calibration (>10 points)
- Distribute markers throughout the measurement volume

### Image Quality
- Use adequate lighting to avoid shadows
- Ensure all cameras are in focus
- Minimize motion blur during image capture
- Use appropriate exposure settings

### Camera Setup
- Mount cameras rigidly to prevent movement
- Choose camera positions that minimize occlusion
- Ensure good coverage of the measurement volume
- Avoid extreme viewing angles

## File Outputs

Successful calibration generates:

```
cal/
├── cam1.tif.ori     # Camera 1 calibration parameters
├── cam2.tif.ori     # Camera 2 calibration parameters  
├── cam3.tif.ori     # Camera 3 calibration parameters
├── cam4.tif.ori     # Camera 4 calibration parameters
├── cam1.tif.addpar  # Additional parameters (distortion, etc.)
├── cam2.tif.addpar
├── cam3.tif.addpar
└── cam4.tif.addpar
```

These files contain the intrinsic and extrinsic camera parameters needed for 3D reconstruction.

## See Also

- [Quick Start Guide](quick-start.md)
- [YAML Parameters Guide](yaml-parameters.md)
- [Examples](examples.md)
- [GUI Usage Guide](running-gui.md)
