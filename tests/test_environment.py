import pytest
import numpy as np
import optv

def test_numpy_version():
    """Verify numpy version compatibility"""
    assert np.__version__ == "1.26.4", f"Expected numpy 1.26.4, got {np.__version__}"

def test_optv_version():
    """Verify optv version compatibility"""
    assert optv.__version__ == "0.3.0", f"Expected optv 0.3.0, got {optv.__version__}"

def test_numpy_functionality():
    """Test basic numpy operations used by PyPTV"""
    test_arr = np.zeros((10, 10))
    test_arr[5:8, 5:8] = 1
    assert test_arr.sum() == 9, "Basic numpy operations failed"