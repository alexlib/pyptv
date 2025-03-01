# PyPTV Example Workflows

This document provides step-by-step examples of common workflows using the modernized PyPTV interface.

## Example 1: Basic Calibration and Tracking

This workflow demonstrates a complete process from calibration to tracking using the modern interface.

### Step 1: Project Setup

1. Create a project directory with the following structure:
   ```
   my_experiment/
   ├── cal/        # Calibration images
   ├── img/        # Experimental images
   ├── parameters/ # Parameter files
   └── res/        # Results directory
   ```

2. Copy calibration images to the `cal/` directory
3. Copy experimental images to the `img/` directory

### Step 2: Launch PyPTV

```bash
python -m pyptv.pyptv_gui
```

### Step 3: Open Project

1. Click **File > Open Directory**
2. Navigate to your project directory and click **Open**

### Step 4: Configure Parameters

1. Click **Parameters > Edit Parameters**
2. In the parameter dialog, configure:
   - Number of cameras
   - Image dimensions
   - Calibration settings
3. Click **Save**

### Step 5: Camera Calibration

1. Click **Calibration > Calibration Setup**
2. Load calibration images for each camera
3. Detect calibration points:
   - Set detection parameters
   - Click **Detect** for each camera
4. Click **Calibration > Run Calibration**
5. Review calibration results
6. Click **Save Calibration**

### Step 6: Particle Detection

1. Click **Detection > Detection Setup**
2. Configure detection parameters:
   - Intensity threshold
   - Particle size
   - Noise reduction settings
3. Click **Run Detection**
4. Review detected particles in the camera views
5. Adjust parameters and repeat if necessary

### Step 7: Tracking

1. Click **Tracking > Tracking Setup**
2. Configure tracking parameters:
   - Search radius
   - Match criteria
   - Trajectory length
3. Click **Run Tracking**
4. Wait for tracking to complete

### Step 8: Visualize Results

1. Click **View > 3D Visualization**
2. In the visualization dialog:
   - Rotate and zoom to inspect trajectories
   - Color trajectories by velocity
   - Filter by trajectory length
3. Export visualization as needed:
   - Click **Export > Save as Image**
   - Click **Export > Save as CSV**

## Example 2: Using the YAML Parameter System

This workflow demonstrates how to work with the new YAML parameter system.

### Step 1: Create or Edit YAML Parameters

1. Click **Parameters > Edit Parameters**
2. Navigate through parameter categories using the tabs
3. Modify parameters as needed
4. Click **Save** to store parameters as YAML files

### Step 2: View Parameter Files

YAML parameter files are stored in the `parameters/` directory:
```yaml
# Example ptv.yaml
cameras:
  num_cams: 4
  image_size:
    width: 1280
    height: 1024

detection:
  threshold: 0.5
  min_particle_size: 3
  max_particle_size: 15

tracking:
  search_radius: 25.0
  similarity_threshold: 0.8
  min_trajectory_length: 4
```

### Step 3: Use Parameters in Processing

1. Load parameters by clicking **Parameters > Load Parameters**
2. Run processing steps with the loaded parameters
3. Parameters will automatically be used by all processing functions

## Example 3: Advanced 3D Visualization

This workflow demonstrates how to use the advanced 3D visualization features.

### Step 1: Complete Tracking

Follow steps from Example 1 to complete tracking

### Step 2: Open Visualization Dialog

1. Click **View > 3D Visualization**
2. Wait for trajectories to load

### Step 3: Customize Visualization

1. **Change View Perspective**:
   - Click and drag to rotate
   - Scroll to zoom in/out
   - Right-click and drag to pan

2. **Change Color Scheme**:
   - Click **Color > Color by Velocity**
   - Click **Color > Color by Frame**
   - Click **Color > Solid Color**

3. **Filter Trajectories**:
   - Click **Filter > By Length**
   - Set minimum length slider
   - Click **Apply Filter**

4. **Add Reference Elements**:
   - Click **View > Show Coordinate Axes**
   - Click **View > Show Bounding Box**
   - Click **View > Show Camera Positions**

### Step 4: Analyze Specific Trajectories

1. Click on a trajectory to select it
2. View trajectory details in the info panel
3. Click **Selection > Focus on Selected**
4. Click **Selection > Hide Unselected**

### Step 5: Export Results

1. Click **Export > Save as Image**
2. Click **Export > Save as OBJ Model**
3. Click **Export > Save Data as CSV**

## Example 4: Using Plugins

This workflow demonstrates how to use the plugin system.

### Step 1: Setup Plugins

1. Copy the `plugins/` directory to your project directory
2. Copy `sequence_plugins.txt` and `tracking_plugins.txt` to your project directory
3. Customize plugin code if needed

### Step 2: Select and Configure Plugins

1. Click **Plugins > Choose**
2. Select desired sequence plugin:
   - **Denis Sequence** (standard)
   - **Contour Sequence** (contour-based detection)
   - **Rembg Sequence** (background removal)
3. Select desired tracking plugin:
   - **Denis Tracker** (standard)
4. Click **OK**

### Step 3: Run with Plugins

1. Click **Init**
2. Click **Sequence** (runs the selected sequence plugin)
3. Click **Tracking** (runs the selected tracking plugin)
4. View results as usual

## Example 5: Batch Processing

This workflow demonstrates how to use batch processing for multiple experiments or parameter sets.

### Step 1: Prepare Batch Configuration

1. Create a batch configuration file `batch_config.yaml`:
   ```yaml
   experiments:
     - name: experiment1
       directory: /path/to/experiment1
       parameters:
         detection:
           threshold: 0.5
         tracking:
           search_radius: 25.0
     
     - name: experiment2
       directory: /path/to/experiment2
       parameters:
         detection:
           threshold: 0.7
         tracking:
           search_radius: 30.0
   ```

### Step 2: Run Batch Processing

1. Launch the CLI interface:
   ```bash
   python -m pyptv.cli
   ```

2. Run batch processing:
   ```bash
   python -m pyptv.cli batch --config batch_config.yaml
   ```

3. Monitor progress and review results
   ```bash
   python -m pyptv.cli analyze --directories /path/to/experiment1 /path/to/experiment2
   ```

## Tips and Best Practices

1. **Parameter Management**:
   - Use descriptive names for parameter sets
   - Keep parameter backups before making major changes
   - Document parameter choices for reproducibility

2. **Calibration**:
   - Use a well-designed calibration target
   - Ensure calibration images cover the entire measurement volume
   - Verify calibration quality with known geometry

3. **Detection**:
   - Start with conservative thresholds and refine
   - Use the image inspector to verify particle detection
   - Apply appropriate preprocessing filters for noisy images

4. **Tracking**:
   - Adjust search radius based on expected particle displacement
   - Use velocity prediction for fast-moving particles
   - Filter short trajectories for final analysis

5. **Visualization**:
   - Save different visualization presets for presentations
   - Export high-resolution images for publications
   - Use color schemes that highlight the phenomena of interest