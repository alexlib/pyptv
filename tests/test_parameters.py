"""
Unit tests for the parameters module
"""

import pytest
import os
import tempfile
from pathlib import Path
import yaml
import shutil

from pyptv.legacy_parameters import Parameters, PtvParams, SequenceParams
from pyptv.parameter_manager import ParameterManager


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
    # with pytest.raises(NotImplementedError):
    #     params.filename

    # Test set method
    with pytest.raises(NotImplementedError):
        params.set("var1", "var2")

    # Test read method
    with pytest.raises(NotImplementedError):
        params.read()


def test_ptv_params(temp_params_dir):
    """Test the PtvParams class"""
    # Create parameters directory
    params_dir = temp_params_dir 

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

    # Test reading from .par file
    original_dir = Path.cwd()
    os.chdir(temp_params_dir.parent)

    try:
        cparams = PtvParams(path=params_dir)
        cparams.read()

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

        cparams.n_img = 3
        cparams.write()

        cparams2 = PtvParams(path=params_dir)
        cparams2.read()
        assert cparams2.n_img == 3
    finally:
        os.chdir(original_dir)


def test_sequence_params(temp_params_dir):
    """Test the SequenceParams class"""
    params_dir = temp_params_dir

    seq_par_path = params_dir / "sequence.par"
    with open(seq_par_path, "w") as f:
        f.write("img/cam1.%d\n")
        f.write("img/cam2.%d\n")
        f.write("img/cam3.%d\n")
        f.write("img/cam4.%d\n")
        f.write("10000\n")
        f.write("10010\n")

    original_dir = Path.cwd()
    os.chdir(temp_params_dir.parent)

    try:
        sparams = SequenceParams(n_img=4, base_name=[], first=0, last=0, path=params_dir)
        sparams.read()

        assert sparams.first == 10000
        assert sparams.last == 10010
        assert len(sparams.base_name) == 4
        assert sparams.base_name[0] == "img/cam1.%d"

        sparams.first = 10001
        sparams.last = 10009
        sparams.write()

        sparams2 = SequenceParams(n_img=4, base_name=[], first=0, last=0, path=params_dir)
        sparams2.read()
        assert sparams2.first == 10001
        assert sparams2.last == 10009
    finally:
        os.chdir(original_dir)


def test_parameter_manager(temp_params_dir):
    """Test the ParameterManager class"""
    params_dir = temp_params_dir
    
    # Create dummy .par files
    with open(params_dir / "ptv.par", "w") as f:
        f.write("2\nimg1.tif\ncal1.ori\nimg2.tif\ncal2.ori\n1\n0\n1\n10\n10\n0.1\n0.1\n0\n1\n1\n1\n1\n")
    with open(params_dir / "sequence.par", "w") as f:
        f.write("img1\nimg2\n1\n2\n")

    pm = ParameterManager()
    pm.from_directory(params_dir)

    assert 'ptv' in pm.parameters
    # num_cams is now at global level, not in ptv section
    assert pm.get_n_cam() == 2
    assert 'sequence' in pm.parameters
    assert pm.parameters['sequence']['first'] == 1

    # Test to_yaml
    yaml_path = temp_params_dir / "parameters.yaml"
    pm.to_yaml(yaml_path)
    assert yaml_path.exists()

    with open(yaml_path, 'r') as f:
        data = yaml.safe_load(f)
    # num_cams should be at top level, not in ptv section
    assert data['num_cams'] == 2
    assert 'num_cams' not in data['ptv']  # Ensure it's not in ptv section

    # Test from_yaml
    pm2 = ParameterManager()
    pm2.from_yaml(yaml_path)
    # num_cams should be accessible via get_n_cam(), not from ptv section
    assert pm2.get_n_cam() == 2
    assert 'num_cams' not in pm2.parameters['ptv']  # Ensure it's not in ptv section

    # Test to_directory
    new_params_dir = temp_params_dir / "new_params"
    pm2.to_directory(new_params_dir)
    assert (new_params_dir / "ptv.par").exists()
    assert (new_params_dir / "sequence.par").exists()


if __name__ == "__main__":
    pytest.main([__file__])    