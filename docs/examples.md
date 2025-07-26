# Examples and Workflows

This guide provides practical examples and common workflows for using PyPTV effectively.

## Test Cavity Example

The test_cavity example is included with PyPTV and demonstrates a complete 4-camera PTV setup.

### Location and Setup

```bash
cd tests/test_cavity
ls -la
```

You'll find:
```
test_cavity/
├── parameters_Run1.yaml     # Main parameter file
├── cal/                     # Calibration data
│   ├── cam1.tif - cam4.tif # Calibration images
│   ├── *.ori               # Calibration results
│   ├── *.addpar            # Additional parameters
│   └── target_on_a_side.txt # Target coordinates
├── img/                     # Image sequence
│   ├── cam1.10001 - cam1.10004
│   ├── cam2.10001 - cam2.10004
│   ├── cam3.10001 - cam3.10004
│   └── cam4.10001 - cam4.10004
└── plugins/                 # Example plugins
    ├── ext_sequence_*.py
    └── ext_tracker_*.py
```

### Running the Test Cavity Example

1. **Navigate to the test directory**
   ```bash
   cd tests/test_cavity
   ```

2. **Start PyPTV GUI**
   ```bash
   python -m pyptv
   ```

3. **Load the experiment**
   - File → Open Experiment
   - Select `parameters_Run1.yaml`

4. **Explore the setup**
   - View calibration images: Tools → Calibration
   - Check detection: Tools → Detection
   - Run tracking: Process → Track Particles

### Key Learning Points

The test_cavity example demonstrates:

- **4-camera setup** with proper calibration
- **Correct YAML structure** with `num_cams: 4`
- **Plugin system** usage
- **Complete workflow** from calibration to tracking

## Common Workflows

### Workflow 1: New Experiment Setup

Starting a new PTV experiment from scratch.

#### Step 1: Create Directory Structure

```bash
mkdir my_experiment
cd my_experiment

# Create subdirectories
mkdir cal img results

# Copy template from test_cavity
cp tests/test_cavity/parameters_Run1.yaml parameters_my_experiment.yaml
```

#### Step 2: Modify Parameters

Edit `parameters_my_experiment.yaml`:

```yaml
num_cams: 3  # Adjust for your camera count

sequence:
  base_name:
    - img/cam1.%d
    - img/cam2.%d  
    - img/cam3.%d
  first: 1
  last: 100

cal_ori:
  img_cal_name:
    - cal/cam1_cal.tif
    - cal/cam2_cal.tif
    - cal/cam3_cal.tif
  fixp_name: cal/my_target.txt
```

#### Step 3: Add Your Data

```bash
# Copy calibration images
cp /path/to/calibration/cam1.tif cal/cam1_cal.tif
cp /path/to/calibration/cam2.tif cal/cam2_cal.tif
cp /path/to/calibration/cam3.tif cal/cam3_cal.tif

# Copy image sequence
cp /path/to/sequence/cam1_* img/
cp /path/to/sequence/cam2_* img/
cp /path/to/sequence/cam3_* img/

# Create target coordinate file
cat > cal/my_target.txt << EOF
# X     Y     Z     ID
-30.0  -30.0  0.0   1
 30.0  -30.0  0.0   2
 30.0   30.0  0.0   3
-30.0   30.0  0.0   4
EOF
```

#### Step 4: Run Calibration

1. Open PyPTV GUI
2. Load your parameter file
3. Tools → Calibration
4. Detect calibration points
5. Run calibration
6. Check residuals

#### Step 5: Process Sequence

1. Tools → Detection (test on single frame)
2. Process → Correspondences
3. Process → Track Particles
4. Analyze results

### Workflow 2: Parameter Optimization

Optimizing parameters for better tracking results.

#### Detection Optimization

Start with conservative detection parameters:

```yaml
detect_plate:
  gvth_1: 50    # Start higher, reduce if too few particles
  gvth_2: 50
  gvth_3: 50
  min_npix: 20  # Minimum particle size
  max_npix: 200 # Maximum particle size
```

Test detection on a representative frame:
1. Tools → Detection
2. Adjust thresholds in real-time
3. Save optimized values to YAML

