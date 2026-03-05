import marimo

__generated_with = "0.20.4"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo

    mo.md(r"""
    # illmenau Multi-Camera Calibration

    interactive calibration workflow for the illmenau 4-camera setup.

    **Workflow:**
    1. **Grid Detection** - Detect 7×6 circular grid in calibration images
    2. **initial Calibration** - OpenCV intrinsic + stereo calibration
    3. **Bundle Ad_justment** - Refine with planarity & distance constraints
    4. **Export** - Generate `.ori` and `.addpar` files for pyPTV GUi
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
        def for_illmenau_run4(cls) -> "CalibrationConfig":
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
    folder_status = []
    all_ok = True

    calib_base = Path(config.calib_base)
    yaml_path = Path(config.yaml_path)

    for _cam_idx, folder_name in config.camera_folders.items():
        folder_path = calib_base / folder_name
        exists = folder_path.exists()
        if not exists:
            all_ok = False
        icon = "✓" if exists else "❌"
        folder_status.append(f"{icon} **Camera {_cam_idx + 1}**: `{folder_path}`")

    yaml_exists = yaml_path.exists()
    if not yaml_exists:
        all_ok = False

    mo.md(
        f"""
    ### File System Check

    {"**✓ All paths valid!**" if all_ok else "**⚠ Some paths missing!**"}

    **Parameter File:**
    - {"✓" if yaml_exists else "❌"} `{yaml_path}`

    **Camera Folders:**
    """
        + "\n".join(folder_status)
    )
    return calib_base, yaml_path


@app.cell
def _(Calibration, Experiment, ParameterManager, Path, np, ptv, yaml_path):
    """
    ## Step 2: Load initial Calibration & Parameters

    Load camera parameters from YAML and initial calibration files.
    """

    yaml_file = Path(yaml_path.value if hasattr(yaml_path, "value") else yaml_path)
    base_path = yaml_file.parent

    pm = ParameterManager()
    pm.from_yaml(yaml_file)
    exp = Experiment(pm=pm)

    params = pm.parameters
    num_cams = int(params.get("num_cams", pm.num_cams or 0) or 0)
    ptv_params = params.get("ptv", {})
    cpar = ptv._populate_cpar(ptv_params, num_cams)

    cal_ori = pm.parameters.get("cal_ori", {})
    ori_names = cal_ori.get("img_ori", [])

    cals = []
    load_status = []

    for _i in range(num_cams):
        cal = Calibration()
        _ori_path = ori_names[_i] if _i < len(ori_names) else None

        if _ori_path:
            ori_file_path = base_path / _ori_path
            addpar_file_path = Path(
                str(ori_file_path).replace(".ori", "") + ".addpar"
            )
            if not addpar_file_path.exists():
                addpar_file_path = Path(
                    str(ori_file_path).replace(".tif.ori", "") + ".addpar"
                )

            if ori_file_path.exists() and addpar_file_path.exists():
                cal.from_file(str(ori_file_path), str(addpar_file_path))
                load_status.append(f"✓ Cam {_i + 1}: {ori_file_path.name}")
            else:
                load_status.append(f"⚠ Cam {_i + 1}: Missing calibration files")
                cal.set_pos(np.array([0.0, 0.0, 1000.0]))
                cal.set_angles(np.array([0.0, 0.0, 0.0]))
        else:
            load_status.append(f"⚠ Cam {_i + 1}: No calibration path")
            cal.set_pos(np.array([0.0, 0.0, 1000.0]))
            cal.set_angles(np.array([0.0, 0.0, 0.0]))

        cals.append(cal)
    return cals, cpar, load_status, num_cams, ptv_params


@app.cell
def _(calib_base, config, cv2, mo, np, num_cams):
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

    # calib_base = Path(config.calib_base)
    # num_cams = len(config.camera_folders)

    # Storage: _frame_idx -> {_cam_idx: corners or None}
    frame_detections = {}
    for _frame_idx in range(config.num_frames):
        frame_detections[_frame_idx] = {
            _cam_idx: None for _cam_idx in config.camera_folders.keys()
        }

    detection_log = []

    print(f"Detecting grids in {config.num_frames} frames × {num_cams} cameras...")

    for _cam_idx, _folder_name in config.camera_folders.items():
        _folder_path = calib_base / _folder_name
        cam_success = 0
        cam_failed = 0

        for _frame_idx in range(config.num_frames):
            # Find image file
            image_file = None
            for f in _folder_path.iterdir():
                if f.name.startswith(f"{_frame_idx:08d}_"):
                    image_file = f
                    break

            if image_file is None:
                cam_failed += 1
                detection_log.append(
                    {"camera": _cam_idx, "frame": _frame_idx, "success": False}
                )
                continue

            img = cv2.imread(str(image_file), cv2.IMREAD_GRAYSCALE)
            if img is None:
                cam_failed += 1
                detection_log.append(
                    {"camera": _cam_idx, "frame": _frame_idx, "success": False}
                )
                continue

            found, corners = cv2.findCirclesGrid(
                img,
                (config.grid_rows, config.grid_cols),
                flags=cv2.CALIB_CB_SYMMETRIC_GRID,
                blobDetector=detector,
            )

            if found:
                corners_squeezed = np.squeeze(corners)
                cam_success += 1
                frame_detections[_frame_idx][_cam_idx] = corners_squeezed
                detection_log.append(
                    {
                        "camera": _cam_idx,
                        "frame": _frame_idx,
                        "success": True,
                        "corners": corners_squeezed,
                        "image_file": str(image_file),
                    }
                )
            else:
                cam_failed += 1
                detection_log.append(
                    {"camera": _cam_idx, "frame": _frame_idx, "success": False}
                )

        print(
            f"  Camera {_cam_idx + 1}: {cam_success}/{config.num_frames} detected"
        )

    # Find synchronized frames
    synchronized_frames = []
    for _frame_idx in range(config.num_frames):
        if all(
            frame_detections[_frame_idx][_cam_idx] is not None
            for _cam_idx in config.camera_folders.keys()
        ):
            synchronized_frames.append(_frame_idx)

    sync_rate = len(synchronized_frames) / config.num_frames * 100

    mo.md(f"""
    ### Detection Results

    | Metric | Value |
    |--------|-------|
    | **Total Frames** | {config.num_frames} |
    | **Synchronized Frames** | {len(synchronized_frames)} |
    | **Synchronization Rate** | {sync_rate:.1f}% |
    | **Total Detections** | {len(synchronized_frames) * num_cams} frames × {num_cams} cams |

    **Synchronized frame indices:** `{synchronized_frames}`
    """)
    return frame_detections, synchronized_frames


@app.cell
def _(
    Path,
    config,
    cv2,
    frame_detections,
    mo,
    num_cams,
    plt,
    synchronized_frames,
):
    def _():
        """Visualize detected grids on sample images."""
        if not synchronized_frames:
            mo.md("❌ No synchronized frames found!")

        # num_cams = len(config.camera_folders)
        sample_frame = synchronized_frames[0]

        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        axes_flat = axes.flatten()

        for _cam_idx in range(num_cams):
            ax = axes_flat[_cam_idx]
            corners = frame_detections[sample_frame][_cam_idx]

            if corners is not None:
                # Load image for display
                folder_name = config.camera_folders[_cam_idx]
                folder_path = Path(config.calib_base) / folder_name
                image_file = None
                for f in folder_path.iterdir():
                    if f.name.startswith(f"{sample_frame:08d}_"):
                        image_file = f
                        break

                if image_file:
                    img = cv2.imread(str(image_file), cv2.IMREAD_GRAYSCALE)
                    ax.imshow(img, cmap="gray")

                    # Draw detected grid
                    corners_grid = corners.reshape(
                        config.grid_rows, config.grid_cols, 2
                    )
                    ax.scatter(
                        corners[:, 0], corners[:, 1], c="red", s=40, marker="o"
                    )

                    # Draw grid lines
                    for _i in range(config.grid_rows):
                        ax.plot(
                            corners_grid[_i, :, 0],
                            corners_grid[_i, :, 1],
                            "b-",
                            lw=0.8,
                            alpha=0.6,
                        )
                    for _j in range(config.grid_cols):
                        ax.plot(
                            corners_grid[:, _j, 0],
                            corners_grid[:, _j, 1],
                            "b-",
                            lw=0.8,
                            alpha=0.6,
                        )

            ax.set_title(f"Camera {_cam_idx + 1} - Frame {sample_frame}")
            ax.set_xlabel("X (pixels)")
            ax.set_ylabel("Y (pixels)")
            ax.invert_yaxis()
            ax.set_aspect("equal")

        plt.tight_layout()
        return mo.ui.matplotlib(fig.gca())


    _()
    return


@app.cell
def _(config, frame_detections, mo, pd, synchronized_frames):
    """Create summary table of detections."""

    if not synchronized_frames:
        error_msg = (
            "❌ No synchronized frames found. Cannot create detection summary."
        )
        mo.md(error_msg)

    # Create pivot table showing detection status
    pivot_data = []
    for _frame_idx in range(config.num_frames):
        row = {"frame": _frame_idx}
        for _cam_idx in config.camera_folders.keys():
            has_detection = frame_detections[_frame_idx][_cam_idx] is not None
            row[f"cam{_cam_idx + 1}"] = "✓" if has_detection else "✗"
        row["sync"] = "✓" if _frame_idx in synchronized_frames else "✗"
        pivot_data.append(row)

    df_pivot = pd.DataFrame(pivot_data)

    mo.md("### Detection Status Matrix (✓ = detected)")
    mo.ui.dataframe(df_pivot.set_index("frame"))
    return


@app.cell
def _(load_status, mo, num_cams, ptv_params):
    mo.md(
        f"""
    ### Calibration Files Loaded

    | Metric | Value |
    |--------|-------|
    | **Number of Cameras** | {num_cams} |
    | **image Size** | {ptv_params.get("imx", "N/A")} × {ptv_params.get("imy", "N/A")} pixels |

    **Status:**
    """
        + "\n".join(load_status)
    )
    return


@app.cell
def _(Poly3DCollection, R, np):
    """
    ### Visualize initial Camera Positions

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
    def _():
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection="3d")

        colors = ["red", "green", "blue", "orange"]

        for _i, cal in enumerate(cals):
            pos = cal.get_pos()
            angles = cal.get_angles()
            draw_camera_pyramid(
                ax,
                pos,
                angles,
                scale=200,
                color=colors[_i % len(colors)],
                label=f"Cam {_i + 1}",
            )

        # Draw origin axes
        length = 200
        ax.quiver(
            0, 0, 0, length, 0, 0, color="r", arrow_length_ratio=0.1, label="X"
        )
        ax.quiver(
            0, 0, 0, 0, length, 0, color="g", arrow_length_ratio=0.1, label="Y"
        )
        ax.quiver(
            0, 0, 0, 0, 0, length, color="b", arrow_length_ratio=0.1, label="Z"
        )

        all_pos = np.array([cal.get_pos() for cal in cals])
        max_range = np.ptp(all_pos, axis=0).max() / 2
        mid = all_pos.mean(axis=0)

        ax.set_xlim(mid[0] - max_range * 1.5, mid[0] + max_range * 1.5)
        ax.set_ylim(mid[1] - max_range * 1.5, mid[1] + max_range * 1.5)
        ax.set_zlim(mid[2] - max_range * 1.5, mid[2] + max_range * 1.5)

        ax.set_xlabel("X (mm)")
        ax.set_ylabel("Y (mm)")
        ax.set_zlabel("Z (mm)")
        ax.set_title("initial Camera Positions")
        ax.legend()

        plt.tight_layout()
        return mo.mpl.interactive(fig.gca())


    _()
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

    if not synchronized_frames:
        mo.md("❌ No synchronized frames to triangulate")


    num_points = config.grid_rows * config.grid_cols
    triangulated_frames = {}
    frame_metrics = {}

    print(
        f"Triangulating {len(synchronized_frames)} frames × {num_points} points..."
    )

    for _frame_idx in synchronized_frames:
        frame_corners = frame_detections[_frame_idx]
        valid_cams = [
            _cam_idx
            for _cam_idx, corners in frame_corners.items()
            if corners is not None
        ]

        if len(valid_cams) < 2:
            continue

        points_3d = np.zeros((num_points, 3))

        for pt_idx in range(num_points):
            pts_2d_list = []
            for _cam_idx in valid_cams:
                if pt_idx < len(frame_corners[_cam_idx]):
                    pts_2d_list.append(frame_corners[_cam_idx][pt_idx])

            if len(pts_2d_list) >= 2:
                pts_2d = np.array(pts_2d_list)[np.newaxis, :, :].astype(np.float64)
                xyz, err = multi_cam_point_positions(pts_2d, cpar, cals)
                points_3d[pt_idx] = xyz[0]

        triangulated_frames[_frame_idx] = points_3d

        # Compute planarity
        centroid = np.mean(points_3d, axis=0)
        centered = points_3d - centroid
        _, _, Vt = np.linalg.svd(centered)
        normal = Vt[2, :]
        deviations = np.dot(centered, normal)
        rms_planarity = np.sqrt(np.mean(deviations**2))

        # Compute distance errors
        dist_errors = []
        for _i in range(config.grid_rows):
            for _j in range(config.grid_cols - 1):
                idx1 = _i * config.grid_cols + _j
                idx2 = _i * config.grid_cols + (_j + 1)
                dist = np.linalg.norm(points_3d[idx2] - points_3d[idx1])
                dist_errors.append(dist - config.grid_spacing_mm)

        for _i in range(config.grid_rows - 1):
            for _j in range(config.grid_cols):
                idx1 = _i * config.grid_cols + _j
                idx2 = (_i + 1) * config.grid_cols + _j
                dist = np.linalg.norm(points_3d[idx2] - points_3d[idx1])
                dist_errors.append(dist - config.grid_spacing_mm)

        rms_distance = np.sqrt(np.mean(np.array(dist_errors) ** 2))

        frame_metrics[_frame_idx] = {
            "rms_planarity": rms_planarity,
            "rms_distance": rms_distance,
        }

    avg_planarity = np.mean([m["rms_planarity"] for m in frame_metrics.values()])
    avg_distance = np.mean([m["rms_distance"] for m in frame_metrics.values()])

    mo.md(f"""
    ### Triangulation Results

    | Metric | Mean ± Std |
    |--------|------------|
    | **RMS Planarity** | {avg_planarity:.3f} ± {np.std([m["rms_planarity"] for m in frame_metrics.values()]):.3f} mm |
    | **RMS Distance** | {avg_distance:.3f} ± {np.std([m["rms_distance"] for m in frame_metrics.values()]):.3f} mm |

    **Frames triangulated:** {len(triangulated_frames)}
    """)
    return frame_metrics, triangulated_frames


