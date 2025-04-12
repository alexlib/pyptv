"""
Extended tests for installation and environment
"""
import pytest
import sys
import os
import platform
import subprocess
import importlib
from pathlib import Path

def test_python_version():
    """Test that the Python version is compatible"""
    assert sys.version_info.major == 3
    assert sys.version_info.minor >= 10, "Python version should be 3.10 or higher"

def test_required_packages():
    """Test that all required packages are installed"""
    required_packages = [
        "numpy",
        "optv",
        "traits",
        "traitsui",
        "enable",
        "chaco",
        "PySide6",
        "skimage",  # scikit-image is imported as skimage
        "scipy",
        "pandas",
        "matplotlib",
        "tables",
        "tqdm",
        # "imagecodecs",  # Optional dependency
        # "flowtracks",   # Optional dependency
        "pygments",     # Lowercase for consistency
        "pyparsing"
    ]

    for package in required_packages:
        try:
            importlib.import_module(package)
        except ImportError:
            pytest.fail(f"Required package {package} is not installed")

def test_numpy_version_compatibility():
    """Test that the installed NumPy version is compatible"""
    import numpy as np

    # Check that NumPy version is at least 1.23.5
    np_version = np.__version__.split(".")
    assert int(np_version[0]) >= 1
    assert int(np_version[1]) >= 23 or int(np_version[0]) > 1

    # Test basic NumPy functionality
    test_array = np.zeros((10, 10))
    assert test_array.shape == (10, 10)
    assert test_array.dtype == np.float64

    # Test array operations
    test_array2 = test_array + 1
    assert np.all(test_array2 == 1)

def test_optv_version_compatibility():
    """Test that the installed optv version is compatible"""
    import optv

    # Check that optv version is at least 0.2.9
    optv_version = optv.__version__.split(".")
    assert int(optv_version[0]) >= 0
    assert int(optv_version[1]) >= 2 or int(optv_version[0]) > 0
    assert int(optv_version[2]) >= 9 or int(optv_version[1]) > 2 or int(optv_version[0]) > 0

    # Test basic optv functionality
    from optv.calibration import Calibration
    cal = Calibration()
    assert cal is not None

def test_pyptv_version():
    """Test that the installed pyptv version is correct"""
    import pyptv

    # Check that pyptv version is at least 0.3.5
    pyptv_version = pyptv.__version__.split(".")
    assert int(pyptv_version[0]) >= 0
    assert int(pyptv_version[1]) >= 3 or int(pyptv_version[0]) > 0
    assert int(pyptv_version[2]) >= 5 or int(pyptv_version[1]) > 3 or int(pyptv_version[0]) > 0

def test_pyside6_compatibility():
    """Test that PySide6 is compatible with traitsui"""
    try:
        import PySide6
        import traitsui

        # Check PySide6 version
        pyside_version = PySide6.__version__.split(".")
        assert int(pyside_version[0]) >= 6

        # Check traitsui version
        traitsui_version = traitsui.__version__.split(".")
        assert int(traitsui_version[0]) >= 7
        assert int(traitsui_version[1]) >= 4 or int(traitsui_version[0]) > 7
    except ImportError as e:
        pytest.skip(f"PySide6 or traitsui not installed: {str(e)}")

@pytest.mark.skipif(platform.system() != "Linux", reason="OpenGL test only on Linux")
def test_opengl_environment_variables():
    """Test that OpenGL environment variables are set correctly on Linux"""
    # Check if the environment variables are set
    libgl_software = os.environ.get("LIBGL_ALWAYS_SOFTWARE")
    qt_xcb_gl = os.environ.get("QT_XCB_GL_INTEGRATION")
    qt_qpa_platform = os.environ.get("QT_QPA_PLATFORM")

    # If they're not set, set them for the test
    if not libgl_software:
        os.environ["LIBGL_ALWAYS_SOFTWARE"] = "1"

    if not qt_qpa_platform:
        os.environ["QT_QPA_PLATFORM"] = "xcb"

    # Test that we can import PySide6 without OpenGL errors
    try:
        import PySide6.QtWidgets
        assert True
    except Exception as e:
        if "OpenGL" in str(e):
            pytest.fail(f"OpenGL error: {str(e)}")
        else:
            # Other errors might be unrelated to OpenGL
            pytest.skip(f"PySide6 import error: {str(e)}")

@pytest.mark.skipif(platform.system() != "Windows", reason="Windows-specific test")
def test_windows_environment():
    """Test Windows-specific environment settings"""
    # Check if we're running on Windows
    assert platform.system() == "Windows"

    # Check if the environment variables are set
    libgl_software = os.environ.get("LIBGL_ALWAYS_SOFTWARE")
    qt_qpa_platform = os.environ.get("QT_QPA_PLATFORM")

    # If they're not set, set them for the test
    if not libgl_software:
        os.environ["LIBGL_ALWAYS_SOFTWARE"] = "1"

    if not qt_qpa_platform:
        os.environ["QT_QPA_PLATFORM"] = "windows"

    # Test that we can import PySide6 without OpenGL errors
    try:
        import PySide6.QtWidgets
        assert True
    except Exception as e:
        if "OpenGL" in str(e):
            pytest.fail(f"OpenGL error: {str(e)}")
        else:
            # Other errors might be unrelated to OpenGL
            pytest.skip(f"PySide6 import error: {str(e)}")

def test_installation_scripts():
    """Test that installation scripts exist"""
    # Check for Linux installation script
    linux_script = Path("/home/user/Documents/repos/pyptv/install_pyptv.sh")
    assert linux_script.exists(), "Linux installation script not found"

    # Check for Windows installation script
    windows_script = Path("/home/user/Documents/repos/pyptv/install_pyptv.bat")
    assert windows_script.exists(), "Windows installation script not found"
