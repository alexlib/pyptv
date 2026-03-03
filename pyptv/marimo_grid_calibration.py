import marimo

__generated_with = "0.20.2"
app = marimo.App(width="full")

with app.setup:
    import marimo as mo
    from pathlib import Path
    import numpy as np
    import cv2
    import matplotlib.pyplot as plt
    from optv.calibration import Calibration
    from optv.imgcoord import image_coordinates
    from optv.transforms import convert_arr_metric_to_pixel, convert_arr_pixel_to_metric
    from optv.tracking_framebuf import TargetArray
    from optv.orientation import multi_cam_point_positions
    from pyptv.parameter_manager import ParameterManager
    from pyptv.experiment import Experiment
    from pyptv import ptv
    from scipy.optimize import least_squares
    from scipy import sparse
    import imageio.v3 as iio
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    from scipy.spatial.transform import Rotation as R


@app.cell
def _():
    mo.md("""
    # Grid-Based Calibration Refinement for OpenPTV

    This notebook performs bundle adjustment calibration refinement using a planar grid target.

    **Workflow:**
    1. Load PyPTV experiment parameters from YAML file
    2. Load calibration images and initial calibration
    3. Detect grid points using OpenCV
    4. Optimize camera exterior orientation using geometric constraints:
       - **Planarity**: All grid points lie on a single plane
       - **Distance**: Adjacent points at known spacing (e.g., 120 mm)

    This is analogous to dumbbell calibration but uses a planar grid with multiple constraints.
    """)
    return


@app.cell
def _():
    # File selection for YAML parameters
    yaml_path_str = mo.ui.text(
        value='/home/user/Downloads/Illmenau/pyPTV_folder/parameters_Run4.yaml',
        label='YAML Parameters File Path',
        full_width=True
    )
    yaml_path_str
    return (yaml_path_str,)


@app.cell
def _(yaml_path_str):
    yaml_path = Path(yaml_path_str.value).expanduser().resolve()

    status_msg = f"**⚠️ File not found:** {yaml_path}" if not yaml_path.exists() else f"**✓ Loaded:** {yaml_path}"
    mo.md(status_msg)
    return (yaml_path,)


@app.cell
def _(yaml_path):
    # Load parameters from YAML
    pm = ParameterManager()
    pm.from_yaml(yaml_path)
    exp = Experiment(pm=pm)

    params = pm.parameters
    num_cams = int(params.get("num_cams", pm.num_cams or 0) or 0)

    mo.md(f"""
    ### Experiment Parameters Loaded

    - **YAML File:** {yaml_path.name}
    - **Number of Cameras:** {num_cams}
    - **Image Size:** {params.get('ptv', {}).get('imx', 'N/A')} × {params.get('ptv', {}).get('imy', 'N/A')} pixels
    """)

    return num_cams, pm


@app.cell
def _(num_cams, pm, yaml_path):
    # Load images and calibrations
    cals = []
    images = []
    images_cv2 = []

    ptv_params = pm.parameters.get('ptv', {})
    cpar = ptv._populate_cpar(ptv_params, num_cams)
    img_names = ptv_params.get('img_name', [])
    _cal_ori = pm.parameters.get('cal_ori', {})
    ori_names = _cal_ori.get('img_ori', [])

    base_path = Path(yaml_path).parent
    load_status = []

    for _i in range(num_cams):
        # Load images
        _img_path = img_names[_i] if _i < len(img_names) else None
        if _img_path:
            if not Path(_img_path).is_absolute():
                _img_path = base_path / _img_path
            try:
                _img = iio.imread(_img_path)
                images.append(_img)
                images_cv2.append(cv2.imread(str(_img_path), 0))
            except Exception as _e:
                load_status.append(f"❌ Camera {_i+1}: Failed to load image - {_e}")
                images.append(np.zeros((ptv_params.get('imy', 1024), ptv_params.get('imx', 1024)), dtype=np.uint8))
                images_cv2.append(np.zeros((ptv_params.get('imy', 1024), ptv_params.get('imx', 1024)), dtype=np.uint8))
        else:
            load_status.append(f"❌ Camera {_i+1}: No image path specified")
            images.append(np.zeros((ptv_params.get('imy', 1024), ptv_params.get('imx', 1024)), dtype=np.uint8))
            images_cv2.append(np.zeros((ptv_params.get('imy', 1024), ptv_params.get('imx', 1024)), dtype=np.uint8))

        # Load calibration
        _cal = Calibration()
        _ori_path = ori_names[_i] if _i < len(ori_names) else None

        if _ori_path:
            _ori_file_path = base_path / _ori_path
            _addpar_file_path = Path(str(_ori_file_path).replace('.ori', '') + '.addpar')
            if not _addpar_file_path.exists():
                _addpar_file_path = Path(str(_ori_file_path).replace('.tif.ori', '') + '.addpar')

            if _ori_file_path.exists() and _addpar_file_path.exists():
                _cal.from_file(str(_ori_file_path), str(_addpar_file_path))
                load_status.append(f"✓ Camera {_i+1}: Calibration loaded")
            else:
                load_status.append(f"⚠ Camera {_i+1}: Missing calibration files")
        else:
            load_status.append(f"⚠ Camera {_i+1}: No calibration path specified")

        cals.append(_cal)

    mo.md("### Images and Calibrations\n\n" + "\n".join(load_status))

    return cals, cpar, images, images_cv2


