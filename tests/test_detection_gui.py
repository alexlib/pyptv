#!/usr/bin/env python
"""
Test script for the refactored detection GUI
"""

import sys
import pathlib
from pyptv.detection_gui import DetectionGUI

def test_detection_gui():
    print("Testing DetectionGUI...")
    
    # Create GUI instance
    gui = DetectionGUI()
    
    # Test parameter loading
    yaml_path = pathlib.Path("tests/test_cavity/parameters_Run1.yaml")
    if yaml_path.exists():
        gui.yaml_path = str(yaml_path)
        print(f"Setting default YAML: {yaml_path}")
        
        # Test parameter loading
        gui._button_load_params()
        print(f"Parameters loaded: {gui.parameters_loaded}")
        
        if gui.parameters_loaded:
            print("✓ Parameter loading successful")
            print(f"  - Grey threshold: {gui.thresholds[0]}")
            print(f"  - Pixel bounds: {gui.pixel_count_bounds}")
            print(f"  - X size bounds: {gui.xsize_bounds}")
            print(f"  - Y size bounds: {gui.ysize_bounds}")
            print(f"  - Sum grey: {gui.sum_grey}")
            print(f"  - Disco: {gui.disco}")
            
            # Test if dynamic traits were created
            if hasattr(gui, 'grey_thresh'):
                print(f"✓ Dynamic traits created successfully")
                print(f"  - Grey threshold trait: {gui.grey_thresh}")
            else:
                print("✗ Dynamic traits not created")
        else:
            print("✗ Parameter loading failed")
    else:
        print(f"✗ YAML file {yaml_path} not found")
    
    # Test image loading
    if gui.parameters_loaded:
        # Try to load a test image
        test_image = "cal/cam1.tif"
        if (gui.working_folder / test_image).exists():
            gui.image_name = test_image
            gui._button_load_image_fired()
            print(f"Image loaded: {gui.image_loaded}")
            
            if gui.image_loaded:
                print("✓ Image loading successful")
                print(f"  - Raw image shape: {gui.raw_image.shape}")
                print(f"  - Processed image shape: {gui.processed_image.shape}")
            else:
                print("✗ Image loading failed")
        else:
            print(f"✗ Test image {test_image} not found")
    
    print("Test completed!")

if __name__ == "__main__":
    test_detection_gui()
