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
                calib_base="/home/user/Downloads/Illmenau/KalibrierungA",
                camera_folders={
                    0: "Kalibrierung1a",
                    1: "Kalibrierung2a",
                    2: "Kalibrierung3a",
                    3: "Kalibrierung4a",
                },
                num_frames=40,
                grid_rows=7,
                grid_cols=6,
                grid_spacing_mm=120.0,
                yaml_path="/home/user/Downloads/Illmenau/pyPTV_folder/parameters_Run4.yaml",
                output_dir="/home/user/Downloads/Illmenau/pyPTV_folder/calibration_output",
            )

    return (CalibrationConfig,)


@app.cell
def _(CalibrationConfig, mo):
    config = CalibrationConfig.for_illmenau_run4()
    mo.md(f"""
    ### Configuration Loaded

    | Parameter | Value |
    |-----------|-------|
    | **Calibration Base** | `{config.calib_base}` |
    | **YAML Parameters** | `{config.yaml_path}` |
    | **Cameras** | {len(config.camera_folders)} |
    | **Frames** | {config.num_frames} |
    | **Grid** | {config.grid_rows}×{config.grid_cols} ({config.grid_rows * config.grid_cols} points) |
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

    _sample_frame_viz = synchronized_frames[0] if synchronized_frames else None

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
        cal = Calibration()
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
                cal.from_file(str(_ori_file_path_cl), str(_addpar_file_path_cl))
                load_status.append(f"✓ Cam {_i_cl + 1}: {_ori_file_path_cl.name}")
            else:
                load_status.append(f"⚠ Cam {_i_cl + 1}: Missing calibration files")
                cal.set_pos(np.array([0.0, 0.0, 1000.0]))
                cal.set_angles(np.array([0.0, 0.0, 0.0]))
        else:
            load_status.append(f"⚠ Cam {_i_cl + 1}: No calibration path")
            cal.set_pos(np.array([0.0, 0.0, 1000.0]))
            cal.set_angles(np.array([0.0, 0.0, 0.0]))

        cals.append(cal)

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

        w, h, d = 0.5 * scale, 0.4 * scale, 1.0 * scale
        local_verts = np.array(
            [[0, 0, 0], [-w, -h, d], [w, -h, d], [w, h, d], [-w, h, d]]
        )

        world_verts = (rot_matrix @ local_verts.T).T + pos

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
                for _cam_idx_tr2 in _valid_cams_tr:
                    if _pt_idx_tr < len(_frame_corners_tr[_cam_idx_tr2]):
                        _pts_2d_list_tr.append(
                            _frame_corners_tr[_cam_idx_tr2][_pt_idx_tr]
                        )

                if len(_pts_2d_list_tr) >= 2:
                    _pts_2d_tr = np.array(_pts_2d_list_tr)[
                        np.newaxis, :, :
                    ].astype(np.float64)
                    _xyz_tr, _err_tr = multi_cam_point_positions(
                        _pts_2d_tr, cpar, cals
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
        ### Triangulation Results

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
    image_coordinates,
    np,
):
    """
    ## Step 4: Bundle Adjustment

    Optimize camera exterior orientation using:
    - **Reprojection error**: Minimize 2D projection error
    - **Planarity constraint**: All grid points lie on a plane
    - **Distance constraint**: Adjacent points at 120mm spacing
    """


    def grid_ba_residuals(
        calib_vec,
        frames_data,
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
        cam_params_len = num_active * 6

        calib_pars = calib_vec[:cam_params_len].reshape(-1, 2, 3)
        ptr = 0
        for cam_ba, cal_ba in enumerate(calibs):
            if not active_cams_arr[cam_ba]:
                continue
            pars = calib_pars[ptr]
            cal_ba.set_pos(pars[0] * pos_scale)
            cal_ba.set_angles(pars[1])
            ptr += 1

        mm_params = cpar.get_multimedia_params()
        residuals = []

        for frame_idx_ba, points_3d_ba in frames_data.items():
            for cam_ba2 in range(num_cams_ba):
                if (
                    not active_cams_arr[cam_ba2]
                    or cam_ba2 not in frames_data[frame_idx_ba]
                ):
                    continue
                corners_ba = frames_data[frame_idx_ba][cam_ba2]
                try:
                    proj = image_coordinates(
                        points_3d_ba, calibs[cam_ba2], mm_params
                    )
                    diff = corners_ba - proj
                    residuals.extend(diff.ravel())
                except Exception:
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
def _(
    cals,
    config,
    cpar,
    grid_ba_residuals,
    least_squares,
    mo,
    np,
    ptv,
    triangulated_frames,
):
    cals_optimized = None
    diagnostics = None
    result = None

    if triangulated_frames:
        num_cams_ba2 = len(cals)
        num_points_ba2 = config.grid_rows * config.grid_cols
        pos_scale = 1.0
        active_cams = np.ones(num_cams_ba2, dtype=bool)
        num_active2 = num_cams_ba2
        cam_params_len2 = num_active2 * 6

        calib_vec = np.empty((num_active2, 2, 3), dtype=float)
        for cam_ba3 in range(num_cams_ba2):
            calib_vec[cam_ba3, 0] = cals[cam_ba3].get_pos() / pos_scale
            calib_vec[cam_ba3, 1] = cals[cam_ba3].get_angles()

        x0 = calib_vec.reshape(-1)

        w_planarity = 0.1
        w_distance = 1.0

        initial_residuals = grid_ba_residuals(
            x0,
            triangulated_frames,
            cpar,
            cals,
            active_cams,
            w_planarity,
            w_distance,
            pos_scale,
        )
        fun_initial = np.sum(initial_residuals**2)

        _ = mo.md(f"""
        ### Bundle Adjustment Setup

        | Parameter | Value |
        |-----------|-------|
        | **Cameras** | {num_cams_ba2} |
        | **Frames** | {len(triangulated_frames)} |
        | **Optimization Parameters** | {len(x0)} ({num_active2} × 6) |
        | **Initial Cost** | {fun_initial:.4f} |
        | **Weights** | planarity={w_planarity}, distance={w_distance} |
        """)

        print(f"Running bundle adjustment...")
        result = least_squares(
            grid_ba_residuals,
            x0,
            args=(
                triangulated_frames,
                cpar,
                cals,
                active_cams,
                w_planarity,
                w_distance,
                pos_scale,
            ),
            method="trf",
            loss="soft_l1",
            xtol=1e-8,
            ftol=1e-8,
            gtol=1e-6,
            max_nfev=5000,
            verbose=2,
        )

        calib_pars = result.x[:cam_params_len2].reshape(-1, 2, 3)

        cals_optimized = []
        for cam_ba4 in range(num_cams_ba2):
            cal_opt = ptv.clone_calibration(cals[cam_ba4])
            cal_opt.set_pos(calib_pars[cam_ba4, 0] * pos_scale)
            cal_opt.set_angles(calib_pars[cam_ba4, 1])
            cals_optimized.append(cal_opt)

        fun_final = np.sum(
            grid_ba_residuals(
                result.x,
                triangulated_frames,
                cpar,
                cals_optimized,
                active_cams,
                w_planarity,
                w_distance,
                pos_scale,
            )
            ** 2
        )

        improvement = (
            100 * (fun_initial - fun_final) / fun_initial if fun_initial > 0 else 0
        )

        _ = mo.md(f"""
        ### Optimization Results

        | Metric | Value |
        |--------|-------|
        | **Initial Cost** | {fun_initial:.4f} |
        | **Final Cost** | {fun_final:.4f} |
        | **Improvement** | {improvement:.1f}% |
        | **Success** | {result.success} |
        | **Message** | {result.message} |
        """)

        diagnostics = {
            "fun_initial": fun_initial,
            "fun_final": fun_final,
            "improvement_pct": improvement,
            "success": result.success,
        }
    else:
        mo.md("❌ No triangulated frames for bundle adjustment")
    return (cals_optimized,)


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

    lines = [
        f"{cc:.10f}  # focal length (mm)",
        f"{xh:.10f}  # principal point x (mm)",
        f"{yh:.10f}  # principal point y (mm)",
        f"{k1:.10f}  # radial distortion k1",
        f"{k2:.10f}  # radial distortion k2",
        f"{p1:.10f}  # decentering p1",
        f"{p2:.10f}  # decentering p2",
        f"{k3:.10f}  # radial distortion k3",
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
                f"```yaml\nk1: {_k1_cp:.8f}\nk2: {_k2_cp:.8f}\nk3: {_k3_cp:.8f}\np1: {_p1_cp:.8f}\np2: {_p2_cp:.8f}\n```\n\n"
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


if __name__ == "__main__":
    app.run()
