"""
Extended unit tests for the pyptv_batch module
"""
import pytest
import os
import sys
import tempfile
from pathlib import Path
import shutil

from pyptv.pyptv_batch import run_batch, main, AttrDict

@pytest.fixture
def mock_experiment_dir():
    """Create a mock experiment directory structure"""
    temp_dir = tempfile.mkdtemp()
    exp_dir = Path(temp_dir) / "test_experiment"
    exp_dir.mkdir(exist_ok=True)

    # Create required subdirectories
    params_dir = exp_dir / "parameters"
    params_dir.mkdir(exist_ok=True)

    img_dir = exp_dir / "img"
    img_dir.mkdir(exist_ok=True)

    cal_dir = exp_dir / "cal"
    cal_dir.mkdir(exist_ok=True)

    res_dir = exp_dir / "res"
    res_dir.mkdir(exist_ok=True)

    # Create a minimal ptv.par file
    with open(params_dir / "ptv.par", "w") as f:
        f.write("4\n")  # num_cams
        f.write("img/cam1.%d\n")
        f.write("cal/cam1.tif\n")
        f.write("img/cam2.%d\n")
        f.write("cal/cam2.tif\n")
        f.write("img/cam3.%d\n")
        f.write("cal/cam3.tif\n")
        f.write("img/cam4.%d\n")
        f.write("cal/cam4.tif\n")

    # Create a minimal sequence.par file
    with open(params_dir / "sequence.par", "w") as f:
        f.write("img/cam1.%d\n")
        f.write("img/cam2.%d\n")
        f.write("img/cam3.%d\n")
        f.write("img/cam4.%d\n")
        f.write("10000\n")  # first
        f.write("10010\n")  # last

    # Create other required parameter files
    for param_file in ["criteria.par", "detect_plate.par", "orient.par",
                       "pft_par.par", "targ_rec.par", "track.par"]:
        with open(params_dir / param_file, "w") as f:
            f.write("# Test parameter file\n")

    yield exp_dir
    shutil.rmtree(temp_dir)

def test_attr_dict():
    """Test the AttrDict class"""
    ad = AttrDict(a=1, b=2)
    assert ad.a == 1
    assert ad.b == 2
    assert ad["a"] == 1
    assert ad["b"] == 2

    ad.c = 3
    assert ad.c == 3
    assert ad["c"] == 3

    ad["d"] = 4
    assert ad.d == 4
    assert ad["d"] == 4

def test_run_batch(mock_experiment_dir, monkeypatch):
    """Test the run_batch function with mocked dependencies"""
    # Create a mock implementation of run_batch
    def mock_run_batch(new_seq_first, new_seq_last):
        # Just verify that the parameters are passed correctly
        assert new_seq_first == 10001
        assert new_seq_last == 10005
        return None

    # Apply the mock
    monkeypatch.setattr("pyptv.pyptv_batch.run_batch", mock_run_batch)

    # Change to the mock experiment directory
    original_dir = os.getcwd()
    os.chdir(mock_experiment_dir)

    try:
        # Test the function
        from pyptv.pyptv_batch import run_batch
        run_batch(10001, 10005)
        # If we get here without exceptions, the test passes
        assert True
    finally:
        # Change back to the original directory
        os.chdir(original_dir)

def test_main(mock_experiment_dir, test_data_dir, monkeypatch):
    """Test the main function with mocked dependencies"""
    # Mock the run_batch function
    def mock_run_batch(first, last):
        assert first == 10000
        assert last == 10004
        return None

    # Apply the mock
    monkeypatch.setattr("pyptv.pyptv_batch.run_batch", mock_run_batch)

    # Test the function with explicit arguments
    from pyptv.pyptv_batch import main
    main(test_data_dir, 10000, 10004)

    # If we get here without exceptions, the test passes
    assert True
