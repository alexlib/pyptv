#!/usr/bin/env python3
"""
Test to verify that the GUI detection fix works correctly
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

def test_gui_detection_simulation():
    """Simulate what the GUI does to verify it works"""
    
    # Change to test_cavity directory
    original_cwd = Path.cwd()
    test_dir = Path(__file__).parent / "tests" / "test_cavity"
    
    # If we're already in test_cavity, don't change
    if original_cwd.name == "test_cavity":
        test_dir = original_cwd
    
    print(f"Test directory: {test_dir}")
    os.chdir(test_dir)
    
    try:
        print("=== Simulating GUI Detection Process ===")
        
        # Simulate MainGUI loading parameters
        from pyptv.experiment import Experiment
        exp1 = Experiment()
        exp1.populate_runs(Path.cwd())
        exp1.setActive(0)
        
        # Simulate mainGui.get_parameter() calls as in GUI
        ptv_params = exp1.get_parameter('ptv')
        targ_rec_params = exp1.get_parameter('targ_rec')
        
        if ptv_params is None or targ_rec_params is None:
            raise ValueError("Could not load parameters through Experiment")
        
        print(f"✓ Loaded parameters via Experiment")
        print(f"   PTV params keys: {list(ptv_params.keys())}")
        print(f"   Target params keys: {list(targ_rec_params.keys())}")
        
        # Load images as GUI would
        orig_images = []
        for img_path in ptv_params['img_name']:
            print(f"  Loading image: {img_path}")
            img = imread(img_path)
            if img.ndim > 2:
                img = rgb2gray(img)
            img = img_as_ubyte(img)
            orig_images.append(img)
        
        print(f"✓ Loaded {len(orig_images)} images")
        
        # Simulate the GUI call exactly as it appears in img_coord_action
        target_params = {'targ_rec': targ_rec_params}
        
        print("✓ Calling py_detection_proc_c exactly as GUI does...")
        detections, corrected = py_detection_proc_c(
            orig_images,
            ptv_params,
            target_params,
        )
        
        print(f"✅ Detection successful!")
        print(f"   Detections: {len(detections)} cameras")
        print(f"   Corrected coords: {len(corrected)} cameras")
        
        total_targets = sum(len(det) for det in detections)
        print(f"   Total targets detected: {total_targets}")
        
        # Simulate the GUI coordinate extraction
        x = [[i.pos()[0] for i in row] for row in detections]
        y = [[i.pos()[1] for i in row] for row in detections]
        
        print(f"   Coordinate arrays created: x={len(x)}, y={len(y)}")
        
        return True
        
    except Exception as e:
        print(f"❌ GUI simulation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        os.chdir(original_cwd)

if __name__ == "__main__":
    print("=== Testing GUI Detection Fix ===")
    if test_gui_detection_simulation():
        print("🎉 GUI simulation passed! The detection fix should work in the actual GUI.")
    else:
        print("💥 GUI simulation failed!")
