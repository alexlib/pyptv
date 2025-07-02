#!/usr/bin/env python3
"""
Test script to verify man_ori.dat migration to YAML.
"""
import sys
from pathlib import Path

# Add the package to the path
sys.path.insert(0, str(Path(__file__).parent))

from pyptv.experiment import Experiment

def test_man_ori_migration():
    """Test the migration of man_ori.dat to YAML."""
    print("Testing man_ori.dat migration to YAML...")
    
    # Use the test_cavity directory
    exp_path = Path("tests/test_cavity")
    
    if not exp_path.exists():
        print(f"Error: Test directory {exp_path} not found")
        return False
    
    print(f"Working with experiment path: {exp_path}")
    
    try:
        # Load the experiment - this should trigger migration if man_ori.dat exists
        experiment = Experiment()
        experiment.populate_runs(exp_path)
        
        # Check if migration was triggered
        man_ori_dat_path = exp_path / "man_ori.dat"
        if man_ori_dat_path.exists():
            print(f"Found man_ori.dat at {man_ori_dat_path}")
            
            # Read the original data
            with open(man_ori_dat_path, 'r') as f:
                original_lines = f.readlines()
            print(f"Original man_ori.dat has {len(original_lines)} lines")
            
            # Display first few lines
            print("First 4 lines of man_ori.dat:")
            for i, line in enumerate(original_lines[:4]):
                print(f"  Line {i+1}: {line.strip()}")
            
            # Check if YAML has the migrated data
            man_ori_coords = experiment.parameter_manager.parameters.get('man_ori_coordinates')
            if man_ori_coords:
                print("\nMigrated data found in YAML:")
                for cam_key, cam_data in man_ori_coords.items():
                    print(f"  {cam_key}:")
                    for point_key, point_data in cam_data.items():
                        print(f"    {point_key}: x={point_data['x']}, y={point_data['y']}")
            else:
                print("ERROR: No man_ori_coordinates found in YAML")
                return False
        else:
            print("No man_ori.dat found - checking if YAML already has the structure")
            man_ori_coords = experiment.parameter_manager.parameters.get('man_ori_coordinates')
            if man_ori_coords:
                print("YAML already has man_ori_coordinates structure:")
                for cam_key, cam_data in man_ori_coords.items():
                    print(f"  {cam_key}:")
                    for point_key, point_data in cam_data.items():
                        print(f"    {point_key}: x={point_data['x']}, y={point_data['y']}")
            else:
                print("No man_ori_coordinates found in YAML - should have defaults")
        
        # Test saving the updated parameters
        print("\nSaving parameters to YAML...")
        experiment.save_parameters()
        print("Parameters saved successfully")
        
        return True
        
    except Exception as e:
        print(f"Error during migration test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_man_ori_migration()
    if success:
        print("\n✓ man_ori.dat migration test completed successfully")
    else:
        print("\n✗ man_ori.dat migration test failed")
        sys.exit(1)
