#!/usr/bin/env python3
"""
Simple test for YAML system
"""

from pathlib import Path
import sys
import os

# Add pyptv to path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("Starting simple test...")

try:
    print("1. Importing modules...")
    from pyptv.parameter_manager import ParameterManager, create_parameter_template
    print("   ParameterManager imported")
    
    from pyptv.experiment import Experiment
    print("   Experiment imported")
    
    print("2. Creating test directory...")
    test_dir = Path.cwd() / "simple_test"
    test_dir.mkdir(exist_ok=True)
    print(f"   Created: {test_dir}")
    
    print("3. Creating parameter template...")
    yaml_file = test_dir / "parameters_Simple.yaml"
    param_manager = create_parameter_template(yaml_file, n_cam=2)
    print(f"   Template created: {yaml_file}")
    
    print("4. Testing parameter access...")
    n_cam = param_manager.get_n_cam()
    print(f"   Number of cameras: {n_cam}")
    
    ptv_params = param_manager.get_parameter('ptv')
    print(f"   PTV params loaded: {ptv_params is not None}")
    
    print("5. Testing Experiment...")
    abs_yaml = yaml_file.absolute()
    print(f"   Using absolute path: {abs_yaml}")
    
    # Check if file exists
    print(f"   File exists: {abs_yaml.exists()}")
    
    exp = Experiment(abs_yaml)
    print(f"   Experiment created successfully")
    print(f"   Number of paramsets: {len(exp.paramsets)}")
    
    print("\n✅ Simple test PASSED")
    
except Exception as e:
    print(f"\n❌ Simple test FAILED: {e}")
    import traceback
    traceback.print_exc()
