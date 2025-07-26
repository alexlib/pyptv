"""
Test that the MainGUI works with the new Experiment-centric design
"""

import pytest
import os
import tempfile
from pathlib import Path
import shutil
from unittest.mock import patch

from pyptv.experiment import Experiment

# Since GUI tests require display and can be problematic in CI
pytestmark = pytest.mark.skipif(
    os.environ.get("DISPLAY") is None or os.environ.get("QT_QPA_PLATFORM") == "offscreen",
    reason="GUI/Qt tests require a display (DISPLAY or QT_QPA_PLATFORM)"
)


@pytest.fixture
def temp_experiment_dir():
    """Create a temporary experiment directory structure"""
    temp_dir = tempfile.mkdtemp()
    exp_dir = Path(temp_dir) / "test_experiment"
    exp_dir.mkdir(exist_ok=True)

    # Create parameters directory with test data
    params_dir = exp_dir / "parameters_Run1"
    params_dir.mkdir(exist_ok=True)

    # Create minimal parameter files
    with open(params_dir / "ptv.par", "w") as f:
        f.write("4\n")  # num_cams
        f.write("img/cam1.%d\n")
        f.write("cal/cam1.tif\n")
        f.write("img/cam2.%d\n")
        f.write("cal/cam2.tif\n")
        f.write("img/cam3.%d\n")
        f.write("cal/cam3.tif\n")
        f.write("img/cam4.%d\n")
        f.write("cal/cam4.tif\n")
        f.write("1\n")  # hp_flag
        f.write("1\n")  # allCam_flag
        f.write("1\n")  # tiff_flag
        f.write("1280\n")  # imx
        f.write("1024\n")  # imy
        f.write("0.012\n")  # pix_x
        f.write("0.012\n")  # pix_y
        f.write("0\n")  # chfield
        f.write("1.0\n")  # mmp_n1
        f.write("1.33\n")  # mmp_n2
        f.write("1.46\n")  # mmp_n3
        f.write("5.0\n")  # mmp_d

    with open(params_dir / "sequence.par", "w") as f:
        f.write("img/cam1.%d\n")
        f.write("img/cam2.%d\n")
        f.write("img/cam3.%d\n")
        f.write("img/cam4.%d\n")
        f.write("10000\n")  # first
        f.write("10010\n")  # last

    # Create other required parameter files
    for param_file in [
        "criteria.par",
        "detect_plate.par",
        "orient.par",
        "pft_par.par",
        "targ_rec.par",
        "track.par",
    ]:
        with open(params_dir / param_file, "w") as f:
            f.write("# Test parameter file\n")

    # Simulate batch conversion to YAML (as in CLI)
    experiment = Experiment()
    experiment.populate_runs(exp_dir)
    yield exp_dir
    shutil.rmtree(temp_dir)


def test_maingui_initialization_design(temp_experiment_dir):
    """Test that MainGUI can be initialized with the new design"""
    try:
        from pyptv.pyptv_gui import MainGUI
        # Find a YAML file in the experiment directory
        yaml_files = list(temp_experiment_dir.glob("*.yaml")) + list(temp_experiment_dir.glob("*.yml"))
        assert yaml_files, "No YAML file found after batch conversion"
        yaml_file = yaml_files[0]

        # Mock the configure_traits method to avoid actually showing the GUI
        with patch.object(MainGUI, 'configure_traits'):
            original_dir = os.getcwd()
            os.chdir(temp_experiment_dir)
            try:
                exp = Experiment()
                exp.populate_runs(temp_experiment_dir)
                gui = MainGUI(yaml_file, exp)
                # Test the clean design principles
                assert hasattr(gui, 'exp1')
                assert hasattr(gui.exp1, 'pm')
                assert hasattr(gui, 'get_parameter')
                assert hasattr(gui, 'save_parameters')
                # Test parameter access delegation
                ptv_params = gui.get_parameter('ptv')
                assert ptv_params is not None
                assert gui.exp1.get_n_cam() == 4
                # Test that GUI uses experiment for parameters, not direct ParameterManager
                assert not hasattr(gui, 'pm')  # Old direct ParameterManager reference should be gone
                # Test the experiment is properly configured
                assert gui.exp1.active_params is not None
                assert len(gui.exp1.paramsets) > 0
                # Test camera configuration loaded correctly
                assert gui.num_cams == 4
                assert len(gui.camera_list) == 4
            finally:
                os.chdir(original_dir)
    except ImportError:
        pytest.skip("GUI components not available")
    except Exception as e:
        if "display" in str(e).lower() or "qt" in str(e).lower():
            pytest.skip(f"Display-related error: {str(e)}")
        else:
            raise


def test_no_circular_dependency_in_maingui():
    """Test that MainGUI doesn't create circular dependencies"""
    try:
        from pyptv.pyptv_gui import MainGUI
        from pyptv.experiment import Experiment
        
        # The key principle: Experiment should not need to know about GUI
        exp = Experiment()
        
        # These attributes should NOT exist (no circular dependency)
        assert not hasattr(exp, 'main_gui')
        assert not hasattr(exp, 'gui')
        
        # Experiment should be self-contained for parameter management
        assert hasattr(exp, 'pm')
        assert hasattr(exp, 'get_parameter')
        assert hasattr(exp, 'save_parameters')
        
    except ImportError:
        pytest.skip("GUI components not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
