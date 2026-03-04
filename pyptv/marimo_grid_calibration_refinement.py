import marimo

__generated_with = "0.20.2"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo

    mo.md("""
    # Grid-Based Calibration Refinement using Pre-detected Points

    This notebook performs bundle adjustment calibration refinement using pre-detected grid points.

    **Workflow:**
    1. Load pre-detected grid points from pickle file (from `marimo_detect_calibration_grid.py`)
    2. Load PyPTV experiment parameters and initial calibration from YAML file
    3. For each synchronized frame:
       - Triangulate 3D positions of all 42 grid points
       - Estimate planarity and distance errors
    4. Create combined error function (reprojection + planarity + distance)
    5. Optimize camera exterior orientation (positions and angles)
    6. Display optimized parameters (no file writing)

    **Geometric Constraints:**
    - **Planarity**: All 42 grid points lie on a single plane
    - **Distance**: Adjacent points at 120 mm spacing
    """)
    return (mo,)


@app.cell
def _():
    import numpy as np
    import pandas as pd
    from pathlib import Path
    import pickle
    import matplotlib.pyplot as plt
    from optv.calibration import Calibration
    from optv.imgcoord import image_coordinates
    from optv.transforms import convert_arr_metric_to_pixel
    from optv.orientation import multi_cam_point_positions
    from pyptv.parameter_manager import ParameterManager
    from pyptv import ptv
    from scipy.optimize import least_squares
    from scipy import sparse


    return (
        Calibration,
        ParameterManager,
        Path,
        image_coordinates,
        least_squares,
        multi_cam_point_positions,
        np,
        pd,
        pickle,
        plt,
        ptv,
    )


@app.cell
def _(mo):
    # File selection for pickle file with detections
    pickle_path_str = mo.ui.text(
        value='/home/user/Downloads/Illmenau/calibration_detections.pkl',
        label='Calibration Detections Pickle File',
        full_width=True
    )
    pickle_path_str
    return (pickle_path_str,)


@app.cell
def _(Path, mo, pickle, pickle_path_str):
    pickle_path = Path(pickle_path_str.value).expanduser().resolve()

    _status_msg = (
        mo.md(f"**❌ Pickle file not found:** {pickle_path}")
        if not pickle_path.exists()
        else mo.md(f"**✓ Loaded:** {pickle_path}")
    )
    _status_msg

    detected_data = (
        None
        if not pickle_path.exists()
        else pickle.load(open(pickle_path, 'rb'))
    )

    if detected_data is not None:
        mo.md(f"**Synchronized frames:** {detected_data['synchronized_frame_list']}")
        mo.md(f"**Total detections:** {len(detected_data['all_detections'])}")

    return (detected_data,)


@app.cell
def _(mo):
    # File selection for YAML parameters
    yaml_path_str = mo.ui.text(
        value='/home/user/Downloads/Illmenau/pyPTV_folder/parameters_Run4.yaml',
        label='YAML Parameters File Path',
        full_width=True
    )
    yaml_path_str
    return (yaml_path_str,)


@app.cell
def _(ParameterManager, Path, mo, yaml_path_str):
    yaml_path = Path(yaml_path_str.value).expanduser().resolve()

    _status_msg = (
        mo.md(f"**❌ YAML file not found:** {yaml_path}")
        if not yaml_path.exists()
        else mo.md(f"**✓ Loaded:** {yaml_path}")
    )
    _status_msg

    pm = None if not yaml_path.exists() else ParameterManager()
    if pm is not None:
        pm.from_yaml(yaml_path)

    params = {} if pm is None else pm.parameters
    num_cams = (
        0
        if pm is None
        else int(params.get("num_cams", pm.num_cams or 0) or 0)
    )

    if pm is not None:
        mo.md(f"""
        ### Experiment Parameters

        - **YAML File:** {yaml_path.name}
        - **Number of Cameras:** {num_cams}
        - **Image Size:** {params.get('ptv', {}).get('imx', 'N/A')} × {params.get('ptv', {}).get('imy', 'N/A')} pixels
        """)

    return num_cams, params, pm, yaml_path