@app.function
def draw_origin_axes(ax, length=2.0):
    """Draws X, Y, Z axes at the origin (0,0,0)."""
    # X axis - Red, Y axis - Green, Z axis - Blue
    origins = np.zeros((3, 3))  # [0,0,0] for all three arrows
    directions = np.eye(3) * length # [[L,0,0], [0,L,0], [0,0,L]]
    colors = ['r', 'g', 'b']
    labels = ['X', 'Y', 'Z']

    for i in range(3):
        ax.quiver(origins[i,0], origins[i,1], origins[i,2], 
                  directions[i,0], directions[i,1], directions[i,2], 
                  color=colors[i], arrow_length_ratio=0.1, label=labels[i])


@app.function
def create_camera_figure(positions, euler_angles, scale=1.0, euler_order='xyz'):
    """
    Generates a 3D plot showing camera positions as pyramids.
    
    Args:
        positions: List or array of [x, y, z] coordinates.
        euler_angles: List or array of [a, b, c] angles in degrees.
        scale: Size of the camera pyramid.
        euler_order: Convention for Euler angles (e.g., 'xyz', 'zyx').
    """
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    # 1. Define base pyramid geometry (local coordinates)
    # Apex at (0,0,0), looking towards +Z
    w, h, d = 0.5 * scale, 0.4 * scale, 1.0 * scale
    local_verts = np.array([
        [0, 0, 0],         # 0: Apex (Focal point)
        [-w, -h, d],       # 1: Top-Left
        [w, -h, d],        # 2: Top-Right
        [w, h, d],         # 3: Bottom-Right
        [-w, h, d]         # 4: Bottom-Left
    ])

    for pos, angles in zip(positions, euler_angles):
        # 2. Compute Rotation and Translation
        rot_matrix = R.from_euler(euler_order, angles, degrees=True).as_matrix()
        
        # Transform local vertices: (Rotate then Translate)
        world_verts = (rot_matrix @ local_verts.T).T + pos

        # 3. Define the faces of the pyramid
        # Each face is a list of vertex indices
        faces = [
            [world_verts[0], world_verts[1], world_verts[2]], # Top side
            [world_verts[0], world_verts[2], world_verts[3]], # Right side
            [world_verts[0], world_verts[3], world_verts[4]], # Bottom side
            [world_verts[0], world_verts[4], world_verts[1]], # Left side
            [world_verts[1], world_verts[2], world_verts[3], world_verts[4]] # Base
        ]

        # 4. Add to plot
        poly = Poly3DCollection(faces, alpha=0.3, linewidths=1, edgecolors='k')
        # Use a random color or specific logic for different cameras
        poly.set_facecolor(np.random.rand(3,))
        ax.add_collection3d(poly)
        
        # Plot the focal point as a dot
        ax.scatter(pos[0], pos[1], pos[2], color='black', s=20)

    # 5. Set axis labels and viewing angle
    ax.set_xlabel('X Axis')
    ax.set_ylabel('Y Axis')
    ax.set_zlabel('Z Axis')
    
    # Adjust plot limits based on positions
    all_pos = np.array(positions)
    max_range = np.array([all_pos[:,0].max()-all_pos[:,0].min(), 
                          all_pos[:,1].max()-all_pos[:,1].min(), 
                          all_pos[:,2].max()-all_pos[:,2].min()]).max() / 2.0
    mid_x, mid_y, mid_z = all_pos.mean(axis=0)
    ax.set_xlim(mid_x - max_range - scale, mid_x + max_range + scale)
    ax.set_ylim(mid_y - max_range - scale, mid_y + max_range + scale)
    ax.set_zlim(mid_z - max_range - scale, mid_z + max_range + scale)

    draw_origin_axes(ax, length=scale)

    plt.title("3D Camera Pose Visualization")
    # plt.show()
    return mo.mpl.interactive(fig)


