import os
import shutil
import pytest
from pathlib import Path
from pyptv.parameter_manager import ParameterManager
from pyptv.ptv import Tracker
from optv.tracker import Tracker, default_naming

@pytest.mark.usefixtures("tmp_path")
def test_tracker_minimal(tmp_path):
    # Use the real test data from tests/track
    test_data_dir = Path(__file__).parent / "track"
    # Copy all necessary files and folders to tmp_path for isolation
    for sub in ["cal", "img", "res"]:
        shutil.copytree(test_data_dir / sub, tmp_path / sub)
    for fname in ["parameters_Run1.yaml"]:
        shutil.copy(test_data_dir / fname, tmp_path / fname)

    # Change working directory to tmp_path
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        # Load parameters using ParameterManager
        param_path = tmp_path / "parameters_Run1.yaml"
        pm = ParameterManager()
        pm.from_yaml(param_path)

        from pyptv.ptv import py_start_proc_c
        cpar, spar, vpar, track_par, tpar, cals, epar = py_start_proc_c(pm)

        for cam_id, short_name in enumerate(pm.get_target_filenames()):
            # print(f"Setting tracker image base name for cam {cam_id+1}: {Path(short_name).resolve()}")
            spar.set_img_base_name(cam_id, str(Path(short_name).resolve())+'.')

        # Set up tracker using loaded parameters
        tracker = Tracker(
            cpar, vpar, track_par, spar, cals, default_naming
        )
        tracker.full_forward()

        # Check that output files are created and contain tracks
        res_dir = tmp_path / "res"
        first = spar.get_first()
        last = spar.get_last()
        for frame in range(first, last + 1):
            ptv_is_file = res_dir / f"ptv_is.{frame}"
            assert ptv_is_file.exists(), f"Output file {ptv_is_file} not created."
            with open(ptv_is_file, "r") as f:
                lines = f.readlines()
            num_tracks = int(lines[0].strip()) if lines else 0
            assert num_tracks > 0, f"No tracks found in {ptv_is_file}."
    finally:
        os.chdir(old_cwd)


if __name__ == "__main__":
    pytest.main(["-v", __file__])
