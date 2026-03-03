import marimo

__generated_with = "0.20.2"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo

    mo.md("""
    # Grid Detection for Multi-Camera Calibration

    This notebook detects 7×6 grid points in calibration images from 4 cameras and stores **only synchronized frames** where all cameras detected the grid.

    **Input:**
    - 4 camera folders (Kalibrierung1a, Kalibrierung2a, Kalibrierung3a, Kalibrierung4a)
    - 40 frames per camera (synchronized across cameras)
    - Each frame contains a 7×6 circular grid pattern

    **Filtering:**
    - Only keeps frames where **ALL 4 cameras** successfully detected the grid
    - Required for triangulation and bundle adjustment

    **Output:**
    - Pickle file with synchronized detections only
    - Visualization of detection results
    - Statistics on synchronization rate

    **Data structure:**
    - Total: 4 cameras × N_sync frames × 42 points (where N_sync = synchronized frames)
    """)
    return (mo,)


@app.cell
def _():
    import cv2
    import numpy as np
    import pandas as pd
    from pathlib import Path
    import pickle
    import matplotlib.pyplot as plt
    from typing import Dict, List, Optional


    return Path, cv2, np, pd, pickle, plt


@app.cell
def _(Path):
    # Base directory for calibration images
    CALIB_BASE = Path("/home/user/Downloads/Illmenau/KalibrierungA")

    # Camera folder names (1-indexed: camera 1 = Kalibrierung1a, etc.)
    CAMERA_FOLDERS = {
        0: "Kalibrierung1a",  # Camera 1
        1: "Kalibrierung2a",  # Camera 2
        2: "Kalibrierung3a",  # Camera 3
        3: "Kalibrierung4a",  # Camera 4
    }

    # Frame range
    NUM_FRAMES = 40

    # Grid configuration
    GRID_ROWS = 7
    GRID_COLS = 6
    GRID_SPACING = 120.0  # mm (for later use)

    # Output file
    OUTPUT_PICKLE = Path("/home/user/Documents/GitHub/pyptv/pyptv/calibration_detections.pkl")
    return (
        CALIB_BASE,
        CAMERA_FOLDERS,
        GRID_COLS,
        GRID_ROWS,
        NUM_FRAMES,
        OUTPUT_PICKLE,
    )


@app.cell
def _(CALIB_BASE, CAMERA_FOLDERS, mo):
    # Verify folders exist
    folder_status = []
    all_folders_exist = True

    for cam_idx_viz, folder_name_viz in CAMERA_FOLDERS.items():
        folder_path_viz = CALIB_BASE / folder_name_viz
        exists = folder_path_viz.exists()
        if not exists:
            all_folders_exist = False
        status_icon = "✓" if exists else "❌"
        folder_status.append(f"{status_icon} Camera {cam_idx_viz + 1}: {folder_path_viz}")

    mo.md(f"""
    ### Calibration Folders

    **Base Path:** {CALIB_BASE}

    {'All folders found!' if all_folders_exist else '⚠️ Some folders missing!'}

    """ + "\n".join(folder_status))
    return


