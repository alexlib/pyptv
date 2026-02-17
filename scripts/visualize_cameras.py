#!/usr/bin/env python3
"""Visualize camera poses from .ori/.addpar files.

Usage:
  python scripts/visualize_cameras.py path/to/parameters.yaml
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

from optv.calibration import Calibration

from pyptv.parameter_manager import ParameterManager


def _load_calibrations(yaml_path: Path) -> list[Calibration]:
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


def _set_axes_equal(ax, points: np.ndarray) -> None:
    mins = points.min(axis=0)
    maxs = points.max(axis=0)
    centers = (mins + maxs) * 0.5
    max_range = (maxs - mins).max() * 0.5

    ax.set_xlim(centers[0] - max_range, centers[0] + max_range)
    ax.set_ylim(centers[1] - max_range, centers[1] + max_range)
    ax.set_zlim(centers[2] - max_range, centers[2] + max_range)


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("yaml", type=Path, help="Path to parameters YAML")
    p.add_argument("--axis-length", type=float, default=50.0, help="Axis length in world units")
    p.add_argument("--save", type=Path, default=None, help="Save figure to file")
    p.add_argument("--no-show", action="store_true", help="Do not display the figure")
    return p.parse_args()


def main() -> int:
    args = _parse_args()
    yaml_path = args.yaml.resolve()

    calibs = _load_calibrations(yaml_path)

    fig = plt.figure(figsize=(9, 7))
    ax = fig.add_subplot(111, projection="3d")

    # World axes at origin
    axis_len = float(args.axis_length)
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
    _set_axes_equal(ax, points)

    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.set_title("Camera Poses from .ori Files")

    if args.save is not None:
        fig.savefig(args.save, dpi=200, bbox_inches="tight")

    if not args.no_show:
        plt.show()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