#### Tracking Optimization

Adjust tracking parameters based on your flow:

```yaml
track:
  # For slow flows
  dvxmax: 5.0
  dvxmin: -5.0
  dvymax: 5.0
  dvymin: -5.0
  dvzmax: 2.0
  dvzmin: -2.0
  
  # For fast flows
  dvxmax: 50.0
  dvxmin: -50.0
  # ... etc
```

### Workflow 3: Multi-Plane Calibration

For large measurement volumes or improved accuracy.

#### Setup Multi-Plane Configuration

```yaml
multi_planes:
  n_planes: 3
  plane_name:
    - cal/plane_front
    - cal/plane_middle  
    - cal/plane_back
```

#### Calibration Process

1. Take calibration images at multiple Z positions
2. Configure plane parameters
3. Run calibration for each plane
4. Combine results for improved 3D accuracy

### Workflow 4: Using Plugins

PyPTV supports plugins for extended functionality.

#### Available Plugins

Check available plugins in your parameter file:

```yaml
plugins:
  available_tracking:
    - default
    - ext_tracker_splitter    # For splitter systems
  available_sequence:
    - default
    - ext_sequence_rembg      # Background removal
    - ext_sequence_contour    # Contour detection
  selected_tracking: default
  selected_sequence: default
```

#### Background Removal Plugin

To use background removal:

1. Install dependencies:
   ```bash
   pip install rembg[cpu]  # or rembg[gpu]
   ```

2. Enable in parameters:
   ```yaml
   plugins:
     selected_sequence: ext_sequence_rembg
   ```

3. The plugin will automatically remove backgrounds during processing

#### Splitter System Plugin

For splitter-based stereo systems:

```yaml
plugins:
  selected_tracking: ext_tracker_splitter

ptv:
  splitter: true

cal_ori:
  cal_splitter: true
```

## Troubleshooting Common Issues

### Issue: Poor Calibration Quality

**Symptoms**: High residuals, tracking errors

**Solutions**:
1. Check target coordinate file accuracy
2. Improve calibration image quality
3. Use more calibration points
4. Verify camera stability

### Issue: Few or No Particles Detected

**Symptoms**: Empty detection results

**Solutions**:
1. Lower detection thresholds
2. Check image contrast
3. Verify image file paths
4. Adjust min/max pixel counts

### Issue: Poor Tracking Performance

**Symptoms**: Broken trajectories, false matches

**Solutions**:
1. Optimize detection parameters first
2. Adjust velocity limits
3. Check correspondence criteria
4. Improve temporal resolution

### Issue: Memory or Performance Problems

**Symptoms**: Slow processing, crashes

**Solutions**:
1. Process smaller batches
2. Reduce image resolution if possible
3. Use efficient file formats
4. Close unnecessary applications

## Data Analysis Examples

### Basic Trajectory Analysis

After tracking, analyze results with Python:

```python
import numpy as np
import matplotlib.pyplot as plt

# Load tracking results (format depends on output)
# trajectories = load_trajectories('results/trajectories.txt')

# Example analysis
# velocities = compute_velocities(trajectories)
# plot_velocity_field(velocities)
```

### Statistical Analysis

```python
# Compute flow statistics
# mean_velocity = np.mean(velocities, axis=0)
# velocity_fluctuations = velocities - mean_velocity
# turbulent_intensity = np.std(velocity_fluctuations, axis=0)
```

## Best Practices Summary

### Experimental Setup
- Use stable camera mounts
- Ensure good lighting and contrast
- Take high-quality calibration images
- Include sufficient calibration points

### Parameter Configuration
- Start with test_cavity as template
- Use only `num_cams`, never `n_img`
- Test parameters on single frames first
- Document parameter changes

### Processing Workflow
- Always calibrate first
- Validate detection on test frames
- Process in small batches initially
- Monitor intermediate results

### Data Management
- Use consistent file naming
- Backup original data
- Document processing parameters
- Archive final results

## See Also

- [Quick Start Guide](quick-start.md)
- [Calibration Guide](calibration.md)
- [YAML Parameters Guide](yaml-parameters.md)
- [GUI Usage Guide](running-gui.md)