@app.cell
def _(
    CALIB_BASE,
    CAMERA_FOLDERS,
    GRID_COLS,
    GRID_ROWS,
    NUM_FRAMES,
    cv2,
    mo,
    np,
):
    """
    Detect grid points in all calibration images.

    Only keeps frames where ALL cameras successfully detected the grid
    (required for triangulation and bundle adjustment).
    """
    # Blob detector parameters
    board_params = cv2.SimpleBlobDetector_Params()
    board_params.filterByColor = False
    board_params.filterByArea = True
    board_params.minArea = 50
    board_params.filterByCircularity = True
    board_params.minCircularity = 0.7
    detector = cv2.SimpleBlobDetector_create(board_params)

    # Storage for all detections (per frame)
    frame_detections = {}  # frame_idx -> {cam_idx: corners or None}

    # Initialize structure
    for frame_idx in range(NUM_FRAMES):
        frame_detections[frame_idx] = {}
        for cam_idx in sorted(CAMERA_FOLDERS.keys()):
            frame_detections[frame_idx][cam_idx] = None

    detection_log = []
    num_cams = len(CAMERA_FOLDERS)

    # Detect grids in all cameras and frames
    for cam_idx in sorted(CAMERA_FOLDERS.keys()):
        folder_name = CAMERA_FOLDERS[cam_idx]
        folder_path = CALIB_BASE / folder_name

        _cam_success = 0
        _cam_failed = 0

        for frame_idx in range(NUM_FRAMES):
            # Find image file starting with frame number
            image_file = None
            for _f in folder_path.iterdir():
                if _f.name.startswith(f"{frame_idx:08d}_"):
                    image_file = _f
                    break

            if image_file is None:
                _cam_failed += 1
                detection_log.append({
                    'camera': cam_idx,
                    'frame': frame_idx,
                    'image_file': None,
                    'corners': None,
                    'success': False
                })
                continue

            # Read image
            img = cv2.imread(str(image_file), cv2.IMREAD_GRAYSCALE)
            if img is None:
                _cam_failed += 1
                detection_log.append({
                    'camera': cam_idx,
                    'frame': frame_idx,
                    'image_file': str(image_file),
                    'corners': None,
                    'success': False
                })
                continue

            # Detect grid
            found, corners = cv2.findCirclesGrid(
                img, (GRID_ROWS, GRID_COLS),
                flags=cv2.CALIB_CB_SYMMETRIC_GRID,
                blobDetector=detector
            )

            if found:
                corners_squeezed = np.squeeze(corners)
                _cam_success += 1
                frame_detections[frame_idx][cam_idx] = corners_squeezed
                detection_log.append({
                    'camera': cam_idx,
                    'frame': frame_idx,
                    'image_file': str(image_file),
                    'corners': corners_squeezed,
                    'success': True
                })
            else:
                _cam_failed += 1
                detection_log.append({
                    'camera': cam_idx,
                    'frame': frame_idx,
                    'image_file': str(image_file),
                    'corners': None,
                    'success': False
                })

    # Filter: Keep only frames where ALL cameras detected the grid
    synchronized_frames = []

    for frame_idx in range(NUM_FRAMES):
        cams_with_detection = sum(
            1 for cam_idx in sorted(CAMERA_FOLDERS.keys())
            if frame_detections[frame_idx][cam_idx] is not None
        )

        if cams_with_detection == num_cams:
            synchronized_frames.append(frame_idx)

    # Build final dataset with only synchronized frames
    all_detections = []
    for frame_idx in synchronized_frames:
        for cam_idx in sorted(CAMERA_FOLDERS.keys()):
            corners = frame_detections[frame_idx][cam_idx]
            # Find image file path from detection_log
            img_file = None
            for log_entry in detection_log:
                if (log_entry['camera'] == cam_idx and 
                    log_entry['frame'] == frame_idx and 
                    log_entry['success'] == True):
                    img_file = log_entry['image_file']
                    break

            all_detections.append({
                'camera': cam_idx,
                'frame': frame_idx,
                'image_file': img_file,
                'corners': corners,
                'success': True
            })

    # Per-camera detection rates
    cam_stats = {}
    for cam_idx in sorted(CAMERA_FOLDERS.keys()):
        cam_detections = sum(
            1 for entry in detection_log
            if entry['camera'] == cam_idx and entry['success'] == True
        )
        cam_stats[cam_idx] = {
            'total': NUM_FRAMES,
            'detected': cam_detections,
            'rate': cam_detections / NUM_FRAMES * 100
        }

    # Summary statistics
    total_raw_frames = NUM_FRAMES
    total_synchronized = len(synchronized_frames)
    sync_rate = total_synchronized / total_raw_frames * 100 if total_raw_frames > 0 else 0

    mo.md(f"""
    ### Detection & Synchronization Results

    | Metric | Value |
    |--------|-------|
    | **Total Raw Frames** | {total_raw_frames} |
    | **Synchronized Frames** (all {num_cams} cameras) | {total_synchronized} |
    | **Synchronization Rate** | {sync_rate:.1f}% |
    | **Total Detections Saved** | {len(all_detections)} ({num_cams} cams × {total_synchronized} frames × 42 points) |

    **Per-Camera Detection Rates:**
    """)

    for cam_idx, stats in cam_stats.items():
        mo.md(f"- **Camera {cam_idx + 1}**: {stats['detected']}/{stats['total']} frames ({stats['rate']:.1f}%)")

    mo.md(f"""
    **Synchronized Frame Numbers:** {synchronized_frames}
    """)
    return all_detections, synchronized_frames


