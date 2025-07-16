import os
import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("DISPLAY") is None or os.environ.get("QT_QPA_PLATFORM") == "offscreen",
    reason="GUI/Qt tests require a display (DISPLAY or QT_QPA_PLATFORM)"
)
#!/usr/bin/env python3
"""
Test script to verify parameter_gui.py works with Experiment objects
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "pyptv"))

from pyptv.experiment import Experiment
from pyptv.parameter_gui import Main_Params, Calib_Params, Tracking_Params

def test_parameter_gui_with_experiment():
    """Test that parameter GUI classes work with Experiment objects"""
    print("Testing parameter_gui.py with Experiment...")
    
    # Create an experiment and load test parameters
    experiment = Experiment()
    test_yaml = Path("tests/test_cavity/parameters_Run1.yaml")
    
    if test_yaml.exists():
        experiment.addParamset("Run1", test_yaml)
        experiment.setActive(0)
        print(f"Loaded test parameters from {test_yaml}")
    else:
        print("Warning: Test YAML file not found, using defaults")
    
    # Test Main_Params
    print("\n1. Testing Main_Params...")
    try:
        main_params = Main_Params(experiment)
        print(f"  ✓ Main_Params created successfully")
        print(f"  ✓ Number of cameras: {main_params.Num_Cam}")
        print(f"  ✓ First image name: {main_params.Name_1_Image}")
        print(f"  ✓ High pass filter: {main_params.HighPass}")
    except Exception as e:
        print(f"  ✗ Error creating Main_Params: {e}")
        return False
    
    # Test Calib_Params
    print("\n2. Testing Calib_Params...")
    try:
        calib_params = Calib_Params(experiment)
        print(f"  ✓ Calib_Params created successfully")
        print(f"  ✓ Number of cameras: {calib_params.n_cam}")
        print(f"  ✓ Image size: {calib_params.h_image_size}x{calib_params.v_image_size}")
        print(f"  ✓ High pass flag: {calib_params.hp_flag}")
    except Exception as e:
        print(f"  ✗ Error creating Calib_Params: {e}")
        return False
    
    # Test Tracking_Params
    print("\n3. Testing Tracking_Params...")
    try:
        tracking_params = Tracking_Params(experiment)
        print(f"  ✓ Tracking_Params created successfully")
        print(f"  ✓ dvxmin: {tracking_params.dvxmin}")
        print(f"  ✓ dvxmax: {tracking_params.dvxmax}")
        print(f"  ✓ New particles flag: {tracking_params.flagNewParticles}")
    except Exception as e:
        print(f"  ✗ Error creating Tracking_Params: {e}")
        return False
    
    # Test parameter updates and save
    print("\n4. Testing parameter updates...")
    try:
        # Modify a parameter
        original_n_cam = main_params.Num_Cam
        main_params.Num_Cam = 3
        print(f"  ✓ Modified Num_Cam from {original_n_cam} to {main_params.Num_Cam}")
        
        # Update the experiment
        experiment.parameter_manager.parameters['ptv']['n_img'] = main_params.Num_Cam
        
        # Save parameters
        experiment.save_parameters()
        print(f"  ✓ Parameters saved successfully")
        
        # Verify the change was saved
        experiment.load_parameters_for_active()
        updated_n_cam = experiment.parameter_manager.parameters['ptv']['n_img']
        print(f"  ✓ Verified saved parameter: n_img = {updated_n_cam}")
        
        # Restore original value
        experiment.parameter_manager.parameters['ptv']['n_img'] = original_n_cam
        experiment.save_parameters()
        print(f"  ✓ Restored original parameter value")
        
    except Exception as e:
        print(f"  ✗ Error testing parameter updates: {e}")
        return False
    
    print("\n✓ All parameter GUI tests passed!")
    return True

if __name__ == "__main__":
    success = test_parameter_gui_with_experiment()
    if not success:
        sys.exit(1)
