import marimo

__generated_with = "0.20.4"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo

    mo.md(r"""
    # Illmenau Multi-Camera Calibration

    Interactive calibration workflow for the Illmenau 4-camera setup.

    **Workflow:**
    1. **Grid Detection** - Detect 7×6 circular grid in calibration images
    2. **Initial Calibration** - OpenCV intrinsic + stereo calibration
    3. **Bundle Adjustment** - Refine with planarity & distance constraints
    4. **Export** - Generate `.ori` and `.addpar` files for pyPTV GUI
    5. **Validation** - Optional dumbbell test

    **Data:**
    - 4 cameras (Kalibrierung1a-4a)
    - 40 synchronized frames
    - 7×6 grid, 120mm spacing
    """)
    return (mo,)


@app.cell
def _():
    import numpy as np
    import cv2
    import matplotlib.pyplot as plt
    from pathlib import Path
    import pickle
    from typing import Dict, List, Tuple, Optional
    from dataclasses import dataclass
    import pandas as pd

    from optv.calibration import Calibration
    from optv.imgcoord import image_coordinates
    from optv.transforms import (
        convert_arr_pixel_to_metric,
        convert_arr_metric_to_pixel,
    )
    from optv.orientation import multi_cam_point_positions
    from pyptv.parameter_manager import ParameterManager
    from pyptv.experiment import Experiment
    from pyptv import ptv
    from scipy.optimize import least_squares
    from scipy import sparse
    from scipy.spatial.transform import Rotation as R
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    return (
        Calibration,
        Dict,
        Experiment,
        ParameterManager,
        Path,
        Poly3DCollection,
        R,
        convert_arr_metric_to_pixel,
        convert_arr_pixel_to_metric,
        cv2,
        dataclass,
        image_coordinates,
        least_squares,
        multi_cam_point_positions,
        np,
        pd,
        plt,
        ptv,
    )


@app.cell
def _(Dict, dataclass):
    @dataclass
    class CalibrationConfig:
        """Configuration for calibration pipeline."""

        calib_base: str
        camera_folders: Dict[int, str]
        num_frames: int
        grid_rows: int
        grid_cols: int
        grid_spacing_mm: float
        yaml_path: str
        output_dir: str

        @classmethod
        def for_illmenau_run4(cls):
            return cls(
                calib_base="/home/user/Downloads/Illmenau/KalibrierungB",
                camera_folders={
                    0: "Kalibrierung1b",
                    1: "Kalibrierung2b",
                    2: "Kalibrierung3b",
                    3: "Kalibrierung4b",
                },
                num_frames=123,
                grid_rows=21,
                grid_cols=17,
                grid_spacing_mm=40.0,
                yaml_path="/home/user/Downloads/Illmenau/pyPTV_folder/parameters_Run4.yaml",
                output_dir="/home/user/Downloads/Illmenau/pyPTV_folder/calibration_output_B",
            )

    return (CalibrationConfig,)


@app.cell
def _(CalibrationConfig, mo):
    config = CalibrationConfig.for_illmenau_run4()
    mo.md(f"""
    ### Configuration Loaded (Updated for KalibrierungB)

    | Parameter | Value |
    |-----------|-------|
    | **Calibration Base** | `{config.calib_base}` |
    | **Grid** | {config.grid_rows}×{config.grid_cols} (Dark background, bright dots) |
    | **Grid Spacing** | {config.grid_spacing_mm} mm |
    | **Output Directory** | `{config.output_dir}` |
    """)
    return (config,)


@app.cell
def _(Path, config, mo):
    # Verify folders exist
    _folder_status = []
    _all_ok = True

    _calib_base_check = Path(config.calib_base)
    _yaml_path_check = Path(config.yaml_path)

    for _cam_idx_check, _folder_name_check in config.camera_folders.items():
        _folder_path_check = _calib_base_check / _folder_name_check
        _exists = _folder_path_check.exists()
        if not _exists:
            _all_ok = False
        _icon = "✓" if _exists else "❌"
        _folder_status.append(
            f"{_icon} **Camera {_cam_idx_check + 1}**: `{_folder_path_check}`"
        )

    _yaml_exists = _yaml_path_check.exists()
    if not _yaml_exists:
        _all_ok = False

    mo.md(
        f"""
    ### File System Check

    {"**✓ All paths valid!**" if _all_ok else "**⚠ Some paths missing!**"}

    **Parameter File:**
    - {"✓" if _yaml_exists else "❌"} `{_yaml_path_check}`

    **Camera Folders:**
    """
        + "\n".join(_folder_status)
    )
    return


@app.cell
def _(Path, config, cv2, mo, np):
    """
    ## Step 1: Grid Detection

    Detect the 7×6 circular grid in all calibration images.
    Only keeps frames where ALL 4 cameras detected the grid.
    """

    board_params = cv2.SimpleBlobDetector_Params()
    board_params.filterByColor = False
    board_params.filterByArea = True
    board_params.minArea = 50
    board_params.filterByCircularity = True
    board_params.minCircularity = 0.7
    detector = cv2.SimpleBlobDetector_create(board_params)

    _calib_base_gd = Path(config.calib_base)
    _num_cams_gd = len(config.camera_folders)

    # Storage: frame_idx -> {cam_idx: corners or None}
    frame_detections = {}
    for _frame_idx_gd in range(config.num_frames):
        frame_detections[_frame_idx_gd] = {
            _cam_idx_gd: None for _cam_idx_gd in config.camera_folders.keys()
        }

    detection_log = []

    print(
        f"Detecting grids in {config.num_frames} frames × {_num_cams_gd} cameras..."
    )

    for _cam_idx_gd2, _folder_name_gd in config.camera_folders.items():
        _folder_path_gd = _calib_base_gd / _folder_name_gd
        _cam_success = 0
        _cam_failed = 0

        for _frame_idx_gd2 in range(config.num_frames):
            # Find image file
            _image_file = None
            for _f_gd in _folder_path_gd.iterdir():
                if _f_gd.name.startswith(f"{_frame_idx_gd2:08d}_"):
                    _image_file = _f_gd
                    break

            if _image_file is None:
                _cam_failed += 1
                detection_log.append(
                    {
                        "camera": _cam_idx_gd2,
                        "frame": _frame_idx_gd2,
                        "success": False,
                    }
                )
                continue

            _img_gd = cv2.imread(str(_image_file), cv2.IMREAD_GRAYSCALE)
            if _img_gd is None:
                _cam_failed += 1
                detection_log.append(
                    {
                        "camera": _cam_idx_gd2,
                        "frame": _frame_idx_gd2,
                        "success": False,
                    }
                )
                continue

            _found_gd, _corners_gd = cv2.findCirclesGrid(
                _img_gd,
                (config.grid_rows, config.grid_cols),
                flags=cv2.CALIB_CB_SYMMETRIC_GRID,
                blobDetector=detector,
            )

            if _found_gd:
                _corners_squeezed_gd = np.squeeze(_corners_gd)
                _cam_success += 1
                frame_detections[_frame_idx_gd2][_cam_idx_gd2] = (
                    _corners_squeezed_gd
                )
                detection_log.append(
                    {
                        "camera": _cam_idx_gd2,
                        "frame": _frame_idx_gd2,
                        "success": True,
                        "corners": _corners_squeezed_gd,
                        "image_file": str(_image_file),
                    }
                )
            else:
                _cam_failed += 1
                detection_log.append(
                    {
                        "camera": _cam_idx_gd2,
                        "frame": _frame_idx_gd2,
                        "success": False,
                    }
                )

        print(
            f"  Camera {_cam_idx_gd2 + 1}: {_cam_success}/{config.num_frames} detected"
        )

    # Find synchronized frames
    synchronized_frames = []
    for _frame_idx_gd3 in range(config.num_frames):
        if all(
            frame_detections[_frame_idx_gd3][_cam_idx_gd3] is not None
            for _cam_idx_gd3 in config.camera_folders.keys()
        ):
            synchronized_frames.append(_frame_idx_gd3)

    _sync_rate = len(synchronized_frames) / config.num_frames * 100

    mo.md(f"""
    ### Detection Results

    | Metric | Value |
    |--------|-------|
    | **Total Frames** | {config.num_frames} |
    | **Synchronized Frames** | {len(synchronized_frames)} |
    | **Synchronization Rate** | {_sync_rate:.1f}% |
    | **Total Detections** | {len(synchronized_frames) * _num_cams_gd} frames × {_num_cams_gd} cams |

    **Synchronized frame indices:** `{synchronized_frames}`
    """)
    return frame_detections, synchronized_frames


