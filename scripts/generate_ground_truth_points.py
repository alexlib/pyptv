#!/usr/bin/env python3
"""Generate synthetic calibration correspondences from ground-truth OpenPTV calibration.

This script reads a PyPTV/OpenPTV YAML, loads the referenced `.ori/.addpar` files
(ground truth), projects the 3D calibration points into each camera, and writes
an `.npz` that can be fed into `scripts/standalone_calibration.py`.

By default, it reads XYZ from `cal_ori.fixp_name`.

Example:
  ./.venv/bin/python scripts/generate_ground_truth_points.py \
      tests/test_cavity/parameters_Run1.yaml out_points.npz --noise-sigma-px 0.2
"""

from __future__ import annotations

import argparse
from pathlib import Path

from pyptv.ground_truth import generate_ground_truth, save_ground_truth_npz


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("yaml", type=Path, help="Path to parameters_*.yaml")
    p.add_argument("out", type=Path, help="Output .npz path")
    p.add_argument("--noise-sigma-px", type=float, default=0.0, help="Gaussian noise sigma in pixels")
    p.add_argument("--seed", type=int, default=0, help="RNG seed")
    return p.parse_args()


def main() -> int:
    ns = _parse_args()
    gt = generate_ground_truth(ns.yaml, noise_sigma_px=float(ns.noise_sigma_px), seed=int(ns.seed))
    save_ground_truth_npz(ns.out, gt)
    print(f"Wrote {ns.out} with xy shape {gt.xy.shape} and xyz shape {gt.xyz.shape}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
