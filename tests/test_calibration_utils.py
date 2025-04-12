"""
Tests for the calibration utilities in pyptv/test_calibration.py
"""
import os
import pytest
import numpy as np
import tempfile
from pathlib import Path

# Import the functions from the original file
from pyptv.test_calibration import (
    read_dt_lsq,
    read_calblock,
    pair_cal_points,
    plot_cal_points,
    plot_cal_err_histogram
)

@pytest.fixture
def sample_dt_lsq_file():
    """Create a sample dt_lsq file for testing"""
    with tempfile.NamedTemporaryFile(delete=False, mode='w') as f:
        f.write("3\n")  # 3 particles
        f.write("1 10.0 20.0 30.0\n")
        f.write("2 40.0 50.0 60.0\n")
        f.write("3 70.0 80.0 90.0\n")

    yield Path(f.name)
    os.unlink(f.name)

@pytest.fixture
def sample_calblock_file():
    """Create a sample calblock file for testing"""
    with tempfile.NamedTemporaryFile(delete=False, mode='w') as f:
        f.write("1 12.0 22.0 32.0\n")
        f.write("2 42.0 52.0 62.0\n")
        f.write("3 72.0 82.0 92.0\n")

    yield Path(f.name)
    os.unlink(f.name)

def test_read_dt_lsq(sample_dt_lsq_file):
    """Test reading a dt_lsq file"""
    points = read_dt_lsq(sample_dt_lsq_file)

    assert len(points) == 3
    assert np.allclose(points[0], np.array([10.0, 20.0, 30.0]))
    assert np.allclose(points[1], np.array([40.0, 50.0, 60.0]))
    assert np.allclose(points[2], np.array([70.0, 80.0, 90.0]))

def test_read_calblock(sample_calblock_file):
    """Test reading a calblock file"""
    points = read_calblock(sample_calblock_file)

    assert len(points) == 3
    assert np.allclose(points[0], np.array([12.0, 22.0, 32.0]))
    assert np.allclose(points[1], np.array([42.0, 52.0, 62.0]))
    assert np.allclose(points[2], np.array([72.0, 82.0, 92.0]))

def test_pair_cal_points():
    """Test pairing calibration points"""
    calblock_points = [
        np.array([10.0, 20.0, 30.0]),
        np.array([40.0, 50.0, 60.0]),
        np.array([70.0, 80.0, 90.0])
    ]

    dt_lsq_points = [
        np.array([12.0, 22.0, 32.0]),
        np.array([42.0, 52.0, 62.0]),
        np.array([72.0, 82.0, 92.0])
    ]

    # Test with large enough max_dist to include all pairs
    # The distance between corresponding points is sqrt(12) ≈ 3.464
    pairs = pair_cal_points(calblock_points, dt_lsq_points, max_dist=6.0)
    assert len(pairs) == 3

    # Test with smaller max_dist that should exclude some pairs
    pairs = pair_cal_points(calblock_points, dt_lsq_points, max_dist=2.0)
    assert len(pairs) == 0  # All distances are > 2.0

    # Test with points that are closer
    dt_lsq_points_closer = [
        np.array([10.1, 20.1, 30.1]),
        np.array([40.1, 50.1, 60.1]),
        np.array([70.1, 80.1, 90.1])
    ]

    # The distance between corresponding points is sqrt(0.03) ≈ 0.173
    pairs = pair_cal_points(calblock_points, dt_lsq_points_closer, max_dist=1.0)
    assert len(pairs) == 3

def test_plot_cal_points():
    """Test plotting calibration points"""
    # Create a simple pair list
    pairs = [
        (np.array([10.0, 20.0, 30.0]), np.array([12.0, 22.0, 32.0])),
        (np.array([40.0, 50.0, 60.0]), np.array([42.0, 52.0, 62.0]))
    ]

    # Just test that the function runs without errors
    fig, ax = plot_cal_points(pairs)
    assert fig is not None
    assert ax is not None

def test_plot_cal_err_histogram():
    """Test plotting calibration error histogram"""
    # Create a simple pair list
    pairs = [
        (np.array([10.0, 20.0, 30.0]), np.array([12.0, 22.0, 32.0])),
        (np.array([40.0, 50.0, 60.0]), np.array([42.0, 52.0, 62.0]))
    ]

    # Just test that the function runs without errors
    fig, ax = plot_cal_err_histogram(pairs)
    assert fig is not None
    assert ax is not None
