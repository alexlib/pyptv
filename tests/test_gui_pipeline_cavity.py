import pytest
pytestmark = pytest.mark.qt

from pathlib import Path
import shutil
import numpy as np
from pyptv.experiment import Experiment
from pyptv.pyptv_gui import MainGUI, TreeMenuHandler

@pytest.mark.skip(reason="Skipping GUI pipeline test for now.")
def test_gui_pipeline_cavity(tmp_path):
    # a) Load test_cavity YAML
    test_dir = Path('tests/test_cavity')
    orig_yaml = test_dir / 'parameters_Run1.yaml'
    assert orig_yaml.exists(), f"Missing test YAML: {orig_yaml}"

    # Copy test_cavity to tmp_path for isolation
    for f in test_dir.glob('*'):
        if f.is_file():
            shutil.copy(f, tmp_path / f.name)
    yaml_path = tmp_path / 'parameters_Run1.yaml'

    # b) Initialize Experiment and MainGUI
    exp = Experiment()
    exp.populate_runs(tmp_path)
    gui = MainGUI(yaml_path, exp)
    handler = TreeMenuHandler()

    # c) Check active parameter set
    assert gui.exp1.active_params.yaml_path == yaml_path

    # d) Run sequence and tracking using handler
    # Simulate menu actions by calling handler methods
    dummy_info = type('Dummy', (), {'object': gui})()
    handler.sequence_action(dummy_info)
    handler.track_no_disp_action(dummy_info)
    results_before = {
        'sorted_pos': [np.copy(arr) for arr in getattr(gui, 'sorted_pos', [])],
        'sorted_corresp': [np.copy(arr) for arr in getattr(gui, 'sorted_corresp', [])],
        'num_targs': getattr(gui, 'num_targs', None)
    }

    # e) Create parameter set copy using handler
    paramset = gui.exp1.active_params
    dummy_editor = type('DummyEditor', (), {'get_parent': lambda self, obj: gui.exp1})()
    handler.copy_set_params(dummy_editor, paramset)
    # Find the new YAML file (should be parameters_Run1_1.yaml)
    new_yaml = tmp_path / f'parameters_{paramset.name}_1.yaml'
    assert new_yaml.exists()

    # f) Set new copy as active using handler
    new_paramset = [ps for ps in gui.exp1.paramsets if ps.yaml_path == new_yaml][0]
    handler.set_active(dummy_editor, new_paramset)
    assert gui.exp1.active_params.yaml_path == new_yaml

    # g) Run sequence and tracking again using handler
    handler.sequence_action(dummy_info)
    handler.track_no_disp_action(dummy_info)
    results_after = {
        'sorted_pos': [np.copy(arr) for arr in getattr(gui, 'sorted_pos', [])],
        'sorted_corresp': [np.copy(arr) for arr in getattr(gui, 'sorted_corresp', [])],
        'num_targs': getattr(gui, 'num_targs', None)
    }

    # h) Compare results
    for before, after in zip(results_before['sorted_pos'], results_after['sorted_pos']):
        np.testing.assert_array_equal(before, after)
    for before, after in zip(results_before['sorted_corresp'], results_after['sorted_corresp']):
        np.testing.assert_array_equal(before, after)
    assert results_before['num_targs'] == results_after['num_targs']

    # Optionally, check output files if needed
    # ...

if __name__ == "__main__":
    pytest.main([__file__])