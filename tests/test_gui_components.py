"""
Integration tests for GUI components
"""

import pytest
import os
import tempfile
from pathlib import Path
import shutil
import numpy as np
from pyptv.code_editor import codeEditor
from pyptv.directory_editor import DirectoryEditorDialog

# Import GUI components

# Skip all tests in this file if running in a headless environment
pytestmark = pytest.mark.skipif(
    os.environ.get("DISPLAY") is None, reason="GUI tests require a display"
)

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
    for param_file in [
        "criteria.par",
        "detect_plate.par",
        "orient.par",
        "pft_par.par",
        "targ_rec.par",
        "track.par",
    ]:
        with open(params_dir / param_file, "w") as f:
            f.write("# Test parameter file\n")

    yield exp_dir
    shutil.rmtree(temp_dir)


@pytest.mark.skipif(
    os.environ.get("DISPLAY") is None, reason="GUI tests require a display"
)
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


@pytest.mark.skipif(
    os.environ.get("DISPLAY") is None, reason="GUI tests require a display"
)
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


@pytest.mark.skipif(
    os.environ.get("DISPLAY") is None, reason="GUI tests require a display"
)
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


@pytest.mark.skipif(
    os.environ.get("DISPLAY") is None, reason="GUI tests require a display"
)
def test_calibration_gui_creation(mock_experiment_dir, test_data_dir):
    """Test that CalibrationGUI can be created"""
    # Skip if CalibrationGUI is not available
    if CalibrationGUI is None:
        pytest.skip("CalibrationGUI not available")

    try:
        # Import the Experiment class
        from pyptv.experiment import Experiment
        
        # Create a test YAML file in the mock experiment directory
        yaml_file = mock_experiment_dir / "parameters_test.yaml"
        yaml_content = """
n_cam: 4
ptv:
  img_name: ['img1.tif', 'img2.tif', 'img3.tif', 'img4.tif']
  img_cal: ['cal1.tif', 'cal2.tif', 'cal3.tif', 'cal4.tif']
  hp_flag: true
  allcam_flag: false
  tiff_flag: true
  imx: 1280
  imy: 1024
  pix_x: 17.0
  pix_y: 17.0
  chfield: 0
  mmp_n1: 1.0
  mmp_n2: 1.33
  mmp_n3: 1.46
  mmp_d: 1.0
  splitter: false
cal_ori:
  fixp_name: 'fixp_file'
  img_cal_name: ['cal1', 'cal2', 'cal3', 'cal4']
  img_ori: ['ori1', 'ori2', 'ori3', 'ori4']
  tiff_flag: true
  pair_flag: false
  chfield: 0
detect_plate:
  gvth_1: 25
  gvth_2: 25
  gvth_3: 25
  gvth_4: 25
  tol_dis: 5
  min_npix: 1
  max_npix: 20
  min_npix_x: 1
  max_npix_x: 20
  min_npix_y: 1
  max_npix_y: 20
  sum_grey: 12
  size_cross: 4
"""
        with open(yaml_file, 'w') as f:
            f.write(yaml_content)

        # Create an Experiment object and add the parameter set
        experiment = Experiment()
        experiment.addParamset("test", yaml_file)
        experiment.setActive(0)

        # Create a CalibrationGUI instance with the Experiment object
        gui = CalibrationGUI(experiment)
        assert gui is not None
        assert gui.n_cams == 4  # Should get this from the experiment
        print("✓ CalibrationGUI created successfully with Experiment object")
        
    except Exception as e:
        # If there's an error related to the display, skip the test
        if "display" in str(e).lower() or "qt" in str(e).lower() or "opengl" in str(e).lower():
            pytest.skip(f"Display-related error: {str(e)}")
        else:
            raise


@pytest.mark.skipif(
    os.environ.get("DISPLAY") is None, reason="GUI tests require a display"
)
def test_parameters_gui_creation(mock_experiment_dir, test_data_dir):
    """Test that Main_Params can be created"""
    # Skip if Main_Params is not available
    if Main_Params is None:
        pytest.skip("Main_Params not available")

    try:
        # Import the Experiment class
        from pyptv.experiment import Experiment
        
        # Create a test YAML file in the mock experiment directory
        yaml_file = mock_experiment_dir / "parameters_test.yaml"
        yaml_content = """
n_cam: 4
ptv:
  img_name: ['img1.tif', 'img2.tif', 'img3.tif', 'img4.tif']
  img_cal: ['cal1.tif', 'cal2.tif', 'cal3.tif', 'cal4.tif']
  hp_flag: true
  allcam_flag: false
  tiff_flag: true
  imx: 1280
  imy: 1024
  pix_x: 17.0
  pix_y: 17.0
  chfield: 0
  mmp_n1: 1.0
  mmp_n2: 1.33
  mmp_n3: 1.46
  mmp_d: 1.0
  splitter: false
cal_ori:
  fixp_name: 'fixp_file'
  img_cal_name: ['cal1', 'cal2', 'cal3', 'cal4']
  img_ori: ['ori1', 'ori2', 'ori3', 'ori4']
  tiff_flag: true
  pair_flag: false
  chfield: 0
targ_rec:
  gvthres: [25, 25, 25, 25]
  disco: 5
  nnmin: 1
  nnmax: 20
  nxmin: 1
  nxmax: 20
  nymin: 1
  nymax: 20
  sumg_min: 12
  cr_sz: 4
sequence:
  base_name: ['seq1_', 'seq2_', 'seq3_', 'seq4_']
  first: 1001
  last: 1100
criteria:
  X_lay: [-100.0, 100.0]
  Zmin_lay: [10.0, 20.0]
  Zmax_lay: [50.0, 60.0]
  cnx: 0.5
  cny: 0.5
  cn: 0.5
  csumg: 12.0
  corrmin: 0.5
  eps0: 0.1
masking:
  mask_flag: false
  mask_base_name: ''
pft_version:
  Existing_Target: false
track:
  dvxmin: -50.0
  dvxmax: 50.0
  dvymin: -50.0
  dvymax: 50.0
  dvzmin: -50.0
  dvzmax: 50.0
  angle: 0.5
  dacc: 5.0
  flagNewParticles: true
"""
        with open(yaml_file, 'w') as f:
            f.write(yaml_content)

        # Create an Experiment object and add the parameter set
        experiment = Experiment()
        experiment.addParamset("test", yaml_file)
        experiment.setActive(0)

        # Create a Main_Params instance with the Experiment object
        gui = Main_Params(experiment)
        assert gui is not None
        assert gui.Num_Cam == 4
        assert gui.Name_1_Image == 'img1.tif'
        print("✓ Main_Params created successfully with Experiment object")
        
    except Exception as e:
        # If there's an error related to the display, skip the test
        if "display" in str(e).lower() or "qt" in str(e).lower():
            pytest.skip(f"Display-related error: {str(e)}")
        else:
            raise


if __name__ == "__main__":
    # Run the tests if this script is executed directly
    pytest.main([__file__, "-v", "--tb=short"])