import marimo

__generated_with = "0.20.2"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo

    mo.md(r"""
    # Epipolar Line Visualization Tool

    Interactive epipolar line verification for multi-camera calibration.

    **Features:**
    - Click on any point in any camera view
    - See epipolar lines projected to all other cameras
    - Verify calibration quality visually
    - Measure epipolar distance errors

    **Usage:**
    1. Load calibration files (`.ori` + `.addpar`)
    2. Load calibration images
    3. Right-click on any detected grid point
    4. Epipolar lines appear in other camera views
    """)
    return (mo,)


@app.cell
def _():
    import numpy as np
    import cv2
    import matplotlib.pyplot as plt
    from pathlib import Path
    from optv.calibration import Calibration
    from optv.epipolar import epipolar_curve
    from optv.parameters import ControlParams, MultimediaPar
    from pyptv.parameter_manager import ParameterManager
    from pyptv import ptv
    import imageio.v3 as iio
    from typing import Dict, List, Optional, Tuple

    return (
        Calibration,
        ControlParams,
        Dict,
        List,
        MultimediaPar,
        Optional,
        ParameterManager,
        Path,
        Tuple,
        cv2,
        epipolar_curve,
        iio,
        imageio,
        mo,
        np,
        plt,
        ptv,
    )


@app.cell
def _(mo) -> Tuple:
    yaml_path_str = mo.ui.text(
        value='/home/user/Downloads/Illmenau/pyPTV_folder/parameters_Run4.yaml',
        label='YAML Parameters File',
        full_width=True
    )
    yaml_path_str
    return (yaml_path_str,)


@app.cell
def _(Calibration, ControlParams, MultimediaPar, mo, np, ParameterManager, Path, ptv, yaml_path_str) -> Tuple:
    yaml_path = Path(yaml_path_str.value).expanduser().resolve()

    if not yaml_path.exists():
        mo.md(f"**❌ YAML file not found:** {yaml_path}")
        return None, None, [], [], {}, None

    pm = ParameterManager()
    pm.from_yaml(yaml_path)

    params = pm.parameters
    num_cams = int(params.get("num_cams", pm.num_cams or 0) or 0)
    ptv_params = params.get('ptv', {})

    cpar = ptv._populate_cpar(ptv_params, num_cams)
    mmp = MultimediaPar(n1=1.0, n2=[1.0], n3=1.0, d=[0.0])

    base_path = yaml_path.parent
    cals = []
    images = []
    images_cv2 = []
    img_names = ptv_params.get('img_name', [])
    cal_ori = pm.parameters.get('cal_ori', {})
    ori_names = cal_ori.get('img_ori', [])

    load_status = []

    for i in range(num_cams):
        # Load image
        img_path = img_names[i] if i < len(img_names) else None
        if img_path:
            if not Path(img_path).is_absolute():
                img_path = base_path / img_path
            try:
                img = iio.imread(str(img_path))
                images.append(img)
                images_cv2.append(cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE))
                load_status.append(f"✓ Cam {i + 1}: Image loaded")
            except Exception as e:
                images.append(np.zeros((ptv_params.get('imy', 1024), ptv_params.get('imx', 1024)), dtype=np.uint8))
                images_cv2.append(np.zeros((ptv_params.get('imy', 1024), ptv_params.get('imx', 1024)), dtype=np.uint8))
                load_status.append(f"⚠ Cam {i + 1}: Failed to load image - {e}")
        else:
            images.append(np.zeros((ptv_params.get('imy', 1024), ptv_params.get('imx', 1024)), dtype=np.uint8))
            images_cv2.append(np.zeros((ptv_params.get('imy', 1024), ptv_params.get('imx', 1024)), dtype=np.uint8))
            load_status.append(f"⚠ Cam {i + 1}: No image path")

        # Load calibration
        cal = Calibration()
        ori_path = ori_names[i] if i < len(ori_names) else None

        if ori_path:
            ori_file_path = base_path / ori_path
            addpar_file_path = Path(str(ori_file_path).replace('.ori', '') + '.addpar')
            if not addpar_file_path.exists():
                addpar_file_path = Path(str(ori_file_path).replace('.tif.ori', '') + '.addpar')

            if ori_file_path.exists() and addpar_file_path.exists():
                cal.from_file(str(ori_file_path), str(addpar_file_path))
                load_status.append(f"✓ Cam {i + 1}: Calibration loaded")
            else:
                load_status.append(f"⚠ Cam {i + 1}: Missing calibration files")
        else:
            load_status.append(f"⚠ Cam {i + 1}: No calibration path")

        cals.append(cal)

    mo.md(f"""
    ### Files Loaded

    **YAML:** `{yaml_path.name}`

    **Status:**
    """ + "\n".join(load_status))

    return base_path, cals, cpar, images, images_cv2, mmp


