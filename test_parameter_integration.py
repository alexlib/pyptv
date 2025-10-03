#!/usr/bin/env python3
"""
Test script for TTK parameter system integration

This script tests the complete parameter management system:
1. ExperimentTTK class functionality
2. Parameter GUI dialogs
3. Parameter synchronization between GUI and YAML files
4. Integration with main TTK GUI
"""

import sys
import tempfile
from pathlib import Path
import yaml

# Add pyptv to path
sys.path.insert(0, str(Path(__file__).parent / 'pyptv'))

try:
    from pyptv.parameter_manager import ParameterManager
    from pyptv.experiment_ttk import ExperimentTTK, create_experiment_from_yaml
    from pyptv.parameter_gui_ttk import MainParamsWindow, CalibParamsWindow, TrackingParamsWindow
    print("✓ Successfully imported TTK parameter system components")
except ImportError as e:
    print(f"✗ Failed to import TTK components: {e}")
    sys.exit(1)

def create_test_yaml():
    """Create a test YAML file with sample parameters"""
    test_params = {
        'ptv': {
            'splitter': False,
            'allcam_flag': True,
            'hp_flag': False,
            'mmp_n1': 1.0,
            'mmp_n2': 1.5,
            'mmp_n3': 1.33,
            'mmp_d': 5.0,
            'img_name': ['cam1.tif', 'cam2.tif', 'cam3.tif', 'cam4.tif'],
            'img_cal': ['cal1.tif', 'cal2.tif', 'cal3.tif', 'cal4.tif']
        },
        'targ_rec': {
            'gvthres': [100, 100, 100, 100],
            'nnmin': 1,
            'nnmax': 100,
            'sumg_min': 10,
            'disco': 5,
            'cr_sz': 3
        },
        'pft_version': {
            'mask_flag': False,
            'existing_target': False,
            'mask_base_name': 'mask'
        },
        'sequence': {
            'first': 1,
            'last': 100,
            'base_name': ['seq1', 'seq2', 'seq3', 'seq4']
        },
        'volume': {
            'xmin': -50.0,
            'xmax': 50.0,
            'zmin1': -50.0,
            'zmin2': -50.0
        },
        'criteria': {
            'cnx': 0.5,
            'cny': 0.5,
            'cn': 0.5,
            'csumg': 100,
            'corrmin': 0.7,
            'eps0': 0.1
        },
        'cal_ori': {
            'fixp_x': 0.0,
            'fixp_y': 0.0,
            'fixp_z': 0.0
        },
        'man_ori': {
            'cam_0': {'x0': 0.0, 'y0': 0.0},
            'cam_1': {'x0': 100.0, 'y0': 0.0},
            'cam_2': {'x0': 0.0, 'y0': 100.0},
            'cam_3': {'x0': 100.0, 'y0': 100.0}
        },
        'tracking': {
            'dvxmin': -10.0,
            'dvxmax': 10.0,
            'daxmin': -1.0,
            'daxmax': 1.0,
            'angle_acc': 0.1
        },
        'examine': {
            'post_flag': True
        },
        'num_cams': 4
    }
    
    # Create temporary YAML file
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
    yaml.dump(test_params, temp_file, default_flow_style=False)
    temp_file.close()
    
    return Path(temp_file.name)

def test_experiment_ttk():
    """Test ExperimentTTK functionality"""
    print("\n=== Testing ExperimentTTK ===")
    
    # Create test YAML file
    yaml_file = create_test_yaml()
    print(f"✓ Created test YAML file: {yaml_file}")
    
    try:
        # Test creating experiment from YAML
        experiment = create_experiment_from_yaml(yaml_file)
        print("✓ Created ExperimentTTK from YAML")
        
        # Test parameter access
        num_cams = experiment.get_n_cam()
        print(f"✓ Number of cameras: {num_cams}")
        
        ptv_params = experiment.get_parameter('ptv')
        print(f"✓ PTV parameters loaded: {len(ptv_params)} keys")
        
        # Test parameter modification
        experiment.set_parameter('test_param', 'test_value')
        test_value = experiment.get_parameter('test_param')
        assert test_value == 'test_value', "Parameter setting/getting failed"
        print("✓ Parameter setting/getting works")
        
        # Test nested parameter access
        mmp_n1 = experiment.get_parameter_nested('ptv', 'mmp_n1')
        print(f"✓ Nested parameter access: mmp_n1 = {mmp_n1}")
        
        # Test parameter updates
        updates = {'ptv': {'mmp_n1': 1.1}}
        experiment.update_parameters(updates)
        new_mmp_n1 = experiment.get_parameter_nested('ptv', 'mmp_n1')
        assert new_mmp_n1 == 1.1, "Parameter update failed"
        print("✓ Parameter updates work")
        
        # Test saving parameters
        experiment.save_parameters()
        print("✓ Parameter saving works")
        
        return experiment, yaml_file
        
    except Exception as e:
        print(f"✗ ExperimentTTK test failed: {e}")
        return None, yaml_file