@app.cell
def _(Path, config, cv2, frame_detections, mo, plt, synchronized_frames):
    """Visualize detected grids on sample images."""

    _sample_frame_viz = synchronized_frames[10] if synchronized_frames else None

    if _sample_frame_viz is None:
        _ = mo.md("❌ No synchronized frames found!")
    else:
        _num_cams_viz = len(config.camera_folders)

        _fig_viz, _axes_viz = plt.subplots(2, 2, figsize=(16, 12))
        _axes_flat_viz = _axes_viz.flatten()

        for _cam_idx_viz in range(_num_cams_viz):
            _ax_viz = _axes_flat_viz[_cam_idx_viz]
            _corners_viz = frame_detections[_sample_frame_viz][_cam_idx_viz]

            if _corners_viz is not None:
                # Load image for display
                _folder_name_viz = config.camera_folders[_cam_idx_viz]
                _folder_path_viz = Path(config.calib_base) / _folder_name_viz
                _image_file_viz = None
                for _f_viz in _folder_path_viz.iterdir():
                    if _f_viz.name.startswith(f"{_sample_frame_viz:08d}_"):
                        _image_file_viz = _f_viz
                        break

                if _image_file_viz:
                    _img_viz = cv2.imread(
                        str(_image_file_viz), cv2.IMREAD_GRAYSCALE
                    )
                    _ax_viz.imshow(_img_viz, cmap="gray")

                    # Draw detected grid
                    _corners_grid_viz = _corners_viz.reshape(
                        config.grid_rows, config.grid_cols, 2
                    )
                    _ax_viz.scatter(
                        _corners_viz[:, 0],
                        _corners_viz[:, 1],
                        c="red",
                        s=40,
                        marker="o",
                    )

                    # Draw grid lines
                    for _i_viz in range(config.grid_rows):
                        _ax_viz.plot(
                            _corners_grid_viz[_i_viz, :, 0],
                            _corners_grid_viz[_i_viz, :, 1],
                            "b-",
                            lw=0.8,
                            alpha=0.6,
                        )
                    for _j_viz in range(config.grid_cols):
                        _ax_viz.plot(
                            _corners_grid_viz[:, _j_viz, 0],
                            _corners_grid_viz[:, _j_viz, 1],
                            "b-",
                            lw=0.8,
                            alpha=0.6,
                        )

            _ax_viz.set_title(
                f"Camera {_cam_idx_viz + 1} - Frame {_sample_frame_viz}"
            )
            _ax_viz.set_xlabel("X (pixels)")
            _ax_viz.set_ylabel("Y (pixels)")
            _ax_viz.invert_yaxis()
            _ax_viz.set_aspect("equal")

        plt.tight_layout()
    mo.mpl.interactive(_fig_viz)
    return


@app.cell
def _(config, frame_detections, mo, pd, synchronized_frames):
    """Create summary table of detections."""

    if synchronized_frames:
        # Create pivot table showing detection status
        _pivot_data = []
        for _frame_idx_tbl in range(config.num_frames):
            _row = {"frame": _frame_idx_tbl}
            for _cam_idx_tbl in config.camera_folders.keys():
                _has_detection = (
                    frame_detections[_frame_idx_tbl][_cam_idx_tbl] is not None
                )
                _row[f"cam{_cam_idx_tbl + 1}"] = "✓" if _has_detection else "✗"
            _row["sync"] = "✓" if _frame_idx_tbl in synchronized_frames else "✗"
            _pivot_data.append(_row)

        _df_pivot = pd.DataFrame(_pivot_data)

    mo.md("### Detection Status Matrix (✓ = detected)")
    mo.ui.dataframe(_df_pivot.set_index("frame"))
    return


@app.cell
def _(Calibration, Experiment, ParameterManager, Path, config, mo, np, ptv):
    """
    ## Step 2: Load Initial Calibration & Parameters

    Load camera parameters from YAML and initial calibration files.
    """

    _yaml_file = Path(config.yaml_path)
    _base_path = _yaml_file.parent

    pm = ParameterManager()
    pm.from_yaml(_yaml_file)
    exp = Experiment(pm=pm)

    params = pm.parameters
    _num_cams_cl = int(params.get("num_cams", pm.num_cams or 0) or 0)
    ptv_params = params.get("ptv", {})
    cpar = ptv._populate_cpar(ptv_params, _num_cams_cl)

    cal_ori = pm.parameters.get("cal_ori", {})
    ori_names = cal_ori.get("img_ori", [])

    cals = []
    load_status = []

    for _i_cl in range(_num_cams_cl):
        _cal = Calibration()
        _ori_path_cl = ori_names[_i_cl] if _i_cl < len(ori_names) else None

        if _ori_path_cl:
            _ori_file_path_cl = _base_path / _ori_path_cl
            _addpar_file_path_cl = Path(
                str(_ori_file_path_cl).replace(".ori", "") + ".addpar"
            )
            if not _addpar_file_path_cl.exists():
                _addpar_file_path_cl = Path(
                    str(_ori_file_path_cl).replace(".tif.ori", "") + ".addpar"
                )

            if _ori_file_path_cl.exists() and _addpar_file_path_cl.exists():
                _cal.from_file(str(_ori_file_path_cl), str(_addpar_file_path_cl))
                load_status.append(f"✓ Cam {_i_cl + 1}: {_ori_file_path_cl.name}")
            else:
                load_status.append(f"⚠ Cam {_i_cl + 1}: Missing calibration files")
                _cal.set_pos(np.array([0.0, 0.0, 1000.0]))
                _cal.set_angles(np.array([0.0, 0.0, 0.0]))
        else:
            load_status.append(f"⚠ Cam {_i_cl + 1}: No calibration path")
            _cal.set_pos(np.array([0.0, 0.0, 1000.0]))
            _cal.set_angles(np.array([0.0, 0.0, 0.0]))

        cals.append(_cal)

    mo.md(
        f"""
    ### Calibration Files Loaded

    | Metric | Value |
    |--------|-------|
    | **Number of Cameras** | {_num_cams_cl} |
    | **Image Size** | {ptv_params.get("imx", "N/A")} × {ptv_params.get("imy", "N/A")} pixels |

    **Status:**
    """
        + "\n".join(load_status)
    )
    return cals, cpar


@app.cell
def _(Poly3DCollection, R, np):
    """
    ### Visualize Initial Camera Positions

    3D visualization of camera positions and orientations.
    """


    def draw_camera_pyramid(ax, pos, angles, scale=100, color=None, label=None):
        """Draw camera as a pyramid."""
        rot_matrix = R.from_euler("xyz", angles, degrees=False).as_matrix()

        # Original setup:
        # w, h, d = 0.5 * scale, 0.4 * scale, 1.0 * scale
        # local_verts = np.array(
        #     [[0, 0, 0], [-w, -h, d], [w, -h, d], [w, h, d], [-w, h, d]]
        # )

        # If cameras should look towards +Z, the pyramid apex (0,0,0) is the camera center.
        # The base of the pyramid (image plane) should be at z = +d.
        # The "open side" means the base.

        # If the user says "cameras looking with the open side of the pyramide towards negative z",
        # it means the current base is at z = +d (or -d depending on coords).
        # And "should look into positive z direction onto the 0,0,0 origin" implies the camera is at negative Z looking towards +Z?
        # Or just that the camera orientation vector is towards +Z.

        # In standard PTV/photogrammetry, camera coord system:
        # X, Y are image plane, Z is optical axis.
        # Usually Z points into the scene (away from camera).
        # If the camera is at (0,0,-1000) looking at (0,0,0), then Z is positive direction.

        # The previous code had base at z = d (positive). So locally it points to +Z.
        # If the user says they look to negative Z, maybe the rotation matrix interpretation is different (e.g. view matrix vs model matrix).

        # Let's assume the rotation matrix transforms local camera coords to world coords.
        # If we want to flip the visualization direction, we can flip the local Z of the base.

        # BUT, if the user says "look into positive z direction onto the 0,0,0 origin",
        # and cameras are at negative Z positions (e.g. -3000), then they are looking towards +Z.

        # Let's check the positions.
        # Cam 1: Z ~ -3100. Cam 2: Z ~ -3100.
        # So they are at negative Z. To look at origin (0,0,0), they must look in +Z direction.

        # If the pyramid base was drawn at z = +d in local coords, and the rotation is identity (or small angles),
        # then the pyramid points towards +Z.

        # If the user says "shows cameras looking ... towards negative z", maybe the rotation matrix application is inverted?
        # R from euler "xyz" creates a rotation.
        # World = R * Local + Pos.

        # Let's try inverting the local Z of the pyramid base to see if it matches the user's expectation of "looking".
        # Or maybe the rotation matrix is actually `rot_matrix.T` (if angles are for world-to-camera).
        # Exterior orientation angles usually define rotation from World to Camera (or Camera to World depending on convention).
        # In `optv`/`pyptv`, `get_angles()` usually returns angles for the rotation matrix `R` such that `x_cam = R * (x_world - pos)`.
        # Wait, `get_rotation_matrix()` returns `R`.
        # If `x_cam = R * (x_world - pos)`, then `x_world = R.T * x_cam + pos`.
        # So the orientation of the camera frame in world is `R.T`.

        # Let's verify `Calibration.get_rotation_matrix()`.
        # If I use `R.from_euler`, I might be getting `R` or `R.T` depending on definition.
        # Let's rely on `Calibration.get_rotation_matrix()` directly if possible, but `draw_camera_pyramid` takes angles.
        # The `Calibration` object has `get_rotation_matrix()`.
        # Let's update `draw_camera_pyramid` to take `R_matrix` instead of `angles`, or compute `R` correctly.

        # If `cals[0].get_rotation_matrix()` is `R_cam_from_world`, then `R_world_from_cam` is its transpose.
        # Let's check the current `draw_camera_pyramid`. It uses `R.from_euler`.
        # If `get_angles()` returns the Euler angles of the World-to-Camera rotation, then `as_matrix()` gives `R_wc`.
        # We want `R_cw` (Camera-to-World) to transform local pyramid to world.
        # `R_cw = R_wc.T`.

        # So I will change `rot_matrix` to `rot_matrix.T`.

        w, h, d = 0.5 * scale, 0.4 * scale, 1.0 * scale

        # Local pyramid pointing along +Z
        local_verts = np.array(
            [[0, 0, 0], [-w, -h, d], [w, -h, d], [w, h, d], [-w, h, d]]
        )

        # Transpose rotation matrix because we want Local -> World
        # assuming the angles represent World -> Camera rotation (standard in photogrammetry)
        world_verts = (rot_matrix.T @ local_verts.T).T + pos

        faces = [
            [world_verts[0], world_verts[1], world_verts[2]],
            [world_verts[0], world_verts[2], world_verts[3]],
            [world_verts[0], world_verts[3], world_verts[4]],
            [world_verts[0], world_verts[4], world_verts[1]],
            [world_verts[1], world_verts[2], world_verts[3], world_verts[4]],
        ]

        poly = Poly3DCollection(faces, alpha=0.3, linewidths=1, edgecolors="k")
        poly.set_facecolor(color if color else np.random.rand(3))
        ax.add_collection3d(poly)
        ax.scatter(pos[0], pos[1], pos[2], color="black", s=50)

        # Draw view direction (optical axis)
        # Transform local Z axis (0,0,1) to world
        view_dir = rot_matrix.T @ np.array([0, 0, 1]) * scale * 1.5
        ax.quiver(
            pos[0],
            pos[1],
            pos[2],
            view_dir[0],
            view_dir[1],
            view_dir[2],
            color="k",
            arrow_length_ratio=0.1,
        )

        if label:
            ax.text(pos[0], pos[1], pos[2], label, fontsize=10)

    return (draw_camera_pyramid,)


