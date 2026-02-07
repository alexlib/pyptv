import marimo

__generated_with = "0.19.9"
app = marimo.App(width="medium", auto_download=["ipynb"])


@app.cell
def _():
    import marimo as mo
    import matplotlib.pyplot as plt
    import numpy as np
    from wigglystuff import ChartPuck
    import sys, os

    return ChartPuck, mo, plt, sys


@app.cell
def _(mo):
    mo.md(f"""
    ## Reading parameters from YAML using `pyptv`

    This example demonstrates how to use `pyptv.parameter_manager.ParameterManager` to load parameters from a YAML file and extract manual orientation data.

    The relevant parameters are:
    - `man_ori`: Contains orientation parameters (e.g., point IDs).
    - `man_ori_coordinates`: Contains the manual orientation coordinates (x, y) for each camera.
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
    return (pm,)


@app.cell
def _():
    from imageio.v3 import imread

    image = imread("tests/test_cavity/cal/cam1.tif")
    return (image,)


@app.cell
def _(ChartPuck, image, plt):
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.imshow(image, cmap="gray")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_title("Drag any puck - closest one will move")
    # ax.grid(True, alpha=0.3)

    multi_puck = ChartPuck(
        fig,
        x=[
            image.shape[0] / 2 - 50,
            image.shape[0] / 2 - 15,
            image.shape[0] / 2 + 15,
            image.shape[0] / 2 + 50,
        ],
        y=[
            image.shape[1] / 2,
            image.shape[1] / 2,
            image.shape[1] / 2,
            image.shape[1] / 2,
        ],
        puck_color="#2196f3",
        puck_radius=11,
        puck_alpha=0.2,
    )
    plt.close(fig)
    return (multi_puck,)


@app.cell
def _(mo, multi_puck):
    multi_widget = mo.ui.anywidget(multi_puck)
    return (multi_widget,)


@app.cell
def _(multi_widget):
    multi_widget
    return


@app.cell
def _(mo, multi_widget):
    positions = [
        f"Puck {i + 1}: ({x:.1f}, {y:.1f})"
        for i, (x, y) in enumerate(zip(multi_widget.x, multi_widget.y))
    ]
    mo.callout("\n".join(positions))
    return


@app.cell
def _(pm):
    # Inspect cal_ori to find calibration image names
    if 'cal_ori' in pm.parameters:
        print("\nCalibration Orientation Parameters (cal_ori):")
        print(pm.parameters['cal_ori'])
    
    # Inspect sequence to see if it helps with paths
    if 'sequence' in pm.parameters:
        print("\nSequence Parameters:")
        print(pm.parameters['sequence'])
    return


if __name__ == "__main__":
    app.run()
