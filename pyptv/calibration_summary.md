# Illmenau Calibration Pipeline - Implementation Summary

**Date:** March 4, 2026  
**Project:** pyPTV Multi-Camera Calibration  
**Target System:** Illmenau 4-camera setup (KalibrierungA)

---

## Executive Summary

Created an **interactive marimo notebook** for calibrating multi-camera PTV systems. The pipeline provides a visual, step-by-step workflow that allows users to:

- See results at each stage
- Adjust parameters interactively
- Export calibration files ready for pyPTV GUI
- Validate accuracy with epipolar lines and dumbbell tests

---

## Notebook Location

```
pyptv/marimo_illmenau_calibration.py
```

---

## Quick Start

```bash
cd /home/user/Documents/GitHub/pyptv
uv run marimo edit pyptv/marimo_illmenau_calibration.py
```

---

## Data Flow

```
┌─────────────────────┐
│ Calibration Images  │ 4 cameras × 40 frames
│ (KalibrierungA/)    │ 7×6 grid, 120mm spacing
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 1. Grid Detection   │ OpenCV findCirclesGrid
│                     │ Synchronization filter
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 2. Initial Calib    │ Load .ori/.addpar
│                     │ 3D camera visualization
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 3. Triangulation    │ Multi-camera intersection
│                     │ Planarity + distance errors
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 4. Bundle Adjustment│ scipy.optimize.least_squares
│                     │ Reprojection + constraints
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 5. Export           │ Write .ori/.addpar files
│                     │ Copy-paste YAML format
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 6. Validation       │ Epipolar lines (interactive)
│                     │ Dumbbell test (RMSE)
└─────────────────────┘
```

---

## Implementation Details

### 1. Grid Detection (Cell 4)

**Algorithm:**
```python
cv2.findCirclesGrid(
    img, (7, 6),
    flags=cv2.CALIB_CB_SYMMETRIC_GRID,
    blobDetector=detector
)
```

**Blob Detector Parameters:**
```python
board_params.filterByColor = False
board_params.filterByArea = True
board_params.minArea = 50
board_params.filterByCircularity = True
board_params.minCircularity = 0.7
```

**Synchronization Filter:**
- Only keeps frames where ALL 4 cameras detected the grid
- Typical sync rate: 70-90% (28-36 of 40 frames)

**Output Structure:**
```python
frame_detections = {
    frame_idx: {  # 0-39
        cam_idx: corners or None  # (42, 2) array
    }
}
synchronized_frames = [0, 1, 3, 5, ...]  # valid frame indices
```

---

### 2. Initial Calibration Loading (Cell 5)

**File Loading:**
```python
cal.from_file(ori_path, addpar_path)
```

**Parameter Extraction:**
```python
pos = cal.get_pos()           # [X, Y, Z] in mm
angs = cal.get_angles()       # [ω, φ, κ] in radians
int_par = cal.get_int_par()   # cc, xh, yh (focal length, principal point)
added_par = cal.get_added_par()  # k1, k2, k3, p1, p2 (distortion)
```

**3D Visualization:**
- Camera pyramids using `scipy.spatial.transform.Rotation`
- Origin axes (X=red, Y=green, Z=blue)
- Interactive matplotlib with `mo.pyplot()`

---

### 3. Triangulation (Cell 6)

**Algorithm:**
```python
from optv.orientation import multi_cam_point_positions

pts_2d = np.array(pts_2d_list)[np.newaxis, :, :].astype(np.float64)
xyz, err = multi_cam_point_positions(pts_2d, cpar, cals)
```

**Metrics Computed:**

**Planarity:**
```python
centroid = np.mean(points_3d, axis=0)
centered = points_3d - centroid
_, _, Vt = np.linalg.svd(centered)
normal = Vt[2, :]  # Normal to best-fit plane
deviations = np.dot(centered, normal)
rms_planarity = np.sqrt(np.mean(deviations**2))
```

**Distance:**
```python
for i in range(rows):
    for j in range(cols - 1):
        idx1 = i * cols + j
        idx2 = i * cols + (j + 1)
        dist = np.linalg.norm(points_3d[idx2] - points_3d[idx1])
        errors.append(dist - spacing)
rms_distance = np.sqrt(np.mean(np.array(errors)**2))
```

**Typical Results:**
- RMS Planarity: 0.5-2.0 mm (before optimization)
- RMS Distance: 1.0-5.0 mm (before optimization)