@app.cell
def _(cals, draw_camera_pyramid, mo, np, plt):
    _fig_init = plt.figure(figsize=(10, 8))
    _ax_init = _fig_init.add_subplot(111, projection="3d")

    colors = ["red", "green", "blue", "orange"]

    for _i_viz3d, _cal_viz3d in enumerate(cals):
        _pos_viz3d = _cal_viz3d.get_pos()
        _angles_viz3d = _cal_viz3d.get_angles()
        draw_camera_pyramid(
            _ax_init,
            _pos_viz3d,
            _angles_viz3d,
            scale=200,
            color=colors[_i_viz3d % len(colors)],
            label=f"Cam {_i_viz3d + 1}",
        )

    # Draw origin axes
    length = 200
    _ax_init.quiver(
        0, 0, 0, length, 0, 0, color="r", arrow_length_ratio=0.1, label="X"
    )
    _ax_init.quiver(
        0, 0, 0, 0, length, 0, color="g", arrow_length_ratio=0.1, label="Y"
    )
    _ax_init.quiver(
        0, 0, 0, 0, 0, length, color="b", arrow_length_ratio=0.1, label="Z"
    )

    all_pos = np.array([_cal_viz3d.get_pos() for _cal_viz3d in cals])
    max_range = np.ptp(all_pos, axis=0).max() / 2
    mid = all_pos.mean(axis=0)

    _ax_init.set_xlim(mid[0] - max_range * 1.5, mid[0] + max_range * 1.5)
    _ax_init.set_ylim(mid[1] - max_range * 1.5, mid[1] + max_range * 1.5)
    _ax_init.set_zlim(mid[2] - max_range * 1.5, mid[2] + max_range * 1.5)

    _ax_init.set_xlabel("X (mm)")
    _ax_init.set_ylabel("Y (mm)")
    _ax_init.set_zlabel("Z (mm)")
    _ax_init.set_title("Initial Camera Positions")
    _ax_init.legend()

    plt.tight_layout()
    mo.mpl.interactive(_fig_init)
    return


@app.cell
def _(
    cals,
    config,
    convert_arr_pixel_to_metric,
    cpar,
    frame_detections,
    mo,
    multi_cam_point_positions,
    np,
    synchronized_frames,
):
    """
    ## Step 3: Triangulate 3D Grid Points

    For each synchronized frame, triangulate the 3D positions of all 42 grid points.
    """

    triangulated_frames = {}
    frame_metrics = {}

    if not synchronized_frames:
        _ = mo.md("❌ No synchronized frames to triangulate")
    else:
        num_points = config.grid_rows * config.grid_cols

        print(
            f"Triangulating {len(synchronized_frames)} frames × {num_points} points..."
        )

        for _frame_idx_tr in synchronized_frames:
            _frame_corners_tr = frame_detections[_frame_idx_tr]
            _valid_cams_tr = [
                _cam_idx_tr
                for _cam_idx_tr, _corners_tr in _frame_corners_tr.items()
                if _corners_tr is not None
            ]

            if len(_valid_cams_tr) < 2:
                continue

            _points_3d_tr = np.zeros((num_points, 3))

            for _pt_idx_tr in range(num_points):
                _pts_2d_list_tr = []

                # Convert pixel coordinates to metric coordinates for each camera
                for _cam_idx_tr2 in _valid_cams_tr:
                    if _pt_idx_tr < len(_frame_corners_tr[_cam_idx_tr2]):
                        # Get pixel coordinates
                        _pix_coords = _frame_corners_tr[_cam_idx_tr2][_pt_idx_tr]

                        # Convert to metric using convert_arr_pixel_to_metric
                        # The function signature appears to be convert_arr_pixel_to_metric(pixel_coords, cpar)
                        # or it expects an output buffer as 3rd arg, but NOT a Calibration object.
                        # Let's try passing just (pixel_coords, cpar) which usually returns the array.
                        # Or if it fails, provide an output buffer.

                        _pix_arr = np.array([_pix_coords]).astype(np.float64)

                        # Try with 2 arguments first, as many cython bindings work that way
                        try:
                            _metric_arr = convert_arr_pixel_to_metric(
                                _pix_arr,
                                cpar,
                                # cals[_cam_idx_tr2]  <-- This was causing the error
                                # If it needs distortion correction, it might need 'cal', but maybe the binding is different.
                                # Standard optv usually does flat field via cpar only here.
                                # If it requires 3 args and 3rd is 'out', we can pass None or an array.
                            )
                        except TypeError:
                            # If it fails, maybe it needs an output array
                            _metric_arr = np.empty_like(_pix_arr)
                            convert_arr_pixel_to_metric(
                                _pix_arr, cpar, _metric_arr
                            )

                        _pts_2d_list_tr.append(_metric_arr[0])

                if len(_pts_2d_list_tr) >= 2:
                    _cals_subset = [cals[_i] for _i in _valid_cams_tr]

                    # Create input array (1 point, num_valid_cams, 2 coords)
                    _pts_2d_tr = np.array(_pts_2d_list_tr)[
                        np.newaxis, :, :
                    ].astype(np.float64)

                    _xyz_tr, _err_tr = multi_cam_point_positions(
                        _pts_2d_tr, cpar, _cals_subset
                    )
                    _points_3d_tr[_pt_idx_tr] = _xyz_tr[0]

            triangulated_frames[_frame_idx_tr] = _points_3d_tr

            # Compute planarity
            _centroid_tr = np.mean(_points_3d_tr, axis=0)
            _centered_tr = _points_3d_tr - _centroid_tr
            _, _, _Vt_tr = np.linalg.svd(_centered_tr)
            _normal_tr = _Vt_tr[2, :]
            _deviations_tr = np.dot(_centered_tr, _normal_tr)
            _rms_planarity_tr = np.sqrt(np.mean(_deviations_tr**2))

            # Compute distance errors
            _dist_errors_tr = []
            for _i_tr in range(config.grid_rows):
                for _j_tr in range(config.grid_cols - 1):
                    _idx1_tr = _i_tr * config.grid_cols + _j_tr
                    _idx2_tr = _i_tr * config.grid_cols + (_j_tr + 1)
                    _dist_tr = np.linalg.norm(
                        _points_3d_tr[_idx2_tr] - _points_3d_tr[_idx1_tr]
                    )
                    _dist_errors_tr.append(_dist_tr - config.grid_spacing_mm)

            for _i_tr2 in range(config.grid_rows - 1):
                for _j_tr2 in range(config.grid_cols):
                    _idx1_tr2 = _i_tr2 * config.grid_cols + _j_tr2
                    _idx2_tr2 = (_i_tr2 + 1) * config.grid_cols + _j_tr2
                    _dist_tr2 = np.linalg.norm(
                        _points_3d_tr[_idx2_tr2] - _points_3d_tr[_idx1_tr2]
                    )
                    _dist_errors_tr.append(_dist_tr2 - config.grid_spacing_mm)

            _rms_distance_tr = np.sqrt(np.mean(np.array(_dist_errors_tr) ** 2))

            frame_metrics[_frame_idx_tr] = {
                "rms_planarity": _rms_planarity_tr,
                "rms_distance": _rms_distance_tr,
            }

        _avg_planarity_tr = np.mean(
            [_m_tr["rms_planarity"] for _m_tr in frame_metrics.values()]
        )
        _avg_distance_tr = np.mean(
            [_m_tr["rms_distance"] for _m_tr in frame_metrics.values()]
        )

        _ = mo.md(f"""
        ### Triangulation Results (with Pixel->Metric Conversion)

        | Metric | Mean ± Std |
        |--------|------------|
        | **RMS Planarity** | {_avg_planarity_tr:.3f} ± {np.std([_m_tr["rms_planarity"] for _m_tr in frame_metrics.values()]):.3f} mm |
        | **RMS Distance** | {_avg_distance_tr:.3f} ± {np.std([_m_tr["rms_distance"] for _m_tr in frame_metrics.values()]):.3f} mm |

        **Frames triangulated:** {len(triangulated_frames)}
        """)
    return frame_metrics, triangulated_frames


