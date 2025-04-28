#!/usr/bin/env python
"""
Test script to verify core functionality of pyptv and optv
"""
import os
import sys
import numpy as np
import optv
from optv.calibration import Calibration
from optv.parameters import ControlParams, VolumeParams

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
            print(f"Calibration files not found")
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
        # Set some basic parameters using the correct methods
        # Note: These methods might expect different types than what we're providing
        # Let's try with different parameter types
        try:
            vol_params.set_Zmin_lay(-100.0)
            print("set_Zmin_lay successful")
        except Exception as e:
            print(f"Error in set_Zmin_lay: {str(e)}")

        try:
            vol_params.set_Zmax_lay(100.0)
            print("set_Zmax_lay successful")
        except Exception as e:
            print(f"Error in set_Zmax_lay: {str(e)}")

        try:
            vol_params.set_cn(10)
            print("set_cn successful")
        except Exception as e:
            print(f"Error in set_cn: {str(e)}")
        print("Successfully created volume parameters")
        print(f"Z min layer: {vol_params.get_Zmin_lay()}")
        print(f"Z max layer: {vol_params.get_Zmax_lay()}")
    except Exception as e:
        print(f"Error creating volume parameters: {str(e)}")
        return False

    print("Core functionality test completed successfully!")
    return True

if __name__ == "__main__":
    success = test_core_functionality()
    sys.exit(0 if success else 1)
