# Unified YAML Parameter System for PyPTV

This document explains the new unified YAML parameter system for PyPTV, which centralizes all parameters in a single file rather than using multiple separate files.

## Overview

The unified YAML parameter system offers several advantages:

1. **Single Source of Truth**: All parameters are stored in a single file (`pyptv_config.yaml`) rather than spread across multiple files.
2. **Direct Parameter Creation**: Parameters for the optv library are created directly from the unified YAML file without intermediate files.
3. **Easier Configuration**: Edit one file instead of navigating through multiple parameter files.
4. **Better Version Control**: Changes to parameters are tracked in a single file, making diffs clearer.

## Setup and Installation

### Using the Virtual Environment

To ensure all dependencies are properly installed, we provide a setup script that creates a virtual environment with Python 3.11 and installs all necessary packages:

```bash
# Create and setup the virtual environment
./setup_environment.sh [venv_path]

# Run the pipeline using the virtual environment
./run_venv_pipeline.sh [experiment_path] [venv_path]
```

Example:
```bash
# Create a virtual environment in ./venv
./setup_environment.sh venv

# Run the pipeline on test_cavity data using the virtual environment
./run_venv_pipeline.sh tests/test_cavity venv
```

This setup ensures compatibility with optv and other dependencies, providing the best experience when running the full pipeline.

## File Structure

The unified YAML parameter file (`pyptv_config.yaml`) is structured as follows:

```yaml
PtvParams:
  # Main PTV parameters (from ptv.par/yaml)
  n_img: 4
  img_name: [...]
  # ...

TrackingParams:
  # Tracking parameters (from track.par/yaml)
  dvxmin: -10.0
  # ...

SequenceParams:
  # Sequence parameters (from sequence.par/yaml)
  first: 10001
  # ...

CriteriaParams:
  # Correspondence criteria parameters (from criteria.par/yaml)
  # ...

TargetParams:
  # Target recognition parameters (from targ_rec.par/yaml)
  # ...
```

## Converting to Unified YAML

To convert an existing experiment with individual parameter files to the unified format, use the conversion utility:

```bash
python -m pyptv.convert_to_unified_yaml /path/to/experiment
```

This will:
1. Load all individual parameter files
2. Combine them into a single unified YAML file
3. Save the unified file as `parameters/pyptv_config.yaml`

## Using the Unified YAML

### In Python Code

```python
from pyptv.yaml_parameters import ParameterManager

# Load all parameters from unified YAML
param_manager = ParameterManager('/path/to/experiment/parameters', unified=True)
yaml_params = param_manager.load_all()

# Access parameters by type
ptv_params = yaml_params.get('PtvParams')
tracking_params = yaml_params.get('TrackingParams')
# ...

# Or load a specific parameter type
from pyptv.yaml_parameters import PtvParams
ptv_params = param_manager.load_param(PtvParams)
```

### Using the Full Pipeline

#### Standard Pipeline

The full pipeline script automatically uses the unified YAML file:

```bash
./run_pipeline.sh /path/to/experiment
```

Or directly:

```bash
python run_full_pipeline.py /path/to/experiment
```

#### Simplified Pipeline (No optv dependency)

If you don't have the optv module properly installed, you can use the simplified pipeline:

```bash
./run_simple_pipeline.sh /path/to/experiment
```

This runs a simulated version of the pipeline that demonstrates the workflow using the unified YAML parameters.

## Pipeline Scripts

The repository includes several scripts for running the pipeline:

1. **run_pipeline.sh**: Main pipeline script that uses the unified YAML parameters
2. **run_simple_pipeline.sh**: Simplified pipeline that works without optv module
3. **run_venv_pipeline.sh**: Runs the pipeline using the virtual environment
4. **run_legacy_pipeline.sh**: Attempts to run the legacy pipeline for comparison
5. **setup_environment.sh**: Creates a virtual environment with all dependencies

## Parameter Definitions

The unified YAML file includes the following parameter sections:

### PtvParams
Main PTV parameters controlling the general setup:
- `n_img`: Number of cameras
- `img_name`: Image names for each camera
- `img_cal`: Calibration image names
- `hp_flag`: Highpass filtering flag
- `allcam_flag`: Use only particles visible in all cameras
- `tiff_flag`: TIFF header flag
- `imx/imy`: Image dimensions
- `pix_x/pix_y`: Pixel size
- `chfield`: Field flag (0=frame, 1=odd, 2=even)
- `mmp_n1/n2/n3`: Refractive indices
- `mmp_d`: Thickness of glass

### SequenceParams
Parameters for image sequences:
- `first`: First frame number
- `last`: Last frame number
- `base_name`: Base filenames for each camera
- `Xmin_lay/Xmax_lay/etc`: Volume coordinates

### TrackingParams
Parameters for particle tracking:
- `dvxmin/dvxmax/etc`: Velocity limits in each dimension
- `angle`: Angle for search cone
- `dacc`: Acceleration limit
- `flagNewParticles`: Allow adding new particles

### CriteriaParams
Parameters for correspondence:
- `X_lay`: X center of illuminated volume
- `Zmin_lay/Zmax_lay/etc`: Volume coordinates
- `cn/cnx/cny`: Convergence limits
- `corrmin`: Minimum correlation coefficient
- `eps0`: Convergence criteria slope

### TargetParams
Parameters for target recognition:
- `gvth_1/gvth_2/etc`: Gray value thresholds for each camera
- `discont`: Allowed discontinuity
- `nnmin/nnmax`: Min/max number of pixels
- `nxmin/nxmax/nymin/nymax`: Size limits
- `sumg_min`: Minimum sum of gray values
- `cr_sz`: Cross size

## Legacy Compatibility

The system maintains compatibility with the legacy parameter files. If the unified YAML file is not found, the system will fall back to individual parameter files.