@app.cell
def _(Calibration, Path, mo, num_cams, params, pm, ptv, yaml_path):
    # Load initial calibrations
    cals = []
    cpar = None

    if pm is not None:
        ptv_params = params.get('ptv', {})
        cpar = ptv._populate_cpar(ptv_params, num_cams)
        cal_ori = pm.parameters.get('cal_ori', {})
        ori_names = cal_ori.get('img_ori', [])

        base_path = Path(yaml_path).parent
        load_status = []

        for _i in range(num_cams):
            _cal = Calibration()
            _ori_path = ori_names[_i] if _i < len(ori_names) else None

            if _ori_path:
                _ori_file_path = base_path / _ori_path
                _addpar_file_path = Path(str(_ori_file_path).replace('.ori', '') + '.addpar')
                if not _addpar_file_path.exists():
                    _addpar_file_path = Path(str(_ori_file_path).replace('.tif.ori', '') + '.addpar')

                if _ori_file_path.exists() and _addpar_file_path.exists():
                    _cal.from_file(str(_ori_file_path), str(_addpar_file_path))
                    load_status.append(f"✓ Camera {_i+1}: {_ori_file_path.name}")
                else:
                    load_status.append(f"⚠ Camera {_i+1}: Missing calibration files")
            else:
                load_status.append(f"⚠ Camera {_i+1}: No calibration path specified")

            cals.append(_cal)

        mo.md("### Initial Calibrations Loaded\n\n" + "\n".join(load_status))

    return cals, cpar


@app.cell
def _(mo):
    # Grid configuration constants
    GRID_ROWS = 7
    GRID_COLS = 6
    GRID_SPACING = 120.0  # mm

    mo.md(f"""
    ### Grid Configuration

    | Parameter | Value |
    |-----------|-------|
    | **Rows** | {GRID_ROWS} |
    | **Columns** | {GRID_COLS} |
    | **Total Points** | {GRID_ROWS * GRID_COLS} |
    | **Grid Spacing** | {GRID_SPACING} mm |
    """)

    return GRID_COLS, GRID_ROWS, GRID_SPACING


@app.cell
def _(GRID_COLS, GRID_ROWS, detected_data, mo):
    """
    Organize detected points by frame for triangulation.
    """
    if detected_data is None:
        mo.md("❌ No detection data loaded")
        frames_data = {}
        synchronized_frames = []
    else:
        # Group detections by frame
        df_frames = detected_data['frame_detections']
        synchronized_frames = detected_data['synchronized_frame_list']

        # Organize: frame_idx -> {cam_idx: corners}
        frames_data = {}
        for _frame_idx in synchronized_frames:
            frames_data[_frame_idx] = {}
            _frame_dets = df_frames[df_frames['frame'] == _frame_idx]
            for _, _row in _frame_dets.iterrows():
                if _row['success']:
                    frames_data[_frame_idx][_row['camera']] = _row['corners']

        mo.md(f"""
        ### Frame Data Organized

        - **Synchronized Frames:** {len(synchronized_frames)}
        - **Frames:** {synchronized_frames}
        - **Points per frame:** {GRID_ROWS * GRID_COLS}
        """)

    return frames_data, synchronized_frames


