#!/usr/bin/env python3
"""
Comprehensive test script for TTK GUI fixes and functionality
Tests the main function logic without requiring a display
"""

import sys
import os
from pathlib import Path
import tempfile
import shutil

# Add the pyptv package to the path
sys.path.insert(0, str(Path(__file__).parent))

def test_yaml_file_argument():
    """Test main function with YAML file argument"""
    print("=== Testing YAML file argument ===")
    
    # Test with existing YAML file
    yaml_file = Path("tests/test_cavity/parameters_Run1.yaml")
    if yaml_file.exists():
        print(f"✓ Found test YAML file: {yaml_file}")
        
        # Mock sys.argv
        original_argv = sys.argv.copy()
        sys.argv = ["pyptv_gui_ttk.py", str(yaml_file)]
        
        try:
            # Import and test the main function logic (without GUI creation)
            from pyptv.pyptv_gui_ttk import main
            from pyptv.experiment_ttk import create_experiment_from_yaml
            
            # Test experiment creation directly
            exp = create_experiment_from_yaml(yaml_file)
            print(f"✓ Successfully created experiment from YAML")
            print(f"✓ Number of cameras: {exp.get_n_cam()}")
            print(f"✓ Active params: {exp.active_params is not None}")
            
        except Exception as e:
            print(f"✗ Error testing YAML file argument: {e}")
        finally:
            sys.argv = original_argv
    else:
        print(f"✗ Test YAML file not found: {yaml_file}")

