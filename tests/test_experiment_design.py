"""
Test the new Experiment-centric design with ParameterManager
"""

import pytest
import os
import tempfile
from pathlib import Path
import shutil

from pyptv.experiment import Experiment, Paramset
from pyptv.parameter_manager import ParameterManager


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

    yield exp_dir
    shutil.rmtree(temp_dir)


def test_experiment_initialization():
    """Test that Experiment can be initialized properly"""
    exp = Experiment()
    
    # Check that ParameterManager is initialized
    assert hasattr(exp, 'parameter_manager')
    assert isinstance(exp.parameter_manager, ParameterManager)
    
    # Check initial state
    assert exp.active_params is None
    assert len(exp.paramsets) == 0
    assert not exp.changed_active_params


def test_experiment_parameter_access():
    """Test parameter access through Experiment"""
    exp = Experiment()
    
    # Initially, get_parameter should return None for non-existent parameters
    ptv_params = exp.get_parameter('ptv')
    assert ptv_params is None


def test_experiment_populate_runs(temp_experiment_dir):
    """Test that Experiment can populate runs from directory"""
    exp = Experiment()
    
    # Change to the experiment directory
    original_dir = os.getcwd()
    os.chdir(temp_experiment_dir)
    
    try:
        exp.populate_runs(temp_experiment_dir)
        
        # Check that parameter sets were loaded
        assert len(exp.paramsets) > 0
        assert exp.active_params is not None
        
        # Check that parameters can be accessed
        ptv_params = exp.get_parameter('ptv')
        assert ptv_params is not None
        # n_img is now accessed via n_cam through the parameter manager
        # But the ptv group now has n_cam from the global setting
        assert ptv_params['n_cam'] == 4  # n_cam instead of n_img
        assert ptv_params['imx'] == 1280
        assert ptv_params['imy'] == 1024
        
        # Check sequence parameters
        seq_params = exp.get_parameter('sequence')
        assert seq_params is not None
        assert seq_params['first'] == 10000
        assert seq_params['last'] == 10010
        
    finally:
        os.chdir(original_dir)


def test_experiment_parameter_saving(temp_experiment_dir):
    """Test that Experiment can save parameters to YAML"""
    exp = Experiment()
    
    # Change to the experiment directory
    original_dir = os.getcwd()
    os.chdir(temp_experiment_dir)
    
    try:
        exp.populate_runs(temp_experiment_dir)
        
        # Save parameters
        exp.save_parameters()
        
        # Check that YAML file was created
        yaml_path = exp.active_params.yaml_path
        assert yaml_path.exists()
        
        # Check that parameters can be loaded from YAML
        exp2 = Experiment()
        exp2.parameter_manager.from_yaml(yaml_path)
        
        ptv_params = exp2.parameter_manager.get_parameter('ptv')
        assert ptv_params is not None
        assert ptv_params['n_cam'] == 4  # n_cam instead of n_img
        
    finally:
        os.chdir(original_dir)


def test_experiment_no_circular_dependency():
    """Test that there's no circular dependency between Experiment and GUI"""
    exp = Experiment()
    
    # The experiment should not need to know about any GUI
    assert not hasattr(exp, 'main_gui')
    assert not hasattr(exp, 'gui')
    
    # The experiment should be self-contained for parameter management
    assert hasattr(exp, 'parameter_manager')
    assert hasattr(exp, 'get_parameter')
    assert hasattr(exp, 'save_parameters')


def test_experiment_parameter_updates(temp_experiment_dir):
    """Test that parameter updates work correctly"""
    exp = Experiment()
    
    # Change to the experiment directory
    original_dir = os.getcwd()
    os.chdir(temp_experiment_dir)
    
    try:
        exp.populate_runs(temp_experiment_dir)
        
        # Get initial parameters
        ptv_params = exp.get_parameter('ptv')
        original_imx = ptv_params['imx']
        
        # Update parameters through the ParameterManager
        exp.parameter_manager.parameters['ptv']['imx'] = 1920
        
        # Verify the change
        updated_params = exp.get_parameter('ptv')
        assert updated_params['imx'] == 1920
        assert updated_params['imx'] != original_imx
        
        # Save and verify persistence
        exp.save_parameters()
        
        # Load in a new experiment instance
        exp2 = Experiment()
        yaml_path = exp.active_params.yaml_path
        exp2.parameter_manager.from_yaml(yaml_path)
        
        reloaded_params = exp2.parameter_manager.get_parameter('ptv')
        assert reloaded_params['imx'] == 1920
        
    finally:
        os.chdir(original_dir)


def test_clean_design_principles():
    """Test that the design follows clean architecture principles"""
    exp = Experiment()
    
    # 1. Experiment is the MODEL - owns data
    assert hasattr(exp, 'parameter_manager')
    assert hasattr(exp, 'paramsets')
    assert hasattr(exp, 'active_params')
    
    # 2. Experiment has clear interface for parameter access
    assert callable(exp.get_parameter)
    assert callable(exp.save_parameters)
    
    # 3. Experiment doesn't depend on GUI
    # We check that no GUI-related attributes are present
    gui_attributes = ['main_gui', 'gui', 'camera_list', 'view', 'plot']
    for attr in gui_attributes:
        assert not hasattr(exp, attr), f"Experiment should not have GUI attribute: {attr}"
    
    # 4. ParameterManager is encapsulated within Experiment
    assert isinstance(exp.parameter_manager, ParameterManager)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