@app.cell
def _(cv2, mo, np) -> Tuple:
    """Detect grid points for interactive visualization."""
    board_params = cv2.SimpleBlobDetector_Params()
    board_params.filterByColor = False
    board_params.filterByArea = True
    board_params.minArea = 50
    board_params.filterByCircularity = True
    board_params.minCircularity = 0.7
    detector = cv2.SimpleBlobDetector_create(board_params)

    mo.md("""
    ### Grid Detection Parameters

    | Parameter | Value |
    |-----------|-------|
    | **Min Area** | 50 pixels² |
    | **Min Circularity** | 0.7 |
    | **Filter by Color** | False |
    """)

    return (board_params, detector)


@app.cell
def _(
    cals,
    cpar,
    cv2,
    detector,
    images,
    images_cv2,
    mo,
    np,
    plt,
) -> Tuple:
    """
    Detect and display grid points with interactive epipolar lines.

    **Instructions:**
    - **Right-click** on any red grid point to draw epipolar lines
    - Epipolar lines show where that 3D point should appear in other cameras
    - Good calibration = epipolar lines pass through corresponding points
    """
    num_cams = len(cals)
    grid_rows = 7
    grid_cols = 6

    all_corners = []
    targets_metric = []

    for cam_idx, (img_cv2, cal) in enumerate(zip(images_cv2, cals)):
        found, corners = cv2.findCirclesGrid(
            img_cv2, (grid_rows, grid_cols),
            flags=cv2.CALIB_CB_SYMMETRIC_GRID,
            blobDetector=detector
        )

        if found:
            corners_squeezed = np.squeeze(corners)
            all_corners.append(corners_squeezed)

            # Convert to metric
            corners_metric = []
            for pt in corners_squeezed:
                from optv.transforms import pixel_to_metric
                x_mm, y_mm = pixel_to_metric(pt[0], pt[1], cpar)
                corners_metric.append([x_mm, y_mm])
            targets_metric.append(np.array(corners_metric))
        else:
            all_corners.append(None)
            targets_metric.append(None)

    # Create figure with 2x2 layout
    fig, axes = plt.subplots(2, 2, figsize=(16, 14))
    axes_flat = axes.flatten()

    colors = ['red', 'green', 'blue', 'orange']

    for cam_idx in range(num_cams):
        ax = axes_flat[cam_idx]
        ax.imshow(images[cam_idx], cmap='gray')
        ax.set_title(f"Camera {cam_idx + 1}")
        ax.set_xlabel("X (pixels)")
        ax.set_ylabel("Y (pixels)")

        corners = all_corners[cam_idx]
        if corners is not None:
            ax.scatter(corners[:, 0], corners[:, 1], c='red', s=50, marker='o', linewidths=2, edgecolors='white')

            # Draw grid connections
            corners_grid = corners.reshape(grid_rows, grid_cols, 2)
            for i in range(grid_rows):
                ax.plot(corners_grid[i, :, 0], corners_grid[i, :, 1], 'b-', lw=0.8, alpha=0.5)
            for j in range(grid_cols):
                ax.plot(corners_grid[:, j, 0], corners_grid[:, j, 1], 'b-', lw=0.8, alpha=0.5)

        ax.set_xlim(0, images[cam_idx].shape[1])
        ax.set_ylim(images[cam_idx].shape[0], 0)
        ax.set_aspect('equal')

    plt.tight_layout()

    # Store for interactive use
    epipolar_data = {
        'fig': fig,
        'axes': axes_flat,
        'all_corners': all_corners,
        'targets_metric': targets_metric,
        'colors': colors
    }

    mo.md("""
    ### Interactive Epipolar Visualization

    **Right-click** on any red grid point to see epipolar lines in other cameras.

    - Red points = detected grid corners
    - Blue lines = grid connections
    - **After clicking:** Colored curves = epipolar lines
    """)

    return epipolar_data