def test_directory_argument():
    """Test main function with directory argument"""
    print("\n=== Testing directory argument ===")
    
    # Test with existing directory
    test_dir = Path("tests/test_cavity")
    if test_dir.exists():
        print(f"✓ Found test directory: {test_dir}")
        
        try:
            from pyptv.experiment_ttk import create_experiment_from_directory
            
            # Test experiment creation from directory
            exp = create_experiment_from_directory(test_dir)
            print(f"✓ Successfully created experiment from directory")
            print(f"✓ Number of cameras: {exp.get_n_cam()}")
            print(f"✓ Parameter manager: {exp.pm is not None}")
            print(f"✓ YAML path: {getattr(exp.pm, 'yaml_path', 'None')}")
            
        except Exception as e:
            print(f"✗ Error testing directory argument: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"✗ Test directory not found: {test_dir}")

def test_directory_without_yaml():
    """Test directory that has only .par files (no YAML)"""
    print("\n=== Testing directory without YAML files ===")
    
    # Create a temporary directory with only .par files
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Copy some .par files from test_cavity
        source_dir = Path("tests/test_cavity/parameters")
        if source_dir.exists():
            # Copy a few essential .par files
            par_files = ["ptv.par", "criteria.par", "detect_plate.par"]
            for par_file in par_files:
                source_file = source_dir / par_file
                if source_file.exists():
                    shutil.copy2(source_file, temp_path / par_file)
            
            print(f"✓ Created temporary directory with .par files: {temp_path}")
            
            try:
                from pyptv.experiment_ttk import create_experiment_from_directory
                
                # Test experiment creation from directory with only .par files
                exp = create_experiment_from_directory(temp_path)
                print(f"✓ Successfully created experiment from .par files")
                print(f"✓ Number of cameras: {exp.get_n_cam()}")
                print(f"✓ Parameter manager: {exp.pm is not None}")
                yaml_path = getattr(exp.pm, 'yaml_path', None)
                print(f"✓ Generated YAML path: {yaml_path}")
                
                # Check if the default YAML file was created
                if yaml_path and yaml_path.exists():
                    print(f"✓ Default YAML file created successfully")
                    print(f"✓ YAML file size: {yaml_path.stat().st_size} bytes")
                else:
                    print(f"✗ Default YAML file not created")
                
            except Exception as e:
                print(f"✗ Error testing directory without YAML: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"✗ Source parameter directory not found: {source_dir}")

def test_parameter_loading():
    """Test parameter loading and validation"""
    print("\n=== Testing parameter loading ===")
    
    yaml_file = Path("tests/test_cavity/parameters_Run1.yaml")
    if yaml_file.exists():
        try:
            from pyptv.parameter_manager import ParameterManager
            
            # Test parameter manager directly
            pm = ParameterManager()
            pm.from_yaml(yaml_file)
            
            print(f"✓ Successfully loaded parameters from YAML")
            print(f"✓ Number of cameras: {pm.num_cams}")
            print(f"✓ Available parameters: {len(pm.parameters)}")
            
            # Test some specific parameters
            if hasattr(pm, 'parameters'):
                param_types = list(pm.parameters.keys())
                print(f"✓ Parameter types loaded: {param_types[:5]}...")  # Show first 5
            
        except Exception as e:
            print(f"✗ Error testing parameter loading: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"✗ Test YAML file not found: {yaml_file}")

def test_experiment_ttk_functionality():
    """Test ExperimentTTK class functionality"""
    print("\n=== Testing ExperimentTTK functionality ===")
    
    try:
        from pyptv.experiment_ttk import ExperimentTTK, ParamsetTTK
        from pyptv.parameter_manager import ParameterManager
        
        # Test empty experiment creation
        exp = ExperimentTTK()
        print(f"✓ Created empty ExperimentTTK")
        print(f"✓ Default number of cameras: {exp.get_n_cam()}")
        
        # Test with parameter manager
        yaml_file = Path("tests/test_cavity/parameters_Run1.yaml")
        if yaml_file.exists():
            pm = ParameterManager()
            pm.from_yaml(yaml_file)
            pm.yaml_path = yaml_file
            
            exp_with_params = ExperimentTTK(pm=pm)
            print(f"✓ Created ExperimentTTK with parameters")
            print(f"✓ Number of cameras: {exp_with_params.get_n_cam()}")
            print(f"✓ Has active params: {exp_with_params.active_params is not None}")
            
            # Test paramset functionality
            if exp_with_params.active_params:
                print(f"✓ Active paramset name: {exp_with_params.active_params.name}")
                print(f"✓ Active paramset YAML path: {exp_with_params.active_params.yaml_path}")
        
    except Exception as e:
        print(f"✗ Error testing ExperimentTTK functionality: {e}")
        import traceback
        traceback.print_exc()

def test_gui_initialization_logic():
    """Test GUI initialization logic without creating the actual GUI"""
    print("\n=== Testing GUI initialization logic ===")
    
    try:
        # Test the main function logic by mocking sys.argv
        original_argv = sys.argv.copy()
        
        # Test 1: With YAML file
        yaml_file = Path("tests/test_cavity/parameters_Run1.yaml")
        if yaml_file.exists():
            sys.argv = ["pyptv_gui_ttk.py", str(yaml_file)]
            
            # Simulate the main function logic
            from pyptv.experiment_ttk import create_experiment_from_yaml
            
            arg_path = Path(sys.argv[1]).resolve()
            if arg_path.is_file() and arg_path.suffix in {".yaml", ".yml"}:
                exp = create_experiment_from_yaml(arg_path)
                print(f"✓ GUI initialization logic works with YAML file")
                print(f"✓ Experiment created with {exp.get_n_cam()} cameras")
        
        # Test 2: With directory
        test_dir = Path("tests/test_cavity")
        if test_dir.exists():
            sys.argv = ["pyptv_gui_ttk.py", str(test_dir)]
            
            from pyptv.experiment_ttk import create_experiment_from_directory
            
            arg_path = Path(sys.argv[1]).resolve()
            if arg_path.is_dir():
                exp = create_experiment_from_directory(arg_path)
                yaml_file = getattr(exp.pm, 'yaml_path', None)
                print(f"✓ GUI initialization logic works with directory")
                print(f"✓ Found/created YAML file: {yaml_file}")
        
        # Test 3: No arguments (default case)
        sys.argv = ["pyptv_gui_ttk.py"]
        software_path = Path.cwd().resolve()
        exp_path = software_path / "tests" / "test_cavity"
        if exp_path.exists():
            exp = create_experiment_from_directory(exp_path)
            yaml_file = getattr(exp.pm, 'yaml_path', None)
            print(f"✓ GUI initialization logic works with default case")
            print(f"✓ Default YAML file: {yaml_file}")
        
        sys.argv = original_argv
        
    except Exception as e:
        print(f"✗ Error testing GUI initialization logic: {e}")
        import traceback
        traceback.print_exc()
        sys.argv = original_argv

def test_error_handling():
    """Test error handling for various edge cases"""
    print("\n=== Testing error handling ===")
    
    try:
        from pyptv.experiment_ttk import create_experiment_from_directory, create_experiment_from_yaml
        
        # Test 1: Non-existent directory
        try:
            fake_dir = Path("/non/existent/directory")
            exp = create_experiment_from_directory(fake_dir)
            print(f"✗ Should have failed with non-existent directory")
        except Exception as e:
            print(f"✓ Correctly handled non-existent directory: {type(e).__name__}")
        
        # Test 2: Non-existent YAML file
        try:
            fake_yaml = Path("/non/existent/file.yaml")
            exp = create_experiment_from_yaml(fake_yaml)
            print(f"✗ Should have failed with non-existent YAML file")
        except Exception as e:
            print(f"✓ Correctly handled non-existent YAML file: {type(e).__name__}")
        
        # Test 3: Empty directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            try:
                exp = create_experiment_from_directory(temp_path)
                print(f"✓ Handled empty directory gracefully")
                print(f"✓ Created experiment with {exp.get_n_cam()} cameras")
            except Exception as e:
                print(f"✗ Failed to handle empty directory: {e}")
        
    except Exception as e:
        print(f"✗ Error in error handling tests: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Run all tests"""
    print("PyPTV TTK GUI Fix Tests")
    print("=" * 50)
    
    # Change to the correct directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    print(f"Working directory: {Path.cwd()}")
    
    # Run all tests
    test_yaml_file_argument()
    test_directory_argument()
    test_directory_without_yaml()
    test_parameter_loading()
    test_experiment_ttk_functionality()
    test_gui_initialization_logic()
    test_error_handling()
    
    print("\n" + "=" * 50)
    print("All tests completed!")

if __name__ == "__main__":
    main()