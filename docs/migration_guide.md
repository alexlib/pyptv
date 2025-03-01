# Migration Guide: Legacy to Modern PyPTV

This guide helps users transition from the legacy PyPTV interface to the modernized version. The updated PyPTV maintains compatibility with existing projects while introducing new features and improvements.

## What Has Changed

### Parameter Management
| Legacy System | Modern System |
|--------------|---------------|
| `.par` files with custom format | `.yaml` files with structured format |
| Manual editing of parameter files | Form-based parameter editing |
| No validation of parameter values | Type checking and validation |
| No default values | Default values for all parameters |

### User Interface
| Legacy Feature | Modern Equivalent |
|--------------|---------------|
| Basic tabbed interface | Modern window with sidebar and toolbars |
| Text-based parameter display | Interactive form-based parameter dialog |
| Basic camera views | Enhanced camera views with zoom and selection |
| Limited visualization | Advanced 3D visualization dialog |
| Manual workflow | Guided workflow with improved feedback |

### Data Storage
| Legacy Approach | Modern Approach |
|--------------|---------------|
| Separate files for each parameter type | Organized YAML files by function |
| Results in fixed-format text files | Results in standard formats (CSV, HDF5) |
| No metadata stored with results | Rich metadata included with results |

## Compatibility

The modernized PyPTV maintains backward compatibility with:
- Existing project directories
- Legacy parameter files (`.par`)
- Result files from previous versions

## Migration Steps

### Step 1: Install the Latest Version

```bash
pip install numpy
python -m pip install pyptv --index-url https://pypi.fury.io/pyptv --extra-index-url https://pypi.org/simple
```

### Step 2: Convert Existing Projects

Your existing projects can be used directly with the new interface. The system will automatically:

1. Read legacy `.par` files
2. Create equivalent `.yaml` files
3. Use the modernized interface with your existing data

No manual conversion is required.

### Step 3: Adjust to the New Interface

#### Main Window
- The main toolbar contains common actions
- The sidebar provides quick access to parameters and tools
- Camera views support more interaction options

#### Parameter Management
- Use **Parameters > Edit Parameters** instead of editing `.par` files directly
- Parameters are organized by functional category
- Changes are validated before saving

#### Visualization
- Use the new 3D visualization tool through **View > 3D Visualization**
- Camera views support enhanced interaction
- Results can be exported in multiple formats

## Feature Mapping

### Parameters

Legacy parameter files are mapped to YAML equivalents:

| Legacy File | Modern File | Purpose |
|------------|------------|---------|
| `ptv.par` | `ptv.yaml` | Main PTV configuration |
| `cal_ori.par` | `calibration.yaml` | Calibration parameters |
| `targ_rec.par` | `detection.yaml` | Particle detection settings |
| `track.par` | `tracking.yaml` | Tracking algorithm settings |
| `criteria.par` | `criteria.yaml` | Correspondence criteria |
| `sequence.par` | `sequence.yaml` | Sequence settings |

### Workflow Steps

| Legacy Workflow | Modern Workflow |
|----------------|----------------|
| Initialize | **Init** button or **Process > Initialize** |
| Run detection | **Detection > Run Detection** |
| Run calibration | **Calibration > Run Calibration** |
| Run tracking | **Tracking > Run Tracking** |
| View results | **View > 3D Visualization** |

## Adapting Custom Workflows

If you have custom scripts that interact with PyPTV:

### Parameter Access
```python
# Legacy approach
with open('parameters/ptv.par', 'r') as f:
    # Parse custom format
    lines = f.readlines()
    # Extract values...

# Modern approach
import yaml
with open('parameters/ptv.yaml', 'r') as f:
    params = yaml.safe_load(f)
    num_cams = params['cameras']['num_cams']
```

### Result Processing
```python
# Legacy approach
with open('res/ptv_is.10000', 'r') as f:
    # Parse fixed-width format
    lines = f.readlines()
    # Extract values...

# Modern approach
import pandas as pd
# Still supports legacy format
with open('res/ptv_is.10000', 'r') as f:
    # Parse as before
    
# Or use new formats if available
df = pd.read_csv('res/trajectories.csv')
```

## Common Migration Issues

### Issue: Parameters Not Migrating Correctly

**Solution:**
1. Check file permissions
2. Manually copy legacy `.par` files to the parameters directory
3. Let the system convert them automatically
4. Verify values in the parameter dialog

### Issue: Legacy Scripts Not Working

**Solution:**
1. Update import paths if needed
2. Modify parameter access as shown above
3. Use the compatibility layer for result access:
   ```python
   from pyptv.legacy_compat import read_legacy_results
   
   particles = read_legacy_results('path/to/res/ptv_is.10000')
   ```

### Issue: Visualization Not Showing Results

**Solution:**
1. Verify result files exist in the `res/` directory
2. Check that tracking completed successfully
3. Use the legacy result viewer if needed:
   - **View > Legacy Result Viewer**

## Getting Additional Help

If you encounter issues during migration:

1. Check the documentation at http://openptv-python.readthedocs.io
2. Post questions to the mailing list: openptv@googlegroups.com
3. Report bugs on GitHub: https://github.com/alexlib/pyptv/issues
4. Include the following in bug reports:
   - PyPTV version
   - Operating system
   - Error messages
   - Steps to reproduce