@app.cell
def _(cals):
    # --- Example Usage ---
    # Camera 1 at origin, no rotation
    # Camera 2 at (3, 3, 3), rotated 45 degrees around Y
    # Camera 3 at (-2, 4, 1), rotated 90 around X and 20 around Z
    # cam_positions = [
    #     [0, 0, 0],
    #     [3, 3, 3],
    #     [-2, 4, 1]
    # ]
    # cam_angles = [
    #     [0, 0, 0],
    #     [0, 45, 0],
    #     [90, 0, 20]
    # ]
    cam_positions = [cal.get_pos() for cal in cals]
    cam_angles = [cal.get_angles() for cal in cals]

    create_camera_figure(cam_positions, cam_angles, scale=1000)
    return


@app.cell
def _():
    # Grid configuration
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
def _(GRID_COLS, GRID_ROWS, images, images_cv2):
    """Detect grid points using OpenCV's findCirclesGrid."""
    board_params = cv2.SimpleBlobDetector_Params()
    board_params.filterByColor = False
    board_params.filterByArea = True
    board_params.minArea = 50
    board_params.filterByCircularity = True
    board_params.minCircularity = 0.7
    detector = cv2.SimpleBlobDetector_create(board_params)

    detection_results = []
    all_corners = []

    for _i_cam, (_im, _im_cv2) in enumerate(zip(images, images_cv2)):
        _found, _corners = cv2.findCirclesGrid(
            _im_cv2, (GRID_ROWS, GRID_COLS),
            flags=cv2.CALIB_CB_SYMMETRIC_GRID,
            blobDetector=detector
        )

        if _found:
            _corners_squeezed = np.squeeze(_corners)
            detection_results.append(f"✓ Camera {_i_cam+1}: Grid detected ({_corners_squeezed.shape[0]} points)")
            all_corners.append(_corners_squeezed)
        else:
            detection_results.append(f"❌ Camera {_i_cam+1}: Grid NOT detected")
            all_corners.append(None)

    mo.md("### Grid Detection Results\n\n" + "\n".join(detection_results))

    return (all_corners,)


@app.cell
def _(GRID_COLS, GRID_ROWS, all_corners, images, num_cams):
    """Visualize detected grid points on each camera image."""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    axes_flat = axes.flatten()

    for _cam_idx in range(num_cams):
        _ax = axes_flat[_cam_idx]
        _ax.imshow(images[_cam_idx], cmap='gray')
        _ax.set_title(f"Camera {_cam_idx + 1}")
        _ax.axis('on')

        _corners = all_corners[_cam_idx]
        if _corners is not None:
            _ax.scatter(_corners[:, 0], _corners[:, 1], c='red', s=30, marker='o', linewidths=2)
            _corners_grid = _corners.reshape(GRID_ROWS, GRID_COLS, 2)

            for _i in range(GRID_ROWS):
                _ax.plot(_corners_grid[_i, :, 0], _corners_grid[_i, :, 1], 'b-', linewidth=0.5, alpha=0.5)
            for _j in range(GRID_COLS):
                _ax.plot(_corners_grid[:, _j, 0], _corners_grid[:, _j, 1], 'b-', linewidth=0.5, alpha=0.5)

        _ax.set_xlim(0, images[_cam_idx].shape[1])
        _ax.set_ylim(images[_cam_idx].shape[0], 0)

    plt.tight_layout()
    mo.mpl.interactive(fig)

    return


