"""
Unit tests for the parameters module
"""
import pytest
import os
import tempfile
from pathlib import Path
import yaml
import shutil

from pyptv.parameters import Parameters, PtvParams, SequenceParams

@pytest.fixture
def temp_params_dir():
    """Create a temporary directory for parameter files"""
    temp_dir = tempfile.mkdtemp()
    params_dir = Path(temp_dir) / "parameters"
    params_dir.mkdir(exist_ok=True)
    yield params_dir
    shutil.rmtree(temp_dir)

def test_parameters_base_class():
    """Test the base Parameters class"""
    # Test initialization
    params = Parameters()
    assert params.path.name == "parameters"

    # Test with custom path
    custom_path = Path("/tmp/custom_params")
    params = Parameters(custom_path)
    assert params.path == custom_path.resolve()

    # Test filepath method
    with pytest.raises(NotImplementedError):
        params.filename()

    # Test set method
    with pytest.raises(NotImplementedError):
        params.set("var1", "var2")

    # Test read method
    with pytest.raises(NotImplementedError):
        params.read()

def test_ptv_params(temp_params_dir):
    """Test the PtvParams class"""
    # Create parameters directory
    params_dir = temp_params_dir / "parameters"
    params_dir.mkdir(exist_ok=True)

    # Create a test ptv.par file
    ptv_par_path = params_dir / "ptv.par"
    with open(ptv_par_path, "w") as f:
        f.write("4\n")  # num_cams
        f.write("img/cam1.%d\n")
        f.write("cal/cam1.tif\n")
        f.write("img/cam2.%d\n")
        f.write("cal/cam2.tif\n")
        f.write("img/cam3.%d\n")
        f.write("cal/cam3.tif\n")
        f.write("img/cam4.%d\n")
        f.write("cal/cam4.tif\n")
        f.write("1\n")  # hp_flag
        f.write("1\n")  # allCam_flag
        f.write("1\n")  # tiff_flag
        f.write("1280\n")  # imx
        f.write("1024\n")  # imy
        f.write("0.012\n")  # pix_x
        f.write("0.012\n")  # pix_y
        f.write("0\n")  # chfield
        f.write("1.0\n")  # mmp_n1
        f.write("1.33\n")  # mmp_n2
        f.write("1.46\n")  # mmp_n3
        f.write("5.0\n")  # mmp_d

    # Create a test ptv.yaml file
    ptv_yaml_path = params_dir / "ptv.yaml"
    ptv_yaml_data = {
        "n_img": 4,
        "img_name": ["img/cam1.%d", "img/cam2.%d", "img/cam3.%d", "img/cam4.%d"],
        "img_cal": ["cal/cam1.tif", "cal/cam2.tif", "cal/cam3.tif", "cal/cam4.tif"],
        "hp_flag": True,
        "allcam_flag": True,
        "tiff_flag": True,
        "imx": 1280,
        "imy": 1024,
        "pix_x": 0.012,
        "pix_y": 0.012,
        "chfield": 0,
        "mmp_n1": 1.0,
        "mmp_n2": 1.33,
        "mmp_n3": 1.46,
        "mmp_d": 5.0
    }
    with open(ptv_yaml_path, "w") as f:
        yaml.dump(ptv_yaml_data, f)

    # Test reading from .par file
    # Change to the temp directory to match how the Parameters class works
    original_dir = Path.cwd()
    os.chdir(temp_params_dir)

    try:
        # Initialize with the correct path
        cparams = PtvParams()
        cparams.read()

        # Verify the parameters were read correctly
        assert cparams.n_img == 4
        assert cparams.img_name[0] == "img/cam1.%d"
        assert cparams.img_cal[0] == "cal/cam1.tif"
        assert cparams.hp_flag == 1
        assert cparams.allcam_flag == 1
        assert cparams.tiff_flag == 1
        assert cparams.imx == 1280
        assert cparams.imy == 1024
        assert cparams.pix_x == 0.012
        assert cparams.pix_y == 0.012
        assert cparams.chfield == 0
        assert cparams.mmp_n1 == 1.0
        assert cparams.mmp_n2 == 1.33
        assert cparams.mmp_n3 == 1.46
        assert cparams.mmp_d == 5.0

        # Test writing to file
        cparams.n_img = 3
        cparams.write()

        # Read back and verify
        cparams2 = PtvParams()
        cparams2.read()
        assert cparams2.n_img == 3
    finally:
        # Change back to the original directory
        os.chdir(original_dir)

def test_sequence_params(temp_params_dir):
    """Test the SequenceParams class"""
    # Create parameters directory
    params_dir = temp_params_dir / "parameters"
    params_dir.mkdir(exist_ok=True)

    # Create a test sequence.par file
    seq_par_path = params_dir / "sequence.par"
    with open(seq_par_path, "w") as f:
        f.write("img/cam1.%d\n")
        f.write("img/cam2.%d\n")
        f.write("img/cam3.%d\n")
        f.write("img/cam4.%d\n")
        f.write("10000\n")  # first
        f.write("10010\n")  # last

    # Test reading from file
    # Change to the temp directory to match how the Parameters class works
    original_dir = Path.cwd()
    os.chdir(temp_params_dir)

    try:
        # Initialize with the correct path and parameters
        sparams = SequenceParams(n_img=4, base_name=[], first=0, last=0)
        sparams.read()

        # Verify the parameters were read correctly
        assert sparams.first == 10000
        assert sparams.last == 10010
        assert len(sparams.base_name) == 4
        assert sparams.base_name[0] == "img/cam1.%d"

        # Test setting values
        sparams.first = 10001
        sparams.last = 10009
        sparams.write()

        # Read back and verify
        sparams2 = SequenceParams(n_img=4, base_name=[], first=0, last=0)
        sparams2.read()
        assert sparams2.first == 10001
        assert sparams2.last == 10009
    finally:
        # Change back to the original directory
        os.chdir(original_dir)

# Add more tests for other parameter classes as needed
