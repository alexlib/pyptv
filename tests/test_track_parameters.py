import pytest
from pyptv.parameter_manager import ParameterManager
from pathlib import Path
from pyptv.experiment import Experiment

HERE = Path(__file__).parent

def get_track_params_from_yaml(yaml_path):
    pm = ParameterManager()
    experiment = Experiment()
    experiment.populate_runs(Path(yaml_path).parent)
    pm.from_yaml(yaml_path)
    return pm.parameters.get('track')  # Use direct dict access if get_parameter is not available

def get_track_params_from_dir(par_dir):
    pm = ParameterManager()
    pm.from_directory(par_dir)
    return pm.parameters.get('track')

REQUIRED_TRACK_PARAMS = [
    'dvxmin', 'dvxmax', 'dvymin', 'dvymax', 'dvzmin', 'dvzmax',
    'angle', 'dacc', 'flagNewParticles'
]

@pytest.mark.parametrize("yaml_path", [
    HERE / 'test_cavity' / 'parameters_Run1.yaml',
    # Add more YAML files as needed
])
def test_track_params_in_yaml(yaml_path):
    track = get_track_params_from_yaml(yaml_path)
    assert track is not None, f"No 'track' section in {yaml_path}"
    for key in REQUIRED_TRACK_PARAMS:
        assert key in track, f"Missing '{key}' in 'track' section of {yaml_path}"
        assert track[key] is not None, f"'{key}' is None in 'track' section of {yaml_path}"

@pytest.mark.parametrize("par_dir", [
    HERE / 'test_cavity' / 'parameters',
    # Add more parameter directories as needed
])
def test_track_params_in_par_dir(par_dir):
    par_dir_path = Path(par_dir)
    experiment = Experiment()
    experiment.populate_runs(par_dir_path.parent)
    track = get_track_params_from_dir(par_dir)
    assert track is not None, f"No 'track' section in {par_dir}"
    for key in REQUIRED_TRACK_PARAMS:
        assert key in track, f"Missing '{key}' in 'track' section of {par_dir}"
        assert track[key] is not None, f"'{key}' is None in 'track' section of {par_dir}"

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])