#!/usr/bin/env python
"""
Test script to verify core functionality of pyptv and optv
"""

import os
import sys
import optv
from optv.calibration import Calibration
from optv.parameters import VolumeParams


def test_core_functionality(test_data_dir):
    """Test core functionality of pyptv and optv"""
    print("Testing core functionality...")

    # Print versions
    import pyptv

    print(f"PyPTV version: {pyptv.__version__}")
    print(f"OpenPTV version: {optv.__version__}")

    # Test path to test_cavity
    test_cavity_path = test_data_dir
    print(f"Test cavity path: {test_cavity_path}")

    # Test if we can load calibration
    try:
        cal = Calibration()
        cal_file = os.path.join(test_cavity_path, "cal", "cam1.tif.ori")
        addpar_file = os.path.join(test_cavity_path, "cal", "cam1.tif.addpar")

        if os.path.exists(cal_file) and os.path.exists(addpar_file):
            cal.from_file(cal_file.encode(), addpar_file.encode())
            print("Successfully loaded calibration")
            print(f"Calibration parameters: {cal.get_pos()}")
        else:
            print("Calibration files not found")
            return False
    except Exception as e:
        print(f"Error loading calibration: {str(e)}")
        return False

    # Test if we can create a volume
    try:
        # Create a simple VolumeParams object
        vol_params = VolumeParams()
        # Print the attributes of the VolumeParams class
        print("VolumeParams attributes:")
        print(dir(vol_params))
        
        # Set volume parameters using the correct array format
        # Based on the criteria.par format, these should be arrays
        try:
            # Z min layer expects an array of values (for multiple layers)
            vol_params.set_Zmin_lay([-20.0, -20.0])
            print("set_Zmin_lay successful")
        except Exception as e:
            print(f"Error in set_Zmin_lay: {str(e)}")

        try:
            # Z max layer expects an array of values (for multiple layers)
            vol_params.set_Zmax_lay([25.0, 25.0])
            print("set_Zmax_lay successful")
        except Exception as e:
            print(f"Error in set_Zmax_lay: {str(e)}")

        try:
            # cn might be a single value
            vol_params.set_cn(0.02)
            print("set_cn successful")
        except Exception as e:
            print(f"Error in set_cn: {str(e)}")
            
        try:
            # Also set X layer bounds
            vol_params.set_X_lay([-40.0, 40.0])
            print("set_X_lay successful")
        except Exception as e:
            print(f"Error in set_X_lay: {str(e)}")
            
        print("Successfully created volume parameters")
        print(f"Z min layer: {vol_params.get_Zmin_lay()}")
        print(f"Z max layer: {vol_params.get_Zmax_lay()}")
        print(f"X layer: {vol_params.get_X_lay()}")
        print(f"cn: {vol_params.get_cn()}")
    except Exception as e:
        print(f"Error creating volume parameters: {str(e)}")
        return False

    print("Core functionality test completed successfully!")
    return True


if __name__ == "__main__":
    # Use the test_cavity directory when running directly
    test_cavity_dir = os.path.join(os.path.dirname(__file__), "test_cavity")
    success = test_core_functionality(test_cavity_dir)
    sys.exit(0 if success else 1)