@app.cell
def _(GRID_COLS, GRID_ROWS, all_corners, cpar, num_cams):
    """Prepare detected points in metric coordinates for bundle adjustment."""
    num_points = GRID_ROWS * GRID_COLS
    valid_cams = [i for i, c in enumerate(all_corners) if c is not None]

    if len(valid_cams) < 2:
        mo.md("❌ **Error:** Need at least 2 cameras with valid grid detection.")

    targets_pixel = []
    targets_metric = []

    for cam_idx in range(num_cams):
        corners = all_corners[cam_idx]
        if corners is not None:
            targets_pixel.append(corners.astype(np.float64))
            targets_metric.append(convert_arr_pixel_to_metric(corners.astype(np.float64), cpar))
        else:
            targets_pixel.append(np.zeros((num_points, 2)))
            targets_metric.append(np.zeros((num_points, 2)))

    targets_pixel = np.array(targets_pixel)
    targets_metric = np.array(targets_metric)

    mo.md(f"""
    ### Targets Prepared

    - **Number of Cameras:** {num_cams}
    - **Points per Camera:** {num_points}
    - **Valid Cameras:** {len(valid_cams)}
    """)

    return num_points, targets_metric, valid_cams


@app.function
def compute_planarity_error(points_3d):
    """Fit plane and compute perpendicular deviations."""
    centroid = np.mean(points_3d, axis=0)
    centered = points_3d - centroid
    _, _, Vt = np.linalg.svd(centered)
    normal = Vt[2, :]
    deviations = np.dot(centered, normal)
    rms = np.sqrt(np.mean(deviations**2))
    return deviations, rms, normal, centroid


@app.cell
def _(GRID_COLS, GRID_ROWS, GRID_SPACING):
    def compute_distance_errors(points_3d, rows=GRID_ROWS, cols=GRID_COLS, spacing=GRID_SPACING):
        """Compute distance constraint errors."""
        errors = []

        # Horizontal
        for i in range(rows):
            for j in range(cols - 1):
                idx1 = i * cols + j
                idx2 = i * cols + (j + 1)
                dist = np.linalg.norm(points_3d[idx2] - points_3d[idx1])
                errors.append(dist - spacing)

        # Vertical
        for i in range(rows - 1):
            for j in range(cols):
                idx1 = i * cols + j
                idx2 = (i + 1) * cols + j
                dist = np.linalg.norm(points_3d[idx2] - points_3d[idx1])
                errors.append(dist - spacing)

        # Diagonal
        diag_spacing = np.sqrt(2) * spacing
        for i in range(rows - 1):
            for j in range(cols - 1):
                idx1 = i * cols + j
                idx2 = (i + 1) * cols + (j + 1)
                dist = np.linalg.norm(points_3d[idx2] - points_3d[idx1])
                errors.append(dist - diag_spacing)

        return np.array(errors)


    return (compute_distance_errors,)


@app.cell
def _(GRID_COLS, GRID_ROWS, compute_distance_errors):
    def grid_ba_residuals(
        calib_vec, targets_metric, cpar, calibs, active_cams,
        w_planarity, w_distance, pos_scale=1.0,
    ):
        """Bundle adjustment residuals."""
        num_cams = len(calibs)
        num_points = GRID_ROWS * GRID_COLS
        active_cams = np.asarray(active_cams, dtype=bool)
        num_active = int(np.sum(active_cams))
        cam_params_len = num_active * 6

        # Update camera parameters
        calib_pars = calib_vec[:cam_params_len].reshape(-1, 2, 3)
        ptr = 0
        for cam, cal in enumerate(calibs):
            if not active_cams[cam]:
                continue
            pars = calib_pars[ptr]
            cal.set_pos(pars[0] * pos_scale)
            cal.set_angles(pars[1])
            ptr += 1

        # Extract 3D points
        points_3d = calib_vec[cam_params_len:].reshape(num_points, 3)

        # Compute residuals
        mm_params = cpar.get_multimedia_params()
        residuals = []

        for cam in range(num_cams):
            if not active_cams[cam]:
                continue
            try:
                proj = image_coordinates(points_3d, calibs[cam], mm_params)
                diff = targets_metric[cam] - proj
                residuals.extend(diff.ravel())
            except Exception:
                residuals.extend([1e6] * (num_points * 2))

        if w_planarity > 0:
            planarity_devs, _, _, _ = compute_planarity_error(points_3d)
            residuals.extend(np.sqrt(w_planarity) * planarity_devs)

        if w_distance > 0:
            distance_errors = compute_distance_errors(points_3d)
            residuals.extend(np.sqrt(w_distance) * distance_errors)

        return np.nan_to_num(np.asarray(residuals, dtype=float), nan=1e6, posinf=1e6, neginf=-1e6)


    return (grid_ba_residuals,)


