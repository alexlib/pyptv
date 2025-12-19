from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np

from optv.imgcoord import image_coordinates
from optv.transforms import convert_arr_metric_to_pixel

from pyptv.ground_truth import generate_ground_truth, save_ground_truth_npz
from pyptv.standalone_calibration import get_flags_from_yaml, load_parameter_manager, run_standalone_calibration
from pyptv import ptv


def _copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def test_standalone_calibration_full_cycle(tmp_path: Path):
    """GT -> synthetic 2D -> full_calibration -> reprojection error ~= 0."""

    src = Path(__file__).parent / "test_cavity"
    work = tmp_path / "cavity"
    _copy_tree(src, work)

    yaml_path = work / "parameters_Run1.yaml"
    assert yaml_path.exists()

    # 1) Generate synthetic correspondences (no noise) from GT `.ori/.addpar`.
    gt = generate_ground_truth(yaml_path, noise_sigma_px=0.0, seed=0)
    points_npz = tmp_path / "points.npz"
    save_ground_truth_npz(points_npz, gt)

    # 2) Run calibration using those correspondences.
    pm = load_parameter_manager(yaml_path)
    flags = get_flags_from_yaml(pm)

    cpar, *_ = ptv.py_start_proc_c(pm)

    cals = run_standalone_calibration(
        yaml_path,
        gt.xyz,
        gt.xy,
        gt.pnr,
        flags=flags,
        init_external="first4",
        write=True,
    )

    # 3) Validate by reprojection error.
    rms_by_cam = []
    for cam, cal in enumerate(cals):
        projected_metric = image_coordinates(gt.xyz, cal, cpar.get_multimedia_params())
        pix = np.asarray(convert_arr_metric_to_pixel(projected_metric, cpar), dtype=float).reshape(-1, 2)
        err = pix - gt.xy[cam]
        rms = float(np.sqrt(np.mean(np.sum(err * err, axis=1))))
        rms_by_cam.append(rms)

    # With perfect correspondences, we expect extremely small reprojection RMS.
    assert max(rms_by_cam) < 1e-3, f"Unexpectedly large RMS: {rms_by_cam}"
