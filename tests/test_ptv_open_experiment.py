import os
from pathlib import Path
import shutil
import tempfile

import pytest
from pyptv.ptv import open_experiment_from_directory


# Autouse fixture to restore cwd after each test, since the function changes it
@pytest.fixture(autouse=True)
def restore_cwd():
    orig = os.getcwd()
    try:
        yield
    finally:
        os.chdir(orig)


def _find_sample_yaml() -> Path | None:
    """Locate a sample YAML in tests/test_cavity to use for integration test."""
    repo_root = Path(__file__).resolve().parents[1]
    cavity_dir = repo_root / "tests" / "test_cavity"
    if not cavity_dir.is_dir():
        return None
    yamls = sorted(cavity_dir.glob("*.yaml")) + sorted(cavity_dir.glob("*.yml"))
    return yamls[0] if yamls else None


def test_open_experiment_from_yaml_happy_path_changes_cwd_and_populates():
    from pyptv import ptv
    from pyptv.experiment import Experiment

    sample_yaml = _find_sample_yaml()
    if sample_yaml is None:
        pytest.skip("tests/test_cavity sample YAML not found")

    exp = ptv.open_experiment_from_yaml(sample_yaml)

    # Returns an Experiment-like object
    assert isinstance(exp, Experiment)
    # CWD is updated to the YAML's directory
    assert Path(os.getcwd()).resolve() == sample_yaml.parent.resolve()
    # Experiment should have paramsets populated
    assert hasattr(exp, "paramsets")
    assert isinstance(exp.paramsets, list)
    assert len(exp.paramsets) >= 1


def test_open_experiment_from_yaml_invalid_path_raises_value_error(tmp_path: Path):
    from pyptv import ptv

    bogus = tmp_path / "no_such.yaml"
    with pytest.raises(ValueError):
        ptv.open_experiment_from_yaml(bogus)


def test_open_experiment_from_yaml_wrong_extension_raises_value_error(tmp_path: Path):
    from pyptv import ptv

    bad = tmp_path / "params.txt"
    bad.write_text("not yaml")
    with pytest.raises(ValueError):
        ptv.open_experiment_from_yaml(bad)


def test_open_experiment_from_yaml_pm_failure_propagates(monkeypatch, tmp_path: Path):
    from pyptv import ptv

    # Minimal valid-looking YAML file path (contents won't be parsed due to mock)
    yaml_file = tmp_path / "params.yaml"
    yaml_file.write_text("ptv: {}\n")

    class FailingPM:
        def from_yaml(self, path):  # noqa: D401
            raise RuntimeError("boom")

    monkeypatch.setattr(ptv, "ParameterManager", FailingPM)

    with pytest.raises(RuntimeError):
        ptv.open_experiment_from_yaml(yaml_file)


def test_open_experiment_from_yaml_calls_populate_runs_and_changes_cwd(monkeypatch, tmp_path: Path):
    from pyptv import ptv

    yaml_file = tmp_path / "params.yaml"
    yaml_file.write_text("ptv: {}\n")

    class DummyPM:
        def from_yaml(self, path):
            # do nothing; downstream code doesn't need fields here
            return None

    class SpyExperiment:
        def __init__(self, pm=None):
            self.pm = pm
            self.populate_runs_called_with = None
            self.paramsets = []

        def populate_runs(self, p: Path):
            self.populate_runs_called_with = Path(p)

    monkeypatch.setattr(ptv, "ParameterManager", DummyPM)
    monkeypatch.setattr(ptv, "Experiment", SpyExperiment)

    exp = ptv.open_experiment_from_yaml(yaml_file)

    # cwd set to yaml parent
    assert Path(os.getcwd()).resolve() == yaml_file.parent.resolve()
    # Our SpyExperiment recorded the populate_runs argument
    assert isinstance(exp, SpyExperiment)
    assert exp.populate_runs_called_with == yaml_file.parent
class DummyExperiment:
    def __init__(self, pm=None):
        self.pm = pm
        self.populated = False
        self.dir = None

    def populate_runs(self, exp_dir):
        self.populated = True
        self.dir = exp_dir

def test_open_experiment_from_directory_valid(monkeypatch):
    # Create a temporary directory to simulate experiment directory
    with tempfile.TemporaryDirectory() as tmpdir:
        exp_dir = Path(tmpdir)
        # Patch os.chdir to avoid actually changing the working directory
        monkeypatch.setattr(os, "chdir", lambda d: None)
        # Patch Experiment only for this test
        import pyptv.ptv as ptv_mod
        monkeypatch.setattr(ptv_mod, "Experiment", DummyExperiment)
        exp = open_experiment_from_directory(exp_dir)
        assert isinstance(exp, DummyExperiment)
        assert exp.populated
        assert exp.dir == exp_dir

def test_open_experiment_from_directory_invalid():
    # Pass a non-existent directory
    with pytest.raises(ValueError):
        open_experiment_from_directory(Path("/non/existent/dir"))

def test_open_experiment_from_directory_not_a_dir(tmp_path):
    # Pass a file instead of a directory
    file_path = tmp_path / "file.txt"
    file_path.write_text("dummy")
    with pytest.raises(ValueError):
        open_experiment_from_directory(file_path)

def test_open_experiment_from_directory_reads_test_cavity(tmp_path, monkeypatch):
    # Setup: Copy the test_cavity directory to a temp location

    # Assume the test_cavity directory is relative to the tests directory
    test_cavity_src = Path(__file__).parent / "test_cavity"
    test_cavity_dst = tmp_path / "test_cavity"
    shutil.copytree(test_cavity_src, test_cavity_dst)

    # Patch os.chdir to avoid changing the working directory
    monkeypatch.setattr(os, "chdir", lambda d: None)

    # Patch DummyExperiment to record the directory and check for the parameters file
    class RecordingExperiment(DummyExperiment):
        def populate_runs(self, exp_dir):
            super().populate_runs(exp_dir)
            # Check that parameters_Run1.yaml exists in the directory
            params_file = exp_dir / "parameters_Run1.yaml"
            assert params_file.exists()
            # Optionally, read and compare contents
            with open(params_file, "r") as f:
                content = f.read()
            # Compare to the original file
            with open(test_cavity_src / "parameters_Run1.yaml", "r") as f:
                original_content = f.read()
            assert content == original_content

    import pyptv.ptv as ptv_mod
    monkeypatch.setattr(ptv_mod, "Experiment", RecordingExperiment)

    exp = open_experiment_from_directory(test_cavity_dst)
    assert isinstance(exp, RecordingExperiment)
    assert exp.populated
    assert exp.dir == test_cavity_dst
