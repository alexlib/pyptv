"""Test tracking parameter propagation through the entire pipeline"""

import pytest
from pathlib import Path
import subprocess
import sys
import tempfile
import shutil
import os
import yaml
from pyptv.pyptv_batch_plugins import run_batch


def test_tracking_parameters_propagation():
    """Test that tracking parameters are correctly transferred from YAML to C/Cython tracking code"""
    
    test_path = Path(__file__).parent / "test_splitter"
    
    if not test_path.exists():
        pytest.skip(f"Test data not found: {test_path}")
    
    # Test parameter reading first
    from pyptv.experiment import Experiment
    from pyptv.ptv import py_start_proc_c
    
    # Create experiment and load parameters
    experiment = Experiment()
    experiment.populate_runs(test_path)
    experiment.set_active(0)
    
    # Check YAML parameters
    track_params_yaml = experiment.pm.get_parameter('track')
    print(f"YAML tracking parameters: {track_params_yaml}")
    
    assert track_params_yaml is not None, "Track parameters are None"
    assert isinstance(track_params_yaml, dict), f"Track parameters should be dict, got {type(track_params_yaml)}"
    
    # Expected values from the YAML file
    expected_values = {
        'dvxmin': -1.9,
        'dvxmax': 1.9,
        'dvymin': -1.9,
        'dvymax': 1.9,
        'dvzmin': -1.9,
        'dvzmax': 1.9
    }
    
    # Verify YAML contains correct values
    for param, expected_value in expected_values.items():
        assert param in track_params_yaml, f"Missing parameter {param} in YAML"
        assert track_params_yaml[param] == expected_value, \
            f"Wrong value for {param}: got {track_params_yaml[param]}, expected {expected_value}"
    
    print("✅ YAML parameters are correct")
    
    # Test parameter conversion to C objects
    try:
        cpar, spar, vpar, track_par, tpar, cals, epar = py_start_proc_c(experiment.pm)
        print("✅ Parameter conversion successful")
    except Exception as e:
        pytest.fail(f"Parameter conversion failed: {e}")
    
    # Test that tracking parameters were correctly transferred
    assert track_par.get_dvxmin() == expected_values['dvxmin'], \
        f"dvxmin not transferred correctly: got {track_par.get_dvxmin()}, expected {expected_values['dvxmin']}"
    assert track_par.get_dvxmax() == expected_values['dvxmax'], \
        f"dvxmax not transferred correctly: got {track_par.get_dvxmax()}, expected {expected_values['dvxmax']}"
    assert track_par.get_dvymin() == expected_values['dvymin'], \
        f"dvymin not transferred correctly: got {track_par.get_dvymin()}, expected {expected_values['dvymin']}"
    assert track_par.get_dvymax() == expected_values['dvymax'], \
        f"dvymax not transferred correctly: got {track_par.get_dvymax()}, expected {expected_values['dvymax']}"
    assert track_par.get_dvzmin() == expected_values['dvzmin'], \
        f"dvzmin not transferred correctly: got {track_par.get_dvzmin()}, expected {expected_values['dvzmin']}"
    assert track_par.get_dvzmax() == expected_values['dvzmax'], \
        f"dvzmax not transferred correctly: got {track_par.get_dvzmax()}, expected {expected_values['dvzmax']}"
    
    print("✅ C parameter objects have correct values")
    
    # Test actual tracking with correct parameters
    print(f"Testing tracking with velocity ranges: x={track_par.get_dvxmin()}-{track_par.get_dvxmax()}, "
          f"y={track_par.get_dvymin()}-{track_par.get_dvymax()}, z={track_par.get_dvzmin()}-{track_par.get_dvzmax()}")


def test_tracking_parameters_missing_fail():
    """Test that missing tracking parameters cause explicit failure"""
    
    from pyptv.ptv import _populate_track_par
    
    # Test with missing parameters
    incomplete_params = {
        'dvxmin': -1.0,
        'dvxmax': 1.0,
        # Missing dvymin, dvymax, dvzmin, dvzmax
    }
    
    with pytest.raises(ValueError, match="Missing required tracking parameters"):
        _populate_track_par(incomplete_params)
    
    # Test with empty dictionary
    with pytest.raises(ValueError, match="Missing required tracking parameters"):
        _populate_track_par({})
    
    print("✅ Missing parameters correctly raise ValueError")


