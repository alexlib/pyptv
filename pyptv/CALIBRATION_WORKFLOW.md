# Interactive Calibration Workflow for pyPTV

A suite of **marimo notebooks** for interactive multi-camera calibration, designed for the Illmenau 4-camera setup but adaptable to other configurations.

## Overview

This calibration pipeline provides an **interactive, visual approach** to camera calibration:

1. **Detect** calibration grid points in synchronized images
2. **Triangulate** 3D positions using initial calibration
3. **Refine** with bundle adjustment (planarity + distance constraints)
4. **Export** calibration files for pyPTV GUI
5. **Validate** with epipolar lines and dumbbell test

## Notebooks

| Notebook | Purpose | Key Features |
|----------|---------|--------------|
| [`marimo_illmenau_calibration.py`](./marimo_illmenau_calibration.py) | **Main calibration workflow** | Grid detection, triangulation, bundle adjustment, export |
| [`marimo_epipolar_visualization.py`](./marimo_epipolar_visualization.py) | **Epipolar line verification** | Interactive click-to-draw epipolar lines, error statistics |
| [`marimo_dumbbell_validation.py`](./marimo_dumbbell_validation.py) | **Accuracy validation** | Dumbbell length measurement, RMSE calculation |

## Quick Start

### 1. Install Dependencies

```bash
# Ensure marimo is installed
pip install marimo

# Install required packages
pip install opencv-python scipy matplotlib pandas numpy
```

### 2. Run the Main Calibration Notebook

```bash
marimo edit pyptv/marimo_illmenau_calibration.py
```

This opens the notebook in your browser. Run cells sequentially:

1. **Configuration** - Verify paths to your calibration images
2. **Grid Detection** - Detects 7×6 grid in all cameras, shows synchronized frames
3. **Initial Calibration** - Loads existing `.ori`/`.addpar` files
4. **Triangulation** - Computes 3D grid positions, shows planarity/distance errors
5. **Bundle Adjustment** - Optimizes camera parameters with constraints
6. **Export** - Generates new `.ori`/`.addpar` files ready for pyPTV GUI

### 3. Verify with Epipolar Visualization

```bash
marimo edit pyptv/marimo_epipolar_visualization.py
```

- **Right-click** on any grid point
- Epipolar lines appear in other camera views
- Check if lines pass through corresponding points
- View epipolar distance error statistics

### 4. Validate with Dumbbell Test (Optional)

```bash
marimo edit pyptv/marimo_dumbbell_validation.py
```

- Load dumbbell images with known sphere distance
- Automatically detects spheres and triangulates 3D positions
- Reports measured vs. actual distance
- Quality assessment: < 5mm = excellent, > 20mm = recalibrate

## Data Structure

### Expected Folder Layout

```
/Illmenau/
├── KalibrierungA/
│   ├── Kalibrierung1a/  # Camera 1 images
│   │   ├── 00000000_*.tif
│   │   ├── 00000001_*.tif
│   │   └── ...
│   ├── Kalibrierung2a/  # Camera 2
│   ├── Kalibrierung3a/  # Camera 3
│   └── Kalibrierung4a/  # Camera 4
├── pyPTV_folder/
│   ├── parameters_Run4.yaml
│   └── cal/
│       ├── cam1.tif.ori
│       ├── cam1.tif.addpar
│       └── ...
└── Dumbbell/  # Optional validation images
    ├── frame_0001_cam1.tif
    ├── frame_0001_cam2.tif
    └── ...
```

### Configuration

The notebook uses these defaults for Illmenau Run 4:

```python
CALIB_BASE = "/home/user/Downloads/Illmenau/KalibrierungA"
CAMERA_FOLDERS = {
    0: "Kalibrierung1a",  # Camera 1
    1: "Kalibrierung2a",  # Camera 2
    2: "Kalibrierung3a",  # Camera 3
    3: "Kalibrierung4a",  # Camera 4
}
GRID_ROWS = 7
GRID_COLS = 6
GRID_SPACING_MM = 120.0  # mm between adjacent dots
NUM_FRAMES = 40
```

Modify these in the first code cell if your setup differs.

## Workflow Details

### Step 1: Grid Detection

- Uses OpenCV's `findCirclesGrid` with symmetric grid flag
- Detects 42 points (7×6) per camera per frame
- **Synchronization filter**: Only keeps frames where ALL cameras detected the grid
- Displays detection rate and sample visualizations

### Step 2: Initial Calibration

- Loads camera parameters from `.ori` (exterior) and `.addpar` (interior + distortion) files
- Visualizes camera positions as 3D pyramids
- Shows initial reprojection errors

### Step 3: Triangulation

- For each synchronized frame:
  - Triangulates all 42 grid points using multi-camera intersection
  - Computes planarity error (how flat is the grid?)
  - Computes distance error (are adjacent points 120mm apart?)
- Displays per-frame and aggregate statistics