@app.cell
def _(GRID_COLS, GRID_ROWS):
    def grid_ba_jac_sparsity(active_cams, w_planarity, w_distance, num_points):
        """Jacobian sparsity pattern."""
        num_cams = len(active_cams)
        active_cams = np.asarray(active_cams, dtype=bool)
        num_active = int(np.sum(active_cams))
        cam_params_len = num_active * 6

        reproj_residuals = num_active * num_points * 2
        planarity_residuals = num_points if w_planarity > 0 else 0

        horiz = GRID_ROWS * (GRID_COLS - 1)
        vert = (GRID_ROWS - 1) * GRID_COLS
        diag = (GRID_ROWS - 1) * (GRID_COLS - 1)
        distance_residuals = horiz + vert + diag if w_distance > 0 else 0

        total_residuals = reproj_residuals + planarity_residuals + distance_residuals
        total_params = cam_params_len + num_points * 3

        pattern = sparse.lil_matrix((total_residuals, total_params), dtype=bool)

        active_map = {}
        active_idx = 0
        for cam_idx, is_active in enumerate(active_cams):
            if is_active:
                active_map[cam_idx] = active_idx
                active_idx += 1

        row = 0

        for cam_idx in range(num_cams):
            if not active_cams[cam_idx]:
                continue
            for pt_idx in range(num_points):
                point_cols = list(range(cam_params_len + pt_idx * 3, cam_params_len + pt_idx * 3 + 3))
                if cam_idx in active_map:
                    cam_cols = list(range(active_map[cam_idx] * 6, active_map[cam_idx] * 6 + 6))
                    for _ in range(2):
                        pattern[row, cam_cols] = True
                        pattern[row, point_cols] = True
                        row += 1
                else:
                    for _ in range(2):
                        pattern[row, point_cols] = True
                        row += 1

        if w_planarity > 0:
            all_point_cols = list(range(cam_params_len, cam_params_len + num_points * 3))
            for _ in range(num_points):
                pattern[row, all_point_cols] = True
                row += 1

        if w_distance > 0:
            for i in range(GRID_ROWS):
                for j in range(GRID_COLS - 1):
                    idx1 = i * GRID_COLS + j
                    idx2 = i * GRID_COLS + (j + 1)
                    cols1 = list(range(cam_params_len + idx1 * 3, cam_params_len + idx1 * 3 + 3))
                    cols2 = list(range(cam_params_len + idx2 * 3, cam_params_len + idx2 * 3 + 3))
                    pattern[row, cols1 + cols2] = True
                    row += 1

            for i in range(GRID_ROWS - 1):
                for j in range(GRID_COLS):
                    idx1 = i * GRID_COLS + j
                    idx2 = (i + 1) * GRID_COLS + j
                    cols1 = list(range(cam_params_len + idx1 * 3, cam_params_len + idx1 * 3 + 3))
                    cols2 = list(range(cam_params_len + idx2 * 3, cam_params_len + idx2 * 3 + 3))
                    pattern[row, cols1 + cols2] = True
                    row += 1

            for i in range(GRID_ROWS - 1):
                for j in range(GRID_COLS - 1):
                    idx1 = i * GRID_COLS + j
                    idx2 = (i + 1) * GRID_COLS + (j + 1)
                    cols1 = list(range(cam_params_len + idx1 * 3, cam_params_len + idx1 * 3 + 3))
                    cols2 = list(range(cam_params_len + idx2 * 3, cam_params_len + idx2 * 3 + 3))
                    pattern[row, cols1 + cols2] = True
                    row += 1

        return pattern.tocsr()


    return (grid_ba_jac_sparsity,)


