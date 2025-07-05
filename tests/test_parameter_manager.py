#!/usr/bin/env python3
"""
Test script for the YAML-centric ParameterManager functionality
"""

import tempfile
from pathlib import Path
from pyptv.parameter_manager import ParameterManager, create_parameter_template

def test_parameter_manager():
    print("=== Testing YAML-centric ParameterManager ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Test basic functionality
        yaml_file = Path(temp_dir) / "parameters_Test.yaml"
        pm = create_parameter_template(yaml_file)
        
        print('\n1. Testing basic parameter access')
        ptv_params = pm.get_parameter('ptv')
        print(f'   PTV parameters loaded: {ptv_params is not None}')
        
        # Test with default values
        masking = pm.get_parameter('masking', default={'mask_flag': False})
        print(f'   masking (with default): {masking}')
        
        print('\n2. Testing parameter modification')
        pm.set_parameter('ptv.imx', 2048)
        imx = pm.get_parameter('ptv.imx')
        print(f'   imx after modification: {imx}')
        
        # Test nested parameter setting
        pm.set_parameter('masking.mask_flag', True)
        mask_flag = pm.get_parameter('masking.mask_flag')
        print(f'   mask_flag after setting: {mask_flag}')
        
        print('\n3. Testing YAML save/load')
        pm.save_yaml()
        
        # Load in new instance
        pm2 = ParameterManager(yaml_file)
        imx2 = pm2.get_parameter('ptv.imx')
        mask_flag2 = pm2.get_parameter('masking.mask_flag')
        print(f'   imx after reload: {imx2}')
        print(f'   mask_flag after reload: {mask_flag2}')
        
        print('\n4. Testing path resolution')
        rel_path = "img/cam1.tif"
        abs_path = pm.resolve_path(rel_path)
        print(f'   Relative path: {rel_path}')
        print(f'   Resolved path: {abs_path}')
        
    print('\n=== YAML-centric ParameterManager tests completed! ===')

if __name__ == '__main__':
    test_parameter_manager()
