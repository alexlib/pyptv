#!/usr/bin/env python
"""
Performance test for parameter access patterns
"""

import sys
import time
from pathlib import Path

# Add pyptv to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pyptv.experiment import Experiment
from pyptv.parameter_manager import ParameterManager


def test_parameter_access_performance():
    """Test different parameter access patterns for performance"""
    
    # Setup experiment with test_cavity data
    test_cavity_path = Path(__file__).parent / "test_cavity"
    if not test_cavity_path.exists():
        print("Test cavity not found, skipping performance test")
        return
    
    import os
    original_cwd = Path.cwd()
    os.chdir(test_cavity_path)
    
    try:
        print("=== PARAMETER ACCESS PERFORMANCE TEST ===")
        
        # Initialize experiment
        experiment = Experiment()
        experiment.populate_runs(test_cavity_path)
        
        # Test 1: Direct parameter manager access
        print("\n1. Testing direct ParameterManager access...")
        pm = experiment.parameter_manager
        
        start_time = time.time()
        for i in range(1000):
            ptv_params = pm.get_parameter('ptv')
            n_cam = ptv_params.get('n_cam', 4)
            img_names = ptv_params.get('img_name', [])
        direct_time = time.time() - start_time
        print(f"Direct access (1000 iterations): {direct_time:.4f} seconds")
        
        # Test 2: Via Experiment delegation
        print("\n2. Testing Experiment delegation...")
        
        start_time = time.time()
        for i in range(1000):
            ptv_params = experiment.get_parameter('ptv')
            n_cam = ptv_params.get('n_cam', 4)
            img_names = ptv_params.get('img_name', [])
        delegation_time = time.time() - start_time
        print(f"Experiment delegation (1000 iterations): {delegation_time:.4f} seconds")
        
        # Test 3: Cached access (storing reference)
        print("\n3. Testing cached parameter access...")
        cached_ptv_params = experiment.get_parameter('ptv')
        
        start_time = time.time()
        for i in range(1000):
            n_cam = cached_ptv_params.get('n_cam', 4)
            img_names = cached_ptv_params.get('img_name', [])
        cached_time = time.time() - start_time
        print(f"Cached access (1000 iterations): {cached_time:.4f} seconds")
        
        # Test 4: File I/O performance
        print("\n4. Testing file I/O performance...")
        yaml_path = experiment.active_params.yaml_path
        
        start_time = time.time()
        for i in range(10):  # Fewer iterations for I/O
            pm_temp = ParameterManager()
            pm_temp.from_yaml(yaml_path)
            ptv_params = pm_temp.get_parameter('ptv')
        io_time = time.time() - start_time
        print(f"File I/O reload (10 iterations): {io_time:.4f} seconds")
        
        # Test 5: Memory usage estimation
        print("\n5. Memory usage analysis...")
        import sys
        
        # Size of parameter manager
        pm_size = sys.getsizeof(pm.parameters)
        print(f"ParameterManager parameters dict size: {pm_size} bytes")
        
        # Size of individual parameter groups
        for param_name, param_data in pm.parameters.items():
            param_size = sys.getsizeof(param_data)
            print(f"  {param_name}: {param_size} bytes")
        
        print("\n=== PERFORMANCE SUMMARY ===")
        print(f"Direct access:        {direct_time:.4f}s")
        print(f"Experiment delegation: {delegation_time:.4f}s ({delegation_time/direct_time:.2f}x slower)")
        print(f"Cached access:        {cached_time:.4f}s ({cached_time/direct_time:.2f}x slower)")
        print(f"File I/O per reload:  {io_time/10:.4f}s ({(io_time/10)/direct_time*1000:.0f}x slower)")
        
        return {
            'direct': direct_time,
            'delegation': delegation_time,
            'cached': cached_time,
            'io_per_reload': io_time/10,
            'memory_total': pm_size
        }
        
    finally:
        os.chdir(original_cwd)


def test_parameter_change_scenarios():
    """Test different scenarios for parameter changes"""
    
    test_cavity_path = Path(__file__).parent / "test_cavity"
    if not test_cavity_path.exists():
        print("Test cavity not found, skipping change scenarios test")
        return
    
    import os
    original_cwd = Path.cwd()
    os.chdir(test_cavity_path)
    
    try:
        print("\n=== PARAMETER CHANGE SCENARIOS ===")
        
        experiment = Experiment()
        experiment.populate_runs(test_cavity_path)
        
        # Scenario 1: GUI parameter change
        print("\n1. GUI parameter change simulation...")
        original_n_cam = experiment.get_parameter('ptv').get('n_cam')
        print(f"Original n_cam: {original_n_cam}")
        
        # Simulate changing n_cam in GUI - using the GLOBAL n_cam only
        experiment.parameter_manager.set_n_cam(6)  # Update global n_cam
        assert experiment.get_n_cam() == 6
        
        new_n_cam = experiment.get_n_cam()  # Get from global, not from ptv section
        print(f"After GUI change: {new_n_cam}")
        
        # Scenario 2: Save changes
        print("\n2. Saving changes to file...")
        experiment.save_parameters()
        
        # Scenario 3: Reload from file (simulating manual file edit)
        print("\n3. Reloading from file...")
        experiment.load_parameters_for_active()
        reloaded_n_cam = experiment.get_n_cam()  # Get from global, not from ptv section
        print(f"After reload: {reloaded_n_cam}")
        
        # Scenario 4: File modification detection
        print("\n4. File modification detection...")
        yaml_path = experiment.active_params.yaml_path
        file_mtime = yaml_path.stat().st_mtime
        print(f"File modification time: {file_mtime}")
        
        return {
            'original_n_cam': original_n_cam,
            'changed_n_cam': new_n_cam,
            'reloaded_n_cam': reloaded_n_cam,
            'file_mtime': file_mtime
        }
        
    finally:
        os.chdir(original_cwd)


if __name__ == "__main__":
    perf_results = test_parameter_access_performance()
    change_results = test_parameter_change_scenarios()
    
    print("\n=== RECOMMENDATIONS ===")
    if perf_results:
        if perf_results['delegation'] < perf_results['direct'] * 1.1:
            print("✓ Experiment delegation has negligible overhead - RECOMMENDED")
        else:
            print("⚠ Experiment delegation has significant overhead - consider caching")
        
        if perf_results['cached'] < perf_results['direct'] * 0.1:
            print("✓ Caching provides excellent performance - RECOMMENDED for frequently accessed params")
        
        if perf_results['io_per_reload'] > 0.001:
            print("⚠ File I/O is expensive - avoid frequent reloads")
        else:
            print("✓ File I/O is fast enough for occasional reloads")
