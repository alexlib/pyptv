#!/usr/bin/env python3
"""
Simple test to verify the detection fix
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
from pyptv.ptv import py_detection_proc_c

def test_detection_with_correct_format():
    """Test detection with the correct parameter format"""
    
    # Change to test_cavity directory
    original_cwd = Path.cwd()
    test_dir = Path(__file__).parent.parent / "tests" / "test_cavity"
    
    # If we're already in test_cavity, don't change
    if original_cwd.name == "test_cavity":
        test_dir = original_cwd
    
    print(f"Test directory: {test_dir}")
    os.chdir(test_dir)
    
    try:
        print("Loading parameters...")
        pm = ParameterManager()
        pm.from_yaml(Path("parameters_Run1.yaml"))
        
        ptv_params = pm.get_parameter('ptv')
        targ_rec_params = pm.get_parameter('targ_rec')
        
        if ptv_params is None:
            raise ValueError("Could not load ptv parameters")
        if targ_rec_params is None:
            raise ValueError("Could not load targ_rec parameters")
        
        print(f"PTV params type: {type(ptv_params)}")
        print(f"Target params type: {type(targ_rec_params)}")
        print(f"Number of cameras: {len(ptv_params['img_name'])}")
        
        # Load all images as required by the function
        images = []
        for img_path in ptv_params['img_name']:
            print(f"Loading image: {img_path}")
            img = imread(img_path)
            if img.ndim > 2:
                img = rgb2gray(img)
            img = img_as_ubyte(img)
            images.append(img)
        
        # Format correctly - this is the fix!
        target_params = {'targ_rec': targ_rec_params}
        
        print("Calling py_detection_proc_c with correct format...")
        detections, corrected = py_detection_proc_c(
            images, 
            ptv_params, 
            target_params
        )
        
        print(f"✅ Detection successful!")
        print(f"   Processed {len(detections)} cameras")
        for i, det in enumerate(detections):
            print(f"   Camera {i}: Found {len(det)} targets")
        
            if len(det) > 0:
                first_target = det[0]
                print(f"      First target at: {first_target.pos()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Detection failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        os.chdir(original_cwd)
        print("Restored original working directory.")

if __name__ == "__main__":
    print("=== Testing Detection Parameter Format Fix ===")
    if test_detection_with_correct_format():
        print("🎉 Test passed! The parameter format fix works.")
    else:
        print("💥 Test failed!")