@app.cell
def _(frame_metrics, mo, pd):
    """Display per-frame triangulation metrics."""

    if not frame_metrics:
        mo.md("Error computing triangulation metrics.")

    df_metrics = pd.DataFrame(frame_metrics).T
    df_metrics.index.name = "Frame"

    mo.md("### Per-Frame Triangulation Metrics")
    mo.ui.dataframe(df_metrics)
    return


@app.cell
def _(config, mo, plt, triangulated_frames):
    """Visualize triangulated 3D points."""

    if not triangulated_frames:
        mo.md("Error triangulating frames. Cannot visualize 3D points.")

    frames_to_show = list(triangulated_frames.keys())[:3]

    fig = plt.figure(figsize=(18, 5))

    for idx, _frame_idx in enumerate(frames_to_show):
        ax = fig.add_subplot(1, len(frames_to_show), idx + 1, projection="3d")
        points = triangulated_frames[_frame_idx]

        ax.scatter(points[:, 0], points[:, 1], points[:, 2], c="red", s=30)

        # Draw grid connections
        points_grid = points.reshape(config.grid_rows, config.grid_cols, 3)
        for _i in range(config.grid_rows):
            ax.plot(
                points_grid[_i, :, 0],
                points_grid[_i, :, 1],
                points_grid[_i, :, 2],
                "b-",
                lw=0.5,
                alpha=0.5,
            )
        for _j in range(config.grid_cols):
            ax.plot(
                points_grid[:, _j, 0],
                points_grid[:, _j, 1],
                points_grid[:, _j, 2],
                "b-",
                lw=0.5,
                alpha=0.5,
            )

        ax.set_xlabel("X (mm)")
        ax.set_ylabel("Y (mm)")
        ax.set_zlabel("Z (mm)")
        ax.set_title(f"Frame {_frame_idx}")
        ax.view_init(elev=20, azim=-60)

    plt.tight_layout()
    mo.mpl.interactive(fig.gca())
    return