@app.cell
def _(
    cals,
    cpar,
    epipolar_data,
    images,
    mo,
    mmp,
    np,
    plt,
    epipolar_curve,
) -> None:
    """Create interactive click handler for epipolar lines."""
    fig = epipolar_data['fig']
    axes = epipolar_data['axes']
    all_corners = epipolar_data['all_corners']
    colors = epipolar_data['colors']
    num_cams = len(cals)

    # Store line objects for cleanup
    line_objects = []

    def on_click(event):
        if event.button != 3:  # Right-click only
            return

        ax = event.inaxes
        if ax is None:
            return

        # Find which camera was clicked
        clicked_cam = None
        for i, axis in enumerate(axes):
            if axis == ax:
                clicked_cam = i
                break

        if clicked_cam is None:
            return

        x, y = event.xdata, event.ydata

        # Remove previous epipolar lines
        for line_obj in line_objects:
            line_obj.remove()
        line_objects.clear()

        # Draw epipolar lines to other cameras
        for other_cam in range(num_cams):
            if other_cam == clicked_cam:
                continue

            try:
                # Generate epipolar curve
                num_points = 100
                epipolar_pts = epipolar_curve(
                    np.array([x, y]),
                    cals[clicked_cam],
                    cals[other_cam],
                    num_points,
                    cpar,
                    mmp
                )

                if len(epipolar_pts) > 1:
                    line, = axes[other_cam].plot(
                        epipolar_pts[:, 0], epipolar_pts[:, 1],
                        color=colors[clicked_cam],
                        linewidth=2,
                        linestyle='--',
                        alpha=0.8,
                        label=f'Epi. from Cam {clicked_cam + 1}'
                    )
                    line_objects.append(line)

                    # Add arrow to show direction
                    mid_idx = len(epipolar_pts) // 2
                    if mid_idx > 0:
                        dx = epipolar_pts[mid_idx, 0] - epipolar_pts[mid_idx - 1, 0]
                        dy = epipolar_pts[mid_idx, 1] - epipolar_pts[mid_idx - 1, 1]
                        axes[other_cam].annotate(
                            '',
                            xy=(epipolar_pts[mid_idx, 0], epipolar_pts[mid_idx, 1]),
                            xytext=(epipolar_pts[mid_idx - 1, 0], epipolar_pts[mid_idx - 1, 1]),
                            arrowprops=dict(arrowstyle='->', color=colors[clicked_cam], lw=2)
                        )

            except Exception as e:
                print(f"Error drawing epipolar line to Cam {other_cam + 1}: {e}")

        # Add legend to first subplot
        if line_objects:
            axes[0].legend(loc='upper right', fontsize=8)

        fig.canvas.draw_idle()
        print(f"Clicked: Camera {clicked_cam + 1}, Point: ({x:.1f}, {y:.1f})")

    # Connect the event
    cid = fig.canvas.mpl_connect('button_press_event', on_click)

    mo.md("""
    ### Epipolar Line Interaction

    - **Right-click** on any point to draw epipolar lines
    - Lines show where the 3D point projects in other cameras
    - **Good calibration:** Epipolar lines pass through corresponding grid points
    - **Poor calibration:** Lines miss the corresponding points
    """)

    mo.pyplot(fig)
    return


