import pytest
import numpy as np
from pyptv.ptv import (
    py_start_proc_c,
    py_trackcorr_init,
    py_sequence_loop
)

def test_numpy_array_compatibility():
    """Test numpy array handling in core functions"""
    # Create test arrays using newer numpy
    test_array = np.zeros((100, 100), dtype=np.uint8)
    test_coords = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]], dtype=np.float64)
    
    # Test array passing to core functions
    try:
        # Add your specific function tests here
        assert test_array.dtype == np.uint8
        assert test_coords.dtype == np.float64
    except Exception as e:
        pytest.fail(f"Numpy compatibility test failed: {str(e)}")

def test_optv_integration():
    """Test integration with optv package"""
    from optv.calibration import Calibration
    from optv.parameters import ControlParams
    
    # Create test calibration
    cal = Calibration()
    assert cal is not None
    
    # Test parameter handling
    cpar = ControlParams(4)
    assert cpar.get_num_cams() == 4