"""Ground-truth generation for dumbbell calibration.

Generates synthetic *target files* (the same on-disk format used by OpenPTV)
for a dumbbell sequence:
- exactly 2 targets per frame per camera (the dumbbell endpoints)

This is designed so tests can run:
GT calib (.ori/.addpar) -> synthetic target files -> dumbbell calibration -> compare.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from optv.calibration import Calibration
from optv.imgcoord import image_coordinates
from optv.transforms import convert_arr_metric_to_pixel
from optv.tracking_framebuf import TargetArray

from pyptv.parameter_manager import ParameterManager
from pyptv import ptv


@dataclass(frozen=True)
class DumbbellGTSpec:
    first: int
    last: int
    length: float
    noise_sigma_px: float = 0.0
    seed: int = 0
    max_tries_per_frame: int = 500


def _load_pm(yaml_path: Path) -> ParameterManager:
    pm = ParameterManager()
    pm.from_yaml(Path(yaml_path))
    return pm


def _load_calibration_pair(base_dir: Path, ori_rel_or_abs: str) -> Calibration:
    ori_path = Path(ori_rel_or_abs)
    if not ori_path.is_absolute():
        ori_path = (base_dir / ori_path).resolve()
    addpar_path = Path(str(ori_path).replace(".ori", ".addpar"))

    cal = Calibration()
    cal.from_file(str(ori_path), str(addpar_path))
    return cal


def _load_gt_calibrations(yaml_path: Path, pm: ParameterManager):
    """Return (cpar, calibrations) loaded relative to the YAML directory."""
    params = pm.parameters
    cal_ori = params.get("cal_ori")
    if not isinstance(cal_ori, dict):
        raise KeyError("YAML must contain cal_ori")

    img_ori = cal_ori.get("img_ori")
    if not img_ori:
        raise ValueError("cal_ori.img_ori missing")

    cpar, *_rest = ptv.py_start_proc_c(pm)
    num_cams = int(cpar.get_num_cams())
    if len(img_ori) < num_cams:
        raise ValueError("cal_ori.img_ori must list one .ori path per camera")

    base_dir = Path(yaml_path).resolve().parent
    cals = [_load_calibration_pair(base_dir, img_ori[i]) for i in range(num_cams)]

    return cpar, cals


def _write_two_targets(
    short_base: Path,
    frame: int,
    xy2: np.ndarray,
    *,
    sum_grey: int = 1000,
    pix_counts=(9, 9, 9),
) -> None:
    """Write exactly two targets to the standard OpenPTV target file via ptv.write_targets."""

    xy2 = np.asarray(xy2, dtype=float)
    if xy2.shape != (2, 2):
        raise ValueError(f"xy2 must be shape (2,2); got {xy2.shape}")

    targs = TargetArray(2)
    for i in range(2):
        t = targs[i]
        t.set_pnr(i)
        t.set_pos([float(xy2[i, 0]), float(xy2[i, 1])])
        t.set_pixel_counts(int(pix_counts[0]), int(pix_counts[1]), int(pix_counts[2]))
        t.set_sum_grey_value(int(sum_grey))
        t.set_tnr(0)

    short_base.parent.mkdir(parents=True, exist_ok=True)
    ptv.write_targets(targs, str(short_base), int(frame))


def _project_points_px(xyz: np.ndarray, cal, cpar) -> np.ndarray:
    metric = image_coordinates(np.asarray(xyz, dtype=float), cal, cpar.get_multimedia_params())
    pix = convert_arr_metric_to_pixel(metric, cpar)
    return np.asarray(pix, dtype=float).reshape(-1, 2)


def generate_dumbbell_target_files(
    yaml_path: Path,
    *,
    out_root: Path | None = None,
    spec: DumbbellGTSpec | None = None,
) -> dict[str, object]:
    """Generate synthetic target files for dumbbell calibration.

    Files are written to the locations implied by `sequence.base_name` in YAML:
    `ParameterManager.get_target_filenames()` produces the short bases.

    Args:
        yaml_path: parameters YAML
        out_root: optional root directory to write under. If provided, the short bases
                  are re-rooted under this directory (preserving relative paths).
                  If None, files are written relative to yaml_path.parent.
        spec: DumbbellGTSpec; if None uses YAML's sequence range and dumbbell length.

    Returns a small summary dict.
    """

    yaml_path = Path(yaml_path).resolve()
    pm = _load_pm(yaml_path)

    dumbbell = pm.get_parameter("dumbbell")
    if dumbbell is None:
        raise KeyError("Missing 'dumbbell' section in YAML")

    seq = pm.get_parameter("sequence")
    if seq is None:
        raise KeyError("Missing 'sequence' section in YAML")

    if spec is None:
        spec = DumbbellGTSpec(
            first=int(seq["first"]),
            last=int(seq["last"]),
            length=float(dumbbell["dumbbell_scale"]),
            noise_sigma_px=0.0,
            seed=0,
        )

    if spec.length <= 0:
        raise ValueError("dumbbell length must be > 0")

    cpar, cals = _load_gt_calibrations(yaml_path, pm)
    num_cams = int(cpar.get_num_cams())

    # Determine output bases
    bases = pm.get_target_filenames()
    if len(bases) != num_cams:
        raise ValueError(f"Expected {num_cams} target bases, got {len(bases)}")

    # Re-root if requested
    def resolve_base(b: Path) -> Path:
        b = Path(b)
        if out_root is None:
            return (yaml_path.parent / b).resolve() if not b.is_absolute() else b
        # preserve relative portion
        rel = b if not b.is_absolute() else b.relative_to(b.anchor)
        return (Path(out_root) / rel).resolve()

    bases = [resolve_base(Path(b)) for b in bases]

    imx = int(pm.get_parameter("ptv")["imx"])
    imy = int(pm.get_parameter("ptv")["imy"])

    rng = np.random.default_rng(spec.seed)

    frames = list(range(spec.first, spec.last + 1))
    written = 0

    for frame in frames:
        ok = False
        for _try in range(spec.max_tries_per_frame):
            # Choose a dumbbell in world coordinates.
            center = np.array(
                [
                    rng.uniform(-20.0, 20.0),
                    rng.uniform(-20.0, 20.0),
                    rng.uniform(-10.0, 10.0),
                ],
                dtype=float,
            )
            v = rng.normal(size=3)
            v /= np.linalg.norm(v) + 1e-12
            half = 0.5 * spec.length
            xyz = np.stack([center - half * v, center + half * v], axis=0)  # (2,3)

            # Project into every camera; require inside image.
            xy_by_cam = []
            in_all = True
            for cam in range(num_cams):
                xy = _project_points_px(xyz, cals[cam], cpar)
                if not (
                    np.all(np.isfinite(xy))
                    and np.all(xy[:, 0] >= 0)
                    and np.all(xy[:, 0] < imx)
                    and np.all(xy[:, 1] >= 0)
                    and np.all(xy[:, 1] < imy)
                ):
                    in_all = False
                    break
                xy_by_cam.append(xy)

            if not in_all:
                continue

            # Add pixel noise if requested
            if spec.noise_sigma_px > 0:
                for cam in range(num_cams):
                    xy_by_cam[cam] = xy_by_cam[cam] + rng.normal(
                        0.0, spec.noise_sigma_px, size=xy_by_cam[cam].shape
                    )

            # Write files
            for cam in range(num_cams):
                _write_two_targets(bases[cam], frame, xy_by_cam[cam])

            ok = True
            written += 1
            break

        if not ok:
            raise RuntimeError(f"Failed to generate an in-FOV dumbbell for frame {frame}")

    return {
        "num_cams": num_cams,
        "frames": frames,
        "frames_written": written,
        "bases": [str(b) for b in bases],
        "noise_sigma_px": spec.noise_sigma_px,
    }
