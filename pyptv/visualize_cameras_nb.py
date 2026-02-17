import marimo

__generated_with = "0.19.9"
app = marimo.App()


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Visualize Camera Poses
    Load camera poses from `.ori/.addpar` files (via the YAML) and plot world + camera axes.
    """)
    return


@app.cell
def _():
    from pathlib import Path

    import numpy as np
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

    from optv.calibration import Calibration
    from pyptv.parameter_manager import ParameterManager

    return Calibration, ParameterManager, Path, np, plt


@app.cell
def _(mo):
    yaml_path_ui = mo.ui.text(
        value="/home/user/Dropbox/3DPTV_Illmenau/Multiview-Calibration/parameters_Run3_1.yaml",
        label="YAML configuration path",
        full_width=True,
    )
    mo.md(f"""
    ### Configuration
    Select the path to the parameter YAML file:
    {yaml_path_ui}
    """)
    return


@app.cell
def _(Path):
    # TODO: set your YAML path
    yaml_path = Path("/home/user/Dropbox/3DPTV_Illmenau/Multiview-Calibration/parameters_Run3_1.yaml").resolve()
    return (yaml_path,)


@app.cell
def _(Calibration, ParameterManager, Path, np):
    def load_calibrations(yaml_path: Path) -> list[Calibration]:
        pm = ParameterManager()
        pm.from_yaml(yaml_path)

        cal_ori = pm.get_parameter("cal_ori")
        if not isinstance(cal_ori, dict):
            raise KeyError("Missing cal_ori section in YAML")

        img_ori = cal_ori.get("img_ori")
        if not img_ori:
            raise ValueError("cal_ori.img_ori is empty")

        base_dir = yaml_path.parent
        calibs = []
        for ori in img_ori:
            ori_path = Path(ori)
            if not ori_path.is_absolute():
                ori_path = (base_dir / ori_path).resolve()
            addpar_path = Path(str(ori_path).replace(".ori", ".addpar"))
            cal = Calibration()
            cal.from_file(str(ori_path), str(addpar_path))
            calibs.append(cal)

        return calibs


    def set_axes_equal(ax, points: np.ndarray) -> None:
        mins = points.min(axis=0)
        maxs = points.max(axis=0)
        centers = (mins + maxs) * 0.5
        max_range = (maxs - mins).max() * 0.5

        ax.set_xlim(centers[0] - max_range, centers[0] + max_range)
        ax.set_ylim(centers[1] - max_range, centers[1] + max_range)
        ax.set_zlim(centers[2] - max_range, centers[2] + max_range)

    return load_calibrations, set_axes_equal


@app.cell
def _(load_calibrations, mo, np, plt, set_axes_equal, yaml_path):
    axis_len = 50.0  # world units
    calibs = load_calibrations(yaml_path)

    fig = plt.figure(figsize=(9, 7))
    ax = fig.add_subplot(111, projection="3d")

    # World axes at origin
    origin = np.zeros(3)
    ax.scatter([0], [0], [0], color="k", s=30)
    ax.quiver(*origin, axis_len, 0, 0, color="r", linewidth=1.5)
    ax.quiver(*origin, 0, axis_len, 0, color="g", linewidth=1.5)
    ax.quiver(*origin, 0, 0, axis_len, color="b", linewidth=1.5)

    points = [origin]

    for idx, cal in enumerate(calibs):
        pos = np.asarray(cal.get_pos(), dtype=float)
        rot = np.asarray(cal.get_rotation_matrix(), dtype=float)

        # Camera axes in world coordinates
        cam_axes = rot.T

        ax.scatter([pos[0]], [pos[1]], [pos[2]], color="k", s=20)
        ax.text(pos[0], pos[1], pos[2], f"Cam {idx + 1}")

        ax.quiver(*pos, *(cam_axes[:, 0] * axis_len), color="r", linewidth=1.0)
        ax.quiver(*pos, *(cam_axes[:, 1] * axis_len), color="g", linewidth=1.0)
        ax.quiver(*pos, *(cam_axes[:, 2] * axis_len), color="b", linewidth=1.0)

        points.append(pos)

    points = np.vstack(points)
    set_axes_equal(ax, points)

    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.set_title("Camera Poses from .ori Files")
    # plt.show()
    mo.mpl.interactive(plt.gca())
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