@app.cell
def _(
    GRID_COLS,
    GRID_ROWS,
    GRID_SPACING,
    cals,
    cpar,
    frames_data,
    mo,
    multi_cam_point_positions,
    np,
    synchronized_frames,
):
    """
    Triangulate 3D positions for each frame.
    """
    if not frames_data:
        mo.md("❌ No frames to triangulate")
        triangulated_frames = {}
        frame_metrics = {}
    else:
        triangulated_frames = {}
        frame_metrics = {}

        for _frame_idx in synchronized_frames:
            _frame_corners = frames_data[_frame_idx]

            # Check if all cameras have detections
            if len(_frame_corners) < 2:
                continue

            # Triangulate each point
            _points_3d = np.zeros((GRID_ROWS * GRID_COLS, 3))
            for _pt_idx in range(GRID_ROWS * GRID_COLS):
                _pts_2d_list = []
                for _cam_idx, _corners in _frame_corners.items():
                    if _pt_idx < len(_corners):
                        _pts_2d_list.append(_corners[_pt_idx])

                if len(_pts_2d_list) >= 2:
                    _pts_2d = np.array(_pts_2d_list)[np.newaxis, :, :].astype(np.float64)
                    _xyz, _err = multi_cam_point_positions(_pts_2d, cpar, cals)
                    _points_3d[_pt_idx] = _xyz[0]

            triangulated_frames[_frame_idx] = _points_3d

            # Compute metrics for this frame
            _centroid = np.mean(_points_3d, axis=0)
            _centered = _points_3d - _centroid
            _, _, _Vt = np.linalg.svd(_centered)
            _normal = _Vt[2, :]
            _deviations = np.dot(_centered, _normal)
            _rms_planarity = np.sqrt(np.mean(_deviations**2))
            _max_planarity = np.max(np.abs(_deviations))

            # Distance errors
            _dist_errors = []
            for _i in range(GRID_ROWS):
                for _j in range(GRID_COLS - 1):
                    _idx1 = _i * GRID_COLS + _j
                    _idx2 = _i * GRID_COLS + (_j + 1)
                    _dist = np.linalg.norm(_points_3d[_idx2] - _points_3d[_idx1])
                    _dist_errors.append(_dist - GRID_SPACING)

            for _i in range(GRID_ROWS - 1):
                for _j in range(GRID_COLS):
                    _idx1 = _i * GRID_COLS + _j
                    _idx2 = (_i + 1) * GRID_COLS + _j
                    _dist = np.linalg.norm(_points_3d[_idx2] - _points_3d[_idx1])
                    _dist_errors.append(_dist - GRID_SPACING)

            _rms_distance = np.sqrt(np.mean(np.array(_dist_errors)**2))
            _max_distance = np.max(np.abs(_dist_errors))

            frame_metrics[_frame_idx] = {
                'rms_planarity': _rms_planarity,
                'max_planarity': _max_planarity,
                'rms_distance': _rms_distance,
                'max_distance': _max_distance,
            }

        # Summary
        _avg_planarity = np.mean([m['rms_planarity'] for m in frame_metrics.values()])
        _avg_distance = np.mean([m['rms_distance'] for m in frame_metrics.values()])

        mo.md(f"""
        ### Triangulation Complete

        | Metric | Mean | Std |
        |--------|------|-----|
        | **RMS Planarity** | {_avg_planarity:.4f} mm | {np.std([m['rms_planarity'] for m in frame_metrics.values()]):.4f} mm |
        | **RMS Distance** | {_avg_distance:.4f} mm | {np.std([m['rms_distance'] for m in frame_metrics.values()]):.4f} mm |

        **Frames triangulated:** {len(triangulated_frames)}
        """)

    return (frame_metrics,)


@app.cell
def _(frame_metrics, mo, pd):
    """
    Display per-frame metrics.
    """
    if not frame_metrics:
        mo.md("❌ No metrics to display")
    else:
        _df_metrics = pd.DataFrame(frame_metrics).T
        _df_metrics.index.name = 'Frame'
        mo.md("### Per-Frame Geometric Metrics (Before Optimization)")
        mo.ui.dataframe(_df_metrics)

    return


@app.cell
def _(np):
    def compute_planarity_error(points_3d):
        """Fit plane and compute perpendicular deviations."""
        _centroid = np.mean(points_3d, axis=0)
        _centered = points_3d - _centroid
        _, _, _Vt = np.linalg.svd(_centered)
        _normal = _Vt[2, :]
        _deviations = np.dot(_centered, _normal)
        _rms = np.sqrt(np.mean(_deviations**2))
        return _deviations, _rms, _normal, _centroid

    return (compute_planarity_error,)


@app.cell
def _(GRID_COLS, GRID_ROWS, GRID_SPACING, np):
    def compute_distance_errors(points_3d, rows=GRID_ROWS, cols=GRID_COLS, spacing=GRID_SPACING):
        """Compute distance constraint errors."""
        _errors = []

        # Horizontal
        for _i in range(rows):
            for _j in range(cols - 1):
                _idx1 = _i * cols + _j
                _idx2 = _i * cols + (_j + 1)
                _dist = np.linalg.norm(points_3d[_idx2] - points_3d[_idx1])
                _errors.append(_dist - spacing)

        # Vertical
        for _i in range(rows - 1):
            for _j in range(cols):
                _idx1 = _i * cols + _j
                _idx2 = (_i + 1) * cols + _j
                _dist = np.linalg.norm(points_3d[_idx2] - points_3d[_idx1])
                _errors.append(_dist - spacing)

        # Diagonal
        _diag_spacing = np.sqrt(2) * spacing
        for _i in range(rows - 1):
            for _j in range(cols - 1):
                _idx1 = _i * cols + _j
                _idx2 = (_i + 1) * cols + (_j + 1)
                _dist = np.linalg.norm(points_3d[_idx2] - points_3d[_idx1])
                _errors.append(_dist - _diag_spacing)

        return np.array(_errors)


    return (compute_distance_errors,)


