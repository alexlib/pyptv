"""Ground-truth projection helpers for calibration testing.

This is used to generate synthetic 2D image measurements from a known
OpenPTV calibration ("ground truth") and known 3D points.

Design goals
- Headless (no Traits/GUI requirements)
- Deterministic (seeded)
- Simple file format for round-trips (`.npz`)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from optv.calibration import Calibration
from optv.imgcoord import image_coordinates
from optv.transforms import convert_arr_metric_to_pixel

from pyptv.parameter_manager import ParameterManager
from pyptv import ptv


@dataclass(frozen=True)
class GroundTruthData:
    xyz: np.ndarray  # (N,3)
    xy: np.ndarray   # (C,N,2)
    pnr: np.ndarray  # (N,)


def load_xyz_from_fixp(fixp_path: Path) -> tuple[np.ndarray, np.ndarray]:
    """Read OpenPTV fixp file.

    Returns
    - ids: (N,) int
    - xyz: (N,3) float
    """
    arr = np.atleast_1d(
        np.loadtxt(
            str(fixp_path),
            dtype=[("id", "i4"), ("pos", "3f8")],
            skiprows=0,
        )
    )
    ids = np.asarray(arr["id"], dtype=int)
    xyz = np.asarray(arr["pos"], dtype=float)
    return ids, xyz


def _load_calibration_pair(base_dir: Path, ori_rel_or_abs: str) -> Calibration:
    ori_path = Path(ori_rel_or_abs)
    if not ori_path.is_absolute():
        ori_path = (base_dir / ori_path).resolve()
    addpar_path = Path(str(ori_path).replace(".ori", ".addpar"))

    cal = Calibration()
    cal.from_file(str(ori_path), str(addpar_path))
    return cal


def generate_ground_truth(
    yaml_path: Path,
    *,
    xyz: np.ndarray | None = None,
    use_fixp_if_xyz_missing: bool = True,
    noise_sigma_px: float = 0.0,
    seed: int = 0,
) -> GroundTruthData:
    """Generate synthetic 2D points from ground-truth calibration.

    - Loads `cpar` and `cal_ori.img_ori` from YAML
    - Uses `xyz` directly, or reads from `cal_ori.fixp_name` when missing
    - Projects XYZ into each camera using OpenPTV projection model
    - Adds optional Gaussian noise in pixel units

    Returns `GroundTruthData` suitable for saving to NPZ.
    """

    yaml_path = Path(yaml_path)
    pm = ParameterManager()
    pm.from_yaml(yaml_path)

    params = pm.parameters
    cal_ori = params.get("cal_ori")
    if not isinstance(cal_ori, dict):
        raise KeyError("YAML must contain 'cal_ori'")

    num_cams = int(pm.num_cams or params.get("num_cams") or 0)
    if num_cams <= 0:
        raise ValueError("num_cams must be > 0")

    # Build cpar from YAML
    cpar, *_rest = ptv.py_start_proc_c(pm)

    if xyz is None:
        if not use_fixp_if_xyz_missing:
            raise ValueError("xyz is None and use_fixp_if_xyz_missing is False")
        fixp_name = cal_ori.get("fixp_name")
        if not fixp_name:
            raise ValueError("cal_ori.fixp_name missing; cannot load xyz")
        fixp_path = Path(fixp_name)
        if not fixp_path.is_absolute():
            fixp_path = (yaml_path.parent / fixp_path).resolve()
        _ids, xyz = load_xyz_from_fixp(fixp_path)

    xyz = np.asarray(xyz, dtype=float)
    if xyz.ndim != 2 or xyz.shape[1] != 3:
        raise ValueError(f"xyz must be (N,3); got {xyz.shape}")

    pnr = np.arange(xyz.shape[0], dtype=int)

    img_ori = cal_ori.get("img_ori")
    if not img_ori or len(img_ori) < num_cams:
        raise ValueError("cal_ori.img_ori must list one .ori path per camera")

    rng = np.random.default_rng(seed)
    xy = np.zeros((num_cams, xyz.shape[0], 2), dtype=float)

    for cam in range(num_cams):
        cal = _load_calibration_pair(yaml_path.parent, img_ori[cam])
        projected_metric = image_coordinates(
            np.asarray(xyz, dtype=float),
            cal,
            cpar.get_multimedia_params(),
        )
        pix = convert_arr_metric_to_pixel(projected_metric, cpar)
        pix = np.asarray(pix, dtype=float).reshape(-1, 2)

        if noise_sigma_px > 0:
            pix = pix + rng.normal(0.0, noise_sigma_px, size=pix.shape)

        xy[cam] = pix

    return GroundTruthData(xyz=xyz, xy=xy, pnr=pnr)


def save_ground_truth_npz(out_path: Path, gt: GroundTruthData) -> None:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out_path, xyz=gt.xyz, xy=gt.xy, pnr=gt.pnr)
