#!/usr/bin/env python3
"""
Test script to debug py_detection_proc_c function issues
"""

import sys
import os
from pathlib import Path
import numpy as np
from skimage.io import imread
from skimage.color import rgb2gray
from skimage.util import img_as_ubyte

# Add the PyPTV path
sys.path.insert(0, str(Path(__file__).parent))

from pyptv.parameter_manager import ParameterManager
from pyptv.ptv import py_detection_proc_c, _populate_cpar, _populate_tpar, _read_calibrations

def load_test_data():
    """Load test data from test_cavity"""
    test_dir = Path("tests/test_cavity")
    yaml_file = test_dir / "parameters_Run1.yaml"
    
    if not yaml_file.exists():
        print(f"Error: {yaml_file} not found")
        return None, None, None
    
    # Change to test directory so relative paths work
    original_cwd = Path.cwd()
    os.chdir(test_dir)
    
    try:
        # Load parameters
        pm = ParameterManager()
        pm.from_yaml(Path("parameters_Run1.yaml"))
        
        # Get PTV and target parameters
        ptv_params = pm.get_parameter('ptv')
        targ_rec_params = pm.get_parameter('targ_rec')
        
        if ptv_params is None:
            print("Error: No ptv parameters found")
            return None, None, None
            
        if targ_rec_params is None:
            print("Error: No targ_rec parameters found")
            return None, None, None
        
        print("PTV parameters:", ptv_params)
        print("Target parameters:", targ_rec_params)
        
        # Load images
        images = []
        for i, img_name in enumerate(ptv_params['img_name']):
            img_path = Path(img_name)
            if img_path.exists():
                print(f"Loading image {i}: {img_path}")
                img = imread(img_path)
                if img.ndim > 2:
                    img = rgb2gray(img)
                img = img_as_ubyte(img)
                images.append(img)
                print(f"  Image shape: {img.shape}, dtype: {img.dtype}")
            else:
                print(f"Warning: Image {img_path} not found")
                # Create dummy image
                h_img = ptv_params['imx']
                v_img = ptv_params['imy']
                img = np.zeros((v_img, h_img), dtype=np.uint8)
                images.append(img)
                print(f"  Created dummy image: {img.shape}")
        
        return images, ptv_params, targ_rec_params
    
    finally:
        os.chdir(original_cwd)

def test_parameter_population():
    """Test individual parameter population functions"""
    print("\n=== Testing Parameter Population ===")
    
    # Load test data
    images, ptv_params, targ_rec_params = load_test_data()
    if images is None:
        return False
    
    n_cam = len(images)
    print(f"Number of cameras: {n_cam}")
    
    try:
        # Test cpar population
        print("\nTesting _populate_cpar...")
        cpar = _populate_cpar(ptv_params, n_cam)
        print(f"  Created ControlParams: {cpar}")
        print(f"  Image size: {cpar.get_image_size()}")
        print(f"  Pixel size: {cpar.get_pixel_size()}")
        print(f"  Number of cameras: {cpar.get_num_cams()}")
        
        # Test calibration base names
        for i in range(n_cam):
            base_name = cpar.get_cal_img_base_name(i)
            print(f"  Camera {i} calibration base: {base_name}")
            
            # Check if calibration files exist
            ori_file = base_name + ".ori"
            addpar_file = base_name + ".addpar"
            print(f"    Checking {ori_file}: {Path(ori_file).exists()}")
            print(f"    Checking {addpar_file}: {Path(addpar_file).exists()}")
        
        # Test tpar population
        print("\nTesting _populate_tpar...")
        target_params_dict = {'targ_rec': targ_rec_params}
        tpar = _populate_tpar(target_params_dict, n_cam)
        print(f"  Created TargetParams: {tpar}")
        print(f"  Grey thresholds: {tpar.get_grey_thresholds()}")
        print(f"  Pixel count bounds: {tpar.get_pixel_count_bounds()}")
        
        # Test calibration reading
        print("\nTesting _read_calibrations...")
        try:
            cals = _read_calibrations(cpar, n_cam)
            print(f"  Successfully read {len(cals)} calibrations")
            for i, cal in enumerate(cals):
                print(f"    Camera {i}: {cal}")
        except Exception as e:
            print(f"  Error reading calibrations: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"Error in parameter population: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_detection_function():
    """Test the py_detection_proc_c function"""
    print("\n=== Testing py_detection_proc_c ===")
    
    # Load test data
    images, ptv_params, targ_rec_params = load_test_data()
    if images is None:
        return False
    
    try:
        print("Calling py_detection_proc_c...")
        print(f"  Images: {len(images)} images")
        print(f"  PTV params keys: {list(ptv_params.keys())}")
        print(f"  Target params keys: {list(targ_rec_params.keys())}")
        
        # Create the target_params dict in the format expected by _populate_tpar
        target_params_dict = {'targ_rec': targ_rec_params}
        
        detections, corrected = py_detection_proc_c(
            images, 
            ptv_params, 
            target_params_dict
        )
        
        print(f"Detection successful!")
        print(f"  Detections: {len(detections)} camera sets")
        print(f"  Corrected: {len(corrected)} camera sets")
        
        for i, (det, corr) in enumerate(zip(detections, corrected)):
            print(f"  Camera {i}: {len(det)} targets detected")
            if len(det) > 0:
                print(f"    First target position: {det[0].pos()}")
            
        return True
        
    except Exception as e:
        print(f"Error in py_detection_proc_c: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_minimal_detection():
    """Test detection with minimal setup"""
    print("\n=== Testing Minimal Detection Setup ===")
    
    # Change to test_cavity directory to ensure relative paths work
    original_cwd = Path.cwd()
    test_dir = Path("tests/test_cavity")
    os.chdir(test_dir)
    
    try:
        # Load parameters
        yaml_file = "parameters_Run1.yaml"
        pm = ParameterManager()
        pm.from_yaml(Path(yaml_file))
        
        ptv_params = pm.get_parameter('ptv')
        targ_rec_params = pm.get_parameter('targ_rec')
        
        # Load just the first image for testing
        img_path = ptv_params['img_name'][0]
        print(f"Loading single image: {img_path}")
        
        if Path(img_path).exists():
            img = imread(img_path)
            if img.ndim > 2:
                img = rgb2gray(img)
            img = img_as_ubyte(img)
            print(f"Image loaded: shape={img.shape}, dtype={img.dtype}")
            
            # Try detection with single image
            images = [img]
            target_params_dict = {'targ_rec': targ_rec_params}
            
            detections, corrected = py_detection_proc_c(
                images, 
                ptv_params, 
                target_params_dict
            )
            
            print(f"Single image detection successful!")
            print(f"  Found {len(detections[0])} targets")
            
            return True
            
        else:
            print(f"Image {img_path} not found")
            return False
            
    except Exception as e:
        print(f"Error in minimal detection: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        os.chdir(original_cwd)

def main():
    """Run all tests"""
    print("=== PyPTV Detection Function Debug ===")
    
    # Test 1: Parameter population
    if not test_parameter_population():
        print("❌ Parameter population test failed")
        return
    else:
        print("✅ Parameter population test passed")
    
    # Test 2: Full detection function
    if not test_detection_function():
        print("❌ Detection function test failed")
        return
    else:
        print("✅ Detection function test passed")
    
    # Test 3: Minimal detection
    if not test_minimal_detection():
        print("❌ Minimal detection test failed")
        return
    else:
        print("✅ Minimal detection test passed")
    
    print("\n🎉 All tests passed!")

if __name__ == "__main__":
    main()