@app.cell
def _(
    GRID_COLS,
    GRID_ROWS,
    compute_distance_errors,
    compute_planarity_error,
    image_coordinates,
    np,
):
    def grid_ba_residuals(
        calib_vec, frames_data, cpar, calibs, active_cams,
        w_planarity, w_distance, pos_scale=1.0,
    ):
        """
        Bundle adjustment residuals using multiple frames.

        calib_vec: Only camera parameters (no 3D points - they're fixed from triangulation)
        """
        num_cams = len(calibs)
        num_points = GRID_ROWS * GRID_COLS
        active_cams = np.asarray(active_cams, dtype=bool)
        num_active = int(np.sum(active_cams))
        cam_params_len = num_active * 6

        # Update camera parameters
        calib_pars = calib_vec[:cam_params_len].reshape(-1, 2, 3)
        _ptr = 0
        for _cam, _cal in enumerate(calibs):
            if not active_cams[_cam]:
                continue
            _pars = calib_pars[_ptr]
            _cal.set_pos(_pars[0] * pos_scale)
            _cal.set_angles(_pars[1])
            _ptr += 1

        # Compute residuals for all frames
        _mm_params = cpar.get_multimedia_params()
        _residuals = []

        for _frame_idx, _points_3d in frames_data.items():
            # Reprojection errors for all cameras
            for _cam in range(num_cams):
                if not active_cams[_cam]:
                    continue
                if _cam not in frames_data[_frame_idx]:
                    continue
                _corners = frames_data[_frame_idx][_cam]
                try:
                    _proj = image_coordinates(_points_3d, calibs[_cam], _mm_params)
                    _diff = _corners - _proj
                    _residuals.extend(_diff.ravel())
                except Exception:
                    _residuals.extend([1e6] * (num_points * 2))

            # Planarity constraint (weighted)
            if w_planarity > 0:
                _planarity_devs, _, _, _ = compute_planarity_error(_points_3d)
                _residuals.extend(np.sqrt(w_planarity) * _planarity_devs)

            # Distance constraints (weighted)
            if w_distance > 0:
                _distance_errors = compute_distance_errors(_points_3d)
                _residuals.extend(np.sqrt(w_distance) * _distance_errors)

        return np.nan_to_num(np.asarray(_residuals, dtype=float), nan=1e6, posinf=1e6, neginf=-1e6)


    return (grid_ba_residuals,)


@app.cell
def _(
    Calibration,
    GRID_COLS,
    GRID_ROWS,
    cals,
    cpar,
    frames_data,
    grid_ba_residuals,
    least_squares,
    mo,
    np,
):
    """
    Run bundle adjustment optimization.
    """
    if not frames_data:
        mo.md("❌ No frames to optimize")
        result = None
        cals_optimized = None
        diagnostics = None
    else:
        num_cams_ba = len(cals)
        num_points = GRID_ROWS * GRID_COLS
        pos_scale = 1.0

        # All cameras active
        active_cams = np.ones(num_cams_ba, dtype=bool)
        num_active = num_cams_ba
        cam_params_len = num_active * 6

        # Initial camera parameters
        calib_vec = np.empty((num_active, 2, 3), dtype=float)
        _ptr = 0
        for _cam in range(num_cams_ba):
            calib_vec[_ptr, 0] = cals[_cam].get_pos() / pos_scale
            calib_vec[_ptr, 1] = cals[_cam].get_angles()
            _ptr += 1

        x0 = calib_vec.reshape(-1)

        # Weights
        w_planarity = 0.1
        w_distance = 1.0

        # Initial cost
        initial_residuals = grid_ba_residuals(
            x0, frames_data, cpar, cals, active_cams, w_planarity, w_distance, pos_scale
        )
        fun_initial = np.sum(initial_residuals**2)

        mo.md(f"""
        ### Bundle Adjustment Setup

        | Parameter | Value |
        |-----------|-------|
        | **Cameras** | {num_cams_ba} |
        | **Frames** | {len(frames_data)} |
        | **Points per frame** | {num_points} |
        | **Optimization parameters** | {len(x0)} ({num_active} cameras × 6 params) |
        | **Initial cost** | {fun_initial:.4f} |
        | **Weights** | planarity={w_planarity}, distance={w_distance} |
        """)

        print(f"Running bundle adjustment over {len(frames_data)} frames...")

        result = least_squares(
            grid_ba_residuals, x0,
            args=(frames_data, cpar, cals, active_cams, w_planarity, w_distance, pos_scale),
            method='trf', loss='soft_l1',
            xtol=1e-8, ftol=1e-8, gtol=1e-6, max_nfev=5000, verbose=2
        )

        # Extract optimized parameters
        calib_pars = result.x[:cam_params_len].reshape(-1, 2, 3)

        # Create optimized calibrations
        cals_optimized = []
        for _cam in range(num_cams_ba):
            _cal_opt = Calibration()
            _cal_opt.copy_from(cals[_cam])
            _cal_opt.set_pos(calib_pars[_cam, 0] * pos_scale)
            _cal_opt.set_angles(calib_pars[_cam, 1])
            cals_optimized.append(_cal_opt)

        # Final cost
        fun_final = np.sum(grid_ba_residuals(
            result.x, frames_data, cpar, cals_optimized, active_cams,
            w_planarity, w_distance, pos_scale
        )**2)

        # Compute diagnostics
        diagnostics = {
            'fun_initial': fun_initial,
            'fun_final': fun_final,
            'improvement_pct': 100 * (fun_initial - fun_final) / fun_initial if fun_initial > 0 else 0,
            'success': result.success,
            'n_function_evals': result.nfev,
            'message': result.message,
        }

        mo.md(f"""
        ### Optimization Results

        | Metric | Value |
        |--------|-------|
        | **Initial Cost** | {fun_initial:.4f} |
        | **Final Cost** | {fun_final:.4f} |
        | **Improvement** | {diagnostics['improvement_pct']:.1f}% |
        | **Success** | {diagnostics['success']} |
        | **Function Evaluations** | {diagnostics['n_function_evals']} |
        """)

    return (cals_optimized,)


