#!/usr/bin/env python3
"""
Test script for the new YAML-centric PyPTV system
"""

from pathlib import Path
import sys
import os

# Add pyptv to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pyptv.parameter_manager import ParameterManager, create_parameter_template
from pyptv.experiment import Experiment

def test_yaml_system():
    """Test the new YAML-centric parameter system"""
    
    print("=== Testing YAML-centric PyPTV System ===\n")
    
    # Create test directory
    test_dir = Path("test_yaml_system")
    test_dir.mkdir(exist_ok=True)
    
    print(f"1. Creating test parameter template in {test_dir}")
    yaml_file = test_dir / "parameters_Test1.yaml"
    
    # Create parameter template
    param_manager = create_parameter_template(yaml_file, n_cam=3)
    print(f"   Created: {yaml_file}")
    print(f"   Working directory: {param_manager.get_working_directory()}")
    print(f"   Number of cameras: {param_manager.get_n_cam()}")
    
    print("\n2. Testing parameter access")
    ptv_params = param_manager.get_parameter('ptv')
    print(f"   PTV parameters loaded: {ptv_params is not None}")
    print(f"   Image names: {ptv_params.get('img_name', [])[:2]}...")
    
    print("\n3. Testing Experiment class")
    exp = Experiment(yaml_file)
    print(f"   Experiment initialized with {len(exp.paramsets)} parameter sets")
    print(f"   Active parameter set: {exp.active_params.get_yaml_path().name if exp.active_params.get_yaml_path() else 'None'}")
    
    print("\n4. Testing parameter set operations")
    # Copy parameter set
    new_paramset = exp.copy_paramset("Test1", "Test2")
    print(f"   Copied parameter set: Test1 -> Test2")
    print(f"   Total parameter sets: {len(exp.paramsets)}")
    
    # Switch active parameter set
    exp.set_active_paramset("Test2")
    print(f"   Switched to parameter set: Test2")
    
    print("\n5. Testing parameter modifications")
    # Modify a parameter
    exp.set_parameter('ptv.imx', 2048)
    exp.set_parameter('ptv.imy', 2048)
    saved = exp.save_parameters()
    print(f"   Modified image size to 2048x2048")
    print(f"   Parameters saved: {saved}")
    
    print("\n6. Testing path resolution")
    if exp.active_params:
        img_names = exp.active_params.get_image_names(frame_num=1)
        print(f"   Image paths for frame 1: {img_names[:2]}...")
        
        cal_files = exp.active_params.get_calibration_files()
        print(f"   Calibration files: {len(cal_files.get('ori', []))} ori files")
    
    print("\n7. Validation")
    issues = exp.validate_experiment()
    print(f"   Validation issues: {len(issues)}")
    for issue in issues[:3]:  # Show first 3 issues
        print(f"     - {issue}")
    
    print(f"\n=== Test completed ===")
    print(f"Test files created in: {test_dir.absolute()}")
    
    return True

if __name__ == "__main__":
    try:
        test_yaml_system()
        print("\n✅ YAML-centric system test PASSED")
    except Exception as e:
        print(f"\n❌ YAML-centric system test FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
