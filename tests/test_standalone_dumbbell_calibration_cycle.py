from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

from optv.calibration import Calibration

from pyptv.dumbbell_ground_truth import generate_dumbbell_target_files, DumbbellGTSpec


def _copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def _read_cal(ori_path: Path) -> Calibration:
    cal = Calibration()
    addpar = Path(str(ori_path).replace(".ori", ".addpar"))
    cal.from_file(str(ori_path), str(addpar))
    return cal


def test_standalone_dumbbell_calibration_cycle(tmp_path: Path):
    """GT calib -> synthetic dumbbell target files -> standalone script -> recover extrinsics."""

    src = Path(__file__).parent / "test_cavity"
    work = tmp_path / "cavity"
    _copy_tree(src, work)

    yaml_path = work / "parameters_Run1.yaml"
    assert yaml_path.exists()

    # 1) Generate synthetic target files for the YAML's frame range.
    # Use a moderate number of attempts per frame to ensure we find in-FOV points.
    summary = generate_dumbbell_target_files(
        yaml_path,
        out_root=None,  # write relative to work dir
        spec=DumbbellGTSpec(first=10001, last=10004, length=25.0, noise_sigma_px=0.0, seed=0, max_tries_per_frame=2000),
    )
    assert summary["frames_written"] == 4

    # 2) Capture ground-truth calibration for camera 2 (we will perturb it).
    # Keep camera 1 fixed during optimization to remove gauge freedom.
    ori1 = work / "cal" / "cam2.tif.ori"
    gt = _read_cal(ori1)

    # 3) Perturb the starting calibration (pos + angles) and write it back.
    start = _read_cal(ori1)
    start.set_pos(start.get_pos() + np.array([2.0, -1.0, 1.5]))
    start.set_angles(start.get_angles() + np.array([0.01, -0.005, 0.008]))
    start.write(str(ori1).encode("utf-8"), str(ori1).replace(".ori", ".addpar").encode("utf-8"))

    # 4) Run the standalone script (as requested) to re-fit extrinsics.
    script = Path(__file__).parents[1] / "scripts" / "standalone_dumbbell_calibration.py"
    proc = subprocess.run(
        [
            sys.executable,
            str(script),
            str(yaml_path),
            "--fixed-cams",
            "0",
            "--maxiter",
            "800",
            "--write",
        ],
        cwd=str(work),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout

    # 5) Read result and verify it's closer to GT than the perturbed start.
    final = _read_cal(ori1)

    d_start = np.linalg.norm(start.get_pos() - gt.get_pos())
    d_final = np.linalg.norm(final.get_pos() - gt.get_pos())

    a_start = np.linalg.norm(start.get_angles() - gt.get_angles())
    a_final = np.linalg.norm(final.get_angles() - gt.get_angles())

    assert d_final < d_start * 0.5, f"Position not improved enough: start={d_start}, final={d_final}"
    assert a_final < a_start * 0.5, f"Angles not improved enough: start={a_start}, final={a_final}"
