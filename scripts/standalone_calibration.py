#!/usr/bin/env python3
"""Standalone OpenPTV calibration runner.

Purpose
- Load PyPTV/OpenPTV parameters from a YAML file.
- Accept externally-generated correspondences:
    - 3D calibration points XYZ (metric units, shape: (N, 3))
    - 2D detected image points per camera xy (pixel units, shape: (C, N, 2))
  where point index i in XY corresponds to point index i in XYZ.
- Run calibration per camera:
    1) Optional external (6DOF) calibration using 4 point pairs (to get a robust initial guess)
    2) Full calibration (bundle-like refinement) using OpenPTV's `full_calibration`
- Write OpenPTV calibration files (`.ori` + `.addpar`) for each camera.

This script is intended for closed-loop testing (ground truth -> synthetic detections -> calibration).

Input format (.npz)
- Required:
    - `xyz` or `XYZ`: float array (N, 3)
    - One of:
        - `xy`: float array (C, N, 2)
        - `xy_cam0`, `xy_cam1`, ... arrays each (N, 2)
- Optional:
    - `pnr`: int array (N,) mapping each provided 2D point to an index in XYZ.
      If absent, assumes pnr = [0..N-1].

Examples
- Run using orient flags from YAML and initialize with first four points:
    python scripts/standalone_calibration.py /path/to/parameters_run.yaml points.npz \
      --init-external first4 --flags-from-yaml --write

- Run without external initialization (requires decent initial .ori/.addpar):
    python scripts/standalone_calibration.py params.yaml points.npz --flags cc xh yh k1 k2 --write
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np

# Allow running from a repo checkout without installation
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from pyptv.standalone_calibration import (
    NAMES as _NAMES,
    get_flags_from_yaml as _get_flags_from_yaml,
    load_parameter_manager as _load_pm,
    load_points_npz as _load_points_npz,
    run_standalone_calibration,
)


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("yaml", type=Path, help="Path to parameters_*.yaml")
    p.add_argument("npz", type=Path, help="Path to .npz containing xyz and xy arrays")

    flags_group = p.add_mutually_exclusive_group()
    flags_group.add_argument(
        "--flags-from-yaml",
        action="store_true",
        help="Use 'orient' section flags from YAML (cc/xh/...)",
    )
    flags_group.add_argument(
        "--flags",
        nargs="+",
        default=None,
        help=f"Explicit flags to optimize. Allowed: {', '.join(_NAMES)}",
    )

    p.add_argument(
        "--init-external",
        choices=["first4"],
        default="first4",
        help="How to choose 4 points for external_calibration init (default: first4). Use --no-init-external to skip.",
    )
    p.add_argument(
        "--no-init-external",
        action="store_true",
        help="Skip external_calibration init step (requires decent initial .ori/.addpar).",
    )

    p.add_argument(
        "--write",
        action="store_true",
        help="Write output .ori/.addpar to paths in cal_ori.img_ori",
    )

    return p.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    ns = _parse_args(argv or sys.argv[1:])

    yaml_path: Path = ns.yaml.resolve()
    npz_path: Path = ns.npz.resolve()

    if not yaml_path.exists():
        raise FileNotFoundError(yaml_path)
    if not npz_path.exists():
        raise FileNotFoundError(npz_path)

    pm = _load_pm(yaml_path)
    num_cams = int(pm.num_cams)

    xyz, xy, pnr = _load_points_npz(npz_path, num_cams=num_cams)

    if ns.flags_from_yaml:
        flags = _get_flags_from_yaml(pm)
    elif ns.flags is not None:
        unknown = [f for f in ns.flags if f not in _NAMES]
        if unknown:
            raise ValueError(f"Unknown flags: {unknown}. Allowed: {_NAMES}")
        flags = list(ns.flags)
    else:
        # Default: mimic GUI behavior (YAML-driven) if present, else optimize nothing.
        flags = _get_flags_from_yaml(pm)

    init_external = None if ns.no_init_external else ns.init_external

    run_standalone_calibration(
        yaml_path,
        xyz,
        xy,
        pnr,
        flags=flags,
        init_external=init_external,
        write=bool(ns.write),
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