@app.cell
def _(all_detections, pd):
    """
    Convert detections to pandas DataFrame for easy manipulation.
    """
    # Create DataFrame with metadata (corners stored as object)
    df_frames = pd.DataFrame(all_detections)

    # Add point-level data (one row per detected point)
    point_rows = []

    for _, row in df_frames.iterrows():
        if row['success'] and row['corners'] is not None:
            corners_df = row['corners']
            for point_idx, (x, y) in enumerate(corners_df):
                grid_row = point_idx // 6  # 6 columns
                grid_col = point_idx % 6
                point_rows.append({
                    'camera': row['camera'],
                    'frame': row['frame'],
                    'point_idx': point_idx,
                    'grid_row': grid_row,
                    'grid_col': grid_col,
                    'x': x,
                    'y': y,
                    'image_file': row['image_file']
                })

    df_points = pd.DataFrame(point_rows)

    # Summary statistics
    summary_stats = {
        'total_frames': len(df_frames),
        'successful_frames': df_frames['success'].sum(),
        'total_points': len(df_points),
        'points_per_successful_frame': len(df_points) / df_frames['success'].sum() if df_frames['success'].sum() > 0 else 0
    }
    return df_frames, df_points, summary_stats


@app.cell
def _(mo, summary_stats):
    """
    Display summary statistics and data preview.
    """
    mo.md(f"""
    ### Dataset Summary

    | Metric | Value |
    |--------|-------|
    | **Total Frames** | {summary_stats['total_frames']} |
    | **Successful Frames** | {summary_stats['successful_frames']} |
    | **Total Detected Points** | {summary_stats['total_points']} |
    | **Points per Successful Frame** | {summary_stats['points_per_successful_frame']:.1f} |

    ### DataFrame Preview (Frame-level)
    """)

    # Show first few rows (without corners data which is too large)
    # df_preview = df_frames[['camera', 'frame', 'image_file', 'success']].head(10)
    # mo.ui.table(df_preview)

    # mo.md("### DataFrame Preview (Point-level)")
    # mo.ui.table(df_points.head(20))
    return


@app.cell
def _():
    return