@app.cell
def _(
    GRID_COLS,
    GRID_SPACING,
    cals,
    cpar,
    grid_ba_jac_sparsity,
    grid_ba_residuals,
    num_cams,
    num_points,
    targets_metric,
    valid_cams,
):
    """Run grid bundle adjustment."""
    pos_scale = 1.0
    active_cams = np.zeros(num_cams, dtype=bool)
    for _cam_idx in valid_cams:
        active_cams[_cam_idx] = True

    num_active = int(np.sum(active_cams))
    cam_params_len = num_active * 6

    calib_vec = np.empty((num_active, 2, 3), dtype=float)
    _ptr = 0
    for _cam in range(num_cams):
        if not active_cams[_cam]:
            continue
        calib_vec[_ptr, 0] = cals[_cam].get_pos() / pos_scale
        calib_vec[_ptr, 1] = cals[_cam].get_angles()
        _ptr += 1

    # Initialize 3D points
    points_3d = np.zeros((num_points, 3), dtype=float)
    for _pt_idx in range(num_points):
        pts_2d_list = []
        for _cam in range(num_cams):
            if active_cams[_cam] and _pt_idx < targets_metric[_cam].shape[0]:
                pts_2d_list.append(targets_metric[_cam][_pt_idx])

        if len(pts_2d_list) >= 2:
            pts_2d = np.array(pts_2d_list)[np.newaxis, :, :]
            xyz, _ = multi_cam_point_positions(pts_2d, cpar, cals)
            points_3d[_pt_idx] = xyz[0]
        else:
            _row = _pt_idx // GRID_COLS
            _col = _pt_idx % GRID_COLS
            points_3d[_pt_idx] = [_col * GRID_SPACING, _row * GRID_SPACING, 500.0]

    x0 = np.concatenate([calib_vec.reshape(-1), points_3d.reshape(-1)])

    w_planarity = 0.1
    w_distance = 1.0

    initial_residuals = grid_ba_residuals(
        x0, targets_metric, cpar, cals, active_cams, w_planarity, w_distance, pos_scale
    )
    fun_initial = np.sum(initial_residuals**2)

    jac_sparsity = grid_ba_jac_sparsity(active_cams, w_planarity, w_distance, num_points)

    print(f"Running grid bundle adjustment...")
    print(f"  Parameters: {len(x0)} ({num_active * 6} camera + {num_points * 3} points)")
    print(f"  Residuals: {len(initial_residuals)}")
    print(f"  Initial cost: {fun_initial:.4f}")

    result = least_squares(
        grid_ba_residuals, x0,
        args=(targets_metric, cpar, cals, active_cams, w_planarity, w_distance, pos_scale),
        jac_sparsity=jac_sparsity, method='trf', loss='soft_l1',
        xtol=1e-8, ftol=1e-8, gtol=1e-6, max_nfev=2000, verbose=2
    )

    # Extract optimized parameters
    calib_pars = result.x[:cam_params_len].reshape(-1, 2, 3)
    points_3d_opt = result.x[cam_params_len:].reshape(num_points, 3)

    return (
        active_cams,
        calib_pars,
        fun_initial,
        points_3d_opt,
        pos_scale,
        result,
        w_distance,
        w_planarity,
    )


