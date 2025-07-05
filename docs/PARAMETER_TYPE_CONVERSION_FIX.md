# Parameter Type Conversion Fix

## Issue

The parameter GUI was failing with the error:
```
The 'chfield' trait of a Main_Params instance must be an integer, but a value of 'Frame' <class 'str'> was specified.
```

## Root Cause

There was a type mismatch between how different parameter GUI classes handle the `chfield` parameter:

1. **Main_Params class**: Expects `chfield` as an `Int` (0, 1, 2)
2. **Calib_Params class**: Uses `chfield` as an `Enum("Frame", "Field odd", "Field even")`

The problem occurred in the `CalHandler.closed()` method, which was saving the string enum values directly to both `ptv.chfield` and `cal_ori.chfield`, overwriting the integer values that Main_Params expected.

## Fix Applied

Modified the `CalHandler` in `parameter_gui.py` to convert the string enum values back to integers before saving:

```python
# Convert chfield enum string back to integer for storage
chfield_int = 0  # Default to "Frame"
if calib_params.chfield == "Field odd":
    chfield_int = 1
elif calib_params.chfield == "Field even":
    chfield_int = 2

# Update both ptv.chfield and cal_ori.chfield with integer values
param_mgr.update_parameter_group('ptv', {
    # ... other parameters ...
    'chfield': chfield_int,
    # ... other parameters ...
})

param_mgr.update_parameter_group('cal_ori', {
    # ... other parameters ...
    'chfield': chfield_int,
    # ... other parameters ...
})
```

## How It Works

1. **Loading**: 
   - Main_Params loads `ptv.chfield` as integer directly
   - Calib_Params loads `cal_ori.chfield` as integer, then converts to string enum for UI display

2. **Saving**:
   - CalHandler converts string enum back to integer before saving
   - Both `ptv.chfield` and `cal_ori.chfield` are saved as integers
   - Main_Params can successfully load the integer values

3. **Data Flow**:
   ```
   YAML (int) → Main_Params (int) → Save (int) → YAML (int) ✓
   YAML (int) → Calib_Params (string enum) → Save (int) → YAML (int) ✓
   ```

## Result

✅ **Parameter GUIs now work correctly without type errors**  
✅ **YAML file maintains consistent integer format for chfield**  
✅ **Both Main_Params and Calib_Params can edit parameters without conflicts**  
✅ **Parameter persistence works correctly through the ParameterManager API**

The parameter editing functionality now properly handles type conversions and maintains data consistency across different GUI components.
