# Unified YAML Parameter System and Pipeline Scripts

This PR introduces a unified YAML parameter system and pipeline scripts for PyPTV, significantly improving the parameter management and experiment workflow.

## Changes

### Unified Parameter System
- Replaced multiple separate parameter files with a single comprehensive YAML file
- Added TargetParams class to handle particle detection parameters
- Updated SequenceParams class to match YAML file format
- Extended CriteriaParams with additional correspondence parameters
- Added parameter conversion utility to migrate from legacy format

### Pipeline Scripts
- Added full pipeline script for complete experiment processing
- Added simplified pipeline script that works without optv module
- Added shell script wrappers for easy CLI usage
- Created example result files to demonstrate the pipeline

### Documentation
- Added comprehensive README_UNIFIED_YAML.md explaining the unified parameter approach
- Documented all parameter types and their usage
- Added examples of using the pipeline scripts

## Benefits
1. **Simplified Configuration**: Single source of truth for all parameters
2. **Better Version Control**: Changes to parameters are tracked in one file
3. **Easier Debugging**: Parameter relationships are more clear
4. **Streamlined Workflow**: Full pipeline can be run with a single command
5. **Backward Compatibility**: Legacy parameter files still supported

## Testing
The unified parameter system and pipeline scripts have been tested with the test_cavity experiment data, successfully generating 3D particle positions and trajectories.

## Future Work
- Add validation for the unified YAML parameters
- Extend the pipeline with visualization tools
- Add more options for customizing the pipeline steps