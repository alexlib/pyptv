# Parameter GUI Integration with Experiment/Paramset API - COMPLETED

## Summary
Successfully updated `pyptv/parameter_gui.py` to work with the Experiment/Paramset API instead of directly with ParameterManager. The GUI now properly updates parameters via the Experiment object and saves changes back to YAML files.

## Key Changes Made

### 1. Updated Class Constructors
- **Main_Params**: Now takes an `Experiment` object instead of `ParameterManager`
- **Calib_Params**: Now takes an `Experiment` object instead of `ParameterManager`  
- **Tracking_Params**: Now takes an `Experiment` object instead of `ParameterManager`

### 2. Updated Handler Classes
- **ParamHandler**: Updates parameters via `experiment.parameter_manager` and calls `experiment.save_parameters()`
- **CalHandler**: Updates parameters via `experiment.parameter_manager` and calls `experiment.save_parameters()`
- **TrackHandler**: Updates parameters via `experiment.parameter_manager` and calls `experiment.save_parameters()`

### 3. Fixed YAML Structure Compatibility
- Updated parameter loading to use top-level `n_cam` instead of looking for `n_img` in ptv section
- Fixed all `_reload` methods to handle None values with proper defaults
- Updated handlers to set top-level `n_cam` correctly when saving

### 4. Proper Parameter Management
- All parameter updates now go through the Experiment/Paramset API
- Changes are automatically saved to YAML files via `experiment.save_parameters()`
- Parameter loading uses the correct YAML structure with top-level `n_cam`

## Testing
Created comprehensive tests to verify:
- ✅ Parameter GUI classes can be instantiated with Experiment objects
- ✅ Parameters are loaded correctly from real YAML files
- ✅ Parameter modifications are saved back to YAML files correctly
- ✅ Handlers work properly with the Experiment API
- ✅ Top-level `n_cam` is handled correctly throughout the system

## Files Modified
- `pyptv/parameter_gui.py` - Main parameter GUI classes and handlers
- `test_parameter_gui_integration.py` - Integration test with real YAML
- `test_parameter_gui_handlers.py` - Handler testing with mock TraitsUI objects

## Integration Points
The parameter GUI now integrates seamlessly with:
- `pyptv/experiment.py` - Uses Experiment and Paramset classes
- `pyptv/parameter_manager.py` - Accesses parameters via experiment.parameter_manager
- YAML parameter files - Properly reads/writes the correct YAML structure
- `pyptv_gui.py` - Can be used by the main GUI with Experiment objects

## Result
✅ **Parameter GUI is now fully compatible with the YAML-centric Experiment/Paramset API and correctly saves parameter changes back to YAML files.**
