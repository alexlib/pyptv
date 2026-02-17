"""Headless dumbbell calibration utilities.

This is a GUI-free runner for the dumbbell calibration routine implemented in
[pyptv/ptv.py](pyptv/ptv.py) (`calib_dumbbell`).

Assumptions / inputs
- You already have per-camera target files written for a sequence, one file per
  frame per camera, in the OpenPTV-style format used by `ptv.read_targets()`.
- For every frame used, each camera must have exactly 2 detected targets
  (the two dumbbell endpoints). Frames that don't satisfy this are skipped.

Outputs
- Updated camera extrinsics (pos + angles) are optimized.
- Writes updated `.ori` and `.addpar` files.

Notes
- This routine optimizes only extrinsics (pos, angles). Intrinsics/distortions
  are taken from the initial `.ori/.addpar` and remain unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
from scipy.optimize import least_squares

from optv.transforms import convert_arr_pixel_to_metric

from pyptv.parameter_manager import ParameterManager
from pyptv import ptv


@dataclass(frozen=True)
class DumbbellResult:
    success: bool
    message: str
    fun_initial: float
    fun_final: float
    n_frames_used: int
    n_frames_total: int


def _load_pm(yaml_path: Path) -> ParameterManager:
    pm = ParameterManager()
    pm.from_yaml(yaml_path)
    return pm


def _read_dumbbell_targets_metric(
    *,
    target_bases: Sequence[str | Path],
    first_frame: int,
    last_frame: int,
    step: int,
    num_cams: int,
    cpar,
) -> tuple[np.ndarray, int, int]:
    """Read dumbbell targets from files and return metric coords.

    Returns
    - targets_metric: (C, T, 2) where T = 2 * n_frames_used
    - n_frames_used
    - n_frames_total
    """

    if step <= 0:
        raise ValueError("step must be > 0")

    all_frames = list(range(first_frame, last_frame + 1, step))
    frames_used = 0
    per_frame: list[list[list[float]]] = []

    for frame in all_frames:
        frame_targets: list[list[list[float]]] = []
        valid = True
        for cam in range(num_cams):
            targs = ptv.read_targets(str(target_bases[cam]), frame)
            if len(targs) != 2:
                valid = False
                break
            frame_targets.append([t.pos() for t in targs])  # [[x,y],[x,y]]
        if valid:
            per_frame.append(frame_targets)
            frames_used += 1

    if frames_used == 0:
        raise ValueError(
            "No valid frames found: each used frame must have exactly 2 targets per camera"
        )

    # per_frame: (F, C, 2, 2)
    arr = np.asarray(per_frame, dtype=float)
    if arr.ndim != 4 or arr.shape[1] != num_cams or arr.shape[2] != 2 or arr.shape[3] != 2:
        raise ValueError(f"Unexpected targets shape: {arr.shape}")

    # reshape into (C, F*2, 2)
    arr = arr.transpose(1, 0, 2, 3).reshape(num_cams, frames_used * 2, 2)

    # convert pixel->metric per camera
    metric = np.asarray(
        [convert_arr_pixel_to_metric(np.asarray(cam_xy), cpar) for cam_xy in arr],
        dtype=float,
    )

    return metric, frames_used, len(all_frames)


def run_dumbbell_calibration(
    yaml_path: Path,
    *,
    step: int | None = None,
    fixed_cams: Sequence[int] = (),
    maxiter: int = 1000,
    write: bool = True,
) -> DumbbellResult:
    """Run dumbbell calibration end-to-end.

    Args:
        yaml_path: parameters_*.yaml
        step: frame step through the sequence. If None, uses dumbbell.dumbbell_step when present, else 1.
        fixed_cams: 0-based camera indices to keep fixed (not optimized).
        maxiter: SciPy `least_squares` max function evaluations
        write: write `.ori/.addpar` outputs

    Returns:
        DumbbellResult summary
    """

    yaml_path = Path(yaml_path).resolve()
    pm = _load_pm(yaml_path)

    # Build the core parameter objects + load current calibrations
    cpar, spar, vpar, track_par, tpar, cals, epar = ptv.py_start_proc_c(pm)
    num_cams = int(cpar.get_num_cams())

    # Dumbbell params
    dumbbell = pm.get_parameter("dumbbell")
    if dumbbell is None:
        raise KeyError("Missing 'dumbbell' section in YAML")

    db_length = dumbbell.get("dumbbell_scale")
    db_weight = dumbbell.get("dumbbell_penalty_weight")
    db_eps = float(dumbbell.get("dumbbell_eps") or 0.0)
    if db_length is None or float(db_length) <= 0:
        raise ValueError("dumbbell.dumbbell_scale must be > 0")
    if db_weight is None or float(db_weight) < 0:
        raise ValueError("dumbbell.dumbbell_penalty_weight must be >= 0")

    if step is None:
        step = int(dumbbell.get("dumbbell_step") or 1)

    first_frame = int(spar.get_first())
    last_frame = int(spar.get_last())

    # Targets are read from the per-camera "short base" as used by ptv.read_targets
    target_bases = pm.get_target_filenames()
    if not target_bases or len(target_bases) < num_cams:
        raise ValueError("ParameterManager.get_target_filenames() returned an empty/short list")

    resolved_bases = []
    for base in target_bases:
        base_path = Path(base)
        if not base_path.is_absolute():
            base_path = (yaml_path.parent / base_path).resolve()
        resolved_bases.append(base_path)

    all_targs_metric, n_used, n_total = _read_dumbbell_targets_metric(
        target_bases=resolved_bases,
        first_frame=first_frame,
        last_frame=last_frame,
        step=step,
        num_cams=num_cams,
        cpar=cpar,
    )
    if db_eps > 0:
        from optv.orientation import multi_cam_point_positions

        num_frames = int(n_used)
        per_frame = all_targs_metric.reshape(num_cams, num_frames, 2, 2)
        keep = np.ones(num_frames, dtype=bool)
        removed = 0
        for frame_idx in range(num_frames):
            frame_targets = per_frame[:, frame_idx, :, :]
            xyz1, _err1 = multi_cam_point_positions(
                frame_targets[:, 0, :][np.newaxis], cpar, cals
            )
            xyz2, _err2 = multi_cam_point_positions(
                frame_targets[:, 1, :][np.newaxis], cpar, cals
            )
            dist = np.linalg.norm(xyz1[0] - xyz2[0])
            if abs(dist - float(db_length)) > db_eps:
                keep[frame_idx] = False
                removed += 1
        if removed > 0:
            print(f"Filtered {removed} frame(s) by dumbbell length eps {db_eps}")
        per_frame = per_frame[:, keep, :, :]
        n_used = int(per_frame.shape[1])
        if n_used == 0:
            raise ValueError("All frames filtered by dumbbell length eps")
        all_targs_metric = per_frame.reshape(num_cams, n_used * 2, 2)

    print(f"Using {n_used} frame(s) for dumbbell calibration (of {n_total})")

    def _print_camera_residuals(label: str, metric_targets: np.ndarray) -> None:
        from optv.imgcoord import image_coordinates
        from optv.orientation import multi_cam_point_positions

        num_cams_local, num_frames_local, num_targs_local, _ = metric_targets.shape
        sums = np.zeros(num_cams_local, dtype=float)
        counts = np.zeros(num_cams_local, dtype=int)
        mm_params = cpar.get_multimedia_params()

        for frame_idx in range(num_frames_local):
            frame_targets = metric_targets[:, frame_idx, :, :]
            xyz1, _err1 = multi_cam_point_positions(
                frame_targets[:, 0, :][np.newaxis], cpar, cals
            )
            xyz2, _err2 = multi_cam_point_positions(
                frame_targets[:, 1, :][np.newaxis], cpar, cals
            )
            xyz = np.vstack([xyz1, xyz2])

            for cam in range(num_cams_local):
                proj = image_coordinates(xyz, cals[cam], mm_params)
                diff = frame_targets[cam] - proj
                mask = np.isfinite(diff).all(axis=1)
                if np.any(mask):
                    sums[cam] += float(np.sum(diff[mask] ** 2))
                    counts[cam] += int(np.sum(mask))

        rms = np.sqrt(sums / np.maximum(counts, 1))
        print(f"{label} per-camera RMS (metric): {rms.tolist()}")

    per_frame_metric = all_targs_metric.reshape(num_cams, n_used, 2, 2)

    # Active cams mask
    active = np.ones(num_cams, dtype=bool)
    for cam in fixed_cams:
        if cam < 0 or cam >= num_cams:
            raise ValueError(f"fixed cam index out of range: {cam}")
        active[cam] = False

    num_active = int(np.sum(active))
    if num_active == 0:
        raise ValueError("All cameras are fixed; nothing to optimize")

    # Build initial optimization vector (pos + angles) for active cams
    pos_scale = 1.0
    print(f"Position scale set to {pos_scale} (optimize in millimeters)")

    # Build initial optimization vector (pos + angles) for active cams
    calib_vec = np.empty((num_active, 2, 3), dtype=float)
    ptr = 0
    for cam in range(num_cams):
        if not active[cam]:
            continue
        calib_vec[ptr, 0] = cals[cam].get_pos() / pos_scale
        calib_vec[ptr, 1] = cals[cam].get_angles()
        ptr += 1

    def _init_dumbbell_points(metric_targets: np.ndarray) -> np.ndarray:
        from optv.orientation import multi_cam_point_positions

        num_cams_local, num_frames_local, _, _ = metric_targets.shape
        points = np.zeros((num_frames_local, 2, 3), dtype=float)

        for frame_idx in range(num_frames_local):
            frame_targets = metric_targets[:, frame_idx, :, :]
            xyz1, _err1 = multi_cam_point_positions(
                frame_targets[:, 0, :][np.newaxis], cpar, cals
            )
            xyz2, _err2 = multi_cam_point_positions(
                frame_targets[:, 1, :][np.newaxis], cpar, cals
            )
            points[frame_idx, 0] = xyz1[0]
            points[frame_idx, 1] = xyz2[0]

        return points

    points_init = _init_dumbbell_points(per_frame_metric)
    x0 = np.concatenate([calib_vec.reshape(-1), points_init.reshape(-1)])

    def residuals(x: np.ndarray) -> np.ndarray:
        return ptv.dumbbell_ba_residuals(
            x,
            per_frame_metric,
            cpar,
            cals,
            active,
            float(db_length),
            float(db_weight),
            pos_scale,
        )

    initial_residuals = residuals(x0)
    fun_initial = float(np.sum(initial_residuals**2))
    _print_camera_residuals("Initial", per_frame_metric)

    method = "trf"
    loss = "soft_l1"
    print(f"Using least_squares method={method} loss={loss}")

    tol_steps = [
        (1e-6, 1e-6, 1e-5),
        (1e-5, 1e-5, 1e-4),
        (1e-4, 1e-4, 1e-3),
    ]
    max_rounds = 3
    nfev_per_round = max(1, int(maxiter) // max_rounds)
    min_improvement = 1e-3

    best_x = x0
    best_fun = float(np.sum(initial_residuals**2))
    res = None

    jac_sparsity = ptv.dumbbell_ba_jac_sparsity(
        per_frame_metric,
        active,
        float(db_weight),
    )

    for idx in range(max_rounds):
        xtol, ftol, gtol = tol_steps[min(idx, len(tol_steps) - 1)]
        res = least_squares(
            residuals,
            best_x,
            xtol=xtol,
            ftol=ftol,
            gtol=gtol,
            jac_sparsity=jac_sparsity,
            x_scale="jac",
            max_nfev=nfev_per_round,
            loss=loss,
            f_scale=1.0,
            verbose=2,
            method=method,
        )
        new_fun = float(np.sum(res.fun**2))
        improvement = (best_fun - new_fun) / max(best_fun, 1e-12)
        print(
            f"Adaptive round {idx + 1}: fun={new_fun:.6g} improvement={improvement:.3g} "
            f"xtol={xtol} ftol={ftol} gtol={gtol}"
        )
        best_x = res.x
        best_fun = new_fun
        if improvement < min_improvement:
            break

    if res is None:
        raise RuntimeError("Adaptive least_squares did not run")

    # Apply solution back to calibration objects
    cam_params_len = num_active * 6
    calib_pars = np.asarray(best_x[:cam_params_len], dtype=float).reshape(-1, 2, 3)
    ptr = 0
    for cam in range(num_cams):
        if not active[cam]:
            continue
        cals[cam].set_pos(calib_pars[ptr, 0] * pos_scale)
        cals[cam].set_angles(calib_pars[ptr, 1])
        ptr += 1

    if write:
        cal_ori = pm.get_parameter("cal_ori")
        img_ori = cal_ori.get("img_ori") if isinstance(cal_ori, dict) else None

        for cam in range(num_cams):
            if img_ori and cam < len(img_ori):
                ori_path = Path(img_ori[cam])
                if not ori_path.is_absolute():
                    ori_path = (yaml_path.parent / ori_path).resolve()
                addpar_path = Path(str(ori_path).replace(".ori", ".addpar"))
                ori_path.parent.mkdir(parents=True, exist_ok=True)
                cals[cam].write(str(ori_path).encode("utf-8"), str(addpar_path).encode("utf-8"))
            else:
                # Fallback: use cpar's calibration base
                base = cpar.get_cal_img_base_name(cam)
                cals[cam].write(f"{base}.ori".encode("utf-8"), f"{base}.addpar".encode("utf-8"))

    fun_final = float(best_fun)
    _print_camera_residuals("Final", per_frame_metric)

    return DumbbellResult(
        success=bool(res.success),
        message=str(res.message),
        fun_initial=fun_initial,
        fun_final=fun_final,
        n_frames_used=n_used,
        n_frames_total=n_total,
    )
