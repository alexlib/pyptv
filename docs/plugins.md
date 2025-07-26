# Plugins System Guide

PyPTV features an extensible plugin system that allows you to customize tracking algorithms and sequence processing without modifying the core code.

## Overview

The plugin system provides two main extension points:

1. **Tracking Plugins** - Custom particle tracking algorithms
2. **Sequence Plugins** - Custom image sequence preprocessing

Plugins are Python files that implement specific interfaces and can be selected via the YAML configuration.

## Plugin Configuration

### Available vs Selected Plugins

In your YAML configuration:

```yaml
plugins:
  available_tracking:          # List of available tracking plugins
    - default
    - ext_tracker_splitter
    - my_custom_tracker
  selected_tracking: default   # Currently active tracking plugin
  
  available_sequence:          # List of available sequence plugins  
    - default
    - ext_sequence_rembg
    - ext_sequence_contour
    - my_custom_sequence
  selected_sequence: default   # Currently active sequence plugin
```

### Plugin Directory

Place custom plugins in the `plugins/` directory of your experiment:

```
my_experiment/
├── parameters_Run1.yaml
├── plugins/
│   ├── my_custom_tracker.py
│   ├── my_custom_sequence.py
│   └── __init__.py
├── cal/
└── img/
```

## Tracking Plugins

Tracking plugins customize how particles are tracked between frames.

### Plugin Interface

Create a tracking plugin by implementing the required functions:

```python
# plugins/my_custom_tracker.py

def default_tracking(exp, step, num_cams):
    """
    Custom tracking algorithm
    
    Args:
        exp: Experiment object
        step: Current time step
        num_cams: Number of cameras
        
    Returns:
        Number of tracked particles
    """
    
    # Your custom tracking logic here
    # Access experiment data via exp object
    # Return number of successfully tracked particles
    
    return num_tracked


# Optional: initialization function
def initialize_tracking(exp):
    """Initialize tracking plugin with experiment data"""
    pass

# Optional: cleanup function  
def finalize_tracking(exp):
    """Clean up after tracking is complete"""
    pass
```

### Example: Velocity-Based Tracker

```python
# plugins/velocity_tracker.py

import numpy as np
from optv.tracking_framebuf import TargetArray

def default_tracking(exp, step, num_cams):
    """Tracking based on velocity prediction"""
    
    # Get current and previous particles
    current_targets = exp.current_step_targets
    previous_targets = exp.previous_step_targets
    
    if previous_targets is None:
        return len(current_targets)
    
    # Predict positions based on velocity
    predicted_positions = predict_next_positions(previous_targets)
    
    # Match current particles to predictions
    matches = match_particles(current_targets, predicted_positions)
    
    # Update particle trajectories
    update_trajectories(exp, matches)
    
    return len(matches)

def predict_next_positions(targets):
    """Predict next positions based on velocity"""
    positions = []
    for target in targets:
        # Simple linear prediction
        next_x = target.x + target.vx
        next_y = target.y + target.vy  
        next_z = target.z + target.vz
        positions.append((next_x, next_y, next_z))
    return positions

def match_particles(current, predicted):
    """Match current particles to predicted positions"""
    # Implement matching algorithm
    # Return list of (current_particle, predicted_particle) pairs
    pass
```

### Built-in Tracking Plugins

PyPTV includes several built-in tracking plugins:

#### default
Standard PTV tracking algorithm using the OpenPTV libraries.

#### ext_tracker_splitter  
Specialized tracking for splitter-based stereo systems.

```python
# Automatically enabled when splitter mode is active
plugins:
  selected_tracking: ext_tracker_splitter
  
ptv:
  splitter: true
```

## Sequence Plugins

Sequence plugins preprocess images before particle detection.

### Plugin Interface

```python
# plugins/my_sequence_plugin.py

def sequence_preprocess(image_data, frame_number, camera_id):
    """
    Preprocess image data
    
    Args:
        image_data: Raw image array
        frame_number: Current frame number
        camera_id: Camera identifier (0, 1, 2, ...)
        
    Returns:
        Processed image array
    """
    
    # Your preprocessing logic here
    processed_image = apply_preprocessing(image_data)
    
    return processed_image
```

### Example: Background Subtraction

```python
# plugins/background_subtraction.py

import numpy as np
import cv2

# Global background storage
background_models = {}

def sequence_preprocess(image_data, frame_number, camera_id):
    """Background subtraction preprocessing"""
    
    # Initialize background model for this camera
    if camera_id not in background_models:
        background_models[camera_id] = cv2.createBackgroundSubtractorMOG2()
    
    # Apply background subtraction
    bg_model = background_models[camera_id]
    foreground_mask = bg_model.apply(image_data)
    
    # Apply mask to original image
    processed_image = cv2.bitwise_and(image_data, image_data, mask=foreground_mask)
    
    return processed_image
```

### Built-in Sequence Plugins

#### default
No preprocessing - passes images through unchanged.

#### ext_sequence_rembg
Background removal using the `rembg` library.

```bash
# Install rembg first
pip install rembg[cpu]  # or rembg[gpu]
```

```yaml
plugins:
  selected_sequence: ext_sequence_rembg
```