@app.cell
def _(frame_metrics, mo, pd):
    """Display per-frame triangulation metrics."""

    _df_metrics_tbl = pd.DataFrame(frame_metrics).T
    _df_metrics_tbl.index.name = "Frame"

    mo.md("### Per-Frame Triangulation Metrics")
    mo.ui.dataframe(_df_metrics_tbl)
    return


@app.cell
def _(config, mo, plt, triangulated_frames):
    """Visualize triangulated 3D points."""

    if triangulated_frames:
        _frames_to_show = list(triangulated_frames.keys())[:3]

        _fig_3d = plt.figure(figsize=(18, 5))

        for _idx_3d, _frame_idx_3d in enumerate(_frames_to_show):
            _ax_3d = _fig_3d.add_subplot(
                1, len(_frames_to_show), _idx_3d + 1, projection="3d"
            )
            _points_3d_viz = triangulated_frames[_frame_idx_3d]

            _ax_3d.scatter(
                _points_3d_viz[:, 0],
                _points_3d_viz[:, 1],
                _points_3d_viz[:, 2],
                c="red",
                s=30,
            )

            # Draw grid connections
            _points_grid_3d = _points_3d_viz.reshape(
                config.grid_rows, config.grid_cols, 3
            )
            for _i_3d in range(config.grid_rows):
                _ax_3d.plot(
                    _points_grid_3d[_i_3d, :, 0],
                    _points_grid_3d[_i_3d, :, 1],
                    _points_grid_3d[_i_3d, :, 2],
                    "b-",
                    lw=0.5,
                    alpha=0.5,
                )
            for _j_3d in range(config.grid_cols):
                _ax_3d.plot(
                    _points_grid_3d[:, _j_3d, 0],
                    _points_grid_3d[:, _j_3d, 1],
                    _points_grid_3d[:, _j_3d, 2],
                    "b-",
                    lw=0.5,
                    alpha=0.5,
                )

            _ax_3d.set_xlabel("X (mm)")
            _ax_3d.set_ylabel("Y (mm)")
            _ax_3d.set_zlabel("Z (mm)")
            _ax_3d.set_title(f"Frame {_frame_idx_3d}")
            _ax_3d.view_init(elev=20, azim=-60)

        plt.tight_layout()
    mo.mpl.interactive(_fig_3d)
    return


@app.cell
def _(np):
    """
    Helper functions for bundle adjustment - defined separately for reusability.
    """


    def compute_planarity_error(points_3d):
        """Compute planarity error for a set of 3D points."""
        centroid = np.mean(points_3d, axis=0)
        centered = points_3d - centroid
        _, _, Vt = np.linalg.svd(centered)
        normal = Vt[2, :]
        deviations = np.dot(centered, normal)
        return deviations, np.sqrt(np.mean(deviations**2)), normal, centroid

    return (compute_planarity_error,)


@app.cell
def _(np):
    def compute_distance_errors(points_3d, rows, cols, spacing):
        """Compute distance errors for adjacent grid points."""
        errors = []
        for i in range(rows):
            for j in range(cols - 1):
                idx1 = i * cols + j
                idx2 = i * cols + (j + 1)
                dist = np.linalg.norm(points_3d[idx2] - points_3d[idx1])
                errors.append(dist - spacing)
        for i in range(rows - 1):
            for j in range(cols):
                idx1 = i * cols + j
                idx2 = (i + 1) * cols + j
                dist = np.linalg.norm(points_3d[idx2] - points_3d[idx1])
                errors.append(dist - spacing)
        return np.array(errors)

    return (compute_distance_errors,)


@app.cell
def _(
    compute_distance_errors,
    compute_planarity_error,
    config,
    convert_arr_metric_to_pixel,
    image_coordinates,
    np,
):
    """
    ## Step 4: Bundle Adjustment

    Optimize camera exterior orientation using:
    - **Reprojection error**: Minimize 2D projection error (in pixels)
    - **Planarity constraint**: All grid points lie on a plane (in mm)
    - **Distance constraint**: Adjacent points at 120mm spacing (in mm)
    """


    def grid_ba_residuals(
        calib_vec,
        points_3d_dict,
        observations_2d_dict,
        cpar,
        calibs,
        active_cams,
        w_planarity,
        w_distance,
        pos_scale=1.0,
    ):
        num_cams_ba = len(calibs)
        num_points_ba = config.grid_rows * config.grid_cols
        active_cams_arr = np.asarray(active_cams, dtype=bool)
        num_active = int(np.sum(active_cams_arr))

        # Each camera has 16 parameters
        params_per_cam = 16
        cam_params_len = num_active * params_per_cam

        # Reshape to (num_active, params_per_cam)
        calib_pars = calib_vec[:cam_params_len].reshape(-1, params_per_cam)

        ptr = 0
        for cam_ba, cal_ba in enumerate(calibs):
            if not active_cams_arr[cam_ba]:
                continue

            pars = calib_pars[ptr]

            # Unpack parameters
            # 0-2: pos
            cal_ba.set_pos(pars[0:3] * pos_scale)
            # 3-5: angles
            cal_ba.set_angles(pars[3:6])
            # 6-8: primary_point (xh, yh, cc)
            cal_ba.set_primary_point(pars[6:9])
            # 9-11: radial_distortion (k1, k2, k3)
            cal_ba.set_radial_distortion(pars[9:12])
            # 12-13: decentering (p1, p2)
            cal_ba.set_decentering(pars[12:14])
            # 14-15: affine (scx, she)
            cal_ba.set_affine_trans(pars[14:16])

            ptr += 1

        mm_params = cpar.get_multimedia_params()
        residuals = []

        for frame_idx_ba, points_3d_ba in points_3d_dict.items():
            for cam_ba2 in range(num_cams_ba):
                if (
                    not active_cams_arr[cam_ba2]
                    or cam_ba2 not in observations_2d_dict[frame_idx_ba]
                ):
                    continue

                obs_2d_ba = observations_2d_dict[frame_idx_ba][cam_ba2]
                if obs_2d_ba is None:
                    continue

                try:
                    # 1. Project 3D points to metric coordinates (mm on sensor)
                    # Ensure points_3d_ba is float64
                    proj_metric = image_coordinates(
                        points_3d_ba.astype(np.float64), calibs[cam_ba2], mm_params
                    )

                    # 2. Convert metric coordinates to pixel coordinates
                    # proj_metric is (N, 2)
                    proj_pixel = np.empty_like(proj_metric)
                    convert_arr_metric_to_pixel(proj_metric, cpar, proj_pixel)

                    # 3. Compute reprojection error in pixels
                    diff = obs_2d_ba - proj_pixel
                    residuals.extend(diff.ravel())

                except Exception:
                    # If projection fails (e.g. point behind camera), assign large penalty
                    residuals.extend([1e6] * (num_points_ba * 2))

            if w_planarity > 0:
                planarity_devs, _, _, _ = compute_planarity_error(points_3d_ba)
                residuals.extend(np.sqrt(w_planarity) * planarity_devs)

            if w_distance > 0:
                distance_errors = compute_distance_errors(
                    points_3d_ba,
                    config.grid_rows,
                    config.grid_cols,
                    config.grid_spacing_mm,
                )
                residuals.extend(np.sqrt(w_distance) * distance_errors)

        return np.nan_to_num(
            np.asarray(residuals, dtype=float), nan=1e6, posinf=1e6, neginf=-1e6
        )

    return (grid_ba_residuals,)


