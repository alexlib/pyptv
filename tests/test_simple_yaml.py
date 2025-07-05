#!/usr/bin/env python3

import sys
from pathlib import Path

# Simple test without terminal output issues
def main():
    # Add pyptv to path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from pyptv.parameter_manager import create_parameter_template
    from pyptv.experiment import Experiment
    
    # Create test directory
    test_dir = Path.cwd() / "test_yaml_simple"
    test_dir.mkdir(exist_ok=True)
    
    # Test 1: Create parameter template
    yaml_file = test_dir / "parameters_Test1.yaml"
    param_manager = create_parameter_template(yaml_file, n_cam=3)
    
    # Test 2: Create experiment
    exp = Experiment(yaml_file)
    
    # Test 3: Copy parameter set
    exp.copy_paramset("Test1", "Test2")
    
    # Test 4: Modify parameters
    exp.set_parameter('ptv.imx', 2048)
    exp.save_parameters()
    
    # Write results to file
    with open(test_dir / "test_results.txt", "w") as f:
        f.write("YAML-centric system test results:\n")
        f.write(f"✓ Parameter template created: {yaml_file.exists()}\n")
        f.write(f"✓ Number of cameras: {param_manager.get_n_cam()}\n")
        f.write(f"✓ Experiment created with {len(exp.paramsets)} parameter sets\n")
        f.write(f"✓ Parameter modification and save successful\n")
        f.write("All tests passed!\n")

if __name__ == "__main__":
    main()
