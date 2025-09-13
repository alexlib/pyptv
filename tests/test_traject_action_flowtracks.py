import pytest
from unittest.mock import MagicMock, patch, call
from pyptv.pyptv_gui import TreeMenuHandler

@pytest.fixture
def mock_info():
    # Mock info.object and its methods/attributes
    obj = MagicMock()
    obj.num_cams = 2
    obj.camera_list = [MagicMock(), MagicMock()]
    obj.clear_plots = MagicMock()
    obj.overlay_set_images = MagicMock()
    obj.get_parameter = MagicMock(return_value={
        'first': 1,
        'last': 2,
        'base_name': ['base1', 'base2']
    })
    obj.cals = ['cal1', 'cal2']
    obj.cpar = MagicMock()
    obj.cpar.get_multimedia_params.return_value = 'multimedia_params'
    info = MagicMock()
    info.object = obj
    return info

@pytest.fixture
def mock_traj():
    # Mock a trajectory object with pos() method
    class Traj:
        def pos(self):
            # 3 points in 3D
            return [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    return [Traj(), Traj()]

@pytest.fixture
def patch_flowtracks_and_helpers(mock_traj):
    with patch("pyptv.flowtracks_utils.compute_flowtracks_trajectories_from_guiobj") as mock_compute:
        # Return dummy results for the plotting step
        mock_compute.return_value = {
            'heads_x': [[1], [2]], 'heads_y': [[3], [4]],
            'tails_x': [[5], [6]], 'tails_y': [[7], [8]],
            'ends_x': [[9], [10]], 'ends_y': [[11], [12]]
        }
        yield mock_compute

def test_traject_action_flowtracks_calls_and_draws(mock_info, patch_flowtracks_and_helpers):
    # Import the class under test

    handler = TreeMenuHandler()
    handler.traject_action_flowtracks(mock_info)

    # Check that clear_plots was called
    mock_info.object.clear_plots.assert_called_once_with(remove_background=False)

    # Check that drawcross was called for each camera and each type
    for cam in mock_info.object.camera_list:
        assert cam.drawcross.call_count == 3
        calls = [
            call("heads_x", "heads_y", list, list, "red", 3),
            call("tails_x", "tails_y", list, list, "green", 2),
            call("ends_x", "ends_y", list, list, "orange", 3),
        ]
        # Check that the correct color and names are used
        actual_calls = [c for c in cam.drawcross.call_args_list]
        assert actual_calls[0][0][0] == "heads_x"
        assert actual_calls[0][0][1] == "heads_y"
        assert actual_calls[0][0][4] == "red"
        assert actual_calls[1][0][0] == "tails_x"
        assert actual_calls[1][0][1] == "tails_y"
        assert actual_calls[1][0][4] == "green"
        assert actual_calls[2][0][0] == "ends_x"
        assert actual_calls[2][0][1] == "ends_y"
        assert actual_calls[2][0][4] == "orange"