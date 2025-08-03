#!/usr/bin/env python
"""
Test the new ParameterManager structure with global num_cams
"""

import sys
import os
from pathlib import Path

# Add pyptv to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pyptv.parameter_manager import ParameterManager


def test_parameter_manager_new_structure():
    """Test the new ParameterManager with global num_cams"""
    
    test_cavity_path = Path(__file__).parent / "test_cavity"
    
    if not test_cavity_path.exists():
        print(f"Test cavity path not found: {test_cavity_path}")
        return
    
    # Change to test cavity directory
    original_cwd = Path.cwd()
    os.chdir(test_cavity_path)
    
    try:
        print("=== TESTING NEW PARAMETER MANAGER STRUCTURE ===")
        
        # Test loading from legacy directory
        print("\n1. Loading from legacy parameter directory...")
        pm = ParameterManager()
        pm.from_directory(test_cavity_path / "parametersRun1")
        
        print(f"Global num_cams: {pm.get_n_cam()}")
        print(f"Parameter groups: {list(pm.parameters.keys())}")
        
        # Check that n_img was removed from non-ptv parameters
        for param_name, param_data in pm.parameters.items():
            if param_name != 'ptv' and isinstance(param_data, dict):
                if 'num_cams' in param_data:
                    print(f"WARNING: Found n_img in {param_name} parameters!")
                else:
                    print(f"✓ No redundant n_img in {param_name}")
        
        # Check ptv parameters
        ptv_params = pm.parameters.get('ptv')
        if ptv_params:
            if 'num_cams' in ptv_params:
                print(f"ERROR: PTV still has num_cams: {ptv_params['num_cams']}")
            else:
                print("✓ PTV section correctly has no num_cams")
            if 'n_img' in ptv_params:
                print(f"ERROR: PTV still has legacy n_img: {ptv_params['n_img']}")
            else:
                print("✓ PTV section correctly has no n_img")
        
        # Check that global num_cams is available
        global_n_cam = pm.get_n_cam()
        print(f"✓ Global num_cams: {global_n_cam}")
        
        # Test saving to new YAML format
        print("\n2. Saving to new YAML format...")
        new_yaml_path = test_cavity_path / "parameters_new_structure.yaml"
        pm.to_yaml(new_yaml_path)
        
        # Test loading from new YAML format
        print("\n3. Loading from new YAML format...")
        pm2 = ParameterManager()
        pm2.from_yaml(new_yaml_path)
        
        print(f"Loaded global num_cams: {pm2.get_n_cam()}")
        print(f"Parameter groups: {list(pm2.parameters.keys())}")
        
        # Test converting back to directory
        print("\n4. Converting back to legacy directory format...")
        new_dir_path = test_cavity_path / "parameters_test_new"
        pm2.to_directory(new_dir_path)
        
        # Check the generated files
        print(f"Generated parameter files:")
        for par_file in sorted(new_dir_path.glob("*.par")):
            print(f"  {par_file.name}")
        
        # Clean up
        if new_yaml_path.exists():
            new_yaml_path.unlink()
            print(f"Cleaned up {new_yaml_path}")
        
        print("\n=== TEST COMPLETED SUCCESSFULLY ===")
        
    finally:
        os.chdir(original_cwd)


if __name__ == "__main__":
    test_parameter_manager_new_structure()
