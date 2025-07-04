# Anti-Pattern Audit Summary

## Task: Eliminate Parameter Management Anti-Patterns

The goal was to ensure the codebase uses clean, modern, Experiment-centric design with ParameterManager as the single source of truth, with no legacy fallback or circular dependencies.

## Anti-Patterns Identified and Fixed

### 1. **Direct ParameterManager Instantiation in GUI Components**

**Anti-Pattern:** GUI classes directly creating `ParameterManager()` instances
```python
# BAD (Anti-pattern)
class DetectionGUI:
    def __init__(self, par_path: Path):
        self.pm = ParameterManager()
        self.pm.from_yaml(par_path / 'parameters.yaml')
```

**Fixed To:** GUI classes accept Experiment objects and delegate parameter access
```python
# GOOD (Clean pattern)
class DetectionGUI:
    def __init__(self, experiment: Experiment):
        self.experiment = experiment
        ptv_params = experiment.get_parameter('ptv')
```

**Files Fixed:**
- `pyptv/detection_gui.py`
- `pyptv/mask_gui.py` 
- `pyptv/calibration_gui.py`
- `pyptv/code_editor.py` (oriEditor, addparEditor)

### 2. **Inconsistent Parameter Structure Usage**

**Anti-Pattern:** Code still accessing legacy `n_img` parameter
```python
# BAD (Anti-pattern)
self.n_cams = ptv_params['n_img']  # n_img no longer exists
```

**Fixed To:** Use new parameter structure with `n_cam`
```python
# GOOD (Clean pattern)  
self.n_cams = ptv_params['n_cam']  # Global n_cam parameter
```

**Files Fixed:**
- `pyptv/pyptv_gui.py`
- `pyptv/detection_gui.py`
- `pyptv/mask_gui.py`
- `pyptv/calibration_gui.py`
- `pyptv/code_editor.py`
- `pyptv/pyptv_batch.py`
- `tests/test_experiment_design.py`
- `tests/test_maingui_design.py`
- `tests/test_parameters.py`
- `tests/test_cavity_comprehensive.py`
- `tests/test_parameter_manager_structure.py`

### 3. **Standalone Scripts Using Direct ParameterManager**

**Anti-Pattern:** Batch processing scripts creating their own ParameterManager
```python
# BAD (Anti-pattern)
pm = ParameterManager()
pm.from_directory(exp_path / "parameters")
```

**Fixed To:** Use Experiment internally for consistency
```python
# GOOD (Clean pattern)
experiment = Experiment()
experiment.populate_runs(exp_path)
ptv_params = experiment.get_parameter('ptv')
```

**Files Fixed:**
- `pyptv/pyptv_batch.py`

### 4. **GUI Parameter Saving Anti-patterns**

**Anti-Pattern:** GUI directly calling ParameterManager methods
```python
# BAD (Anti-pattern)
self.pm.to_yaml(yaml_path)
```

**Fixed To:** Delegate to Experiment
```python
# GOOD (Clean pattern)
self.experiment.save_parameters()
```

**Files Fixed:**
- `pyptv/pyptv_gui.py`
- `pyptv/calibration_gui.py`

## Legitimate ParameterManager Usage (Not Anti-patterns)

The following usage patterns are **correct** and were preserved:

1. **Within Experiment class** - Experiment owns a ParameterManager instance
2. **In parameter_gui.py** - Takes ParameterManager as injected dependency  
3. **In test files** - Tests are allowed to use ParameterManager directly
4. **In ptv.py** - Only imports ParameterManager, doesn't instantiate it

## Updated Call Patterns

### MainGUI Parameter Delegation
```python
# OLD (Anti-pattern)
detection_gui = DetectionGUI(info.object.exp1.active_params.par_path)

# NEW (Clean pattern)
detection_gui = DetectionGUI(info.object.exp1)
```

### Parameter Access
```python
# OLD (Anti-pattern)
ptv_params = self.pm.get_parameter('ptv')
n_cams = ptv_params['n_img']

# NEW (Clean pattern)  
ptv_params = self.experiment.get_parameter('ptv')
n_cams = ptv_params['n_cam']
```

## Verification

### Tests Passing
- `tests/test_experiment_design.py` - All 7 tests pass ✓
- `tests/test_maingui_design.py` - All 2 tests pass ✓  

### Architecture Verification
- No circular dependencies between GUI and Experiment ✓
- Single source of truth (ParameterManager) maintained ✓
- Clean Experiment-centric parameter access ✓
- Modern YAML-based parameter structure ✓

## Result

The codebase now follows clean, modern parameter management patterns:

1. **Single Responsibility:** ParameterManager handles parameter I/O and structure
2. **Dependency Injection:** GUI components receive Experiment dependencies  
3. **Consistent Interface:** All parameter access goes through Experiment.get_parameter()
4. **No Anti-patterns:** No direct ParameterManager instantiation in application code
5. **Future-proof:** Easy to extend and maintain parameter management

The parameter management system is now architected according to best practices with clear separation of concerns and no circular dependencies.