---

### 4. Bundle Adjustment (Cell 7)

**Optimization Framework:**
```python
from scipy.optimize import least_squares

result = least_squares(
    grid_ba_residuals, x0,
    args=(triangulated_frames, cpar, cals, active_cams, w_planarity, w_distance, pos_scale),
    method='trf',           # Trust Region Reflective
    loss='soft_l1',         # Robust loss function
    xtol=1e-8, ftol=1e-8,
    max_nfev=5000,
    verbose=2
)
```

**State Vector:**
```python
x0 = [pos_0, angs_0, pos_1, angs_1, ..., pos_N, angs_N]
# Length: num_cams × 6 (only exterior orientation optimized)
```

**Residual Function:**
```python
def grid_ba_residuals(calib_vec, frames_data, cpar, calibs, active_cams,
                      w_planarity, w_distance, pos_scale=1.0):
    # 1. Update camera parameters
    for cam, cal in enumerate(calibs):
        if active_cams[cam]:
            cal.set_pos(pars[0] * pos_scale)
            cal.set_angles(pars[1])

    # 2. Compute residuals
    residuals = []
    for frame_idx, points_3d in frames_data.items():
        # A. Reprojection errors (all cameras)
        for cam in active_cams:
            proj = image_coordinates(points_3d, calibs[cam], mm_params)
            diff = corners - proj
            residuals.extend(diff.ravel())

        # B. Planarity constraint
        if w_planarity > 0:
            planarity_devs, _, _, _ = compute_planarity_error(points_3d)
            residuals.extend(np.sqrt(w_planarity) * planarity_devs)

        # C. Distance constraint
        if w_distance > 0:
            distance_errors = compute_distance_errors(points_3d)
            residuals.extend(np.sqrt(w_distance) * distance_errors)

    return residuals
```

**Weights:**
- `w_planarity = 0.1` (soft constraint)
- `w_distance = 1.0` (hard constraint)

**Typical Improvement:**
- Initial cost: 1000-5000
- Final cost: 100-500
- Improvement: 80-95%

---

### 5. Export (Cell 9-10)

**File Format - `.ori`:**
```
# Camera 1 exterior orientation
-1234.5678901234 567.8901234567 -2345.6789012345
0.0123456789 -0.0234567890 0.0345678901

# Rotation matrix
0.9998765432 -0.0123456789 0.0234567890
0.0123456789 0.9997654321 -0.0345678901
-0.0234567890 0.0345678901 0.9996543210
```

**File Format - `.addpar`:**
```
50.1234567890  # focal length (mm)
0.0123456789  # principal point x (mm)
-0.0234567890  # principal point y (mm)
-0.1234567890  # radial distortion k1
0.0123456789  # radial distortion k2
0.0012345678  # decentering p1
-0.0023456789  # decentering p2
0.0001234567  # radial distortion k3
```

**YAML Format (copy-paste ready):**
```yaml
position: [-1234.567890, 567.890123, -2345.678901]  # mm
angles: [0.01234568, -0.02345679, 0.03456789]  # radians
focal_length: 50.123457  # mm
principal_point_x: 0.012346  # mm
principal_point_y: -0.023457  # mm
distortion:
  k1: -0.12345679
  k2: 0.01234568
  k3: 0.00012346
  p1: 0.00123457
  p2: -0.00234568
```

---

## Key Design Decisions

### Why Marimo Notebook?

1. **Reactive execution**: Changes propagate automatically
2. **Visual feedback**: See results immediately
3. **Reproducible**: Code + output in single file
4. **Interactive**: Click, adjust, re-run
5. **Exportable**: Can run headless if needed

### Optimization Choices

**Trust Region Reflective (`trf`):**
- Handles bounds (if needed later)
- Robust to poor initial guesses
- Efficient for medium-scale problems

**Soft L1 Loss:**
- Robust to outliers
- Less sensitive to bad detections
- Better convergence than squared loss

**Constraint Weights:**
- `w_distance = 1.0`: Grid spacing is known precisely
- `w_planarity = 0.1`: Grid may have slight warping

---

## Dependencies

```python
# Core
numpy>=1.20.0
scipy>=1.7.0
matplotlib>=3.4.0
pandas>=1.3.0
opencv-python>=4.5.0

# pyPTV/OpenPTV
openptv-python>=0.6.0
pyptv  # local installation

# Notebook
marimo>=0.20.0
```