@app.cell
def _(
    cals_optimized,
    compute_distance_errors,
    compute_planarity_error,
    frames_data,
    mo,
    np,
):
    """
    Compute post-optimization metrics.
    """
    if cals_optimized is None:
        mo.md("❌ No optimization results")
        optimized_metrics = {}
    else:
        # Recompute metrics with optimized calibration
        optimized_metrics = {}

        for _frame_idx, _points_3d in frames_data.items():
            # Planarity
            _planarity_devs, _rms_planarity, _, _ = compute_planarity_error(_points_3d)
            _max_planarity = np.max(np.abs(_planarity_devs))

            # Distance errors
            _dist_errors = compute_distance_errors(_points_3d)
            _rms_distance = np.sqrt(np.mean(_dist_errors**2))
            _max_distance = np.max(np.abs(_dist_errors))

            optimized_metrics[_frame_idx] = {
                'rms_planarity': _rms_planarity,
                'max_planarity': _max_planarity,
                'rms_distance': _rms_distance,
                'max_distance': _max_distance,
            }

        # Summary
        _avg_planarity_opt = np.mean([m['rms_planarity'] for m in optimized_metrics.values()])
        _avg_distance_opt = np.mean([m['rms_distance'] for m in optimized_metrics.values()])

        mo.md(f"""
        ### Geometric Metrics After Optimization

        | Metric | Mean | Std |
        |--------|------|-----|
        | **RMS Planarity** | {_avg_planarity_opt:.4f} mm | {np.std([m['rms_planarity'] for m in optimized_metrics.values()]):.4f} mm |
        | **RMS Distance** | {_avg_distance_opt:.4f} mm | {np.std([m['rms_distance'] for m in optimized_metrics.values()]):.4f} mm |
        """)

    return