@app.cell
def _():
    """
    ## Step 4: Bundle Ad_justment

    Optimize camera exterior orientation using:
    - **Reprojection error**: Minimize 2D projection error
    - **Planarity constraint**: All grid points lie on a plane
    - **Distance constraint**: Ad_jacent points at 120mm spacing
    """
    return


@app.cell
def _(np):
    def compute_planarity_error(points_3d):
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
        errors = []
        for _i in range(rows):
            for _j in range(cols - 1):
                idx1 = _i * cols + _j
                idx2 = _i * cols + (_j + 1)
                dist = np.linalg.norm(points_3d[idx2] - points_3d[idx1])
                errors.append(dist - spacing)
        for _i in range(rows - 1):
            for _j in range(cols):
                idx1 = _i * cols + _j
                idx2 = (_i + 1) * cols + _j
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
        num_cams = len(calibs)
        num_points = config.grid_rows * config.grid_cols
        active_cams = np.asarray(active_cams, dtype=bool)
        num_active = int(np.sum(active_cams))
        cam_params_len = num_active * 6

        calib_pars = calib_vec[:cam_params_len].reshape(-1, 2, 3)
        ptr = 0
        for cam, cal in enumerate(calibs):
            if not active_cams[cam]:
                continue
            pars = calib_pars[ptr]
            cal.set_pos(pars[0] * pos_scale)
            cal.set_angles(pars[1])
            ptr += 1

        mm_params = cpar.get_multimedia_params()
        residuals = []

        for _frame_idx, points_3d in frames_data.items():
            for cam in range(num_cams):
                if not active_cams[cam] or cam not in frames_data[_frame_idx]:
                    continue
                corners = frames_data[_frame_idx][cam]
                try:
                    pro_j = image_coordinates(points_3d, calibs[cam], mm_params)
                    diff = corners - pro_j
                    residuals.extend(diff.ravel())
                except Exception:
                    residuals.extend([1e6] * (num_points * 2))

            if w_planarity > 0:
                planarity_devs, _, _, _ = compute_planarity_error(points_3d)
                residuals.extend(np.sqrt(w_planarity) * planarity_devs)

            if w_distance > 0:
                distance_errors = compute_distance_errors(
                    points_3d,
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
def _(cals, config, cpar, grid_ba_residuals, mo, np, triangulated_frames):
    if not triangulated_frames:
        mo.md("❌ No triangulated frames for bundle ad_justment")


    num_cams_ba = len(cals)
    _num_points = config.grid_rows * config.grid_cols
    pos_scale = 1.0
    active_cams = np.ones(num_cams_ba, dtype=bool)
    num_active = num_cams_ba
    cam_params_len = num_active * 6

    calib_vec = np.empty((num_active, 2, 3), dtype=float)
    for _cam in range(num_cams_ba):
        calib_vec[_cam, 0] = cals[_cam].get_pos() / pos_scale
        calib_vec[_cam, 1] = cals[_cam].get_angles()

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
    return (
        active_cams,
        cam_params_len,
        fun_initial,
        num_active,
        num_cams_ba,
        pos_scale,
        w_distance,
        w_planarity,
        x0,
    )


@app.cell
def _(
    Calibration,
    active_cams,
    cals,
    cam_params_len,
    cpar,
    fun_initial,
    grid_ba_residuals,
    least_squares,
    mo,
    np,
    num_active,
    num_cams_ba,
    pos_scale,
    triangulated_frames,
    w_distance,
    w_planarity,
    x0,
):
    mo.md(f"""
    ### Bundle Ad_justment Setup

    | Parameter | Value |
    |-----------|-------|
    | **Cameras** | {num_cams_ba} |
    | **Frames** | {len(triangulated_frames)} |
    | **Optimization Parameters** | {len(x0)} ({num_active} × 6) |
    | **initial Cost** | {fun_initial:.4f} |
    | **Weights** | planarity={w_planarity}, distance={w_distance} |
    """)

    print(f"Running bundle ad_justment...")
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

    calib_pars = result.x[:cam_params_len].reshape(-1, 2, 3)
    cals_optimized = []
    for cam in range(num_cams_ba):
        cal_opt = Calibration()
        cal_opt = cals[cam]
        cal_opt.set_pos(calib_pars[cam, 0] * pos_scale)
        cal_opt.set_angles(calib_pars[cam, 1])
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
    return cals_optimized, cam, fun_final, improvement, result


@app.cell
def _(fun_final, fun_initial, improvement, mo, result):
    mo.md(f"""
    ### Optimization Results

    | Metric | Value |
    |--------|-------|
    | **initial Cost** | {fun_initial:.4f} |
    | **Final Cost** | {fun_final:.4f} |
    | **improvement** | {improvement:.1f}% |
    | **Success** | {result.success} |
    | **Message** | {result.message} |
    """)

    diagnostics = {
        "fun_initial": fun_initial,
        "fun_final": fun_final,
        "improvement_pct": improvement,
        "success": result.success,
    }
    return


@app.cell
def _(cals, cals_optimized, cam, mo, np):
    """Display optimized camera parameters."""

    if cals_optimized is None:
        mo.md("Error computing optimized calibration parameters.")

    _num_cams = len(cals)

    mo.md("""
    ### Optimized Camera Parameters

    **Positions (mm) and Angles (degrees):**
    """)

    results_table = """
    | Camera | X (mm) | Y (mm) | Z (mm) | ω (deg) | φ (deg) | κ (deg) |
    |--------|--------|--------|--------|---------|---------|---------|
    """

    for _cam in range(_num_cams):
        _pos = cals_optimized[cam].get_pos()
        _angs = cals_optimized[cam].get_angles()
        results_table += f"| {_cam + 1} | {_pos[0]:.3f} | {_pos[1]:.3f} | {_pos[2]:.3f} | {np.degrees(_angs[0]):.4f} | {np.degrees(_angs[1]):.4f} | {np.degrees(_angs[2]):.4f} |\n"

    mo.md(results_table)
    return


@app.cell
def _(cals, cals_optimized, mo, np):
    def _():
        mo.md("""
        ### Changes (Optimized - initial)
        """)

        delta_table = """
        | Camera | ΔX (mm) | ΔY (mm) | ΔZ (mm) | Δω (deg) | Δφ (deg) | Δκ (deg) |
        |--------|---------|---------|---------|----------|----------|----------|
        """

        for cam in range(_num_cams):
            pos_init = cals[cam].get_pos()
            pos_opt = cals_optimized[cam].get_pos()
            angs_init = cals[cam].get_angles()
            angs_opt = cals_optimized[cam].get_angles()

            delta_pos = pos_opt - pos_init
            delta_angs = np.degrees(angs_opt - angs_init)
            delta_table += f"| {cam + 1} | {delta_pos[0]:.3f} | {delta_pos[1]:.3f} | {delta_pos[2]:.3f} | {delta_angs[0]:.4f} | {delta_angs[1]:.4f} | {delta_angs[2]:.4f} |\n"
        return mo.md(delta_table)


    _()
    return


@app.cell
def _(cals, cals_optimized, mo, np, plt):
    """Compare camera positions before and after optimization."""

    _fig, axes = plt.subplots(
        1, 2, figsize=(16, 6), subplot_kw={"projection": "3d"}
    )


    def draw_cameras(ax, cal_list, title, colors):
        for _i, cal in enumerate(cal_list):
            pos = cal.get_pos()
            ax.scatter(
                pos[0],
                pos[1],
                pos[2],
                s=100,
                color=colors[_i % len(colors)],
                label=f"Cam {_i + 1}",
            )
            ax.text(pos[0], pos[1], pos[2], f"C{_i + 1}", fontsize=10)

        all_pos = np.array([cal.get_pos() for cal in cal_list])
        max_range = np.ptp(all_pos, axis=0).max() / 2
        mid = all_pos.mean(axis=0)

        ax.set_xlim(mid[0] - max_range * 1.5, mid[0] + max_range * 1.5)
        ax.set_ylim(mid[1] - max_range * 1.5, mid[1] + max_range * 1.5)
        ax.set_zlim(mid[2] - max_range * 1.5, mid[2] + max_range * 1.5)

        ax.set_xlabel("X (mm)")
        ax.set_ylabel("Y (mm)")
        ax.set_zlabel("Z (mm)")
        ax.set_title(title)
        ax.legend()
        ax.grid(True, alpha=0.3)


    colors = ["red", "green", "blue", "orange"]
    draw_cameras(axes[0], cals, "initial Camera Positions", colors)
    draw_cameras(axes[1], cals_optimized, "Optimized Camera Positions", colors)

    plt.tight_layout()
    mo.mpl.interactive(_fig)
    return


app._unparsable_cell(
    """
    \"\"\"Compute post-optimization geometric metrics.\"\"\"

    if cals_optimized is None:
        return

    optimized_metrics = {}

    for _frame_idx, points_3d in triangulated_frames.items():
        planarity_devs, rms_planarity, _, _ = compute_planarity_error(points_3d)
        max_planarity = np.max(np.abs(planarity_devs))

        distance_errors = compute_distance_errors(
            points_3d, config.grid_rows, config.grid_cols, config.grid_spacing_mm
        )
        rms_distance = np.sqrt(np.mean(distance_errors**2))
        max_distance = np.max(np.abs(distance_errors))

        optimized_metrics[_frame_idx] = {
            \"rms_planarity\": rms_planarity,
            \"max_planarity\": max_planarity,
            \"rms_distance\": rms_distance,
            \"max_distance\": max_distance,
        }

    avg_planarity_opt = np.mean(
        [m[\"rms_planarity\"] for m in optimized_metrics.values()]
    )
    avg_distance_opt = np.mean(
        [m[\"rms_distance\"] for m in optimized_metrics.values()]
    )

    mo.md(f\"\"\"
    ### Geometric Metrics After Optimization

    | Metric | Mean ± Std | Max |
    |--------|------------|-----|
    | **RMS Planarity** | {avg_planarity_opt:.3f} ± {np.std([m[\"rms_planarity\"] for m in optimized_metrics.values()]):.3f} mm | {np.max([m[\"max_planarity\"] for m in optimized_metrics.values()]):.3f} mm |
    | **RMS Distance** | {avg_distance_opt:.3f} ± {np.std([m[\"rms_distance\"] for m in optimized_metrics.values()]):.3f} mm | {np.max([m[\"max_distance\"] for m in optimized_metrics.values()]):.3f} mm |
    \"\"\")
    """,
    name="_"
)


@app.cell
def _():
    """
    ## Step 5: Export Calibration Files

    Generate `.ori` and `.addpar` files for pyPTV GUi.
    """
    return


@app.cell
def _(Calibration):
    def format_ori_content(cal: Calibration, cam_id: int) -> str:
        """Format .ori file content."""
        pos = cal.get_pos()
        angs = cal.get_angles()

        # Rotation matrix
        R_mat = cal.get_rotation_matrix()

        lines = [
            f"# Camera {cam_id + 1} exterior orientation",
            f"{pos[0]:.10f} {pos[1]:.10f} {pos[2]:.10f}",
            f"{angs[0]:.10f} {angs[1]:.10f} {angs[2]:.10f}",
            "",
            "# Rotation matrix",
            f"{R_mat[0, 0]:.10f} {R_mat[0, 1]:.10f} {R_mat[0, 2]:.10f}",
            f"{R_mat[1, 0]:.10f} {R_mat[1, 1]:.10f} {R_mat[1, 2]:.10f}",
            f"{R_mat[2, 0]:.10f} {R_mat[2, 1]:.10f} {R_mat[2, 2]:.10f}",
        ]

        return "\n".join(lines)

    return (format_ori_content,)


@app.cell
def _(Calibration):
    def format_addpar_content(cal: Calibration) -> str:
        """Format .addpar file content."""
        int_par = cal.get_int_par()
        added_par = cal.get_added_par()

        lines = [
            f"{int_par.cc:.10f}  # focal length (mm)",
            f"{int_par.xh:.10f}  # principal point x (mm)",
            f"{int_par.yh:.10f}  # principal point y (mm)",
            f"{added_par.k1:.10f}  # radial distortion k1",
            f"{added_par.k2:.10f}  # radial distortion k2",
            f"{added_par.p1:.10f}  # decentering p1",
            f"{added_par.p2:.10f}  # decentering p2",
            f"{added_par.k3:.10f}  # radial distortion k3",
        ]

        return "\n".join(lines)

    return (format_addpar_content,)


@app.cell
def _(
    Path,
    addpar_content,
    addpar_filename,
    cals,
    cals_optimized,
    config,
    format_addpar_content,
    format_ori_content,
    mo,
    ori_content,
    ori_filename,
):
    if cals_optimized is None:
        cals_to_export = cals
        mo.md("### Export initial Calibration (no optimization performed)")
    else:
        cals_to_export = cals_optimized
        mo.md("### Export Optimized Calibration")

    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    export_content = []

    for _cam_idx, _cal in enumerate(cals_to_export):
        # _pos = _cal.get_pos()
        # _angs = _cal.get_angles()
        # _int_par = _cal.get_int_par()
        # _added_par = _cal.get_added_par()

        _ori_content = format_ori_content(_cal, _cam_idx)
        _addpar_content = format_addpar_content(_cal)

        _ori_filename = f"cam{_cam_idx + 1}_calibrated.ori"
        _addpar_filename = f"cam{_cam_idx + 1}_calibrated.addpar"

        _ori_path = output_dir / _ori_filename
        _addpar_path = output_dir / _addpar_filename

        with open(_ori_path, "w") as _f:
            _f.write(_ori_content)
        with open(_addpar_path, "w") as _f:
            _f.write(_addpar_content)

        export_content.append(f"""
    **Camera {_cam_idx + 1}:**
    - `{_ori_path}`
    - `{_addpar_path}`

    <details>
    <summary>📋 {ori_filename} (click to expand)</summary>
    ```
    {ori_content}
    ```
    </details>

    <details>
    <summary>📋 {addpar_filename} (click to expand)</summary>
    ```
    {addpar_content}
    ```
    </details>

    ---
    """)

    mo.md(
        f"""
    ### Files Written to `{output_dir}`

    """
        + "\n".join(export_content)
    )
    return


app._unparsable_cell(
    """
    \"\"\"Show copy-paste ready calibration parameters.\"\"\"

    if cals_to_export is None:
        return

    num_cams = len(cals_to_export)

    mo.md(\"\"\"
    ### Copy-Paste Ready Parameters

    Use these values to manually update your YAML or configuration files.
    \"\"\")

    for _cam_idx, cal in enumerate(cals_to_export):
        pos = cal.get_pos()
        angs = cal.get_angles()
        int_par = cal.get_int_par()
        added_par = cal.get_added_par()

        mo.md(f\"\"\"
    #### Camera {_cam_idx + 1}

    **Exterior Orientation:**
    ```yaml
    position: [{pos[0]:.6f}, {pos[1]:.6f}, {pos[2]:.6f}]  # mm
    angles: [{angs[0]:.8f}, {angs[1]:.8f}, {angs[2]:.8f}]  # radians
    ```

    **interior Orientation:**
    ```yaml
    focal_length: {int_par.cc:.6f}  # mm
    principal_point_x: {int_par.xh:.6f}  # mm
    principal_point_y: {int_par.yh:.6f}  # mm
    ```

    **Distortion Parameters:**
    ```yaml
    k1: {added_par.k1:.8f}
    k2: {added_par.k2:.8f}
    k3: {added_par.k3:.8f}
    p1: {added_par.p1:.8f}
    p2: {added_par.p2:.8f}
    ```

    ---
    \"\"\")
    """,
    name="_"
)


@app.cell
def _():
    """
    ## Next Steps

    1. **Test in pyPTV GUi:**
       - Load the generated `.ori` and `.addpar` files
       - Run epipolar line verification
       - Test with particle images

    2. **Optional: Dumbbell Validation**
       - if you have dumbbell images, run validation to check accuracy

    3. **iterate if needed:**
       - Ad_just weights in bundle ad_justment
       - Remove outlier frames
       - Re-run optimization
    """
    return


if __name__ == "__main__":
    app.run()