#### ext_sequence_contour
Contour-based preprocessing for improved particle detection.

#### ext_sequence_rembg_contour
Combines background removal with contour detection.

## Advanced Plugin Development

### Accessing Experiment Data

Plugins have access to the full experiment object:

```python
def default_tracking(exp, step, num_cams):
    # Access parameters
    detect_params = exp.pm.get_parameter('detect_plate')
    track_params = exp.pm.get_parameter('track')
    
    # Access calibration data
    calibration = exp.calibration
    
    # Access current tracking data
    current_targets = exp.current_step_targets
    
    # Access file paths
    working_dir = exp.working_directory
```

### State Management

Maintain state between plugin calls:

```python
# Global state storage
plugin_state = {}

def default_tracking(exp, step, num_cams):
    # Initialize state if needed
    if 'initialized' not in plugin_state:
        plugin_state['particle_histories'] = {}
        plugin_state['initialized'] = True
    
    # Use state data
    histories = plugin_state['particle_histories']
    
    # Update state
    histories[step] = current_tracking_data
```

### Error Handling

Implement robust error handling:

```python
def sequence_preprocess(image_data, frame_number, camera_id):
    try:
        # Main processing
        result = process_image(image_data)
        return result
        
    except Exception as e:
        # Log error and return original image
        print(f"Plugin error on frame {frame_number}, camera {camera_id}: {e}")
        return image_data
```

## Plugin Testing

### Unit Testing

Create tests for your plugins:

```python
# test_my_plugin.py

import unittest
import numpy as np
from plugins.my_custom_tracker import default_tracking

class TestCustomTracker(unittest.TestCase):
    
    def setUp(self):
        # Create mock experiment object
        self.exp = create_mock_experiment()
    
    def test_tracking_basic(self):
        # Test basic tracking functionality
        result = default_tracking(self.exp, step=1, num_cams=4)
        self.assertIsInstance(result, int)
        self.assertGreaterEqual(result, 0)
```

### Integration Testing

Test plugins with real data:

```python
# Test with test_cavity dataset
def test_with_real_data():
    exp = Experiment('tests/test_cavity/parameters_Run1.yaml')
    
    # Enable your plugin
    exp.pm.set_parameter('plugins', {
        'selected_tracking': 'my_custom_tracker'
    })
    
    # Run a few frames
    for step in range(1, 5):
        result = run_tracking_step(exp, step)
        assert result > 0
```

## Plugin Examples

### Particle Size Filter

```python
# plugins/size_filter.py

def sequence_preprocess(image_data, frame_number, camera_id):
    """Filter particles by size"""
    
    # Apply morphological operations to remove small noise
    kernel = np.ones((3,3), np.uint8)
    
    # Remove small particles
    opened = cv2.morphologyEx(image_data, cv2.MORPH_OPEN, kernel)
    
    # Remove holes in particles
    closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel)
    
    return closed
```

### Multi-Exposure Fusion

```python
# plugins/hdr_fusion.py

exposure_buffers = {}

def sequence_preprocess(image_data, frame_number, camera_id):
    """Fuse multiple exposures for better dynamic range"""
    
    # Store multiple exposures
    if camera_id not in exposure_buffers:
        exposure_buffers[camera_id] = []
    
    exposure_buffers[camera_id].append(image_data)
    
    # Fuse when we have enough exposures
    if len(exposure_buffers[camera_id]) >= 3:
        fused = fuse_exposures(exposure_buffers[camera_id])
        exposure_buffers[camera_id] = []  # Reset buffer
        return fused
    else:
        return image_data  # Return single exposure for now
```

## Best Practices

### Plugin Design
- Keep plugins focused on a single task
- Handle errors gracefully
- Document plugin parameters and behavior
- Test with various datasets

### Performance
- Minimize memory allocation in tracking plugins
- Use efficient image processing operations
- Consider parallel processing for independent operations
- Profile plugin performance with real data

### Compatibility
- Follow the standard plugin interface
- Test with different PyPTV versions
- Document plugin dependencies
- Provide fallback behavior when possible

## Debugging Plugins

### Logging

Add logging to your plugins:

```python
import logging

logger = logging.getLogger(__name__)

def default_tracking(exp, step, num_cams):
    logger.info(f"Starting tracking for step {step}")
    
    try:
        result = perform_tracking()
        logger.debug(f"Tracked {result} particles")
        return result
    except Exception as e:
        logger.error(f"Tracking failed: {e}")
        raise
```

### Visual Debugging

Create debug visualizations:

```python
def sequence_preprocess(image_data, frame_number, camera_id):
    processed = apply_processing(image_data)
    
    # Save debug images
    if DEBUG_MODE:
        cv2.imwrite(f'debug/frame_{frame_number}_cam_{camera_id}_original.png', image_data)
        cv2.imwrite(f'debug/frame_{frame_number}_cam_{camera_id}_processed.png', processed)
    
    return processed
```

## See Also

- [Examples and Workflows](examples.md)
- [YAML Parameters Reference](yaml-parameters.md)
- [Splitter Mode Guide](splitter-mode.md)
- [Calibration Guide](calibration.md)