@app.cell
def _(cals, cals_optimized, mo, np):
    """
    Display optimized camera parameters.
    """
    if cals_optimized is None:
        mo.md("❌ No optimization results")
    else:
        num_cams_disp = len(cals)

        mo.md("""
        ### Optimized Camera Parameters

        **Positions (mm) and Angles (degrees):**
        """)

        _results_text = """
        | Camera | X (mm) | Y (mm) | Z (mm) | ω (deg) | φ (deg) | κ (deg) |
        |--------|--------|--------|--------|---------|---------|---------|
        """

        for _cam in range(num_cams_disp):
            _pos = cals_optimized[_cam].get_pos()
            _angs = cals_optimized[_cam].get_angles()
            _results_text += f"| {_cam + 1} | {_pos[0]:.3f} | {_pos[1]:.3f} | {_pos[2]:.3f} | {np.degrees(_angs[0]):.4f} | {np.degrees(_angs[1]):.4f} | {np.degrees(_angs[2]):.4f} |\n"

        mo.md(_results_text)

        mo.md("""
        ### Parameter Changes (Optimized - Initial)
        """)

        _delta_text = """
        | Camera | ΔX (mm) | ΔY (mm) | ΔZ (mm) | Δω (deg) | Δφ (deg) | Δκ (deg) |
        |--------|---------|---------|---------|----------|----------|----------|
        """

        for _cam in range(num_cams_disp):
            _pos_init = cals[_cam].get_pos()
            _pos_opt = cals_optimized[_cam].get_pos()
            _angs_init = cals[_cam].get_angles()
            _angs_opt = cals_optimized[_cam].get_angles()

            _delta_pos = np.array(_pos_opt) - np.array(_pos_init)
            _delta_angs = np.degrees(np.array(_angs_opt) - np.array(_angs_init))

            _delta_text += f"| {_cam + 1} | {_delta_pos[0]:.3f} | {_delta_pos[1]:.3f} | {_delta_pos[2]:.3f} | {_delta_angs[0]:.4f} | {_delta_angs[1]:.4f} | {_delta_angs[2]:.4f} |\n"

        mo.md(_delta_text)

    return


@app.cell
def _(cals, cals_optimized, mo, plt):
    """
    Visualize camera positions before and after optimization.
    """
    if cals_optimized is None:
        mo.md("❌ No optimization results")
    else:
        num_cams_viz = len(cals)

        _fig, _axes = plt.subplots(1, 2, figsize=(16, 6), subplot_kw={'projection': '3d'})

        # Before optimization
        _ax = _axes[0]
        for _cam in range(num_cams_viz):
            _pos = cals[_cam].get_pos()
            _ax.scatter(_pos[0], _pos[1], _pos[2], s=100, label=f'Cam {_cam+1}')
            _ax.text(_pos[0], _pos[1], _pos[2], f'C{_cam+1}', fontsize=12)

        _ax.set_xlabel('X (mm)')
        _ax.set_ylabel('Y (mm)')
        _ax.set_zlabel('Z (mm)')
        _ax.set_title('Initial Camera Positions')
        _ax.legend()
        _ax.grid(True, alpha=0.3)

        # After optimization
        _ax = _axes[1]
        for _cam in range(num_cams_viz):
            _pos = cals_optimized[_cam].get_pos()
            _ax.scatter(_pos[0], _pos[1], _pos[2], s=100, label=f'Cam {_cam+1}')
            _ax.text(_pos[0], _pos[1], _pos[2], f'C{_cam+1}', fontsize=12)

        _ax.set_xlabel('X (mm)')
        _ax.set_ylabel('Y (mm)')
        _ax.set_zlabel('Z (mm)')
        _ax.set_title('Optimized Camera Positions')
        _ax.legend()
        _ax.grid(True, alpha=0.3)

        plt.tight_layout()
        mo.pyplot(_fig)

    return


@app.cell
def _(GRID_COLS, GRID_ROWS, cals_optimized, frames_data, mo, plt):
    """
    Visualize triangulated grid points.
    """
    if not frames_data or cals_optimized is None:
        mo.md("❌ No data to visualize")
    else:
        # Show first 3 frames
        _frames_to_show = list(frames_data.keys())[:3]

        _fig = plt.figure(figsize=(18, 6))

        for _idx, _frame_idx in enumerate(_frames_to_show):
            _ax = _fig.add_subplot(1, len(_frames_to_show), _idx+1, projection='3d')
            _points = frames_data[_frame_idx]

            _ax.scatter(_points[:, 0], _points[:, 1], _points[:, 2], c='red', s=30)

            # Draw grid connections
            _points_grid = _points.reshape(GRID_ROWS, GRID_COLS, 3)
            for _i in range(GRID_ROWS):
                _ax.plot(_points_grid[_i, :, 0], _points_grid[_i, :, 1], _points_grid[_i, :, 2], 'b-', linewidth=0.5, alpha=0.5)
            for _j in range(GRID_COLS):
                _ax.plot(_points_grid[:, _j, 0], _points_grid[:, _j, 1], _points_grid[:, _j, 2], 'b-', linewidth=0.5, alpha=0.5)

            _ax.set_xlabel('X (mm)')
            _ax.set_ylabel('Y (mm)')
            _ax.set_zlabel('Z (mm)')
            _ax.set_title(f'Frame {_frame_idx}')
            _ax.view_init(elev=20, azim=45)

        plt.tight_layout()
        mo.pyplot(_fig)

    return


if __name__ == "__main__":
    app.run()
