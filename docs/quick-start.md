# Quick Start Guide

Get up and running with PyPTV using the included test dataset in under 10 minutes.

## Prerequisites

- PyPTV installed and working (see [Installation Guide](installation.md))
- Basic familiarity with particle tracking concepts

## Overview

This guide walks you through:
1. **Loading test data** - Use the included test_cavity experiment
2. **Running the GUI** - Launch and navigate the PyPTV interface
3. **Viewing calibration** - Check camera calibration
4. **Processing images** - Detect and track particles
5. **Exporting results** - Save tracking data

## Step 1: Activate PyPTV

Open your terminal (or Anaconda Prompt on Windows) and activate the PyPTV environment:

```bash
conda activate pyptv
cd /path/to/pyptv  # Navigate to your PyPTV installation
```

## Step 2: Launch the GUI

Start the PyPTV graphical interface:

```bash
python -m pyptv.pyptv_gui
```

The main PyPTV window should open with a parameter tree on the left and camera views on the right.

## Step 3: Load Test Data

The test_cavity experiment is included with PyPTV and provides a complete working example.

1. **Load the experiment**:
   - In the GUI, go to **File → Load Experiment**
   - Navigate to `tests/test_cavity/`
   - Select `parameters_Run1.yaml`
   - Click **Open**

2. **Verify loading**:
   - The parameter tree should now show "Run1" with expandable sections
   - You should see 4 camera tabs at the bottom
   - Status bar should show "Experiment loaded successfully"

## Step 4: Initialize Parameters

1. **Load images and parameters**:
   - Click **"Load images/parameters"** button
   - This reads all configuration and prepares the cameras
   - Camera views should show calibration images

2. **Check the setup**:
   - **Camera count**: 4 cameras (cam1, cam2, cam3, cam4)
   - **Image format**: TIFF calibration images
   - **Parameters**: Detection thresholds, tracking parameters loaded

## Step 5: Explore Calibration

The test_cavity experiment comes with pre-calculated camera calibrations:

1. **View calibration**:
   - Go to **Calibration → Open Calibration** (or click the calibration button)
   - The calibration GUI opens showing camera positions and target images

2. **Check calibration quality**:
   - Click **"Load images/parameters"** in calibration GUI
   - Click **"Show initial guess"** to see projected calibration points
   - Observe how well points align with detected features

## Step 6: Detect Particles

Return to the main GUI and detect particles in the sequence:

1. **Go to Sequence Processing**:
   - In the main GUI, ensure parameters are loaded
   - Click **"Detection"** button
   - This detects particles in all camera views for the current frame

2. **Review detection results**:
   - Blue crosses appear on detected particles
   - Check all 4 camera views for reasonable particle detection
   - Particles should be clearly marked on the images

## Step 7: Find Correspondences

Find matching particles across cameras:

1. **Run correspondence**:
   - Click **"Correspondences"** button
   - This matches particles between camera views
   - Look for colored lines connecting corresponding particles

2. **Check results**:
   - Good correspondences show consistent particle matches
   - Status bar shows number of correspondences found

## Step 8: Determine 3D Positions

Calculate 3D particle positions:

1. **Run determination**:
   - Click **"Determination"** button
   - This triangulates 3D positions from 2D correspondences
   - Results are saved to files

2. **View output files**:
   - Check the experiment directory for result files
   - Look for files like `rt_is.XXXXX` with 3D positions

## Step 9: Process Sequence (Optional)

For multiple frames:

1. **Set frame range**:
   - Adjust sequence parameters if needed
   - Set first and last frame numbers

2. **Run sequence**:
   - Click **"Sequence"** button
   - This processes the entire image sequence
   - Progress is shown in the status bar

## Understanding the Test Data

The test_cavity experiment includes:

### Directory Structure
```
test_cavity/
├── parameters_Run1.yaml     # Main parameter file
├── cal/                     # Calibration data
│   ├── cam1.tif            # Calibration images
│   ├── cam1.tif.ori        # Camera orientations
│   ├── cam1.tif.addpar     # Additional parameters
│   └── target_on_a_side.txt # Calibration target coordinates
├── img/                     # Image sequences
│   ├── cam1.10000          # Frame images
│   ├── cam1.10001
│   └── ...
└── plugins/                 # Custom processing plugins
```

### Key Parameters
- **4 cameras** in a stereo configuration
- **Calibration target** with known 3D coordinates
- **Particle detection** tuned for dark particles on bright background
- **Tracking parameters** set for moderate particle velocities

## Typical Results

After processing, you should see:
- **~20-50 particles** detected per camera per frame
- **~10-30 correspondences** per frame
- **3D positions** with coordinate accuracy of ~0.1 mm
- **Tracking data** suitable for velocity analysis

## Next Steps

Now that you've successfully run the test case:

1. **Learn calibration**: Follow the [Calibration Guide](calibration.md)
2. **Set up your own experiment**: See [Parameter Migration](parameter-migration.md)
3. **Explore plugins**: Check out the [Plugins Guide](plugins.md)
4. **Use advanced features**: Try [Splitter Mode](splitter-mode.md)

## Common Issues

### "No images found"
- **Check file paths** in the YAML parameter file
- **Verify image format** (should match what's in img/ directory)

### "Calibration failed"
- **Calibration files missing** - check cal/ directory
- **Try the calibration GUI** to debug calibration issues

### "No particles detected"
- **Adjust detection thresholds** in detect_plate parameters
- **Check image quality** - particles should be clearly visible

### "Poor correspondences"
- **Check calibration quality** first
- **Adjust correspondence tolerances** in criteria parameters

## Performance Tips

- **RAM usage**: Large image sequences require significant memory
- **Disk space**: Allow ~1GB per 1000 frames for results
- **Processing time**: Expect ~1-10 seconds per frame depending on particle count

---

**Success!** You've completed your first PyPTV analysis. Ready to set up your own experiment? See [Parameter Migration](parameter-migration.md) to convert your existing setup.

---

**Next**: [Running the GUI](running-gui.md) or [Calibration Guide](calibration.md)
