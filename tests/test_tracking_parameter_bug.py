#!/usr/bin/env python3
"""Test to debug tracking parameter translation bug in test_cavity."""

import pytest
import os
from pathlib import Path
from pyptv.ptv import py_start_proc_c
from pyptv.parameter_manager import ParameterManager


class TestTrackingParameterBug:
    """Test class to debug tracking parameter translation issues."""
    
    def test_cavity_tracking_parameter_translation(self):
        """Test tracking parameter translation in test_cavity to debug poor tracking performance."""
        
        # Load test_cavity parameters
        test_cavity_path = Path(__file__).parent / "test_cavity"
        param_file = test_cavity_path / "parameters_Run1.yaml"
        
        if not param_file.exists():
            pytest.skip(f"Parameter file not found: {param_file}")
        
        print(f"\n=== Loading parameters from: {param_file} ===")
        
        # Change to test_cavity directory (required for relative paths)
        original_cwd = Path.cwd()
        os.chdir(test_cavity_path)
        
        try:
            # Create parameter manager
            pm = ParameterManager()
            pm.from_yaml(param_file)
            
            print("\n=== Raw YAML tracking parameters ===")
            track_params = pm.parameters.get('track', {})
            for key, value in track_params.items():
                print(f"  {key}: {value}")
            
            # Check if parameters seem reasonable
            assert 'dvxmin' in track_params, "dvxmin missing from tracking parameters"
            assert 'dvxmax' in track_params, "dvxmax missing from tracking parameters"
            assert 'dvymin' in track_params, "dvymin missing from tracking parameters"
            assert 'dvymax' in track_params, "dvymax missing from tracking parameters"
            assert 'dvzmin' in track_params, "dvzmin missing from tracking parameters"
            assert 'dvzmax' in track_params, "dvzmax missing from tracking parameters"
            assert 'angle' in track_params, "angle missing from tracking parameters"
            assert 'dacc' in track_params, "dacc missing from tracking parameters"
            
            # Load and translate parameters through py_start_proc_c
            print("\n=== Loading parameters through py_start_proc_c ===")
            cpar, spar, vpar, track_par, tpar, cals, epar = py_start_proc_c(pm)
            
            print("\n=== Translated TrackingParams values ===")
            translated_params = {
                'dvxmin': track_par.get_dvxmin(),
                'dvxmax': track_par.get_dvxmax(),
                'dvymin': track_par.get_dvymin(),
                'dvymax': track_par.get_dvymax(),
                'dvzmin': track_par.get_dvzmin(),
                'dvzmax': track_par.get_dvzmax(),
                'dangle': track_par.get_dangle(),
                'dacc': track_par.get_dacc(),
                'add': track_par.get_add()
            }
            
            for key, value in translated_params.items():
                print(f"  {key}: {value}")
            
            print("\n=== Checking parameter consistency ===")
            
            # Check if YAML parameters match translated parameters
            yaml_to_cython_mapping = {
                'dvxmin': 'dvxmin',
                'dvxmax': 'dvxmax', 
                'dvymin': 'dvymin',
                'dvymax': 'dvymax',
                'dvzmin': 'dvzmin',
                'dvzmax': 'dvzmax',
                'angle': 'dangle',
                'dacc': 'dacc'
            }
            
            mismatches = []
            for yaml_key, cython_key in yaml_to_cython_mapping.items():
                yaml_val = track_params[yaml_key]
                cython_val = translated_params[cython_key]
                
                if abs(yaml_val - cython_val) > 1e-6:  # Allow for small floating point differences
                    mismatches.append(f"{yaml_key}: YAML={yaml_val} vs Cython={cython_val}")
                    print(f"  MISMATCH {yaml_key}: YAML={yaml_val} vs Cython={cython_val}")
                else:
                    print(f"  OK {yaml_key}: {yaml_val}")
            
            # Check for unreasonable parameter values that might cause poor tracking
            print("\n=== Checking for unreasonable parameter values ===")
            warnings = []
            
            # Check velocity bounds
            vel_range_x = translated_params['dvxmax'] - translated_params['dvxmin']
            vel_range_y = translated_params['dvymax'] - translated_params['dvymin']
            vel_range_z = translated_params['dvzmax'] - translated_params['dvzmin']
            
            print(f"  Velocity range X: {vel_range_x} (min: {translated_params['dvxmin']}, max: {translated_params['dvxmax']})")
            print(f"  Velocity range Y: {vel_range_y} (min: {translated_params['dvymin']}, max: {translated_params['dvymax']})")
            print(f"  Velocity range Z: {vel_range_z} (min: {translated_params['dvzmin']}, max: {translated_params['dvzmax']})")
            
            # Warn about very restrictive velocity bounds
            if vel_range_x < 5:
                warnings.append(f"Very restrictive X velocity range: {vel_range_x}")
            if vel_range_y < 5:
                warnings.append(f"Very restrictive Y velocity range: {vel_range_y}")
            if vel_range_z < 5:
                warnings.append(f"Very restrictive Z velocity range: {vel_range_z}")
            
            # Check angle parameter
            angle_val = translated_params['dangle']
            print(f"  Angle parameter: {angle_val}")
            if angle_val > 180:
                warnings.append(f"Very large angle parameter: {angle_val} (typical values are 0-180)")
            
            # Check acceleration parameter
            dacc_val = translated_params['dacc']
            print(f"  Acceleration parameter: {dacc_val}")
            if dacc_val < 1:
                warnings.append(f"Very small acceleration parameter: {dacc_val}")
            
            print("\n=== Analysis Results ===")
            if mismatches:
                print("❌ PARAMETER TRANSLATION MISMATCHES FOUND:")
                for mismatch in mismatches:
                    print(f"   {mismatch}")
                # Don't fail the test, just report the issue
                print("   This could explain poor tracking performance!")
            else:
                print("✅ All parameters translated correctly from YAML to Cython")
            
            if warnings:
                print("\n⚠️  POTENTIALLY PROBLEMATIC PARAMETER VALUES:")
                for warning in warnings:
                    print(f"   {warning}")
                print("   These values might explain poor tracking performance")
            else:
                print("\n✅ All parameter values seem reasonable")
            
            print(f"\n=== Parameter translation test completed ===")
            
            # Return the parameters for potential further analysis
            return {
                'yaml_params': track_params,
                'translated_params': translated_params,
                'mismatches': mismatches,
                'warnings': warnings
            }
            
        finally:
            os.chdir(original_cwd)
    
    def test_splitter_tracking_parameter_translation(self):
        """Test tracking parameter translation in test_splitter for comparison."""
        
        test_splitter_path = Path(__file__).parent / "test_splitter"
        param_file = test_splitter_path / "parameters_Run1.yaml"
        
        if not param_file.exists():
            pytest.skip(f"Parameter file not found: {param_file}")
        
        print(f"\n=== COMPARISON: Loading test_splitter parameters ===")
        
        original_cwd = Path.cwd()
        os.chdir(test_splitter_path)
        
        try:
            pm = ParameterManager()
            pm.from_yaml(param_file)
            
            track_params = pm.parameters.get('track', {})
            print("\n=== test_splitter tracking parameters ===")
            for key, value in track_params.items():
                print(f"  {key}: {value}")
            
            # Load and translate parameters
            cpar, spar, vpar, track_par, tpar, cals, epar = py_start_proc_c(pm)
            
            translated_params = {
                'dvxmin': track_par.get_dvxmin(),
                'dvxmax': track_par.get_dvxmax(),
                'dvymin': track_par.get_dvymin(),
                'dvymax': track_par.get_dvymax(),
                'dvzmin': track_par.get_dvzmin(),
                'dvzmax': track_par.get_dvzmax(),
                'dangle': track_par.get_dangle(),
                'dacc': track_par.get_dacc(),
                'add': track_par.get_add()
            }
            
            print("\n=== test_splitter translated values ===")
            for key, value in translated_params.items():
                print(f"  {key}: {value}")
            
            vel_range_x = translated_params['dvxmax'] - translated_params['dvxmin']
            vel_range_y = translated_params['dvymax'] - translated_params['dvymin'] 
            vel_range_z = translated_params['dvzmax'] - translated_params['dvzmin']
            
            print(f"\n=== test_splitter velocity ranges ===")
            print(f"  X range: {vel_range_x}")
            print(f"  Y range: {vel_range_y}")
            print(f"  Z range: {vel_range_z}")
            
        finally:
            os.chdir(original_cwd)
    
    def test_parameter_comparison(self):
        """Compare parameters between test_cavity and test_splitter to identify differences."""
        
        print("\n=== COMPARATIVE ANALYSIS ===")
        
        # This test will run after the other two and compare their results
        # For now, just run both and let the user compare the output
        cavity_result = self.test_cavity_tracking_parameter_translation()
        splitter_result = self.test_splitter_tracking_parameter_translation()
        
        print("\n=== COMPARISON COMPLETE ===")
        print("Review the output above to identify differences between test_cavity and test_splitter")
        print("Look for:")
        print("  1. Parameter translation mismatches")
        print("  2. Unreasonable parameter values")
        print("  3. Differences in velocity ranges between the two test cases")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