@app.cell
def _(
    active_cams,
    calib_pars,
    cals,
    compute_distance_errors,
    cpar,
    fun_initial,
    grid_ba_residuals,
    num_cams,
    points_3d_opt,
    pos_scale,
    result,
    targets_metric,
    w_distance,
    w_planarity,
):
    import copy
    cals_optimized = [Calibration() for _ in range(num_cams)]
    cals_optimized = copy.copy(cals)

    _ptr = 0
    for _cam in range(num_cams):
        # cals_optimized[_cam].copy_from(cals[_cam])
        if active_cams[_cam]:
            cals_optimized[_cam].set_pos(calib_pars[_ptr, 0] * pos_scale)
            cals_optimized[_cam].set_angles(calib_pars[_ptr, 1])
            _ptr += 1

    # Diagnostics
    _planarity_devs, rms_planarity, normal, centroid = compute_planarity_error(points_3d_opt)
    distance_errors = compute_distance_errors(points_3d_opt)
    rms_distance = np.sqrt(np.mean(distance_errors**2))

    fun_final = np.sum(grid_ba_residuals(
        result.x, targets_metric, cpar, cals_optimized, active_cams,
        w_planarity, w_distance, pos_scale
    )**2)

    def compute_per_camera_rms(cals_list):
        _sums = np.zeros(num_cams)
        _counts = np.zeros(num_cams, dtype=int)
        _mm_params = cpar.get_multimedia_params()
        for _cam in range(num_cams):
            if not active_cams[_cam]:
                continue
            try:
                _proj = image_coordinates(points_3d_opt, cals_list[_cam], _mm_params)
                _diff = targets_metric[_cam] - _proj
                _mask = np.isfinite(_diff).all(axis=1)
                if np.any(_mask):
                    _sums[_cam] += float(np.sum(_diff[_mask] ** 2))
                    _counts[_cam] += int(np.sum(_mask))
            except:
                pass
        return np.sqrt(_sums / np.maximum(_counts, 1))

    rms_initial = compute_per_camera_rms(cals)
    rms_final = compute_per_camera_rms(cals_optimized)

    diagnostics = {
        'fun_initial': fun_initial, 'fun_final': fun_final,
        'improvement_pct': 100 * (fun_initial - fun_final) / fun_initial if fun_initial > 0 else 0,
        'rms_initial_per_cam': rms_initial, 'rms_final_per_cam': rms_final,
        'rms_planarity': rms_planarity, 'max_planarity': np.max(np.abs(_planarity_devs)),
        'plane_normal': normal, 'centroid': centroid,
        'rms_distance': rms_distance, 'max_distance': np.max(np.abs(distance_errors)),
        'success': result.success, 'n_function_evals': result.nfev,
    }
    return cals_optimized, diagnostics


@app.cell
def _(active_cams, diagnostics, num_cams):
    results_summary = f"""
    ### Bundle Adjustment Results

    | Metric | Value |
    |--------|-------|
    | **Optimization Success** | {diagnostics['success']} |
    | **Cost Improvement** | {diagnostics['improvement_pct']:.1f}% |
    | **Initial Cost** | {diagnostics['fun_initial']:.4f} |
    | **Final Cost** | {diagnostics['fun_final']:.4f} |

    ### Geometric Constraints

    | Constraint | RMS | Max |
    |------------|-----|-----|
    | **Planarity** | {diagnostics['rms_planarity']:.4f} mm | {diagnostics['max_planarity']:.4f} mm |
    | **Distance** | {diagnostics['rms_distance']:.4f} mm | {diagnostics['max_distance']:.4f} mm |

    ### Reprojection Error (pixels RMS)

    | Camera | Before | After | Improvement |
    |--------|--------|-------|-------------|
    """

    for _cam in range(num_cams):
        if active_cams[_cam]:
            _before = diagnostics['rms_initial_per_cam'][_cam]
            _after = diagnostics['rms_final_per_cam'][_cam]
            _improvement = 100 * (_before - _after) / _before if _before > 0 else 0
            results_summary += f"| {_cam + 1} | {_before:.4f} | {_after:.4f} | {_improvement:.1f}% |\n"

    mo.md(results_summary)

    return


@app.cell
def _(GRID_COLS, GRID_ROWS, points_3d_opt, targets_metric):
    """Visualize bundle adjustment results."""
    _num_cams_viz = len(targets_metric)

    # Plot 1: 3D optimized grid
    fig_3d = plt.figure(figsize=(8, 6))
    ax_3d = fig_3d.add_subplot(projection='3d')
    points_grid = points_3d_opt.reshape(GRID_ROWS, GRID_COLS, 3)

    ax_3d.scatter(points_grid[:, :, 0], points_grid[:, :, 1], points_grid[:, :, 2],
                  c='steelblue', s=50)

    for _i in range(GRID_ROWS):
        ax_3d.plot(points_grid[_i, :, 0], points_grid[_i, :, 1], points_grid[_i, :, 2],
                   'b-', linewidth=0.5, alpha=0.5)
    for _j in range(GRID_COLS):
        ax_3d.plot(points_grid[:, _j, 0], points_grid[:, _j, 1], points_grid[:, _j, 2],
                   'b-', linewidth=0.5, alpha=0.5)

    ax_3d.set_xlabel('X (mm)')
    ax_3d.set_ylabel('Y (mm)')
    ax_3d.set_zlabel('Z (mm)')
    ax_3d.set_title('Optimized 3D Grid Points')
    ax_3d.view_init(elev=20, azim=45)
    plt.tight_layout()
    mo.mpl.interactive(fig_3d)
    return


