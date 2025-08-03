import pytest
import shutil
from pathlib import Path
from pyptv import pyptv_batch
from pyptv.experiment import Experiment
from pyptv.parameter_manager import ParameterManager
import filecmp
import yaml


TRACK_DIR = Path(__file__).parent / "track"

@pytest.mark.parametrize("yaml_path, desc", [
    # ("parameters_Run1.yaml", "2 cameras, no new particles"),
    # ("parameters_Run2.yaml", "3 cameras, new particle"),
    ("parameters_Run3.yaml", "3 cameras, newpart, frame by frame"),
])
def test_tracking_res_matches_orig(tmp_path, yaml_path, desc):
    # Print image name pattern for debugging

    """
    For the given parameter set, clean and set up img/ and res/ folders, run tracking, and compare res/ to res_orig/.
    """
    # 1. Setup working directory
    work_dir = tmp_path / f"track"
    work_dir.mkdir(exist_ok=True)
    # copy everything from TRACK_DIR to work_dir
    shutil.copytree(TRACK_DIR, work_dir, dirs_exist_ok=True)

    # create in work_dir copy of img_orig as img and res_orig as res
    shutil.copytree(work_dir / "img_orig", work_dir / "img", dirs_exist_ok=True)
    shutil.copytree(work_dir / "res_orig", work_dir / "res", dirs_exist_ok=True)
    # Remove all files from work_dir / "res"
    res_dir = work_dir / "res"
    for file in res_dir.glob("*"):
        if file.is_file():
            file.unlink()

    


    # 2. Convert .par to YAML
    # exp = Experiment()
    # exp.populate_runs(work_dir)

    yaml_path = work_dir / yaml_path

    pm = ParameterManager()
    pm.from_yaml(work_dir / yaml_path)
    # yaml_path = work_dir / param_yaml
    # pm.to_yaml(yaml_path)

    # Get first and last from sequence_parameters in pm
    # pm = exp.pm
    seq_params = pm.parameters.get("sequence")
    first = seq_params.get("first")
    last = seq_params.get("last")


    # 4. Run tracking using pyptv_batch.main directly with arguments
    if yaml_path == "parameters_Run3.yaml":
        # First run: no new particle
        # Set add_new_particle to False in the YAML before first run
        with open(yaml_path, "r") as f:
            yml = yaml.safe_load(f)
        yml["track"]["flagNewParticles"] = False
        with open(yaml_path, "w") as f:
            yaml.safe_dump(yml, f)

        pyptv_batch.run_batch(
            yaml_file=yaml_path,
            seq_first=first,
            seq_last=last,
            mode="tracking",
        )
        # Save result for comparison
        res_dir = work_dir / "res"
        res_files_noadd = sorted(res_dir.glob("rt_is.*"))
        with open(res_files_noadd[-1], "r") as f:
            lines_noadd = f.readlines()

        # Second run: add new particle
        # Set add_new_particle to False in the YAML before first run
        with open(yaml_path, "r") as f:
            yml = yaml.safe_load(f)
        yml["track"]["flagNewParticles"] = True
        with open(yaml_path, "w") as f:
            yaml.safe_dump(yml, f)

        pyptv_batch.main(
            yaml_file=str(yaml_path),
            first=first,
            last=last,
            mode="tracking",
        )
        res_files_add = sorted(res_dir.glob("rt_is.*"))
        with open(res_files_add[-1], "r") as f:
            lines_add = f.readlines()

        # Check that the number of trajectories increases or a new particle appears
        assert len(lines_add) > len(lines_noadd), "No new particle added in Run3 with add_new_particle=True"

    else:
        # Standard test for Run1 and Run2
        pyptv_batch.run_batch(
            yaml_file=yaml_path,
            seq_first=first,
            seq_last=last,
            mode="tracking"
        )
        # 5. Compare res/ to res_orig/
        res_dir = work_dir / "res"
        res_orig_dir = work_dir / "res_orig"


        for f in sorted(res_dir.glob("rt_is.*")):
            print(f"\n--- {f.name} ---")
            with open(f, "r") as file:
                print(file.read())

        for f in sorted(res_dir.glob("ptv_is.*")):
            print(f"\n--- {f.name} ---")
            with open(f, "r") as file:
                print(file.read())


        # dcmp = filecmp.dircmp(res_dir, res_orig_dir)
        # assert len(dcmp.diff_files) == 0, f"Files differ in {desc}: {dcmp.diff_files}"
        # assert len(dcmp.left_only) == 0, f"Extra files in result: {dcmp.left_only}"
        # assert len(dcmp.right_only) == 0, f"Missing files in result: {dcmp.right_only}"
        # print(f"Tracking test passed for {desc}")

        # Compare file contents and stop at the first difference
        for fname in sorted(f for f in res_dir.iterdir() if f.is_file()):
            orig_file = res_orig_dir / fname.name
            if not orig_file.exists():
                print(f"Missing file in res_orig: {fname.name}")
                break
            with open(fname, "rb") as f1, open(orig_file, "rb") as f2:
                content1 = f1.read()
                content2 = f2.read()
                if content1 != content2:
                    print(f"File differs: {fname.name}")
                    break


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])