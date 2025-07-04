#!/usr/bin/env python3
"""
Test to verify the correspondence fix works correctly
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
from pyptv.ptv import py_detection_proc_c, py_correspondences_proc_c, py_start_proc_c

class MockMainGUI:
    """Mock MainGUI object for testing correspondence function"""
    
    def __init__(self, parameter_manager):
        self.parameter_manager = parameter_manager
        self.n_cams = parameter_manager.n_cam
        self.detections = None
        self.corrected = None
        self.cpar = None
        self.vpar = None
        self.tpar = None
        self.cals = None
        self.spar = None
        self.track_par = None
        self.epar = None
    
    def get_parameter(self, key):
        """Delegate parameter access to parameter manager"""
        return self.parameter_manager.get_parameter(key)
    
    def ensure_parameter_objects(self):
        """Initialize parameter objects"""
        if (self.cpar is None or self.vpar is None or 
            self.tpar is None or self.cals is None):
            print("Initializing parameter objects...")
            (self.cpar, self.spar, self.vpar, 
             self.track_par, self.tpar, self.cals, self.epar) = py_start_proc_c(self.parameter_manager)
            print("Parameter objects initialized successfully")

def test_correspondence_with_gui_simulation():
    """Test correspondence function with GUI simulation"""
    
    # Change to test_cavity directory
    original_cwd = Path.cwd()
    test_dir = Path(__file__).parent / "tests" / "test_cavity"
    
    # If we're already in test_cavity, don't change
    if original_cwd.name == "test_cavity":
        test_dir = original_cwd
    
    print(f"Test directory: {test_dir}")
    os.chdir(test_dir)
    
    try:
        print("=== Testing Correspondence Fix ===")
        
        # Load parameters
        pm = ParameterManager()
        pm.from_yaml(Path("parameters_Run1.yaml"))
        
        # Create mock GUI object
        mock_gui = MockMainGUI(pm)
        
        # Load parameters
        ptv_params = mock_gui.get_parameter('ptv')
        targ_rec_params = mock_gui.get_parameter('targ_rec')
        
        if ptv_params is None or targ_rec_params is None:
            raise ValueError("Could not load parameters")
        
        print("✓ Parameters loaded successfully")
        
        # Load images and run detection first
        images = []
        for img_path in ptv_params['img_name']:
            img = imread(img_path)
            if img.ndim > 2:
                img = rgb2gray(img)
            img = img_as_ubyte(img)
            images.append(img)
        
        # Run detection
        target_params = {'targ_rec': targ_rec_params}
        detections, corrected = py_detection_proc_c(
            images, 
            ptv_params, 
            target_params
        )
        
        # Store detection results in mock GUI
        mock_gui.detections = detections
        mock_gui.corrected = corrected
        
        print("✓ Detection completed successfully")
        
        # Ensure parameter objects are initialized
        mock_gui.ensure_parameter_objects()
        
        print("✓ Parameter objects initialized")
        
        # Test correspondence function
        print("Testing correspondence function...")
        sorted_pos, sorted_corresp, num_targs = py_correspondences_proc_c(mock_gui)
        
        print(f"✅ Correspondence successful!")
        print(f"   Sorted positions: {len(sorted_pos)} sets")
        print(f"   Sorted correspondences: {len(sorted_corresp)} sets")
        print(f"   Number of targets: {num_targs}")
        
        # Verify the results
        if len(sorted_pos) > 0:
            for i, pos_set in enumerate(sorted_pos):
                print(f"   Position set {i}: shape {pos_set.shape}")
                
        return True
        
    except Exception as e:
        print(f"❌ Correspondence test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        os.chdir(original_cwd)

if __name__ == "__main__":
    print("=== Testing Correspondence Fix ===")
    if test_correspondence_with_gui_simulation():
        print("🎉 Correspondence test passed! The fix should work in the actual GUI.")
    else:
        print("💥 Correspondence test failed!")