def test_tracking_parameters_in_batch_run():
    """Test tracking parameters in actual batch run using pyptv_batch_splitter functions with detailed output"""
    test_path = Path(__file__).parent / "test_splitter"
    if not test_path.exists():
        pytest.skip(f"Test data not found: {test_path}")

    # Prepare a temporary copy of test_splitter
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_test_path = Path(temp_dir) / "test_splitter"
        shutil.copytree(test_path, temp_test_path)
        yaml_file = temp_test_path / "parameters_Run1.yaml"
        if not yaml_file.exists():
            pytest.skip(f"YAML file not found: {yaml_file}")

        # Patch YAML if needed (optional, but can ensure splitter mode)
        with open(yaml_file, "r") as f:
            params = yaml.safe_load(f)
        if "ptv" not in params:
            params["ptv"] = {}
        params["ptv"]["splitter"] = True
        with open(yaml_file, "w") as f:
            yaml.safe_dump(params, f)

        # Import and run batch function directly

        # Run batch with tracking mode
        run_batch(
            yaml_file,
            1000001,
            1000004,
            mode="tracking",
            tracking_plugin = "ext_tracker_splitter",
        )

        # Check for tracking output in res directory
        res_dir = temp_test_path / "res"
        tracking_lines = []
        for frame in range(1000001, 1000005):
            output_file = res_dir / f"tracking_output_{frame}.txt"
            if output_file.exists():
                with open(output_file, "r") as f:
                    for line in f:
                        if "step:" in line and "links:" in line:
                            tracking_lines.append(line.strip())
        assert len(tracking_lines) > 0, "No tracking output found in batch run"
        for line in tracking_lines:
            parts = line.split(',')
            links_part = [p for p in parts if 'links:' in p][0]
            links_count = int(links_part.split(':')[1].strip())
            print(f"Found tracking line: {line}")
            print(f"Links count: {links_count}")
            assert links_count > 50, f"Very low link count {links_count} suggests tracking parameters may not be working"
    print("✅ Batch tracking run shows reasonable link numbers")


def test_parameter_propagation_with_corrupted_yaml():
    """Test behavior when YAML has corrupted tracking parameters"""
    
    test_path = Path(__file__).parent / "test_splitter"
    
    if not test_path.exists():
        pytest.skip(f"Test data not found: {test_path}")
    
    # Create a temporary copy with corrupted tracking parameters
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_test_path = Path(temp_dir) / "test_splitter"
        shutil.copytree(test_path, temp_test_path)
        
        # Corrupt the YAML file by removing tracking parameters
        yaml_file = temp_test_path / "parameters_Run1.yaml"
        
        with open(yaml_file, 'r') as f:
            content = f.read()
        
        # Remove tracking parameters section
        lines = content.split('\n')
        filtered_lines = []
        skip_tracking = False
        
        for line in lines:
            if line.strip().startswith('track:'):
                skip_tracking = True
                continue
            elif skip_tracking and line.startswith(' ') and ':' in line:
                continue  # Skip tracking parameter lines
            else:
                skip_tracking = False
                filtered_lines.append(line)
        
        with open(yaml_file, 'w') as f:
            f.write('\n'.join(filtered_lines))
        
        # Test that this causes proper failure
        from pyptv.experiment import Experiment
        from pyptv.ptv import py_start_proc_c
        
        experiment = Experiment()
        experiment.populate_runs(temp_test_path)
        experiment.set_active(0)
        
        # This should now fail explicitly instead of using default 0.0 values
        with pytest.raises(KeyError):
            py_start_proc_c(experiment.pm)
    
    print("✅ Corrupted YAML correctly raises explicit error")




# All tests below are pure pytest unit tests and do not use subprocess or CLI integration.

def test_tracking_parameters_yaml_and_c_conversion():
    """Test YAML tracking parameters and their conversion to C/Cython objects."""
    test_path = Path(__file__).parent / "test_splitter"
    if not test_path.exists():
        pytest.skip(f"Test data not found: {test_path}")
    from pyptv.experiment import Experiment
    from pyptv.ptv import py_start_proc_c
    experiment = Experiment()
    experiment.populate_runs(test_path)
    experiment.set_active(0)
    track_params_yaml = experiment.pm.get_parameter('track')
    expected_values = {
        'dvxmin': -1.9,
        'dvxmax': 1.9,
        'dvymin': -1.9,
        'dvymax': 1.9,
        'dvzmin': -1.9,
        'dvzmax': 1.9
    }
    for param, expected_value in expected_values.items():
        assert param in track_params_yaml, f"Missing parameter {param} in YAML"
        assert track_params_yaml[param] == expected_value, (
            f"Wrong value for {param}: got {track_params_yaml[param]}, expected {expected_value}")
    cpar, spar, vpar, track_par, tpar, cals, epar = py_start_proc_c(experiment.pm)
    assert track_par.get_dvxmin() == expected_values['dvxmin']
    assert track_par.get_dvxmax() == expected_values['dvxmax']
    assert track_par.get_dvymin() == expected_values['dvymin']
    assert track_par.get_dvymax() == expected_values['dvymax']
    assert track_par.get_dvzmin() == expected_values['dvzmin']
    assert track_par.get_dvzmax() == expected_values['dvzmax']


