import pytest
from pathlib import Path
from pyptv.parameter_manager import ParameterManager
import yaml

TRACK_DIR = Path(__file__).parent / "test_cavity"

@pytest.mark.parametrize("param_dir,param_yaml", [
    ("parameters", "parameters_Run1.yaml"),
])
def test_experiment_par_to_yaml(tmp_path, param_dir, param_yaml):
    """
    Test that all .par files in the parameter set are correctly copied to YAML, especially sequence.par.
    """
    import shutil
    param_src = TRACK_DIR / param_dir
    param_dst = tmp_path / param_dir
    shutil.copytree(param_src, param_dst)

    # Load and convert to YAML
    pm = ParameterManager()
    pm.from_directory(param_dst)
    yaml_path = tmp_path / param_yaml
    pm.to_yaml(yaml_path)

    # Load YAML and check sequence section
    with open(yaml_path) as f:
        yml = yaml.safe_load(f)
    assert "sequence" in yml, "YAML missing 'sequence' section!"
    # Check that all expected fields from sequence.par are present
    seq_file = param_src / "sequence.par"
    with open(seq_file) as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    # sequence.par: [img1, img2, ... imgN, first, last]
    base_names = yml["sequence"].get("base_name", [])
    num_imgs = len(base_names)
    for i in range(num_imgs):
        assert base_names[i] == lines[i], f"Image pattern {i+1} mismatch"
    assert str(yml["sequence"].get("first")) == lines[num_imgs], "First frame mismatch"
    assert str(yml["sequence"].get("last")) == lines[num_imgs+1], "Last frame mismatch"
    print(f"YAML sequence section for {param_dir}: {yml['sequence']}")