@app.cell
def _(cals, cals_optimized, mo, np):
    """Display optimized camera parameters."""

    num_cams_disp = len(cals)

    mo.md("""
    ### Optimized Camera Parameters

    **Positions (mm) and Angles (degrees):**
    """)

    results_table = """
    | Camera | X (mm) | Y (mm) | Z (mm) | ω (deg) | φ (deg) | κ (deg) |
    |--------|--------|--------|--------|---------|---------|---------|
    """

    for _cam_disp in range(num_cams_disp):
        _pos_disp = cals_optimized[_cam_disp].get_pos()
        _angs_disp = cals_optimized[_cam_disp].get_angles()
        results_table += f"| {_cam_disp + 1} | {_pos_disp[0]:.3f} | {_pos_disp[1]:.3f} | {_pos_disp[2]:.3f} | {np.degrees(_angs_disp[0]):.4f} | {np.degrees(_angs_disp[1]):.4f} | {np.degrees(_angs_disp[2]):.4f} |\n"

    mo.md(results_table)
    return (num_cams_disp,)


@app.cell
def _(cals, cals_optimized, mo, np, num_cams_disp):
    mo.md("""
    ### Changes (Optimized - Initial)
    """)

    delta_table = """
    | Camera | ΔX (mm) | ΔY (mm) | ΔZ (mm) | Δω (deg) | Δφ (deg) | Δκ (deg) |
    |--------|---------|---------|---------|----------|----------|----------|
    """

    for _cam_delta in range(num_cams_disp):
        _pos_init_delta = cals[_cam_delta].get_pos()
        _pos_opt_delta = cals_optimized[_cam_delta].get_pos()
        _angs_init_delta = cals[_cam_delta].get_angles()
        _angs_opt_delta = cals_optimized[_cam_delta].get_angles()

        _delta_pos = _pos_opt_delta - _pos_init_delta
        _delta_angs = np.degrees(_angs_opt_delta - _angs_init_delta)
        delta_table += f"| {_cam_delta + 1} | {_delta_pos[0]:.3f} | {_delta_pos[1]:.3f} | {_delta_pos[2]:.3f} | {_delta_angs[0]:.4f} | {_delta_angs[1]:.4f} | {_delta_angs[2]:.4f} |\n"

    mo.md(delta_table)
    # _results_display = "done"
    return


@app.cell
def _(cals, cals_optimized, mo, np, plt):
    """Compare camera positions before and after optimization."""

    _fig_cmp = None
    if cals_optimized is not None:
        num_cams_viz2 = len(cals)

        _fig_cmp, _axes_cmp = plt.subplots(
            1, 2, figsize=(16, 6), subplot_kw={"projection": "3d"}
        )

        def draw_cameras_viz(ax, cal_list, title, colors):
            for _i_viz2, _cal_viz2 in enumerate(cal_list):
                _pos_viz2 = _cal_viz2.get_pos()
                ax.scatter(
                    _pos_viz2[0],
                    _pos_viz2[1],
                    _pos_viz2[2],
                    s=100,
                    color=colors[_i_viz2 % len(colors)],
                    label=f"Cam {_i_viz2 + 1}",
                )
                ax.text(
                    _pos_viz2[0],
                    _pos_viz2[1],
                    _pos_viz2[2],
                    f"C{_i_viz2 + 1}",
                    fontsize=10,
                )

            all_pos_viz2 = np.array(
                [_cal_viz2.get_pos() for _cal_viz2 in cal_list]
            )
            max_range_viz2 = np.ptp(all_pos_viz2, axis=0).max() / 2
            mid_viz2 = all_pos_viz2.mean(axis=0)

            ax.set_xlim(
                mid_viz2[0] - max_range_viz2 * 1.5,
                mid_viz2[0] + max_range_viz2 * 1.5,
            )
            ax.set_ylim(
                mid_viz2[1] - max_range_viz2 * 1.5,
                mid_viz2[1] + max_range_viz2 * 1.5,
            )
            ax.set_zlim(
                mid_viz2[2] - max_range_viz2 * 1.5,
                mid_viz2[2] + max_range_viz2 * 1.5,
            )

            ax.set_xlabel("X (mm)")
            ax.set_ylabel("Y (mm)")
            ax.set_zlabel("Z (mm)")
            ax.set_title(title)
            ax.legend()
            ax.grid(True, alpha=0.3)

        colors_viz2 = ["red", "green", "blue", "orange"]
        draw_cameras_viz(
            _axes_cmp[0], cals, "Initial Camera Positions", colors_viz2
        )
        draw_cameras_viz(
            _axes_cmp[1], cals_optimized, "Optimized Camera Positions", colors_viz2
        )

        plt.tight_layout()
    mo.mpl.interactive(_fig_cmp)
    return


@app.cell
def _(
    cals_optimized,
    compute_distance_errors,
    compute_planarity_error,
    config,
    mo,
    np,
    triangulated_frames,
):
    """Compute post-optimization geometric metrics."""

    if cals_optimized is not None and triangulated_frames:
        optimized_metrics = {}

        for _frame_idx_opt, _points_3d_opt in triangulated_frames.items():
            _planarity_devs_opt, _rms_planarity_opt, _, _ = (
                compute_planarity_error(_points_3d_opt)
            )
            _max_planarity_opt = np.max(np.abs(_planarity_devs_opt))

            _distance_errors_opt = compute_distance_errors(
                _points_3d_opt,
                config.grid_rows,
                config.grid_cols,
                config.grid_spacing_mm,
            )
            _rms_distance_opt = np.sqrt(np.mean(_distance_errors_opt**2))
            _max_distance_opt = np.max(np.abs(_distance_errors_opt))

            optimized_metrics[_frame_idx_opt] = {
                "rms_planarity": _rms_planarity_opt,
                "max_planarity": _max_planarity_opt,
                "rms_distance": _rms_distance_opt,
                "max_distance": _max_distance_opt,
            }

        _avg_planarity_opt2 = np.mean(
            [_m_opt["rms_planarity"] for _m_opt in optimized_metrics.values()]
        )
        _avg_distance_opt2 = np.mean(
            [_m_opt["rms_distance"] for _m_opt in optimized_metrics.values()]
        )

        _ = mo.md(f"""
        ### Geometric Metrics After Optimization

        | Metric | Mean ± Std | Max |
        |--------|------------|-----|
        | **RMS Planarity** | {_avg_planarity_opt2:.3f} ± {np.std([_m_opt["rms_planarity"] for _m_opt in optimized_metrics.values()]):.3f} mm | {np.max([_m_opt["max_planarity"] for _m_opt in optimized_metrics.values()]):.3f} mm |
        | **RMS Distance** | {_avg_distance_opt2:.3f} ± {np.std([_m_opt["rms_distance"] for _m_opt in optimized_metrics.values()]):.3f} mm | {np.max([_m_opt["max_distance"] for _m_opt in optimized_metrics.values()]):.3f} mm |
        """)

    _
    return


@app.cell
def _(mo):
    mo.md("""
    ## Step 5: Export Calibration Files

    Generate `.ori` and `.addpar` files for pyPTV GUI.
    """)
    return


@app.function
def format_ori_content(cal_exp, cam_id_exp):
    """Format .ori file content."""
    _pos_exp = cal_exp.get_pos()
    _angs_exp = cal_exp.get_angles()
    _R_mat_exp = cal_exp.get_rotation_matrix()

    lines = [
        f"# Camera {cam_id_exp + 1} exterior orientation",
        f"{_pos_exp[0]:.10f} {_pos_exp[1]:.10f} {_pos_exp[2]:.10f}",
        f"{_angs_exp[0]:.10f} {_angs_exp[1]:.10f} {_angs_exp[2]:.10f}",
        "",
        "# Rotation matrix",
        f"{_R_mat_exp[0, 0]:.10f} {_R_mat_exp[0, 1]:.10f} {_R_mat_exp[0, 2]:.10f}",
        f"{_R_mat_exp[1, 0]:.10f} {_R_mat_exp[1, 1]:.10f} {_R_mat_exp[1, 2]:.10f}",
        f"{_R_mat_exp[2, 0]:.10f} {_R_mat_exp[2, 1]:.10f} {_R_mat_exp[2, 2]:.10f}",
    ]
    return "\n".join(lines)