def test_tracking_parameters_missing_raises():
    """Test that missing tracking parameters raise ValueError."""
    from pyptv.ptv import _populate_track_par
    incomplete_params = {'dvxmin': -1.0, 'dvxmax': 1.0}
    with pytest.raises(ValueError, match="Missing required tracking parameters"):
        _populate_track_par(incomplete_params)
    with pytest.raises(ValueError, match="Missing required tracking parameters"):
        _populate_track_par({})


def test_parameter_propagation_with_corrupted_yaml_unit():
    """Test behavior when YAML has corrupted tracking parameters (unit test)."""
    test_path = Path(__file__).parent / "test_splitter"
    if not test_path.exists():
        pytest.skip(f"Test data not found: {test_path}")
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_test_path = Path(temp_dir) / "test_splitter"
        shutil.copytree(test_path, temp_test_path)
        yaml_file = temp_test_path / "parameters_Run1.yaml"
        with open(yaml_file, 'r') as f:
            content = f.read()
        lines = content.split('\n')
        filtered_lines = []
        skip_tracking = False
        for line in lines:
            if line.strip().startswith('track:'):
                skip_tracking = True
                continue
            elif skip_tracking and line.startswith(' ') and ':' in line:
                continue
            else:
                skip_tracking = False
                filtered_lines.append(line)
        with open(yaml_file, 'w') as f:
            f.write('\n'.join(filtered_lines))
        from pyptv.experiment import Experiment
        from pyptv.ptv import py_start_proc_c
        experiment = Experiment()
        experiment.populate_runs(temp_test_path)
        experiment.set_active(0)
        with pytest.raises(KeyError):
            py_start_proc_c(experiment.pm)


def test_tracking_parameters_in_batch_run_plugin():
    """Test tracking parameters in actual batch run using plugin with detailed output"""
    
    test_path = Path(__file__).parent / "test_splitter"
    
    if not test_path.exists():
        pytest.skip(f"Test data not found: {test_path}")
    
    # Prepare a temporary copy of test_splitter and patch YAML for plugin usage
    import yaml
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_test_path = Path(temp_dir) / "test_splitter"
        shutil.copytree(test_path, temp_test_path)
        yaml_file = temp_test_path / "parameters_Run1.yaml"
        # Patch YAML: ensure ptv section has splitter: True
        with open(yaml_file, "r") as f:
            params = yaml.safe_load(f)
        if "ptv" not in params:
            params["ptv"] = {}
        params["ptv"]["splitter"] = True
        # Ensure plugins section requests splitter tracking
        if "plugins" not in params:
            params["plugins"] = {}
        params["plugins"]["available_tracking"] = ["ext_tracker_splitter"]
        params["plugins"]["available_sequence"] = ["ext_sequence_splitter"]
        with open(yaml_file, "w") as f:
            yaml.safe_dump(params, f)
        # Import and run batch function directly
        from pyptv.pyptv_batch_plugins import run_batch

        # Run batch with tracking mode
        run_batch(yaml_file, 1000001, 1000004, tracking_plugin="ext_tracker_splitter", sequence_plugin="ext_sequence_splitter", mode="tracking")
        # Check for tracking output in res directory
        res_dir = temp_test_path / "res"
        tracking_lines = []
        for frame in range(1000001, 1000005):
            output_file = res_dir / f"tracking_output_{frame}.txt"
            if output_file.exists():
                with open(output_file, "r") as f:
                    for line in f:
                        if "step:" in line and "links:" in line:
                            tracking_lines.append(line.strip())
        assert len(tracking_lines) > 0, "No tracking output found in plugin batch run"
        for line in tracking_lines:
            parts = line.split(',')
            links_part = [p for p in parts if 'links:' in p][0]
            links_count = int(links_part.split(':')[1].strip())
            print(f"Found tracking line: {line}")
            print(f"Links count: {links_count}")
            assert links_count > 50, f"Very low link count {links_count} suggests tracking parameters may not be working"
    print("✅ Plugin batch tracking run shows reasonable link numbers")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])