@app.cell
def _(df_frames, df_points, mo, plt):
    """
    Visualize detection results.
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes_flat = axes.flatten()

    # Plot 1: Detection success by camera
    cam_success = df_frames.groupby('camera')['success'].agg(['sum', 'count'])
    cam_success['rate'] = cam_success['sum'] / cam_success['count'] * 100

    axes_flat[0].bar(
        [f"Cam {i+1}" for i in cam_success.index],
        cam_success['rate'],
        color=['steelblue', 'coral', 'green', 'orange'][:len(cam_success)]
    )
    axes_flat[0].set_ylabel('Success Rate (%)')
    axes_flat[0].set_title('Detection Success Rate by Camera')
    axes_flat[0].set_ylim(0, 105)
    axes_flat[0].grid(True, alpha=0.3, axis='y')

    # Plot 2: Detection success by frame
    frame_success = df_frames.groupby('frame')['success'].sum()
    axes_flat[1].plot(frame_success.index, frame_success.values, 'o-', linewidth=2)
    axes_flat[1].set_xlabel('Frame Number')
    axes_flat[1].set_ylabel('Successful Detections (cameras)')
    axes_flat[1].set_title('Detection Success by Frame')
    axes_flat[1].grid(True, alpha=0.3)

    # Plot 3: Sample detected grid (first successful detection)
    sample_row = df_frames[df_frames['success']].iloc[0] if df_frames['success'].any() else None
    if sample_row is not None:
        corners_sample = sample_row['corners']
        axes_flat[2].scatter(corners_sample[:, 0], corners_sample[:, 1], c='red', s=30)

        # Draw grid connections
        corners_grid = corners_sample.reshape(7, 6, 2)
        for i in range(7):
            axes_flat[2].plot(corners_grid[i, :, 0], corners_grid[i, :, 1], 'b-', linewidth=0.5, alpha=0.5)
        for j in range(6):
            axes_flat[2].plot(corners_grid[:, j, 0], corners_grid[:, j, 1], 'b-', linewidth=0.5, alpha=0.5)

        axes_flat[2].set_title(f"Sample Grid (Cam {sample_row['camera']+1}, Frame {sample_row['frame']})")
        axes_flat[2].set_xlabel('X (pixels)')
        axes_flat[2].set_ylabel('Y (pixels)')
        axes_flat[2].invert_yaxis()
        axes_flat[2].set_aspect('equal')
    else:
        axes_flat[2].text(0.5, 0.5, 'No successful detections', ha='center', va='center')
        axes_flat[2].set_title('Sample Grid')

    # Plot 4: Point distribution (all points from all cameras/frames)
    # Just show a sample to avoid overcrowding
    sample_points = df_points[df_points['camera'] == 0].head(42)  # First camera, first frame
    if len(sample_points) > 0:
        scatter = axes_flat[3].scatter(
            sample_points['x'],
            sample_points['y'],
            c=sample_points['point_idx'],
            cmap='viridis',
            s=50
        )
        axes_flat[3].set_xlabel('X (pixels)')
        axes_flat[3].set_ylabel('Y (pixels)')
        axes_flat[3].set_title('Point Positions (Sample)')
        axes_flat[3].invert_yaxis()
        axes_flat[3].set_aspect('equal')
        plt.colorbar(scatter, ax=axes_flat[3], label='Point Index')

    plt.tight_layout()
    mo.ui.matplotlib(fig.gca())
    return


@app.cell
def _(
    CALIB_BASE,
    CAMERA_FOLDERS,
    GRID_COLS,
    GRID_ROWS,
    OUTPUT_PICKLE,
    all_detections,
    df_frames,
    df_points,
    pickle,
    synchronized_frames,
):
    """
    Save detection results to pickle file.
    """
    # Prepare metadata
    metadata = {
        'calib_base': str(CALIB_BASE),
        'camera_folders': CAMERA_FOLDERS,
        'grid_rows': GRID_ROWS,
        'grid_cols': GRID_COLS,
        'total_raw_frames': 40,
        'synchronized_frames': synchronized_frames,
        'num_synchronized': len(synchronized_frames),
        'total_frames': len(df_frames),
        'successful_frames': int(df_frames['success'].sum()),
        'total_points': len(df_points)
    }

    # Save to pickle
    save_data = {
        'metadata': metadata,
        'frame_detections': df_frames,
        'point_detections': df_points,
        'all_detections': all_detections,
        'synchronized_frame_list': synchronized_frames
    }

    OUTPUT_PICKLE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PICKLE, 'wb') as _f:
        pickle.dump(save_data, _f)

    return


@app.cell
def _(OUTPUT_PICKLE, mo):
    mo.md(f"""
    ### ✅ Data Saved Successfully!

    **Output File:** `{OUTPUT_PICKLE}`

    **Contents:**
    - `metadata`: Configuration and summary statistics
    - `frame_detections`: DataFrame with one row per frame (42 points each)
    - `point_detections`: DataFrame with one row per detected point
    - `all_detections`: Raw detection list
    - `synchronized_frame_list`: List of frame numbers where all 4 cameras detected the grid

    **File Size:** {OUTPUT_PICKLE.stat().st_size / 1024 / 1024:.2f} MB

    ---

    ### Next Steps

    You can now load this data in other notebooks:
    """)
    return


@app.cell
def _(OUTPUT_PICKLE, df_points, mo, pickle):
    print(OUTPUT_PICKLE)
    with open(OUTPUT_PICKLE, 'rb') as f:
        data = pickle.load(f)

    _df_frames = data['frame_detections']
    _df_points = data['point_detections']
    _sync_frames = data['synchronized_frame_list']
    _metadata = data['metadata']

    print(f"Synchronized frames: {_sync_frames}")
    print(f"Total points: {len(df_points)}")


    mo.ui.table(_df_frames)
    return


@app.cell
def _():
    return


@app.cell
def _():
    # """
    # Create a pivot table view of detection success.
    # """
    # # Pivot table: cameras as rows, frames as columns
    # pivot_success = df_frames.pivot_table(
    #     index='camera',
    #     columns='frame',
    #     values='success',
    #     aggfunc='first'
    # )

    # mo.md("### Detection Success Matrix (✓ = detected)")

    # # Convert to display format
    # display_df = pivot_success.apply(lambda x: '✓' if x else '✗')
    # mo.ui.table(display_df)
    return


@app.cell
def _(df_points, mo):
    """
    Analyze point positions across all detections.
    """
    # Calculate mean position for each grid point (across all frames/cameras)
    mean_positions = df_points.groupby(['camera', 'grid_row', 'grid_col'])[['x', 'y']].mean().reset_index()

    # Calculate standard deviation
    std_positions = df_points.groupby(['camera', 'grid_row', 'grid_col'])[['x', 'y']].std().reset_index()

    mo.md("""
    ### Mean Point Positions by Camera

    Average pixel coordinates for each grid point across all synchronized frames.
    """)

    mo.ui.table(mean_positions)
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