@app.cell
def _(GRID_COLS, GRID_ROWS, points_3d_opt):

    # Plot 2: Planarity heatmap
    fig_planarity, ax_planarity = plt.subplots(figsize=(10, 4))
    _planarity_devs_viz, _, _, _ = compute_planarity_error(points_3d_opt)
    _planarity_grid = _planarity_devs_viz.reshape(GRID_ROWS, GRID_COLS)

    _im = ax_planarity.imshow(_planarity_grid.T, origin='lower', cmap='RdBu', aspect='auto',
                              extent=[0, GRID_COLS, 0, GRID_ROWS])
    ax_planarity.set_xlabel('Column Index')
    ax_planarity.set_ylabel('Row Index')
    ax_planarity.set_title('Planarity Deviation (mm)')
    plt.colorbar(_im, ax=ax_planarity, label='Deviation (mm)')
    plt.tight_layout()
    mo.mpl.interactive(fig_planarity)
    return


@app.cell
def _(diagnostics, num_cams):
    # Plot 3: Reprojection comparison
    fig_reproj, ax_reproj = plt.subplots(figsize=(10, 4))
    _cameras = np.arange(1, num_cams + 1)
    _width = 0.35

    ax_reproj.bar(_cameras - _width/2, diagnostics['rms_initial_per_cam'], _width,
                  label='Before', color='coral')
    ax_reproj.bar(_cameras + _width/2, diagnostics['rms_final_per_cam'], _width,
                  label='After', color='steelblue')

    ax_reproj.set_xlabel('Camera')
    ax_reproj.set_ylabel('RMS Reprojection Error (pixels)')
    ax_reproj.set_title('Reprojection Error Before and After')
    ax_reproj.set_xticks(_cameras)
    ax_reproj.set_xticklabels([f'Cam {_c}' for _c in _cameras])
    ax_reproj.legend()
    ax_reproj.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    mo.mpl.interactive(fig_reproj)

    return


@app.cell
def _(cals, cals_optimized):
    cals_optimized[0].get_pos(), cals[0].get_pos()
    return


@app.cell
def _():
    # """Save optimized calibration."""
    # save_calibration = mo.ui.checkbox(label="Save optimized calibration to .ori/.addpar files")

    # _save_msg = mo.md("✓ Check the box above to save optimized calibration files.")
    # if save_calibration.value:
    #     _cal_ori = pm.get_parameter("cal_ori")
    #     _img_ori = _cal_ori.get("img_ori") if isinstance(_cal_ori, dict) else []
    #     _base_path = yaml_path.parent

    #     _saved_files = []
    #     for _cam_idx, _cal in enumerate(cals_optimized):
    #         if _cam_idx < len(_img_ori):
    #             _ori_path = Path(_img_ori[_cam_idx])
    #             if not _ori_path.is_absolute():
    #                 _ori_path = _base_path / _ori_path
    #             _addpar_path = Path(str(_ori_path).replace(".ori", ".addpar"))

    #             _ori_path.parent.mkdir(parents=True, exist_ok=True)
    #             _cal.write(str(_ori_path).encode("utf-8"), str(_addpar_path).encode("utf-8"))
    #             _saved_files.append(f"✓ Camera {_cam_idx+1}: {_ori_path.name}, {_addpar_path.name}")

    #     _save_msg = mo.md("### Calibration Files Saved\n\n" + "\n".join(_saved_files))

    # _save_msg

    return


if __name__ == "__main__":
    app.run()
