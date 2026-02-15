import yaml

from pyptv.experiment import Experiment
from pyptv.pyptv_gui import TreeMenuHandler


def _write_yaml(path, data):
    with path.open("w") as handle:
        yaml.safe_dump(data, handle, default_flow_style=False, sort_keys=False)


class _DummyEditor:
    def __init__(self, experiment):
        self._experiment = experiment

    def get_parent(self, _object):
        return self._experiment


class _DummyDialog:
    def __init__(self, experiment):
        self.experiment = experiment

    def edit_traits(self, view=None, kind=None):
        self.experiment.pm.parameters["ptv"]["imx"] = 999
        self.experiment.save_parameters()
        return True


def test_open_non_active_paramset_saves_without_switching_active(tmp_path):
    active_yaml = tmp_path / "parameters_active.yaml"
    other_yaml = tmp_path / "parameters_other.yaml"

    active_data = {"num_cams": 1, "ptv": {"imx": 100}}
    other_data = {"num_cams": 1, "ptv": {"imx": 200}}

    _write_yaml(active_yaml, active_data)
    _write_yaml(other_yaml, other_data)

    experiment = Experiment()
    experiment.addParamset("active", active_yaml)
    experiment.addParamset("other", other_yaml)
    experiment.set_active(0)

    handler = TreeMenuHandler()
    editor = _DummyEditor(experiment)

    non_active_paramset = experiment.paramsets[1]
    result = handler._open_param_dialog(
        editor,
        non_active_paramset,
        _DummyDialog,
        "Main_Params_View",
        "Test dialog",
    )

    assert result is True

    with active_yaml.open("r") as handle:
        active_after = yaml.safe_load(handle)

    with other_yaml.open("r") as handle:
        other_after = yaml.safe_load(handle)

    assert active_after["ptv"]["imx"] == 100
    assert other_after["ptv"]["imx"] == 999
    assert experiment.active_params.yaml_path == active_yaml
    assert experiment.pm.parameters["ptv"]["imx"] == 100
    assert experiment._override_save_path is None
