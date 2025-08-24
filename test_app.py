#!/usr/bin/env python3
"""
Simple test script to debug initialization issues.
"""

import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
import traceback

def test_init():
    """Test initialization steps without GUI."""
    try:
        # Configure NumPy first
        import numpy as np
        try:
            print("Setting NumPy options...")
            np.set_printoptions(precision=4, suppress=True, threshold=50)
            
            # Monkey patch the ndarray.__repr__ to avoid the error
            if hasattr(np.ndarray, '__repr__'):
                # Create a simple repr function
                def simple_repr(self):
                    return f"<ndarray: shape={self.shape}, dtype={self.dtype}>"
                # Replace the problematic repr
                np.ndarray.__repr__ = simple_repr
                print("Fixed NumPy array repr")
            
            print("NumPy configured successfully")
        except Exception as np_error:
            print(f"WARNING: NumPy configuration failed: {np_error}")
        
        # Import PTVCore bridge directly to bypass the problematic import
        print("Importing PTVCoreBridge...")
        try:
            from pyptv.ui.ptv_core.bridge import PTVCoreBridge as PTVCore
            print("Using PTVCoreBridge directly")
        except Exception as import_error:
            print(f"Error importing PTVCoreBridge: {import_error}")
            print("Falling back to standard import...")
            from pyptv.ui.ptv_core import PTVCore
        
        # Get experiment path
        exp_path = Path('tests/test_cavity')
        print(f"Using experiment path: {exp_path}")
        
        # Create PTV core
        print("Creating PTVCore instance...")
        ptv_core = PTVCore(exp_path)
        
        # Initialize
        print("Initializing experiment...")
        images = ptv_core.initialize()
        
        print(f"Initialized successfully with {ptv_core.n_cams} cameras")
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    # Initialize Qt application
    app = QApplication(sys.argv)
    
    # Run test
    success = test_init()
    
    if success:
        print("Test completed successfully!")
    else:
        print("Test failed!")
    
    sys.exit(0)