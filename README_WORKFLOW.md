# PyPTV Processing Workflow Explanation

This document explains the typical workflow of the PyPTV system for 3D particle tracking.

## Processing Steps

1. **Image Processing**: Camera images are processed to detect particle targets
   - Creates `cam*.*` files with detected target coordinates for each camera

2. **Correspondence**: Matches targets across cameras using epipolar geometry to get 3D positions
   - Creates `rt_is.*` files with 3D positions in each frame
   - Each rt_is file contains 3D coordinates (x,y,z) of particles in a specific frame

3. **Tracking**: Links 3D positions across time to form trajectories
   - Creates `ptv_is.*` files with trajectory links
   - Each ptv_is file contains links between particle IDs in consecutive frames

## Output Files

The result files are generated in the experiment's `/res` directory:

- **cam*.NNNN**: 2D target coordinates in each camera for frame NNNN
- **rt_is.NNNN**: 3D positions in frame NNNN
- **ptv_is.NNNN**: Trajectory links between frame NNNN and NNNN+1

## Installation Issues with optv

Currently, there are issues with the optv Python package that's required by PyPTV:

1. **Python 3.12 Compatibility**: The optv package on PyPI doesn't install on Python 3.12
2. **Import Structure**: The installed optv package is missing expected modules like `optv.calibration`

### Potential Solutions

1. Use Python 3.11 instead of 3.12
2. Build optv from source using the version from https://github.com/openptv/openptv-python
3. Create a Docker container with a compatible environment
4. Use the mock_run.py script we created to demonstrate the workflow without optv

## Complete Installation Steps (when working correctly)

1. Create a Python environment with Python 3.11
   ```bash
   python -m venv env
   source env/bin/activate  # Linux/Mac
   # or
   env\Scripts\activate  # Windows
   ```

2. Install optv from GitHub
   ```bash
   git clone https://github.com/openptv/openptv-python.git
   cd openptv-python/py_bind
   pip install -e .
   ```

3. Install PyPTV
   ```bash
   git clone https://github.com/OpenPTV/pyptv.git
   cd pyptv
   pip install -e .
   ```

4. Run PyPTV batch processing
   ```bash
   python -m pyptv.pyptv_batch path/to/experiment first_frame last_frame
   ```

## Data Structure

A typical experiment directory should have this structure:
```
experiment/
├── cal/               # Calibration images and parameters
├── img/               # Sequence images (cam*.NNNNN)
├── parameters/        # Parameter files
└── res/               # Results directory (created if not exists)
```

## Understanding Tracking Results

After running the pipeline, you can analyze the results:
- Use tools like flowtracks to load and analyze trajectories
- Use matplotlib or other visualization tools to plot trajectories
- Export to other formats like Paraview for 3D visualization