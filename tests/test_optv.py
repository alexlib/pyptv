#!/usr/bin/env python
import os
import optv
from optv.calibration import Calibration
from optv.parameters import ControlParams


def test_optv_functionality(test_data_dir):
    """Test basic OpenPTV functionality"""
    print("Testing OpenPTV functionality...")
    print(f"OpenPTV version: {optv.__version__}")

    # Test path to test_cavity
    test_cavity_path = test_data_dir
    print(f"Test cavity path: {test_cavity_path}")

    # Test if we can read parameters
    try:
        control_params_file = os.path.join(test_cavity_path, "parameters", "ptv.par")
        print(f"Control parameters file: {control_params_file}")
        if os.path.exists(control_params_file):
            control_params = ControlParams(control_params_file)
            print("Successfully loaded control parameters")
            print(f"Number of cameras: {control_params.get_num_cams()}")
        else:
            print("Control parameters file not found")
    except Exception as e:
        print(f"Error loading control parameters: {str(e)}")

    # Test if we can read calibration
    try:
        cal = Calibration()
        cal_file = os.path.join(test_cavity_path, "cal", "cam1.tif.ori")
        addpar_file = os.path.join(test_cavity_path, "cal", "cam1.tif.addpar")
        print(f"Calibration file: {cal_file}")
        print(f"Addpar file: {addpar_file}")

        if os.path.exists(cal_file) and os.path.exists(addpar_file):
            cal.from_file(cal_file.encode(), addpar_file.encode())
            print("Successfully loaded calibration")
            print(f"Calibration parameters: {cal.get_pos()}")
        else:
            print("Calibration files not found")
    except Exception as e:
        print(f"Error loading calibration: {str(e)}")

    print("OpenPTV functionality test completed")


if __name__ == "__main__":
    test_optv_functionality()