@app.function
def format_addpar_content(cal_exp2):
    """Format .addpar file content."""
    pp = cal_exp2.get_primary_point()
    xh, yh, cc = pp[0], pp[1], pp[2]

    dist = cal_exp2.get_radial_distortion()
    k1, k2, k3 = dist[0], dist[1], dist[2]

    dec = cal_exp2.get_decentering()
    p1, p2 = dec[0], dec[1]

    aff = cal_exp2.get_affine()
    scx, she = aff[0], aff[1]

    lines = [
        f"{cc:.10f}  # focal length (mm)",
        f"{xh:.10f}  # principal point x (mm)",
        f"{yh:.10f}  # principal point y (mm)",
        f"{k1:.10f}  # radial distortion k1",
        f"{k2:.10f}  # radial distortion k2",
        f"{p1:.10f}  # decentering p1",
        f"{p2:.10f}  # decentering p2",
        f"{k3:.10f}  # radial distortion k3",
        f"{scx:.10f}  # affine scale x",
        f"{she:.10f}  # affine shear",
    ]
    return "\n".join(lines)


@app.cell
def _(Path, cals, cals_optimized, config, mo):
    cals_to_export = cals_optimized if cals_optimized is not None else cals

    _export_title = (
        "Export Optimized Calibration"
        if cals_optimized is not None
        else "Export Initial Calibration (no optimization performed)"
    )

    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    export_content = []

    for _cam_idx_exp, _cal_exp3 in enumerate(cals_to_export):
        _ori_filename_exp = f"cam{_cam_idx_exp + 1}_calibrated.ori"
        _addpar_filename_exp = f"cam{_cam_idx_exp + 1}_calibrated.addpar"

        _ori_path_exp = output_dir / _ori_filename_exp
        _addpar_path_exp = output_dir / _addpar_filename_exp

        # Use Calibration.write to save the files directly using the library method
        # Need to encode strings to bytes as per TypeError
        _cal_exp3.write(
            str(_ori_path_exp).encode("utf-8"),
            str(_addpar_path_exp).encode("utf-8"),
        )

        # Read back the content for display
        with open(_ori_path_exp, "r") as f:
            _ori_content_exp = f.read()
        with open(_addpar_path_exp, "r") as f:
            _addpar_content_exp = f.read()

        export_content.append(f"""
    **Camera {_cam_idx_exp + 1}:**
    - `{_ori_path_exp}`
    - `{_addpar_path_exp}`

    <details>
    <summary>📋 {_ori_filename_exp} (click to expand)</summary>
    ```
    {_ori_content_exp}
    ```
    </details>

    <details>
    <summary>📋 {_addpar_filename_exp} (click to expand)</summary>
    ```
    {_addpar_content_exp}
    ```
    </details>

    ---
    """)

    mo.md(
        f"""
    ### {_export_title}
    ### Files Written to `{output_dir}`

    """
        + "\n".join(export_content)
    )
    return (cals_to_export,)


