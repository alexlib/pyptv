from __future__ import annotations

import shutil
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

from pyptv.dumbbell_ground_truth import DumbbellGTSpec, generate_dumbbell_target_files


def _copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


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
    # Keep all other cameras fixed during optimization to remove gauge freedom.
    ori1 = work / "cal" / "cam2.tif.ori"
    # 3) Perturb the starting calibration (pos + angles) and write it back.
    from optv.calibration import Calibration
    start = Calibration()
    addpar = Path(str(ori1).replace(".ori", ".addpar"))
    start.from_file(str(ori1), str(addpar))
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
            "2",
            "3",
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

    # 5) Parse residuals summary and verify improvement.
    match = re.search(r"fun_initial=([0-9eE+.-]+) fun_final=([0-9eE+.-]+)", proc.stdout)
    assert match, f"Expected residual summary in output. Output:\n{proc.stdout}"

    fun_start = float(match.group(1))
    fun_final = float(match.group(2))

    assert fun_final < fun_start * 0.5, (
        f"Residuals not improved enough: start={fun_start}, final={fun_final}"
    )


