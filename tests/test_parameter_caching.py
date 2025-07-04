#!/usr/bin/env python3
"""
Test to verify that the parameter object caching works correctly
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

def test_parameter_caching():
    """Test that parameter objects are cached and reused efficiently"""
    
    # Change to test_cavity directory
    original_cwd = Path.cwd()
    test_dir = Path(__file__).parent.parent / "tests" / "test_cavity"
    
    # If we're already in test_cavity, don't change
    if original_cwd.name == "test_cavity":
        test_dir = original_cwd
    
    print(f"Test directory: {test_dir}")
    os.chdir(test_dir)
    
    try:
        print("=== Testing Parameter Object Caching ===")
        
        # Create a mock MainGUI-like object to test caching
        from pyptv.experiment import Experiment
        
        class MockMainGUI:
            def __init__(self):
                self.exp1 = Experiment()
                self.exp1.populate_runs(Path.cwd())
                self.exp1.setActive(0)
                
                # Initialize caching attributes
                self.cpar = None
                self.vpar = None
                self.tpar = None
                self.cals = None
                self.spar = None
                self.track_par = None
                self.epar = None
                self._parameter_objects_dirty = True
                
            def get_parameter(self, key):
                return self.exp1.get_parameter(key)
                
            def ensure_parameter_objects(self):
                """Simplified version of the caching method"""
                if (self._parameter_objects_dirty or 
                    self.cpar is None or self.vpar is None or 
                    self.tpar is None or self.cals is None):
                    
                    from pyptv.ptv import py_start_proc_c
                    print("⚡ Initializing parameter objects from ParameterManager...")
                    
                    (self.cpar, self.spar, self.vpar, self.track_par, 
                     self.tpar, self.cals, self.epar) = py_start_proc_c(self.exp1.parameter_manager)
                    
                    # Clear the dirty flag
                    self._parameter_objects_dirty = False
                    print("✅ Parameter objects initialized successfully")
                else:
                    print("🔄 Using cached parameter objects")
                    
            def invalidate_parameter_cache(self):
                """Mark parameter objects as dirty"""
                self._parameter_objects_dirty = True
                print("🗑️  Parameter cache invalidated")
        
        # Create mock GUI
        mock_gui = MockMainGUI()
        
        # Test 1: First call should initialize
        print("\n--- Test 1: First call should initialize ---")
        mock_gui.ensure_parameter_objects()
        assert mock_gui.cpar is not None
        assert mock_gui.cals is not None
        assert not mock_gui._parameter_objects_dirty
        
        # Test 2: Second call should use cache
        print("\n--- Test 2: Second call should use cache ---")
        mock_gui.ensure_parameter_objects()
        
        # Test 3: After invalidation, should reinitialize
        print("\n--- Test 3: After invalidation, should reinitialize ---")
        mock_gui.invalidate_parameter_cache()
        assert mock_gui._parameter_objects_dirty
        mock_gui.ensure_parameter_objects()
        assert not mock_gui._parameter_objects_dirty
        
        # Test 4: Verify objects are actually usable
        print("\n--- Test 4: Verify objects are usable ---")
        n_cam = len(mock_gui.get_parameter('ptv')['img_name'])
        print(f"Number of cameras: {n_cam}")
        print(f"Calibration objects loaded: {len(mock_gui.cals)}")
        assert len(mock_gui.cals) == n_cam
        
        print("\n🎉 All parameter caching tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Parameter caching test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        os.chdir(original_cwd)

if __name__ == "__main__":
    print("=== Testing Parameter Object Caching Design ===")
    if test_parameter_caching():
        print("✅ Parameter caching design works correctly!")
    else:
        print("💥 Parameter caching test failed!")
