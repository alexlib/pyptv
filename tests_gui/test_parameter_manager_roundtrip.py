
import shutil
from pathlib import Path
import pytest
import yaml as _yaml
import tempfile
from pyptv.parameter_manager import ParameterManager

@pytest.mark.parametrize("rel_dir", [
    "test_cavity/parameters",
])
def test_parameter_manager_roundtrip(rel_dir, tmp_path):
    base_dir = Path(__file__).parent
    src_dir = base_dir / rel_dir
    assert src_dir.exists(), f"Source directory {src_dir} does not exist!"

    # Copy original .par files to temp working directory
    work_dir = tmp_path / "parameters"
    work_dir.mkdir(exist_ok=True)
    for f in src_dir.glob('*.par'):
        shutil.copy(f, work_dir / f.name)

    # 1. Load parameters from directory and write to YAML
    pm = ParameterManager()
    pm.from_directory(work_dir)
    yaml_path = tmp_path / f"parameters_{src_dir.name}.yaml"
    pm.to_yaml(yaml_path)

    # 2. Read YAML back into a new ParameterManager and write to new YAML
    pm2 = ParameterManager()
    pm2.from_yaml(yaml_path)
    yaml_path2 = tmp_path / f"parameters_{src_dir.name}_copy.yaml"
    pm2.to_yaml(yaml_path2)

    # 3. Compare the two YAML files
    with open(yaml_path, 'r') as f1, open(yaml_path2, 'r') as f2:
        yaml1 = f1.read()
        yaml2 = f2.read()
    assert yaml1 == yaml2, "YAML roundtrip failed: files differ!"

    # 4. Convert YAML back to .par files and compare to original
    out_dir = tmp_path / f"parameters_from_yaml_{src_dir.name}"
    out_dir.mkdir(exist_ok=True)
    pm2.to_directory(out_dir)

    skip_files = {'unsharp_mask.par', 'control_newpart.par', 'sequence_newpart.par'}
    DEFAULT_STRING = '---'
    def normalize(line):
        return DEFAULT_STRING if line.strip() in ('', DEFAULT_STRING) else line.strip()

    for f in work_dir.glob('*.par'):
        if f.name in skip_files:
            continue
        out_file = out_dir / f.name
        assert out_file.exists(), f"Missing output file: {out_file}"
        with open(f, 'r') as orig, open(out_file, 'r') as new:
            orig_lines = [normalize(line) for line in orig.readlines()]
            new_lines = [normalize(line) for line in new.readlines()]
            assert len(new_lines) <= len(orig_lines), f"Output file {out_file} has more lines than input!"
            assert len(new_lines) > 0, f"Output file {out_file} is empty!"
            for i, (orig_line, new_line) in enumerate(zip(orig_lines, new_lines)):
                assert orig_line == new_line, f"Mismatch in {f.name} at line {i+1}: '{orig_line}' != '{new_line}'"

    print(f"ParameterManager roundtrip test passed for {src_dir.name}.")

def test_parameter_manager_roundtrip():
    # Path to original parameters directory
    ORIG_PAR_DIR = Path(__file__).parent / 'test_cavity/parameters'
    # Step 1: Load parameters from directory to YAML using Experiment and ParameterManager
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        # Copy original parameters directory to temp
        temp_par_dir = tmpdir / 'parameters'
        shutil.copytree(ORIG_PAR_DIR, temp_par_dir)
        temp_yaml = tmpdir / 'params.yaml'

        # Create Experiment and ParameterManager, convert to YAML
        pm = ParameterManager()
        pm.from_directory(temp_par_dir)
        pm.to_yaml(temp_yaml)

        # Save original YAML content for comparison
        with open(temp_yaml) as f:
            original_yaml_content = f.read()
        print("\n--- YAML after ParameterManager.to_yaml() ---")
        print(original_yaml_content)
        print("--- END YAML ---\n")

        # Step 2: Open GUIs and simulate closing (saving)
        from pyptv.experiment import Experiment
        exp = Experiment(pm=pm)

        # exp.active_params = type('Dummy', (), {'yaml_path': temp_yaml})()  # Dummy object with yaml_path

        class DummyInfo:
            def __init__(self, obj):
                self.object = obj

        # Main GUI
        from pyptv.parameter_gui import Main_Params, Calib_Params, Tracking_Params
        from pyptv.parameter_gui import ParamHandler, CalHandler, TrackHandler
        
        main_gui = Main_Params(exp)
        ParamHandler().closed(DummyInfo(main_gui), is_ok=True)
        pm.to_yaml(temp_yaml)
        with open(temp_yaml) as f:
            after_main_yaml = f.read()
        print("\n--- YAML after Main_Params GUI ---")
        print(after_main_yaml)
        print("--- END YAML ---\n")

        # Calibration GUI
        calib_gui = Calib_Params(exp)
        CalHandler().closed(DummyInfo(calib_gui), is_ok=True)
        pm.to_yaml(temp_yaml)
        with open(temp_yaml) as f:
            after_calib_yaml = f.read()
        print("\n--- YAML after Calib_Params GUI ---")
        print(after_calib_yaml)
        print("--- END YAML ---\n")

        # Tracking GUI
        tracking_gui = Tracking_Params(exp)
        TrackHandler().closed(DummyInfo(tracking_gui), is_ok=True)
        pm.to_yaml(temp_yaml)
        with open(temp_yaml) as f:
            after_track_yaml = f.read()
        print("\n--- YAML after Tracking_Params GUI ---")
        print(after_track_yaml)
        print("--- END YAML ---\n")

        # Step 3: Compare temp YAML with original YAML
        with open(temp_yaml) as f:
            new_yaml_content = f.read()
        if new_yaml_content != original_yaml_content:
            print("\n--- YAML DIFF DETECTED ---")
            import difflib
            diff = difflib.unified_diff(
                original_yaml_content.splitlines(),
                new_yaml_content.splitlines(),
                fromfile='original',
                tofile='after_gui',
                lineterm=''
            )
            print('\n'.join(diff))
            print("--- END DIFF ---\n")
        assert new_yaml_content == original_yaml_content, "YAML file changed after GUI roundtrip!"
        print("Roundtrip test passed: YAML unchanged after GUI edits.")

def normalize_types(params):
    # Example for criteria
    if 'criteria' in params:
        for key in ['X_lay', 'Zmax_lay', 'Zmin_lay']:
            if key in params['criteria']:
                params['criteria'][key] = [int(x) for x in params['criteria'][key]]
    # Example for pft_version
    if 'pft_version' in params and 'Existing_Target' in params['pft_version']:
        val = params['pft_version']['Existing_Target']
        params['pft_version']['Existing_Target'] = int(val) if isinstance(val, bool) else val
    # ...repeat for other fields as needed...
    return params

def to_yaml(self, yaml_path):
    params = self.parameters.copy()
    params = normalize_types(params)
    with open(yaml_path, "w") as f:
        _yaml.safe_dump(params, f)

if __name__ == "__main__":
    # Run the test directly if this script is executed
    pytest.main([__file__, '-v'])
    test_parameter_manager_roundtrip()
    print('Test completed.')
