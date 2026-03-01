"""
Verification script to check numpy and optv compatibility
"""

import sys
from packaging import version
import numpy as np
import optv
import pyptv


def verify_environment():
    print("Environment Verification Report")
    print("-" * 30)
    print(f"Python version: {sys.version}")

    # Check NumPy version
    min_numpy = "1.26.4"
    max_numpy = "2.7"
    np_version = np.__version__
    if not (version.parse(min_numpy) <= version.parse(np_version) < version.parse(max_numpy)):
        print(
            f"WARNING: NumPy version out of range. Required: >={min_numpy} <{max_numpy}, Found: {np_version}"
        )
    else:
        print(f"NumPy version: {np_version} (OK)")

    # Check OpenPTV version
    required_optv = "0.3.0"
    if optv.__version__ != required_optv:
        print(
            f"WARNING: OpenPTV version mismatch. Required: {required_optv}, Found: {optv.__version__}"
        )
    else:
        print(f"OpenPTV version: {optv.__version__} (OK)")

    print(f"PyPTV version: {pyptv.__version__}")

    # Verify numpy functionality
    try:
        # Test basic numpy operations used by PyPTV
        test_arr = np.zeros((10, 10))
        test_arr[5:8, 5:8] = 1
        print("\nNumPy array operations: OK")
    except Exception as e:
        print(f"\nNumPy array operations failed: {str(e)}")

    # Verify optv compatibility
    try:
        from optv.calibration import Calibration

        Calibration()
        print("OpenPTV calibration module: OK")
    except Exception as e:
        print(f"OpenPTV calibration module error: {str(e)}")


if __name__ == "__main__":
    verify_environment()