def test_parameter_gui_creation(experiment):
    """Test parameter GUI creation (without showing them)"""
    print("\n=== Testing Parameter GUI Creation ===")
    
    if not experiment:
        print("✗ Cannot test GUIs without valid experiment")
        return False
    
    try:
        # Test creating parameter windows (but don't show them)
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()  # Hide the root window
        
        # Test MainParamsWindow
        main_window = MainParamsWindow(root, experiment)
        main_window.withdraw()  # Hide the window
        print("✓ MainParamsWindow created successfully")
        
        # Test CalibParamsWindow
        calib_window = CalibParamsWindow(root, experiment)
        calib_window.withdraw()  # Hide the window
        print("✓ CalibParamsWindow created successfully")
        
        # Test TrackingParamsWindow
        tracking_window = TrackingParamsWindow(root, experiment)
        tracking_window.withdraw()  # Hide the window
        print("✓ TrackingParamsWindow created successfully")
        
        # Test parameter loading
        main_window.load_values()
        print("✓ Parameter loading works")
        
        # Test parameter saving (without actually saving to file)
        original_save = experiment.save_parameters
        experiment.save_parameters = lambda: None  # Mock save method
        
        main_window.save_values()
        print("✓ Parameter saving works")
        
        # Restore original save method
        experiment.save_parameters = original_save
        
        # Clean up
        main_window.destroy()
        calib_window.destroy()
        tracking_window.destroy()
        root.destroy()
        
        return True
        
    except Exception as e:
        print(f"✗ Parameter GUI test failed: {e}")
        return False

def test_parameter_synchronization(experiment, yaml_file):
    """Test parameter synchronization between GUI and YAML"""
    print("\n=== Testing Parameter Synchronization ===")
    
    if not experiment:
        print("✗ Cannot test synchronization without valid experiment")
        return False
    
    try:
        # Modify parameters through experiment
        original_mmp_n1 = experiment.get_parameter_nested('ptv', 'mmp_n1')
        new_mmp_n1 = original_mmp_n1 + 0.5
        
        experiment.update_parameter_nested('ptv', 'mmp_n1', new_mmp_n1)
        print(f"✓ Updated mmp_n1 from {original_mmp_n1} to {new_mmp_n1}")
        
        # Save to YAML
        experiment.save_parameters(yaml_file)
        print("✓ Saved parameters to YAML")
        
        # Create new experiment from saved YAML
        new_experiment = create_experiment_from_yaml(yaml_file)
        loaded_mmp_n1 = new_experiment.get_parameter_nested('ptv', 'mmp_n1')
        
        assert loaded_mmp_n1 == new_mmp_n1, f"Synchronization failed: expected {new_mmp_n1}, got {loaded_mmp_n1}"
        print("✓ Parameter synchronization works correctly")
        
        return True
        
    except Exception as e:
        print(f"✗ Parameter synchronization test failed: {e}")
        return False

def test_main_gui_integration():
    """Test integration with main TTK GUI"""
    print("\n=== Testing Main GUI Integration ===")
    
    try:
        from pyptv.pyptv_gui_ttk import EnhancedMainApp
        print("✓ Successfully imported EnhancedMainApp")
        
        # Test creating GUI without showing it
        import tkinter as tk
        
        # Create test experiment
        yaml_file = create_test_yaml()
        experiment = create_experiment_from_yaml(yaml_file)
        
        # Create main app (but don't show it)
        app = EnhancedMainApp(experiment=experiment, yaml_file=yaml_file)
        app.withdraw()  # Hide the window
        print("✓ EnhancedMainApp created with experiment")
        
        # Test that experiment is properly connected
        assert app.experiment is not None, "Experiment not connected to main app"
        assert app.experiment.get_n_cam() == 4, "Camera count not correct"
        print("✓ Experiment properly connected to main GUI")
        
        # Clean up
        app.destroy()
        yaml_file.unlink()  # Delete temp file
        
        return True
        
    except Exception as e:
        print(f"✗ Main GUI integration test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("PyPTV TTK Parameter System Integration Test")
    print("=" * 50)
    
    # Test ExperimentTTK
    experiment, yaml_file = test_experiment_ttk()
    
    # Test parameter GUI creation
    gui_success = test_parameter_gui_creation(experiment)
    
    # Test parameter synchronization
    sync_success = test_parameter_synchronization(experiment, yaml_file)
    
    # Test main GUI integration
    main_gui_success = test_main_gui_integration()
    
    # Clean up
    if yaml_file and yaml_file.exists():
        yaml_file.unlink()
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY:")
    print(f"ExperimentTTK: {'✓ PASS' if experiment else '✗ FAIL'}")
    print(f"Parameter GUIs: {'✓ PASS' if gui_success else '✗ FAIL'}")
    print(f"Parameter Sync: {'✓ PASS' if sync_success else '✗ FAIL'}")
    print(f"Main GUI Integration: {'✓ PASS' if main_gui_success else '✗ FAIL'}")
    
    all_passed = all([experiment, gui_success, sync_success, main_gui_success])
    print(f"\nOVERALL: {'✓ ALL TESTS PASSED' if all_passed else '✗ SOME TESTS FAILED'}")
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())