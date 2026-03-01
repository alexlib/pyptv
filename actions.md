# Dumbbell orientation notes

## Error context
- SciPy minimize reports: "Desired error not necessarily achieved due to precision loss."
- The optimizer returns almost the same parameters as the initial guess.

## Call path
- GUI button: calibration_gui.py -> _button_orient_dumbbell_fired -> ptv.py_calibration(12, self)
- Dispatch: ptv.py -> py_calibration -> calib_dumbbell
- Objective + optimizer: ptv.py -> dumbbell_target_func, calib_convergence, minimize

## Likely cause
- Poor scaling and weak constraints (all cameras free).
- Objective mixes positions (~1e3) and angles (~1e0), plus abs() term for length.

## Improvement ideas
1) Fix at least one camera (anchor the gauge) or allow fixed cameras in the GUI flow.
2) Scale parameters (e.g., optimize positions in meters or divide by 1000).
3) Use a more robust optimizer (Powell or L-BFGS-B with bounds) or least_squares on residuals.
4) Replace abs() in dumbbell length error with squared or Huber loss.
5) Ensure enough valid frames with exactly 2 targets per camera; use cleaner subset.
6) Tune dumbbell_penalty_weight to avoid dominating/flattening the objective.