### Step 4: Bundle Adjustment

Optimizes camera exterior orientation (position + angles) using:

- **Reprojection error**: Minimize 2D projection error (all cameras, all frames)
- **Planarity constraint**: All 42 points must lie on a single plane
- **Distance constraint**: Adjacent points must be exactly 120mm apart

Weights:
- `w_planarity = 0.1` (soft constraint)
- `w_distance = 1.0` (hard constraint)

Shows before/after comparison and improvement percentage.

### Step 5: Export

Generates two files per camera:

- `camN_calibrated.ori` - Exterior orientation (position + angles + rotation matrix)
- `camN_calibrated.addpar` - Interior + distortion parameters

Also provides **copy-paste ready YAML** format for easy integration.

## Quality Metrics

### Epipolar Distance Error

| Range | Quality | Action |
|-------|---------|--------|
| < 1 px | Excellent | Ready for production |
| 1-3 px | Good | Acceptable for most work |
| 3-5 px | Fair | Consider refinement |
| > 5 px | Poor | Recalibrate recommended |

### Dumbbell Validation

| Error | Quality | Action |
|-------|---------|--------|
| < 5mm | Excellent | Highly accurate calibration |
| 5-10mm | Good | Acceptable for most applications |
| 10-20mm | Fair | Consider refinement for precision work |
| > 20mm | Poor | Recalibration required |

### Planarity Error

Should be < 1mm RMS for a well-calibrated system with a flat grid.

### Distance Error

Should be < 2mm RMS for adjacent grid points (known spacing: 120mm).

## Troubleshooting

### Grid Detection Fails

**Symptoms:** Low synchronization rate, many frames rejected

**Solutions:**
- Adjust blob detector parameters (minArea, minCircularity)
- Check image quality (lighting, focus, contrast)
- Verify grid orientation (try `CALIB_CB_ASYMMETRIC_GRID` if needed)

### Large Epipolar Errors

**Symptoms:** Epipolar lines miss corresponding points by > 5px

**Solutions:**
- Check initial calibration files are correct
- Increase bundle adjustment iterations (`max_nfev`)
- Adjust constraint weights (increase `w_distance`)
- Remove outlier frames from triangulation

### Dumbbell Validation Fails

**Symptoms:** Measured length differs from actual by > 20mm

**Solutions:**
- Verify dumbbell length value is correct
- Check sphere detection (adjust blob params)
- Ensure dumbbell is fully visible in all cameras
- Try multiple frames, exclude outliers

### Optimization Doesn't Converge

**Symptoms:** `result.success = False`, high final cost

**Solutions:**
- Provide better initial guess (use OpenCV calibration first)
- Reduce constraint weights temporarily
- Increase `ftol`/`xtol` tolerance
- Try different optimization method (`'lm'` instead of `'trf'`)

## Tips for Best Results

1. **Use high-quality images**: Good lighting, sharp focus, minimal noise
2. **Cover the volume**: Calibration grid should span the full measurement volume
3. **Multiple orientations**: If possible, capture grid at different angles
4. **Check synchronization**: Ensure all cameras trigger simultaneously
5. **Validate early**: Run epipolar check before bundle adjustment
6. **Iterate**: Refine parameters based on validation results

## Integration with pyPTV GUI

After running the calibration notebook:

1. Copy generated `.ori` and `.addpar` files to your experiment folder
2. Update YAML to point to new calibration files:
   ```yaml
   cal_ori:
     img_ori:
       - cal/cam1_calibrated.ori
       - cal/cam2_calibrated.ori
       - cal/cam3_calibrated.ori
       - cal/cam4_calibrated.ori
   ```
3. Open pyPTV GUI and load parameters
4. Run epipolar line verification in GUI
5. Proceed with particle tracking

## Advanced Usage

### Custom Grid Configuration

Modify in the first code cell:

```python
GRID_ROWS = 9  # Your grid rows
GRID_COLS = 7  # Your grid columns
GRID_SPACING_MM = 100.0  # Your spacing in mm
```

### Adding Custom Constraints

Edit `grid_ba_residuals()` to add:

```python
# Example: Add scale constraint
if w_scale > 0:
    scale_error = compute_scale_error(points_3d, known_dimension)
    residuals.extend(np.sqrt(w_scale) * scale_error)
```

### Batch Processing

For multiple calibration sessions:

```python
# Run notebook programmatically
import marimo as mo
app = mo.load_notebook('marimo_illmenau_calibration.py')
app.run()
```

## See Also

- [pyPTV Documentation](https://github.com/pyptv/pyptv)
- [OpenPTV Documentation](https://github.com/openptv/openptv)
- [Marimo Documentation](https://github.com/marimo-team/marimo)
- [OpenCV Calibration Documentation](https://docs.opencv.org/master/d9/d0c/group__calib3d.html)

## License

Part of the pyPTV project. See main repository for license details.
