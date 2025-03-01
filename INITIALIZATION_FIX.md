# PyPTV Initialization Fix

## The Problem

The PyPTV application sometimes gets stuck in an infinite loop when trying to initialize an experiment after opening a directory. This happens because:

1. There are two different implementations of `PTVCore`:
   - The original implementation in `/pyptv/ui/ptv_core.py`
   - A simplified bridge implementation in `/pyptv/ui/ptv_core/bridge.py`

2. The bridge implementation is being imported when code tries to use the original implementation, due to an import in `/pyptv/ui/ptv_core/__init__.py`:
   ```python
   from pyptv.ui.ptv_core.bridge import PTVCoreBridge as PTVCore
   ```

3. The dialogs and windows expect the full functionality of the original `PTVCore`, but get the limited bridge version, which causes errors or infinite loops.

## The Solution

The fix consists of two patches:

1. **Main Window Fix** (`patches/ptv_core_fix.patch`):
   - Directly imports the full PTVCore implementation using `importlib` to bypass the bridge
   - Adds more debug logging to help identify initialization issues
   - Ensures the PTVCore is properly created and initialized

2. **Bridge Fix** (`patches/ptv_core_bridge_fix.patch`):
   - Modifies the `__init__.py` to try loading the full implementation first
   - Falls back to the bridge if the full implementation can't be loaded
   - Adds warning messages when the bridge is used

## How to Apply the Fix

Run the following command to apply the fixes:

```bash
./apply_fixes.sh
```

## Testing the Fix

After applying the fixes, test the application by:

1. Run the application with the modern UI: `python -m pyptv.pyptv_gui --modern`
2. Open an experiment directory using the "File" > "Open Experiment..." menu
3. Click "Initialize" to load the experiment

The initialization should now work correctly without getting stuck in an infinite loop.

## Debugging the Issue

If you need to debug the initialization process further:

1. Run the interactive debug script: `python debug_init_simple.py path/to/experiment`
2. Look for error messages or warnings in the output
3. Check the bridges and import paths being used

## Technical Details

### Import Resolution

The core issue was an import conflict. When code tried to import `PTVCore` from `pyptv.ui.ptv_core`, it would get the bridge version instead of the full implementation.

The main fix uses Python's `importlib` to load the module directly from the file path, bypassing the normal import mechanism.

### Parameter Loading

The full `PTVCore` implementation properly loads YAML parameters, while the bridge implementation only has a minimal subset of functionality.

### GUI Initialization

The GUI initialization process has been made more robust by:
1. Ensuring we get the right implementation
2. Adding more error handling
3. Providing debug logging for troubleshooting