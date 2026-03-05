import pytest
import numpy as np
from optv.calibration import Calibration
from pyptv.ptv import clone_calibration

def test_clone_calibration_basic():
    cal = Calibration()
    pos = np.array([1.0, 2.0, 3.0])
    angles = np.array([0.1, 0.2, 0.3])
    cal.set_pos(pos)
    cal.set_angles(angles)
    if hasattr(cal, 'set_primary_point') and hasattr(cal, 'get_primary_point'):
        primary_point = np.array([4.0, 5.0, 6.0])
        cal.set_primary_point(primary_point)
    
    cal2 = clone_calibration(cal)
    assert not (cal is cal2)
    np.testing.assert_array_equal(cal.get_pos(), cal2.get_pos())
    np.testing.assert_array_equal(cal.get_angles(), cal2.get_angles())
    if hasattr(cal, 'get_primary_point'):
        np.testing.assert_array_equal(cal.get_primary_point(), cal2.get_primary_point())

def test_clone_calibration_all_fields():
    cal = Calibration()
    pos = np.array([1.0, 2.0, 3.0])
    angles = np.array([0.1, 0.2, 0.3])
    cal.set_pos(pos)
    cal.set_angles(angles)
    # Set all optional fields if available
    if hasattr(cal, 'set_primary_point'):
        primary_point = np.array([4.0, 5.0, 6.0])
        cal.set_primary_point(primary_point)
    if hasattr(cal, 'set_glass'):
        glass = np.array([0.5, 0.6, 0.7])
        cal.set_glass(glass)
    if hasattr(cal, 'set_radial_distortion'):
        radial = np.array([0.01, 0.02, 0.03])
        cal.set_radial_distortion(radial)
    if hasattr(cal, 'set_decentering'):
        decentering = np.array([0.001, 0.002])
        cal.set_decentering(decentering)
    if hasattr(cal, 'set_affine'):
        affine = np.array([1.0, 0.0])
        cal.set_affine(affine)
    
    cal2 = clone_calibration(cal)
    assert not (cal is cal2)
    np.testing.assert_array_equal(cal.get_pos(), cal2.get_pos())
    np.testing.assert_array_equal(cal.get_angles(), cal2.get_angles())
    if hasattr(cal, 'get_primary_point'):
        np.testing.assert_array_equal(cal.get_primary_point(), cal2.get_primary_point())
    if hasattr(cal, 'get_glass'):
        np.testing.assert_array_equal(cal.get_glass(), cal2.get_glass())
    if hasattr(cal, 'get_radial_distortion'):
        np.testing.assert_array_equal(cal.get_radial_distortion(), cal2.get_radial_distortion())
    if hasattr(cal, 'get_decentering'):
        np.testing.assert_array_equal(cal.get_decentering(), cal2.get_decentering())
    if hasattr(cal, 'get_affine'):
        np.testing.assert_array_equal(cal.get_affine(), cal2.get_affine())

def test_clone_calibration_independence_all_fields():
    cal = Calibration()
    cal.set_pos(np.array([1.0, 2.0, 3.0]))
    cal.set_angles(np.array([0.1, 0.2, 0.3]))
    if hasattr(cal, 'set_primary_point'):
        cal.set_primary_point(np.array([4.0, 5.0, 6.0]))
    if hasattr(cal, 'set_glass'):
        cal.set_glass(np.array([0.5, 0.6, 0.7]))
    if hasattr(cal, 'set_radial_distortion'):
        cal.set_radial_distortion(np.array([0.01, 0.02, 0.03]))
    if hasattr(cal, 'set_decentering'):
        cal.set_decentering(np.array([0.001, 0.002]))
    if hasattr(cal, 'set_affine'):
        cal.set_affine(np.array([1.0, 0.0]))
    cal2 = clone_calibration(cal)
    # Change cal2 and check cal is not affected
    cal2.set_pos(np.array([7.0, 8.0, 9.0]))
    assert not np.allclose(cal.get_pos(), cal2.get_pos())
    cal2.set_angles(np.array([0.7, 0.8, 0.9]))
    assert not np.allclose(cal.get_angles(), cal2.get_angles())
    if hasattr(cal2, 'set_primary_point'):
        cal2.set_primary_point(np.array([7.0, 8.0, 9.0]))
        assert not np.allclose(cal.get_primary_point(), cal2.get_primary_point())
    if hasattr(cal2, 'set_glass'):
        cal2.set_glass(np.array([0.9, 0.8, 0.7]))
        assert not np.allclose(cal.get_glass(), cal2.get_glass())
    if hasattr(cal2, 'set_radial_distortion'):
        cal2.set_radial_distortion(np.array([0.09, 0.08, 0.07]))
        assert not np.allclose(cal.get_radial_distortion(), cal2.get_radial_distortion())
    if hasattr(cal2, 'set_decentering'):
        cal2.set_decentering(np.array([0.009, 0.008]))
        assert not np.allclose(cal.get_decentering(), cal2.get_decentering())
    if hasattr(cal2, 'set_affine'):
        cal2.set_affine(np.array([0.0, 1.0]))
        assert not np.allclose(cal.get_affine(), cal2.get_affine())
