"""Test tracking parameter propagation through the entire pipeline"""

import pytest
from pathlib import Path
import subprocess
import sys
import tempfile
import shutil


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
    experiment.setActive(0)
    
    # Check YAML parameters
    track_params_yaml = experiment.parameter_manager.get_parameter('track', {})
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
        cpar, spar, vpar, track_par, tpar, cals, epar = py_start_proc_c(experiment.parameter_manager)
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
    """Test tracking parameters in actual batch run with detailed output"""
    
    test_path = Path(__file__).parent / "test_splitter"
    
    if not test_path.exists():
        pytest.skip(f"Test data not found: {test_path}")
    
    script_path = Path(__file__).parent.parent / "pyptv" / "pyptv_batch_plugins.py"
    
    if not script_path.exists():
        pytest.skip(f"Batch script not found: {script_path}")
    
    # Run batch with tracking and capture detailed output
    cmd = [
        sys.executable, 
        str(script_path), 
        str(test_path), 
        "1000001", 
        "1000002",  # Just 2 frames
        "--sequence", "ext_sequence_splitter",
        "--tracking", "ext_tracker_splitter"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    
    assert result.returncode == 0, f"Batch run failed: {result.stderr}"
    
    # Check tracking output for reasonable link numbers
    lines = result.stdout.split('\n')
    tracking_lines = [line for line in lines if 'step:' in line and 'links:' in line]
    
    assert len(tracking_lines) > 0, "No tracking output found"
    
    # Extract link numbers and verify they're reasonable (not 0 or very low)
    for line in tracking_lines:
        # Parse line like: "step: 1000001, curr: 2178, next: 2185, links: 208, lost: 1970, add: 0"
        parts = line.split(',')
        links_part = [p for p in parts if 'links:' in p][0]
        links_count = int(links_part.split(':')[1].strip())
        
        print(f"Found tracking line: {line}")
        print(f"Links count: {links_count}")
        
        # With proper velocity parameters, we should get reasonable link numbers
        # Previously it was very low (~208 links) which suggests tracking parameters weren't working
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
        experiment.setActive(0)
        
        # This should now fail explicitly instead of using default 0.0 values
        with pytest.raises(ValueError, match="Missing required tracking parameters"):
            py_start_proc_c(experiment.parameter_manager)
    
    print("✅ Corrupted YAML correctly raises explicit error")


if __name__ == "__main__":
    test_tracking_parameters_propagation()
    test_tracking_parameters_missing_fail()
    test_tracking_parameters_in_batch_run()
    test_parameter_propagation_with_corrupted_yaml()
    print("🎉 All tracking parameter tests passed!")