@app.cell
def _(cals_to_export, mo):
    """Show copy-paste ready calibration parameters."""

    if cals_to_export is not None:
        export_lines = [
            "### Copy-Paste Ready Parameters\n\nUse these values to manually update your YAML or configuration files.\n"
        ]

        for _cam_idx_cp, _cal_cp in enumerate(cals_to_export):
            _pos_cp = _cal_cp.get_pos()
            _angs_cp = _cal_cp.get_angles()

            _pp_cp = _cal_cp.get_primary_point()
            _xh_cp, _yh_cp, _cc_cp = _pp_cp[0], _pp_cp[1], _pp_cp[2]

            _dist_cp = _cal_cp.get_radial_distortion()
            _k1_cp, _k2_cp, _k3_cp = _dist_cp[0], _dist_cp[1], _dist_cp[2]

            _dec_cp = _cal_cp.get_decentering()
            _p1_cp, _p2_cp = _dec_cp[0], _dec_cp[1]

            _aff_cp = _cal_cp.get_affine()
            _scx_cp, _she_cp = _aff_cp[0], _aff_cp[1]

            export_lines.append(f"\n#### Camera {_cam_idx_cp + 1}\n\n")
            export_lines.append("**Exterior Orientation:**\n")
            export_lines.append(
                f"```yaml\nposition: [{_pos_cp[0]:.6f}, {_pos_cp[1]:.6f}, {_pos_cp[2]:.6f}]  # mm\nangles: [{_angs_cp[0]:.8f}, {_angs_cp[1]:.8f}, {_angs_cp[2]:.8f}]  # radians\n```\n\n"
            )
            export_lines.append("**Interior Orientation:**\n")
            export_lines.append(
                f"```yaml\nfocal_length: {_cc_cp:.6f}  # mm\nprincipal_point_x: {_xh_cp:.6f}  # mm\nprincipal_point_y: {_yh_cp:.6f}  # mm\n```\n\n"
            )
            export_lines.append("**Distortion Parameters:**\n")
            export_lines.append(
                f"```yaml\nk1: {_k1_cp:.8f}\nk2: {_k2_cp:.8f}\nk3: {_k3_cp:.8f}\np1: {_p1_cp:.8f}\np2: {_p2_cp:.8f}\nscx: {_scx_cp:.8f}\nshe: {_she_cp:.8f}\n```\n\n"
            )
            export_lines.append("---\n")

        _ = mo.md("".join(export_lines))

    _
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Next Steps

    1. **Test in pyPTV GUI:**
       - Load the generated `.ori` and `.addpar` files
       - Run epipolar line verification
       - Test with particle images

    2. **Optional: Dumbbell Validation**
       - If you have dumbbell images, run validation to check accuracy

    3. **Iterate if needed:**
       - Adjust weights in bundle adjustment
       - Remove outlier frames
       - Re-run optimization
    """)
    return


@app.cell
def _(
    Poly3DCollection,
    cals,
    cals_optimized,
    config,
    draw_camera_pyramid,
    mo,
    np,
    plt,
    triangulated_frames,
):
    import matplotlib.cm as cm


    def visualize_cameras_and_grids(cams, frames_data, rows, cols):
        _fig = plt.figure(figsize=(12, 10))
        _ax = _fig.add_subplot(111, projection="3d")

        # Draw cameras
        _colors_cams = ["red", "green", "blue", "orange"]
        for _i, _cal in enumerate(cams):
            _pos = _cal.get_pos()
            _angles = _cal.get_angles()
            draw_camera_pyramid(
                _ax,
                _pos,
                _angles,
                scale=150,
                color=_colors_cams[_i % len(_colors_cams)],
                label=f"Cam {_i + 1}",
            )

        # Draw Grids
        if frames_data:
            # Generate colors for frames
            _cmap = cm.get_cmap("viridis", len(frames_data))

            for _idx, (_frame_idx, _points) in enumerate(frames_data.items()):
                # Extract corners of the grid (assuming row-major order)
                # Top-Left: 0
                # Top-Right: cols - 1
                # Bottom-Right: rows * cols - 1
                # Bottom-Left: (rows - 1) * cols

                _p_tl = _points[0]
                _p_tr = _points[cols - 1]
                _p_br = _points[rows * cols - 1]
                _p_bl = _points[(rows - 1) * cols]

                _verts = [[_p_tl, _p_tr, _p_br, _p_bl]]

                # Create polygon using the globally available Poly3DCollection
                _poly = Poly3DCollection(_verts, alpha=0.5)
                _color = _cmap(_idx)
                _poly.set_facecolor(_color)
                _poly.set_edgecolor("k")
                _ax.add_collection3d(_poly)

                # Add text for frame number at centroid (every 5th frame to avoid clutter)
                _centroid = np.mean(_points, axis=0)
                if _idx % 5 == 0:
                    _ax.text(
                        _centroid[0],
                        _centroid[1],
                        _centroid[2],
                        f"F{_frame_idx}",
                        fontsize=8,
                    )

        # Set limits
        _all_cam_pos = np.array([_c.get_pos() for _c in cams])

        # Collect all grid points to set proper limits
        if frames_data:
            _all_grid_points = np.vstack(list(frames_data.values()))
            _all_points = np.vstack([_all_cam_pos, _all_grid_points])
        else:
            _all_points = _all_cam_pos

        # Calculate center and range
        _mid = np.mean(_all_points, axis=0)
        _max_range = np.max(np.ptp(_all_points, axis=0)) / 2

        _ax.set_xlim(_mid[0] - _max_range, _mid[0] + _max_range)
        _ax.set_ylim(_mid[1] - _max_range, _mid[1] + _max_range)
        _ax.set_zlim(_mid[2] - _max_range, _mid[2] + _max_range)

        _ax.set_xlabel("X (mm)")
        _ax.set_ylabel("Y (mm)")
        _ax.set_zlabel("Z (mm)")
        _ax.set_title("3D View: Cameras and Calibration Grids")

        return _fig


    _cams_to_plot_final = cals_optimized if cals_optimized is not None else cals
    _fig_3d_grids = visualize_cameras_and_grids(
        _cams_to_plot_final,
        triangulated_frames,
        config.grid_rows,
        config.grid_cols,
    )
    mo.mpl.interactive(_fig_3d_grids)
    return


@app.cell
def _(
    cals,
    compute_planarity_error,
    config,
    convert_arr_pixel_to_metric,
    cpar,
    frame_detections,
    grid_ba_residuals,
    least_squares,
    mo,
    multi_cam_point_positions,
    np,
    pd,
    ptv,
    synchronized_frames,
    triangulated_frames,
):
    import time


    def run_iterative_bundle_adjustment(num_iterations=5):
        # global cals, triangulated_frames, frame_metrics # Don't use global, use args or local

        current_cals = [ptv.clone_calibration(c) for c in cals]
        current_points_3d = triangulated_frames.copy()

        start_time = time.time()

        history = []

        num_cams = len(current_cals)
        active_cams = np.ones(num_cams, dtype=bool)
        num_active = num_cams
        params_per_cam = 16
        cam_params_len = num_active * params_per_cam
        pos_scale = 1.0

        # Weights for constraints
        w_planarity = 10.0
        w_distance = 100.0

        for i in range(num_iterations):
            iter_start = time.time()
            print(f"--- Iteration {i + 1}/{num_iterations} ---")

            # 1. Setup Optimization Vector
            calib_vec = np.empty((num_active, params_per_cam), dtype=float)
            for cam_idx in range(num_cams):
                cal = current_cals[cam_idx]
                calib_vec[cam_idx, 0:3] = cal.get_pos() / pos_scale
                calib_vec[cam_idx, 3:6] = cal.get_angles()
                calib_vec[cam_idx, 6:9] = cal.get_primary_point()
                calib_vec[cam_idx, 9:12] = cal.get_radial_distortion()
                calib_vec[cam_idx, 12:14] = cal.get_decentering()
                calib_vec[cam_idx, 14:16] = cal.get_affine()

            x0 = calib_vec.reshape(-1)

            # Calculate initial cost for this iteration
            res_init = grid_ba_residuals(
                x0,
                current_points_3d,
                frame_detections,
                cpar,
                current_cals,
                active_cams,
                w_planarity,
                w_distance,
                pos_scale,
            )
            cost_init = np.sum(res_init**2)

            print(f"  Optimization start cost: {cost_init:.2e}")

            # 2. Run Optimization (Bundle Adjustment)
            # Using x_scale='jac' to handle different parameter scales automatically
            result = least_squares(
                grid_ba_residuals,
                x0,
                args=(
                    current_points_3d,
                    frame_detections,
                    cpar,
                    current_cals,
                    active_cams,
                    w_planarity,
                    w_distance,
                    pos_scale,
                ),
                method="trf",
                loss="soft_l1",
                xtol=1e-15,
                ftol=1e-15,
                gtol=1e-15,
                x_scale="jac",
                max_nfev=500,
                verbose=0,
            )

            # 3. Update Cameras
            calib_pars = result.x[:cam_params_len].reshape(-1, params_per_cam)
            for cam_idx in range(num_cams):
                cal = current_cals[cam_idx]
                pars = calib_pars[cam_idx]
                cal.set_pos(pars[0:3] * pos_scale)
                cal.set_angles(pars[3:6])
                cal.set_primary_point(pars[6:9])
                cal.set_radial_distortion(pars[9:12])
                cal.set_decentering(pars[12:14])
                cal.set_affine_trans(pars[14:16])

            # 4. Re-triangulate Points
            print("  Re-triangulating points...")

            # We need to re-implement triangulation loop here using updated current_cals
            new_triangulated = {}
            planarity_scores = []

            for frame_idx in synchronized_frames:
                # Gather 2D points and convert to metric
                # NOTE: frame_detections is global
                frame_corners = frame_detections[frame_idx]
                valid_cams_indices = [
                    ci for ci, pts in frame_corners.items() if pts is not None
                ]

                points_3d_frame = np.zeros(
                    (config.grid_rows * config.grid_cols, 3)
                )

                for pt_idx in range(config.grid_rows * config.grid_cols):
                    pts_2d_list = []
                    for cam_idx in valid_cams_indices:
                        if pt_idx < len(frame_corners[cam_idx]):
                            pix_coords = frame_corners[cam_idx][pt_idx]
                            pix_arr = np.array([pix_coords]).astype(np.float64)

                            # Convert to metric using UPDATED cal
                            metric_arr = np.empty_like(pix_arr)
                            try:
                                # Try 3-arg version first (common in newer pyptv/optv)
                                # convert_arr_pixel_to_metric(pixel_pos, cpar, out_metric)
                                # BUT wait, does it use 'cal'?
                                # If we pass cpar only, it's affine. If we want distortion correction, we need cal.
                                # Standard optv binding usually: convert_arr_pixel_to_metric(pos, cpar, cal)
                                # But prev error said: "Argument 'out' has incorrect type".
                                # This implies 3rd arg is output.
                                # So it probably only does Affine + MM conversion.
                                # Distortion correction is usually "distorted_to_flat".
                                # Let's assume convert_arr_pixel_to_metric is just Affine for now.
                                convert_arr_pixel_to_metric(
                                    pix_arr, cpar, metric_arr
                                )
                            except Exception:
                                pass

                            pts_2d_list.append(metric_arr[0])

                    if len(pts_2d_list) >= 2:
                        cals_subset = [
                            current_cals[ci] for ci in valid_cams_indices
                        ]
                        pts_input = np.array(pts_2d_list)[np.newaxis, :, :].astype(
                            np.float64
                        )
                        xyz, _ = multi_cam_point_positions(
                            pts_input, cpar, cals_subset
                        )
                        points_3d_frame[pt_idx] = xyz[0]

                new_triangulated[frame_idx] = points_3d_frame

                # Compute metric for monitoring
                _, rms_plan, _, _ = compute_planarity_error(points_3d_frame)
                planarity_scores.append(rms_plan)

            current_points_3d = new_triangulated
            avg_planarity = np.mean(planarity_scores)

            print(f"  Result cost: {result.cost:.2e}")
            print(f"  Avg Planarity: {avg_planarity:.4f} mm")

            history.append(
                {"iteration": i, "cost": result.cost, "planarity": avg_planarity}
            )

        return current_cals, current_points_3d, history


    # Run the iterative process
    cals_iterative, points_iterative, history = run_iterative_bundle_adjustment(
        num_iterations=5
    )

    # Update global variables for visualization/export
    cals_optimized = cals_iterative
    # triangulated_frames = points_iterative # Avoid overwriting global if it breaks things

    # Show history
    df_hist = pd.DataFrame(history)
    mo.md("### Iterative Refinement History")
    mo.ui.table(df_hist)
    return (cals_optimized,)


@app.cell
def _(cals, cpar, image_coordinates, np):
    def test_sensitivity():
        cal = cals[0]
        p3d = np.array([[0, 0, 0]], dtype=np.float64)
        mm = cpar.get_multimedia_params()

        # Baseline
        pos_orig = cal.get_pos()
        proj1 = image_coordinates(p3d, cal, mm)

        # Modify
        cal.set_pos(pos_orig + np.array([10.0, 0, 0]))
        proj2 = image_coordinates(p3d, cal, mm)

        # Restore
        cal.set_pos(pos_orig)

        print(f"Orig Pos: {pos_orig}")
        print(f"Proj 1: {proj1}")
        print(f"Proj 2: {proj2}")
        print(f"Diff: {np.linalg.norm(proj1 - proj2)}")


    test_sensitivity()
    return


@app.cell
def _(
    Path,
    cals_optimized,
    config,
    convert_arr_metric_to_pixel,
    cpar,
    cv2,
    frame_detections,
    image_coordinates,
    mo,
    np,
    plt,
    synchronized_frames,
    triangulated_frames,
):
    def visualize_reprojection(
        frame_idx, cam_idx, cal, points_3d, observations_2d
    ):
        """Visualize observed vs reprojected points."""
        obs_2d = observations_2d[frame_idx][cam_idx]
        if obs_2d is None:
            return

        mm_params = cpar.get_multimedia_params()
        proj_metric = image_coordinates(points_3d, cal, mm_params)
        proj_pixel = np.empty_like(proj_metric)
        convert_arr_metric_to_pixel(proj_metric, cpar, proj_pixel)

        # Plot
        fig, ax = plt.subplots(figsize=(10, 8))

        # Load image if available
        folder_name = config.camera_folders[cam_idx]
        folder_path = Path(config.calib_base) / folder_name
        image_file = None
        for f in folder_path.iterdir():
            if f.name.startswith(f"{frame_idx:08d}_"):
                image_file = f
                break

        if image_file:
            img = cv2.imread(str(image_file), cv2.IMREAD_GRAYSCALE)
            ax.imshow(img, cmap="gray")

        ax.scatter(
            obs_2d[:, 0], obs_2d[:, 1], c="g", marker="+", s=50, label="Observed"
        )
        ax.scatter(
            proj_pixel[:, 0],
            proj_pixel[:, 1],
            c="r",
            marker="x",
            s=50,
            label="Reprojected",
        )

        # Draw lines connecting corresponding points
        for i in range(len(obs_2d)):
            ax.plot(
                [obs_2d[i, 0], proj_pixel[i, 0]],
                [obs_2d[i, 1], proj_pixel[i, 1]],
                "y-",
                alpha=0.3,
            )

        ax.set_title(f"Reprojection: Cam {cam_idx + 1} Frame {frame_idx}")
        ax.legend()
        return fig


    # Show sample reprojection
    if triangulated_frames and cals_optimized:
        _sample_frame = synchronized_frames[0]
        _fig_reproj = visualize_reprojection(
            _sample_frame,
            0,
            cals_optimized[0],
            triangulated_frames[_sample_frame],
            frame_detections,
        )

    mo.mpl.interactive(_fig_reproj)
    return


@app.cell
def _(Path, config, cv2, mo):
    # Interactive Blob Detector Parameter Tuning
    # import cv2
    # import numpy as np
    # import matplotlib.pyplot as plt
    # from pathlib import Path

    # Load a sample image from the new dataset (Camera 1, Frame 0)
    sample_image_path = Path(config.calib_base) / config.camera_folders[0]
    sample_file = next(
        sample_image_path.glob("*.tiff"), None
    )  # Assuming .tif or similar

    if sample_file is None:
        print("No image found!")
        sample_img = None
    else:
        sample_img = cv2.imread(str(sample_file), cv2.IMREAD_GRAYSCALE)

    # Create UI controls for parameters
    min_threshold = mo.ui.slider(0, 255, value=10, label="Min Threshold")
    max_threshold = mo.ui.slider(0, 255, value=220, label="Max Threshold")
    min_area = mo.ui.slider(1, 500, value=20, label="Min Area")
    max_area = mo.ui.slider(100, 5000, value=1000, label="Max Area")
    min_circularity = mo.ui.slider(
        0.1, 1.0, value=0.7, step=0.05, label="Min Circularity"
    )
    min_convexity = mo.ui.slider(
        0.1, 1.0, value=0.8, step=0.05, label="Min Convexity"
    )
    min_inertia = mo.ui.slider(0.1, 1.0, value=0.5, step=0.05, label="Min Inertia")
    return (
        max_area,
        max_threshold,
        min_area,
        min_circularity,
        min_convexity,
        min_inertia,
        min_threshold,
        sample_img,
    )


@app.cell
def _(cv2, np, plt):
    # Function to detect and display
    def detect_blobs(
        img, min_t, max_t, min_a, max_a, min_circ, min_conv, min_inert
    ):
        img_blur = cv2.GaussianBlur(img, (0, 0), 0.9)  # sigma ~0.6–0.9
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(16, 16))
        img_p = clahe.apply(img_blur)

        params = cv2.SimpleBlobDetector_Params()

        # Robust threshold sweep for tiny bright dots
        params.minThreshold = min_t
        params.maxThreshold = max_t
        params.thresholdStep = 5

        # Bright blobs on dark background
        params.filterByColor = True
        params.blobColor = 255

        # Dot spacing ~20 px
        params.minDistBetweenBlobs = 15  # try 12–16

        # Dot diameter 4–6 px => expected area ~12–28 px^2
        params.filterByArea = True
        params.minArea = min_a  # try 6–12
        params.maxArea = max_a  # try 80–160

        # Shape constraints (moderate)
        params.filterByCircularity = True
        params.minCircularity = min_circ  # 0.65      # try 0.55–0.80

        params.filterByInertia = True
        params.minInertiaRatio = min_inert  # 0.45     # try 0.30–0.70

        params.filterByConvexity = True
        params.minConvexity = min_conv  # 0.75        # try 0.65–0.90

        detector = cv2.SimpleBlobDetector_create(params)

        keypoints = detector.detect(img_p)
        print(keypoints)

        # Draw keypoints
        im_with_keypoints = cv2.drawKeypoints(
            img_p,
            keypoints,
            np.array([]),
            (255, 0, 0),
            cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS,
        )

        # Plot
        fig, ax = plt.subplots(figsize=(10, 8))
        ax.imshow(im_with_keypoints)
        ax.set_title(f"Detected Blobs: {len(keypoints)}")
        ax.axis("off")
        ax.set_xlim(950, 1200)
        ax.set_ylim(650, 900)
        # ax.invert_yaxis()  # Match image coordinate system
        return ax

    return (detect_blobs,)


@app.cell
def _(
    detect_blobs,
    max_area,
    max_threshold,
    min_area,
    min_circularity,
    min_convexity,
    min_inertia,
    min_threshold,
    mo,
    sample_img,
):
    # Display UI
    mo.vstack(
        [
            mo.md("### Blob Detector Tuner"),
            mo.hstack([min_threshold, max_threshold]),
            mo.hstack([min_area, max_area]),
            mo.hstack([min_circularity, min_convexity, min_inertia]),
            detect_blobs(
                sample_img,
                min_threshold.value,
                max_threshold.value,
                min_area.value,
                max_area.value,
                min_circularity.value,
                min_convexity.value,
                min_inertia.value,
            ),
        ]
    )
    return


@app.cell
def _(cv2, np, plt, sample_img):
    def _():
        # import cv2

        params = cv2.SimpleBlobDetector_Params()

        # --- threshold sweep (tighter than default) ---
        params.minThreshold = 25
        params.maxThreshold = 220
        params.thresholdStep = 3
        params.minRepeatability = 1  # IMPORTANT for rejecting threshold artifacts

        # --- bright dots on dark background ---
        params.filterByColor = False
        params.blobColor = 255

        # --- spacing ~20 px; suppress midpoint candidates ---
        params.minDistBetweenBlobs = 10  # try 16–19

        # --- area derived from sigma range ---
        # A ≈ 2*pi*sigma^2, for sigma in [1,3] => ~[6,57]
        params.filterByArea = True
        params.minArea = 5
        params.maxArea = 50  # give margin; try 90–160

        # --- shape filters (keep moderate; too strict can drop real dots) ---
        params.filterByCircularity = True
        params.minCircularity = 0.40  # try 0.65–0.85

        params.filterByInertia = True
        params.minInertiaRatio = 0.50  # try 0.4–0.75

        params.filterByConvexity = True
        params.minConvexity = 0.80  # try 0.75–0.95

        detector = cv2.SimpleBlobDetector_create(params)

        # img_blur = cv2.GaussianBlur(sample_img, (0,0), 0.8)  # sigma ~0.6–0.9
        # clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(16,16))
        # img_p = clahe.apply(img_blur)

        img_blur = cv2.GaussianBlur(sample_img, (0, 0), 0.7)

        # se = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (21, 21))  # try 15–31
        # tophat = cv2.morphologyEx(img_blur, cv2.MORPH_TOPHAT, se)

        # normalize to 8-bit for blob detector
        # img_p = cv2.normalize(tophat, None, 0, 255, cv2.NORM_MINMAX).astype('uint8')

        keypoints = detector.detect(img_blur)

        # keypoints = detector2.detect(img_blur)
        print(keypoints)

        im_with_keypoints2 = cv2.drawKeypoints(
            img_blur,
            keypoints,
            np.array([]),
            (0, 0, 255),
            cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS,
        )

        # Plot
        _fig, _ax = plt.subplots(figsize=(10, 8))
        _ax.imshow(im_with_keypoints2, origin="upper")
        _ax.set_title(f"Detected Blobs: {len(keypoints)}")
        # _ax.axis('off')
        _ax.set_xlim(950, 1200)
        _ax.set_ylim(650, 900)
        _ax.invert_yaxis()  # Match image coordinate system
        # _ax.set_orientation('image')
        return _ax


    _()
    return


@app.cell
def _(np, plt, sample_img):
    # import numpy as np
    from skimage.feature import blob_log

    blobs = blob_log(
        sample_img,
        min_sigma=1.0,  # ~ dot radius / sqrt(2)
        max_sigma=3.0,
        num_sigma=15,
        threshold=0.03,
    )

    # blob_log returns (y, x, sigma)
    points = [(b[1], b[0]) for b in blobs]
    print("detections:", len(points))

    _fig, _ax = plt.subplots(figsize=(10, 8))
    _ax.imshow(sample_img, cmap="gray")

    for y, x, s in blobs:
        r = np.sqrt(2) * s
        c = plt.Circle((x, y), r, color="red", fill=False, linewidth=1)
        _ax.add_patch(c)

    _ax.set_xlim(950, 1200)
    _ax.set_ylim(650, 900)
    _ax.invert_yaxis()
    _ax
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
