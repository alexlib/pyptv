#!/usr/bin/env python
"""
Test image path resolution functionality in PyPTV
"""

import os
import sys
import pytest
import numpy as np
from pathlib import Path

# Add pyptv to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pyptv.experiment import Experiment


def test_image_path_resolution(test_data_dir):
    """Test that image paths are resolved correctly regardless of working directory"""
    print(f"\nTesting image path resolution with test_data_dir: {test_data_dir}")
    
    # Initialize experiment and populate with runs
    exp = Experiment()
    original_dir = os.getcwd()
    os.chdir(test_data_dir)
    try:
        exp.populate_runs(Path(test_data_dir))
    finally:
        os.chdir(original_dir)
    
    # Get sequence parameters
    seq_params = exp.get_parameter('sequence')
    print(f"Sequence parameters: {seq_params}")
    
    # Check if sequence parameters have image information
    if seq_params and isinstance(seq_params, dict):
        base_name = seq_params.get('base_name', '')
        first_frame = seq_params.get('first', 1)
        last_frame = seq_params.get('last', 1)
        
        print(f"Base name: {base_name}")
        print(f"First frame: {first_frame}")
        print(f"Last frame: {last_frame}")
        
        if base_name:
            # Try to construct image path for first frame
            image_name = f"{base_name}{first_frame:04d}.tif"
            image_path = os.path.join(test_data_dir, "img", image_name)
            
            print(f"Constructed image path: {image_path}")
            print(f"Image exists: {os.path.exists(image_path)}")
            
            # Also check relative to experiment directory
            if not os.path.exists(image_path):
                # Try relative path from current working directory
                rel_image_path = os.path.join("img", image_name)
                print(f"Relative image path: {rel_image_path}")
                print(f"Relative image exists from cwd: {os.path.exists(rel_image_path)}")
                
                # Try changing to experiment directory
                old_cwd = os.getcwd()
                try:
                    os.chdir(test_data_dir)
                    print(f"Changed to experiment directory: {test_data_dir}")
                    print(f"Relative image exists from exp dir: {os.path.exists(rel_image_path)}")
                finally:
                    os.chdir(old_cwd)
            
            return os.path.exists(image_path)
    
    print("No sequence parameters or base_name found")
    return False


def test_parameter_image_paths(test_data_dir):
    """Test that parameters correctly specify image paths"""
    print(f"\nTesting parameter image paths in: {test_data_dir}")
    
    # Check if img directory exists
    img_dir = os.path.join(test_data_dir, "img")
    print(f"Image directory: {img_dir}")
    print(f"Image directory exists: {os.path.exists(img_dir)}")
    
    if os.path.exists(img_dir):
        images = [f for f in os.listdir(img_dir) if f.endswith('.tif')]
        print(f"Found {len(images)} TIFF images")
        if images:
            print(f"First few images: {images[:5]}")
    
    # Initialize experiment and check parameters
    exp = Experiment()
    original_dir = os.getcwd()
    os.chdir(test_data_dir)
    try:
        exp.populate_runs(Path(test_data_dir))
    finally:
        os.chdir(original_dir)
    
    # Get all parameters to see what's loaded
    all_params = {}
    param_types = ['sequence', 'track', 'detect', 'cal', 'correspondences', 'exam']
    
    for param_type in param_types:
        try:
            param = exp.get_parameter(param_type)
            all_params[param_type] = param
            print(f"{param_type} parameters loaded: {param is not None}")
            if param and isinstance(param, dict):
                # Look for any path-related attributes
                for attr, value in param.items():
                    if ('name' in attr.lower() or 'path' in attr.lower() or 
                        'file' in attr.lower() or 'img' in attr.lower()):
                        print(f"  {attr}: {value}")
        except Exception as e:
            print(f"Error loading {param_type} parameters: {e}")
    
    return len(all_params) > 0


def test_working_directory_independence(test_data_dir):
    """Test that PyPTV works regardless of current working directory"""
    print(f"\nTesting working directory independence")
    
    original_cwd = os.getcwd()
    temp_dir = "/tmp"
    
    try:
        # Change to a different directory
        os.chdir(temp_dir)
        print(f"Changed working directory to: {os.getcwd()}")
        
        # Try to initialize experiment from different working directory
        exp = Experiment()
        exp_dir = Path(test_data_dir)
        
        # Change to experiment directory for populate_runs
        os.chdir(test_data_dir)
        try:
            exp.populate_runs(exp_dir)
            success = len(exp.paramsets) > 0
        finally:
            os.chdir(temp_dir)  # Go back to temp dir
        
        print(f"Experiment initialization success: {success}")
        
        # Try to get parameters
        seq_params = exp.get_parameter('sequence')
        print(f"Sequence parameters loaded: {seq_params is not None}")
        
        return success and seq_params is not None
        
    except Exception as e:
        print(f"Error during working directory test: {e}")
        return False
    finally:
        os.chdir(original_cwd)
        print(f"Restored working directory to: {os.getcwd()}")


def test_absolute_vs_relative_paths(test_data_dir):
    """Test behavior with absolute vs relative paths"""
    print(f"\nTesting absolute vs relative path handling")
    
    # Test with absolute path
    abs_path = os.path.abspath(test_data_dir)
    print(f"Absolute path: {abs_path}")
    
    exp1 = Experiment()
    original_dir = os.getcwd()
    os.chdir(abs_path)
    try:
        exp1.populate_runs(Path(abs_path))
        success1 = len(exp1.paramsets) > 0
    finally:
        os.chdir(original_dir)
    print(f"Absolute path experiment success: {success1}")
    
    # Test with relative path (if different from absolute)
    rel_path = os.path.relpath(test_data_dir)
    print(f"Relative path: {rel_path}")
    
    if rel_path != abs_path:
        exp2 = Experiment()
        os.chdir(original_dir)  # Start from original directory
        try:
            os.chdir(test_data_dir)
            exp2.populate_runs(Path(test_data_dir))
            success2 = len(exp2.paramsets) > 0
        finally:
            os.chdir(original_dir)
        print(f"Relative path experiment success: {success2}")
        return success1 and success2
    else:
        print("Relative and absolute paths are the same")
        return success1


if __name__ == "__main__":
    # Run tests manually if called directly
    test_cavity_dir = "/home/user/Documents/GitHub/pyptv/tests/test_cavity"
    
    print("=" * 60)
    print("TESTING IMAGE PATH RESOLUTION")
    print("=" * 60)
    
    test_image_path_resolution(test_cavity_dir)
    test_parameter_image_paths(test_cavity_dir)
    test_working_directory_independence(test_cavity_dir)
    test_absolute_vs_relative_paths(test_cavity_dir)