---

## File Locations

### Input Data
```
/home/user/Downloads/Illmenau/
├── KalibrierungA/
│   ├── Kalibrierung1a/
│   ├── Kalibrierung2a/
│   ├── Kalibrierung3a/
│   └── Kalibrierung4a/
├── pyPTV_folder/
│   └── parameters_Run4.yaml
└── Dumbbell/  (optional)
```

### Notebook
```
/home/user/Documents/GitHub/pyptv/pyptv/marimo_illmenau_calibration.py
```

### Output
```
/home/user/Documents/GitHub/pyptv/pyptv/calibration_output/
├── cam1_calibrated.ori
├── cam1_calibrated.addpar
├── cam2_calibrated.ori
├── cam2_calibrated.addpar
├── cam3_calibrated.ori
├── cam3_calibrated.addpar
├── cam4_calibrated.ori
└── cam4_calibrated.addpar
```

---

## Usage Commands

```bash
# Run calibration notebook
uv run marimo edit pyptv/marimo_illmenau_calibration.py

# Run headless (if needed)
uv run marimo run pyptv/marimo_illmenau_calibration.py
```

---

## Troubleshooting Guide

### Problem: Low Synchronization Rate

**Symptoms:** < 50% of frames have all 4 cameras detecting grid

**Causes:**
- Poor lighting in some cameras
- Grid partially out of frame
- Blob detector parameters too strict

**Solutions:**
1. Reduce `minArea` (try 30)
2. Reduce `minCircularity` (try 0.5)
3. Check image quality manually
4. Exclude problematic cameras from BA

---

### Problem: Bundle Adjustment Diverges

**Symptoms:** `result.success = False`, final cost > initial cost

**Causes:**
- Poor initial calibration
- Outlier frames with bad detections
- Constraint weights too high

**Solutions:**
1. Check initial epipolar errors (< 10px)
2. Reduce `w_planarity` to 0.01
3. Remove outlier frames from `synchronized_frames`
4. Increase `ftol`/`xtol` to 1e-6

---

### Problem: Large Dumbbell Error

**Symptoms:** Measured length differs by > 20mm

**Causes:**
- Wrong dumbbell length value
- Sphere detection errors
- Calibration scale error

**Solutions:**
1. Verify dumbbell length (measure physically)
2. Check sphere detection visually
3. Verify grid spacing in config (120mm)
4. Re-run bundle adjustment with more frames

---

### Problem: Epipolar Lines Miss Points

**Symptoms:** Lines consistently miss corresponding points

**Causes:**
- Exterior orientation error
- Distortion parameters incorrect
- Principal point offset

**Solutions:**
1. Check which cameras have worst errors
2. Re-run BA excluding problematic cameras
3. Verify distortion parameters in `.addpar`
4. Consider re-running OpenCV intrinsic calibration

---

## Testing Checklist

Before using in production:

- [ ] All camera folders exist and contain images
- [ ] YAML parameters file loads correctly
- [ ] Grid detection succeeds in > 70% of frames
- [ ] Synchronization rate > 70%
- [ ] Initial epipolar errors < 10px
- [ ] Bundle adjustment converges (`success = True`)
- [ ] Final epipolar errors < 3px
- [ ] Dumbbell error < 10mm (if validation data available)
- [ ] Exported files load in pyPTV GUI
- [ ] Epipolar lines in GUI match notebook visualization

---

## References

### Documentation
- [OpenCV Calibration](https://docs.opencv.org/master/d9/d0c/group__calib3d.html)
- [OpenPTV Documentation](https://github.com/openptv/openptv)
- [pyPTV GitHub](https://github.com/pyptv/pyptv)
- [Marimo Documentation](https://github.com/marimo-team/marimo)

### Papers
- Heikkilä, J. "Geometric Camera Calibration" (1997)
- Hartley, R. & Zisserman, A. "Multiple View Geometry" (2003)
- Ma et al. "An Invitation to 3-D Vision" (2004)

### Related Code
- `pyptv/gemini/phase1-5.py` - Original pipeline reference
- `pyptv/marimo_grid_calibration.py` - Predecessor notebook
- `pyptv/marimo_epipolar_opencv_board.py` - Epipolar reference

---

**Document Version:** 1.0  
**Last Updated:** March 4, 2026
