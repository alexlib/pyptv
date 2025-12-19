#!/usr/bin/env python3
"""Standalone dumbbell calibration runner (headless).

This script runs dumbbell calibration using existing target files.

Prerequisites
- You must already have per-frame target files on disk in the format written by
  `pyptv.ptv.write_targets()` (e.g. `cam1.0001_targets`).
- For each frame used, each camera must contain exactly 2 targets (the dumbbell endpoints).

Typical workflow
1) Run detection on a dumbbell sequence and write target files.
2) Run this script to optimize camera extrinsics.

Example
  ./.venv/bin/python scripts/standalone_dumbbell_calibration.py \
      tests/test_cavity/parameters_Run1.yaml --maxiter 500 --write

Note
- This optimizes only camera position+angles.
- Intrinsics/distortions are left as-is.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from pyptv.standalone_dumbbell_calibration import run_dumbbell_calibration


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("yaml", type=Path, help="Path to parameters_*.yaml")
    p.add_argument("--step", type=int, default=None, help="Frame step (default: dumbbell.dumbbell_step or 1)")
    p.add_argument("--fixed-cams", nargs="*", type=int, default=[], help="0-based camera indices to keep fixed")
    p.add_argument("--maxiter", type=int, default=1000, help="SciPy minimize maxiter")
    p.add_argument("--write", action="store_true", help="Write updated .ori/.addpar")
    p.add_argument("--no-write", action="store_true", help="Do not write outputs")
    return p.parse_args()


def main() -> int:
    ns = _parse_args()
    write = bool(ns.write) and not bool(ns.no_write)

    result = run_dumbbell_calibration(
        ns.yaml,
        step=ns.step,
        fixed_cams=ns.fixed_cams,
        maxiter=ns.maxiter,
        write=write,
    )

    print(
        "Dumbbell calibration result: "
        f"success={result.success} fun_initial={result.fun_initial:.6g} fun_final={result.fun_final:.6g} "
        f"frames_used={result.n_frames_used}/{result.n_frames_total} msg={result.message}"
    )

    # SciPy occasionally reports `success=False` with messages like
    # "Desired error not necessarily achieved due to precision loss." even when
    # the objective has converged to a very small value. Treat that as a
    # successful run when the objective improved substantially.
    if result.success:
        return 0

    improved = result.fun_final < result.fun_initial
    converged_enough = result.fun_final < 1e-2
    if improved and converged_enough:
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
