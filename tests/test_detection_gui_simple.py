#!/usr/bin/env python3
"""
Simple test script for the refactored detection GUI
"""

import sys
from pathlib import Path

# Add the pyptv module to the path
sys.path.insert(0, str(Path(__file__).parent))

from pyptv.detection_gui import DetectionGUI

def test_detection_gui():
    """Test the detection GUI with working directory approach"""
    
    # Test with default directory
    print("Testing with default test_cavity directory...")
    test_dir = Path("tests/test_cavity")
    
    if not test_dir.exists():
        print(f"Warning: Test directory {test_dir} does not exist")
        return False
        
    try:
        # Create GUI instance
        gui = DetectionGUI(test_dir)
        
        # Check that working directory is set correctly
        assert gui.working_directory == test_dir
        print(f"✓ Working directory set correctly: {gui.working_directory}")
        
        # Check initial state
        assert not gui.parameters_loaded
        assert not gui.image_loaded
        print("✓ Initial state is correct")
        
        # Test parameter loading (this also loads the image)
        gui._button_load_params()
        
        if gui.parameters_loaded:
            print("✓ Parameters loaded successfully")
        else:
            print("✗ Parameters failed to load")
            return False
            
        if gui.image_loaded:
            print("✓ Image loaded successfully")
        else:
            print("✗ Image failed to load")
            return False
            
        print("✓ Detection GUI test passed!")
        return True
        
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    success = test_detection_gui()
    sys.exit(0 if success else 1)
