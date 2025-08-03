# Splitter Mode Guide

This guide covers PyPTV's splitter mode functionality for stereo camera systems using beam splitters.

## Overview

Splitter mode is designed for stereo PTV systems where a single camera is split using a beam splitter to create two views of the same region. This technique is commonly used to achieve stereo vision with a single camera sensor.

## Environment Setup and Testing

PyPTV uses a modern conda environment (`environment.yml`) and separates tests into headless (`tests/`) and GUI (`tests_gui/`) categories. See the README for details.

## When to Use Splitter Mode

Use splitter mode when:
- You have a beam splitter-based stereo system
- Single camera sensor captures multiple views
- Views are arranged side-by-side or top-bottom on the sensor
- You need stereo 3D tracking with limited camera hardware

## Configuration

### Basic Splitter Setup

Enable splitter mode in your YAML configuration:

```yaml
num_cams: 4  # Even though it's one physical camera

ptv:
  splitter: true
  imx: 512      # Half width - will be width of splitted
  imy: 512      # Half height - will be height of splitted
  img_name: img/unsplitted_%d.tif

cal_ori:
  cal_splitter: true
  img_cal_name:
    - cal/unsplitted.tif   # unsplitted image

plugins:
  selected_tracking: ext_tracker_splitter
  available_tracking:
    - default
    - ext_tracker_splitter
```

### Image Processing

In splitter mode, PyPTV automatically:
1. **Splits images** into left and right portions
2. **Processes each portion** as a separate camera view
3. **Applies stereo matching** between the split views
4. **Reconstructs 3D positions** using the stereo geometry

### Splitter Geometry
So far it's fixed into 4, but probably can work for 2 

## Calibration with Splitter

Profidve the unsplitted image and check in the GUI option
the splitter will work automatically 


### Calibration Process

1. **Capture calibration image** with target visible in both views
2. **Split the image** manually or use PyPTV's splitter tools
3. **Run calibration** on each split view separately
4. **Verify stereo geometry** by checking calibration residuals

### Manual Splitting

If needed, manually split calibration images:

Look into the plugins/ folder there is an example of manual splitting but this obsolete now.


## Processing Workflow

### 1. Image Sequence Setup

Configure image sequence for splitter processing:

```yaml
sequence:
  base_name:
    - img/splitter.%d    # Single image file per frame
  first: 1
  last: 100

# Or for pre-split images:
sequence:
  base_name:
    - img/left.%d        # Left view sequence
    - img/right.%d       # Right view sequence
  first: 1
  last: 100
```

### 2. Detection Parameters

Tune detection for each split view:

```yaml
detect_plate:
  gvth_1: 40    # Threshold for left view
  gvth_2: 45    # Threshold for right view (may differ)
  min_npix: 20
  max_npix: 200
```

### 3. Stereo Matching

Configure stereo correspondence:

```yaml
criteria:
  corrmin: 50.0      # Higher threshold for stereo matching
  cn: 0.01           # Tighter correspondence tolerance
  eps0: 0.1          # Smaller search window
```

## Plugin System

### Splitter Tracking Plugin

The `ext_tracker_splitter` plugin provides specialized functionality:

```python
# Example plugin functionality (simplified)
class SplitterTracker:
    def process_frame(self, image):
        # Split image into left and right views
        left_view, right_view = self.split_image(image)
        
        # Detect particles in each view
        left_particles = self.detect_particles(left_view)
        right_particles = self.detect_particles(right_view)
        
        # Perform stereo matching
        matched_pairs = self.stereo_match(left_particles, right_particles)
        
        # Reconstruct 3D positions
        positions_3d = self.reconstruct_3d(matched_pairs)
        
        return positions_3d
```

### Custom Splitter Plugins

Create custom plugins for specialized splitter setups:

```python
# plugins/my_splitter_plugin.py
def my_splitter_sequence(frame_data):
    """Custom sequence processing for specific splitter setup"""
    
    # Custom splitting logic
    left_view = extract_left_view(frame_data)
    right_view = extract_right_view(frame_data)
    
    # Apply custom preprocessing
    left_processed = preprocess_view(left_view)
    right_processed = preprocess_view(right_view)
    
    return [left_processed, right_processed]
```

## Troubleshooting

### Common Issues

**Issue**: Poor stereo matching between split views
**Solution**: 
- Check calibration quality for both views
- Verify splitting geometry is correct
- Adjust correspondence criteria
- Ensure good overlap between views

**Issue**: Inconsistent detection between views
**Solution**:
- Use different detection thresholds for each view
- Check illumination uniformity
- Verify image splitting is consistent

**Issue**: Calibration residuals too high
**Solution**:
- Ensure calibration target is visible in both views
- Check that split views don't have distortion artifacts
- Use more calibration points
- Verify beam splitter optical quality

### Validation

Test your splitter setup:

1. **Split View Alignment**: Verify views are properly aligned
2. **Stereo Geometry**: Check calibration produces reasonable camera positions
3. **3D Reconstruction**: Test with known 3D points
4. **Temporal Consistency**: Verify tracking works across frames

## Best Practices

### Hardware Setup
- Use high-quality beam splitters to minimize distortion
- Ensure uniform illumination across both views
- Mount beam splitter rigidly to prevent movement
- Use appropriate filters if needed for contrast

### Software Configuration
- Start with the test_cavity example as template
- Use conservative detection parameters initially
- Validate calibration thoroughly before tracking
- Monitor stereo matching quality

### Data Processing
- Process test sequences before full datasets
- Check 3D reconstruction accuracy with known objects
- Validate temporal tracking consistency
- Export data in appropriate formats for analysis

## Advanced Features

### Multi-Frame Splitter

For time-resolved measurements:

```yaml
sequence:
  base_name:
    - img/splitter_early.%d
    - img/splitter_late.%d   # Different timing
  first: 1
  last: 100
```

### Splitter with Multiple Cameras

Combine splitter mode with multi-camera setups:

```yaml
num_cams: 4  # 2 physical cameras, each with splitter

ptv:
  splitter: true
  
# Configure as 4 logical cameras
sequence:
  base_name:
    - img/cam1_left.%d
    - img/cam1_right.%d
    - img/cam2_left.%d
    - img/cam2_right.%d
```

## See Also

- [Calibration Guide](calibration.md)
- [YAML Parameters Reference](yaml-parameters.md)
- [Examples and Workflows](examples.md)
- [Plugin Development Guide](plugins.md)
