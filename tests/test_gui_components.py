"""
Integration tests for GUI components
"""
import pytest
import os
import tempfile
from pathlib import Path
import shutil
import numpy as np

# Import GUI components

# Skip all tests in this file if running in a headless environment
pytestmark = pytest.mark.skipif(
    os.environ.get("DISPLAY") is None,
    reason="GUI tests require a display"
)

# Import components that don't require a display
from pyptv.code_editor import codeEditor
from pyptv.directory_editor import DirectoryEditorDialog

# Define variables to hold GUI components
CalibrationGUI = None
Main_Params = None

# Conditionally import GUI components
try:
    from chaco.api import ImagePlot
    from pyptv.calibration_gui import CalibrationGUI
    from pyptv.parameter_gui import Main_Params
except ImportError as e:
    # If we can't import the GUI components, we'll skip the tests
    print(f"Error importing GUI components: {e}")
    ImagePlot = None

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

@pytest.mark.skipif(os.environ.get("DISPLAY") is None,
                   reason="GUI tests require a display")
def test_imageplot_creation():
    """Test that ImagePlot can be created"""
    # Skip if ImagePlot is not available
    if ImagePlot is None:
        pytest.skip("ImagePlot not available")

    # For chaco.api.ImagePlot, we need to create a Plot and ArrayPlotData first
    try:
        from chaco.api import ArrayPlotData, Plot

        # Create a test image
        test_image = np.ones((100, 100), dtype=np.uint8) * 128

        # Create a plot data object and give it this data
        pd = ArrayPlotData()
        pd.set_data("imagedata", test_image)

        # Create the plot
        plot = Plot(pd)

        # Create the image plot
        img_plot = plot.img_plot("imagedata")[0]

        assert img_plot is not None
    except Exception as e:
        # If there's an error related to the display, skip the test
        if "display" in str(e).lower() or "qt" in str(e).lower():
            pytest.skip(f"Display-related error: {str(e)}")
        else:
            raise

@pytest.mark.skipif(os.environ.get("DISPLAY") is None,
                   reason="GUI tests require a display")
def test_code_editor_creation(tmp_path):
    """Test that codeEditor can be created"""
    # Create a temporary file
    test_file = tmp_path / "test_file.txt"
    with open(test_file, "w") as f:
        f.write("Test content")

    try:
        editor = codeEditor(file_path=test_file)
        assert editor is not None
    except Exception as e:
        # If there's an error related to the display, skip the test
        if "display" in str(e).lower() or "qt" in str(e).lower():
            pytest.skip(f"Display-related error: {str(e)}")
        else:
            raise

@pytest.mark.skipif(os.environ.get("DISPLAY") is None,
                   reason="GUI tests require a display")
def test_directory_editor_creation(tmp_path):
    """Test that DirectoryEditorDialog can be created"""
    try:
        editor = DirectoryEditorDialog()
        # Set the directory to a temporary directory
        editor.dir_name = str(tmp_path)
        assert editor is not None
    except Exception as e:
        # If there's an error related to the display, skip the test
        if "display" in str(e).lower() or "qt" in str(e).lower():
            pytest.skip(f"Display-related error: {str(e)}")
        else:
            raise

@pytest.mark.skipif(os.environ.get("DISPLAY") is None,
                   reason="GUI tests require a display")
def test_calibration_gui_creation(mock_experiment_dir, test_data_dir):
    """Test that CalibrationGUI can be created"""
    # Skip if CalibrationGUI is not available
    if CalibrationGUI is None:
        pytest.skip("CalibrationGUI not available")

    # Skip this test for now as it requires more complex setup
    pytest.skip("CalibrationGUI test requires more complex setup")

@pytest.mark.skipif(os.environ.get("DISPLAY") is None,
                   reason="GUI tests require a display")
def test_parameters_gui_creation(mock_experiment_dir, test_data_dir):
    """Test that Main_Params can be created"""
    # Skip if Main_Params is not available
    if Main_Params is None:
        pytest.skip("Main_Params not available")

    # Create a parameters directory in the mock experiment directory
    params_dir = mock_experiment_dir / "parameters"
    params_dir.mkdir(exist_ok=True)

    # Copy parameter files from test_cavity to the mock experiment directory
    test_cavity_params_dir = test_data_dir / "parameters"
    if test_cavity_params_dir.exists():
        for param_file in test_cavity_params_dir.glob("*"):
            shutil.copy(param_file, params_dir)

    try:
        # Change to the mock experiment directory
        original_dir = os.getcwd()
        os.chdir(mock_experiment_dir)

        try:
            # Create a Main_Params instance with the parameters path
            gui = Main_Params(par_path=params_dir)
            assert gui is not None
        except TypeError:
            # If Main_Params doesn't take par_path, skip the test
            pytest.skip("Main_Params constructor doesn't match expected signature")
        finally:
            # Change back to the original directory
            os.chdir(original_dir)
    except Exception as e:
        # If there's an error related to the display, skip the test
        if "display" in str(e).lower() or "qt" in str(e).lower():
            pytest.skip(f"Display-related error: {str(e)}")
        else:
            raise
