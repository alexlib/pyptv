import os
import optv
import pytest
from optv.calibration import Calibration
from optv.parameters import VolumeParams

@pytest.fixture
def test_cavity_dir():
    # Fixture to provide the test_cavity directory path
    return os.path.join(os.path.dirname(__file__), "test_cavity")

def test_core_functionality(test_cavity_dir, capsys):
    """Test core functionality of pyptv and optv"""

    import pyptv

    # Print versions
    print(f"PyPTV version: {pyptv.__version__}")
    print(f"OpenPTV version: {optv.__version__}")

    # Test path to test_cavity
    test_cavity_path = test_cavity_dir
    print(f"Test cavity path: {test_cavity_path}")

    # Test if we can load calibration
    cal = Calibration()
    cal_file = os.path.join(test_cavity_path, "cal", "cam1.tif.ori")
    addpar_file = os.path.join(test_cavity_path, "cal", "cam1.tif.addpar")

    assert os.path.exists(cal_file), "Calibration file not found"
    assert os.path.exists(addpar_file), "Addpar file not found"

    cal.from_file(cal_file.encode(), addpar_file.encode())
    print("Successfully loaded calibration")
    assert cal.get_pos() is not None

    # Test if we can create a volume
    vol_params = VolumeParams()
    print("VolumeParams attributes:")
    print(dir(vol_params))

    # Set volume parameters using the correct array format
    vol_params.set_Zmin_lay([-20.0, -20.0])
    vol_params.set_Zmax_lay([25.0, 25.0])
    vol_params.set_cn(0.02)
    vol_params.set_X_lay([-40.0, 40.0])

    print("Successfully created volume parameters")
    assert vol_params.get_Zmin_lay() == [-20.0, -20.0]
    assert vol_params.get_Zmax_lay() == [25.0, 25.0]
    assert vol_params.get_X_lay() == [-40.0, 40.0]
    assert vol_params.get_cn() == 0.02

    print("Core functionality test completed successfully!")