@app.cell
def _(
    cals,
    cpar,
    epipolar_data,
    mo,
    mmp,
    np,
) -> None:
    """
    Calculate and display epipolar distance errors for quality assessment.
    """
    all_corners = epipolar_data['all_corners']
    targets_metric = epipolar_data['targets_metric']
    num_cams = len(cals)

    if not all(all_corners):
        mo.md("⚠️ Some cameras don't have detected grids. Epipolar errors calculated only for valid cameras.")

    epipolar_errors = []

    for cam_idx in range(num_cams):
        if all_corners[cam_idx] is None:
            continue

        corners = all_corners[cam_idx]
        corners_metric = targets_metric[cam_idx]

        for pt_idx, (px, py) in enumerate(corners):
            pt_metric = corners_metric[pt_idx]

            for other_cam in range(num_cams):
                if other_cam == cam_idx or all_corners[other_cam] is None:
                    continue

                try:
                    # Generate epipolar curve
                    num_points = 50
                    epipolar_pts = epipolar_curve(
                        np.array([px, py]),
                        cals[cam_idx],
                        cals[other_cam],
                        num_points,
                        cpar,
                        mmp
                    )

                    # Find closest point on epipolar line to actual correspondence
                    other_corner = all_corners[other_cam][pt_idx]

                    # Calculate distance from point to epipolar line
                    min_dist = float('inf')
                    for ept in epipolar_pts:
                        dist = np.linalg.norm(ept - other_corner)
                        if dist < min_dist:
                            min_dist = dist

                    epipolar_errors.append(min_dist)

                except Exception as e:
                    pass

    if epipolar_errors:
        epipolar_errors = np.array(epipolar_errors)
        mean_error = np.mean(epipolar_errors)
        std_error = np.std(epipolar_errors)
        max_error = np.max(epipolar_errors)
        median_error = np.median(epipolar_errors)

        mo.md(f"""
        ### Epipolar Distance Error Statistics

        | Metric | Value |
        |--------|-------|
        | **Mean Error** | {mean_error:.3f} pixels |
        | **Median Error** | {median_error:.3f} pixels |
        | **Std Deviation** | {std_error:.3f} pixels |
        | **Max Error** | {max_error:.3f} pixels |
        | **Samples** | {len(epipolar_errors)} point pairs |

        **Quality Assessment:**
        - **< 1 pixel:** Excellent calibration
        - **1-3 pixels:** Good calibration
        - **3-5 pixels:** Acceptable
        - **> 5 pixels:** Consider recalibration
        """)

        # Error distribution
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.hist(epipolar_errors, bins=30, color='steelblue', edgecolor='black', alpha=0.7)
        ax.axvline(mean_error, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_error:.2f}px')
        ax.axvline(median_error, color='green', linestyle='--', linewidth=2, label=f'Median: {median_error:.2f}px')
        ax.set_xlabel('Epipolar Distance Error (pixels)')
        ax.set_ylabel('Frequency')
        ax.set_title('Distribution of Epipolar Distance Errors')
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        mo.pyplot(fig)
    else:
        mo.md("⚠️ Could not calculate epipolar errors. Check that all cameras have valid detections.")
    return


@app.cell
def _(mo) -> None:
    mo.md("""
    ## Tips for Epipolar Verification

    ### What are Epipolar Lines?

    For a point seen in camera A, the **epipolar line** in camera B shows where that same 3D point must appear.
    This is a fundamental geometric constraint in multi-view systems.

    ### How to Interpret

    1. **Click on a grid point** in any camera view
    2. **Observe the epipolar lines** in other cameras:
       - Do they pass through the corresponding grid point? → **Good calibration**
       - Do they miss significantly? → **Calibration needs refinement**

    3. **Check multiple points** across the image:
       - Center points usually have smaller errors
       - Edge/corner points reveal distortion issues

    ### Common Issues

    | Symptom | Likely Cause |
    |---------|--------------|
    | Systematic offset | Exterior orientation error |
    | Rotating lines | Angular misalignment (ω, φ, κ) |
    | Curved instead of straight | Distortion parameters (k1, k2, p1, p2) |
    | Large errors everywhere | Wrong focal length or principal point |

    ### Next Steps

    - If epipolar errors are > 3 pixels, consider running bundle adjustment
    - Use the main calibration notebook to refine parameters
    - Re-export and test again
    """)
    return


if __name__ == "__main__":
    app.run()
