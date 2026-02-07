import marimo

__generated_with = "0.19.9"
app = marimo.App(width="medium", auto_download=["ipynb"])


@app.cell
def _():
    import marimo as mo
    import matplotlib.pyplot as plt
    import numpy as np
    from wigglystuff import ChartPuck
    import sys

    return ChartPuck, mo, plt, sys


@app.cell
def _(mo):
    mo.md(f"""
    ## Interactive Manual Orientation with `pyptv`

    This notebook demonstrates how to load parameters from a YAML file, display calibration images, and allow manual adjustment of orientation points (pucks).

    ### Workflow:
    1.  **Load Parameters**: Using `pyptv.parameter_manager.ParameterManager` to read from `tests/test_cavity/parameters_Run1.yaml`.
    2.  **Display Images**: Loading calibration images specified in `cal_ori` parameters.
    3.  **Interactive Adjustment**: Using `wigglystuff.ChartPuck` to create draggable points for the 4 manual orientation markers on each image.
    4.  **Save Changes**: Updating the in-memory parameters and saving back to the YAML file.
    """)
    return


@app.cell
def _(sys):
    from pathlib import Path

    # Add the parent directory to sys.path if not present to import pyptv package
    parent_dir = str(Path(".").absolute())
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

    from pyptv.parameter_manager import ParameterManager

    # Path to the YAML file
    yaml_path = Path("tests/test_cavity/parameters_Run1.yaml")

    # Check if file exists
    if yaml_path.exists():
        pm = ParameterManager()
        pm.from_yaml(yaml_path)
        print("YAML loaded successfully.")

        # Check keys
        print("Keys in parameters:", pm.parameters.keys())

        # Look for manual orientation parameters
        if "man_ori" in pm.parameters:
            print("\nManual Orientation Parameters (man_ori):")
            print(pm.parameters["man_ori"])

        if "man_ori_coordinates" in pm.parameters:
            print("\nManual Orientation Coordinates (man_ori_coordinates):")
            print(pm.parameters["man_ori_coordinates"])
    else:
        print(f"File not found: {yaml_path}")
    return Path, pm


@app.cell
def _():
    # Deleted cell
    return


@app.cell
def _():
    # Deleted cell
    return


@app.cell
def _():
    # Deleted cell
    return


@app.cell
def _():
    # Deleted cell
    return


@app.cell
def _():
    # Deleted cell
    return


@app.cell
def _(ChartPuck, Path, mo, plt, pm):
    from imageio.v3 import imread

    # Assuming pm is already initialized and populated
    cal_images = pm.parameters["cal_ori"]["img_cal_name"]
    coords = pm.parameters.get("man_ori_coordinates", {})
    num_cams = len(cal_images)

    calibration_widgets = {}

    # Base directory for relative paths (should be tests/test_cavity based on previous context)
    # Or I can use pm.yaml_path.parent if available, but pm doesn't store yaml_path by default unless modified
    # Let's use the path relative to where the notebook is or where yaml was loaded
    base_dir = Path("tests/test_cavity")

    for i, img_name in enumerate(cal_images):
        cam_key = f"camera_{i}"

        # Construct full path
        img_path = base_dir / img_name

        if not img_path.exists():
            print(f"Warning: Image not found: {img_path}")
            continue

        image = imread(img_path)

        # Get initial coordinates
        cam_coords = coords.get(cam_key, {})
        x_init = []
        y_init = []
        for pt_idx in range(1, 5):  # 4 points
            pt_key = f"point_{pt_idx}"
            pt = cam_coords.get(pt_key, {"x": 100, "y": 100})  # Default if missing
            x_init.append(pt["x"])
            y_init.append(pt["y"])

        # Create figure
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.imshow(image, cmap="gray")
        ax.set_title(f"Camera {i + 1} - {img_name}")
        ax.axis("off")

        # Create pucks
        puck = ChartPuck(
            fig,
            x=x_init,
            y=y_init,
            puck_color="#2196f3",
            puck_radius=10,
            puck_alpha=0.5,
        )
        plt.close(fig)  # Prevent duplicate display

        # Create widget
        widget = mo.ui.anywidget(puck)
        calibration_widgets[f"Camera {i + 1}"] = widget

    # Display tabs
    tabs = mo.ui.tabs(calibration_widgets)
    save_btn = mo.ui.run_button(label="Save Parameters to YAML")
    mo.vstack([tabs, save_btn])
    return calibration_widgets, num_cams, save_btn


@app.cell
def _():
    # Deleted cell
    return


@app.cell
def _(calibration_widgets, num_cams, pm, save_btn):
    # This cell reacts to the save button click
    if save_btn.value:
        updated_coords = {}
        for idx in range(num_cams):
            c_key = f"camera_{idx}"
            widget_key = f"Camera {idx + 1}"
            if widget_key in calibration_widgets:
                w = calibration_widgets[widget_key]
                # Accessing .x and .y directly assumes they are synced traits
                # For AnyWidget, accessing attributes returns current synced value
                x_vals = w.x
                y_vals = w.y

                updated_coords[c_key] = {}
                for p_idx in range(4):
                    if p_idx < len(x_vals) and p_idx < len(y_vals):
                        updated_coords[c_key][f"point_{p_idx + 1}"] = {
                            "x": float(x_vals[p_idx]),
                            "y": float(y_vals[p_idx]),
                        }

        # Update parameter manager
        if updated_coords:
            pm.parameters["man_ori_coordinates"] = updated_coords

            # Save to YAML
            pm.to_yaml(pm.yaml_path)
            print(
                f"✅ Successfully saved manual orientation coordinates to {pm.yaml_path}"
            )
        else:
            print("⚠️ No coordinates found to save.")
    return


if __name__ == "__main__":
    app.run()
