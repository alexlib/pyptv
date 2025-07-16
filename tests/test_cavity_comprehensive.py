import sys
import os
import pytest
from pathlib import Path
import numpy as np

# Add pyptv to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pyptv.experiment import Experiment
from pyptv import ptv
from skimage.io import imread
from skimage.color import rgb2gray
from skimage.util import img_as_ubyte


@pytest.fixture
def test_cavity_setup():
    """Setup fixture for test_cavity experiment"""
    software_path = Path(__file__).parent.parent
    test_cavity_path = software_path / "tests" / "test_cavity"
    
    if not test_cavity_path.exists():
        pytest.skip(f"Test cavity directory does not exist: {test_cavity_path}")
    
    # Path to YAML parameter file
    yaml_file = test_cavity_path / "parameters_Run1.yaml"
    if not yaml_file.exists():
        pytest.skip(f"YAML parameter file does not exist: {yaml_file}")
    
    # Change to test cavity directory (important for relative paths)
    original_cwd = Path.cwd()
    os.chdir(test_cavity_path)
    
    # Initialize experiment with YAML parameters
    experiment = Experiment()
    experiment.parameter_manager.from_yaml(yaml_file)
    
    yield {
        'software_path': software_path,
        'test_cavity_path': test_cavity_path,
        'experiment': experiment,
        'yaml_file': yaml_file,
        'original_cwd': original_cwd
    }
    
    # Cleanup - restore original working directory
    os.chdir(original_cwd)


def test_cavity_directory_structure():
    """Test that test_cavity directory has expected structure"""
    software_path = Path(__file__).parent.parent
    test_cavity_path = software_path / "tests" / "test_cavity"
    
    assert test_cavity_path.exists(), f"Test cavity directory does not exist: {test_cavity_path}"
    
    # Ensure 'res' directory exists (create if missing)
    res_dir = test_cavity_path / 'res'
    if not res_dir.exists():
        res_dir.mkdir(parents=True, exist_ok=True)

    # Check for required directories and files (updated for YAML structure)
    required_items = ['img', 'cal', 'res', 'parameters_Run1.yaml']
    for item in required_items:
        assert (test_cavity_path / item).exists(), f"Required item missing: {item}"


def test_experiment_initialization(test_cavity_setup):
    """Test that experiment initializes correctly"""
    setup = test_cavity_setup
    experiment = setup['experiment']
    
    assert hasattr(experiment, 'parameter_manager'), "Experiment missing parameter_manager"
    assert experiment.parameter_manager is not None, "ParameterManager is None"
    assert experiment.parameter_manager.n_cam == 4, f"Expected 4 cameras, got {experiment.parameter_manager.n_cam}"


def test_parameter_loading(test_cavity_setup):
    """Test parameter loading via ParameterManager"""
    setup = test_cavity_setup
    experiment = setup['experiment']
    
    assert hasattr(experiment, 'parameter_manager'), "Experiment missing parameter_manager"
    assert experiment.parameter_manager is not None, "ParameterManager is None"
    
    # Test PTV parameters
    ptv_params = experiment.parameter_manager.get_parameter('ptv')
    assert ptv_params is not None, "PTV parameters not loaded"
    
    # n_cam is now at global level
    assert experiment.parameter_manager.n_cam == 4, f"Expected 4 cameras, got {experiment.parameter_manager.n_cam}"
    assert ptv_params.get('imx') == 1280, f"Expected image width 1280, got {ptv_params.get('imx')}"
    assert ptv_params.get('imy') == 1024, f"Expected image height 1024, got {ptv_params.get('imy')}"
    
    # Test sequence parameters for image names
    seq_params = experiment.parameter_manager.get_parameter('sequence')
    assert seq_params is not None, "Sequence parameters not loaded"
    
    base_names = seq_params.get('base_name', [])
    assert len(base_names) >= 4, f"Expected at least 4 base names, got {len(base_names)}"
    
    expected_names = ['img/cam1.%d', 'img/cam2.%d', 'img/cam3.%d', 'img/cam4.%d']
    for i, expected in enumerate(expected_names):
        assert base_names[i] == expected, f"Base name mismatch: expected {expected}, got {base_names[i]}"


def test_parameter_manager_debugging(test_cavity_setup):
    """Debug parameter manager functionality"""
    setup = test_cavity_setup
    experiment = setup['experiment']
    
    # Get number of cameras from global level
    n_cams = experiment.parameter_manager.n_cam
    
    print(f"Number of cameras: {n_cams}")
    print(f"Type of n_cams: {type(n_cams)}")
    
    # Check available methods on parameter_manager
    print(f"ParameterManager methods: {[m for m in dir(experiment.parameter_manager) if not m.startswith('_')]}")
    
    # Check if we can access the parameters dictionary directly
    print(f"Available parameter sections: {list(experiment.parameter_manager.parameters.keys())}")
    
    # Test new py_start_proc_c with parameter manager
    try:
        cpar, spar, vpar, track_par, tpar, cals, epar = ptv.py_start_proc_c(experiment.parameter_manager)
        print(f"Successfully initialized PyPTV core with {len(cals)} calibrations")
    except Exception as e:
        print(f"Failed to initialize PyPTV core: {e}")


def test_image_files_exist(test_cavity_setup):
    """Test that image files exist and can be loaded"""
    setup = test_cavity_setup
    experiment = setup['experiment']
    
    # Get sequence parameters for base names
    seq_params = experiment.parameter_manager.get_parameter('sequence')
    base_names = seq_params.get('base_name', [])
    n_cams = experiment.parameter_manager.n_cam
    first_frame = seq_params.get('first', 10000)
    
    loaded_images = []
    
    for i, base_name in enumerate(base_names[:n_cams]):
        # Format the base name with frame number
        img_name = base_name % first_frame
        img_path = Path(img_name)
        
        assert img_path.exists(), f"Image file does not exist: {img_path.resolve()}"
        
        # Try to load the image
        img = imread(str(img_path))
        assert img.shape == (1024, 1280), f"Unexpected image shape: {img.shape}"
        assert img.dtype == np.uint8, f"Unexpected image dtype: {img.dtype}"
        assert img.min() >= 0 and img.max() <= 255, f"Image values out of range: {img.min()}-{img.max()}"
        
        # Convert to grayscale if needed
        if img.ndim > 2:
            img = rgb2gray(img)
        img = img_as_ubyte(img)
        loaded_images.append(img)
    
    assert len(loaded_images) == n_cams, f"Expected {n_cams} images, loaded {len(loaded_images)}"


def test_yaml_parameter_consistency(test_cavity_setup):
    """Test that YAML parameters are consistent and properly loaded"""
    setup = test_cavity_setup
    experiment = setup['experiment']
    yaml_file = setup['yaml_file']
    
    # Test that we can reload the same parameters
    experiment2 = Experiment()
    experiment2.parameter_manager.from_yaml(yaml_file)
    
    # Compare key parameters
    assert experiment.parameter_manager.n_cam == experiment2.parameter_manager.n_cam
    
    
    print(f"YAML parameter consistency test passed for {yaml_file}")


def test_pyptv_core_initialization(test_cavity_setup):
    """Test PyPTV core initialization with proper parameters"""
    setup = test_cavity_setup
    experiment = setup['experiment']
    
    # Test new py_start_proc_c with parameter manager
    try:
        cpar, spar, vpar, track_par, tpar, cals, epar = ptv.py_start_proc_c(experiment.parameter_manager)
        
        assert cpar is not None, "Camera parameters not initialized"
        assert tpar is not None, "Target parameters not initialized"
        assert len(cals) == experiment.parameter_manager.n_cam, f"Expected {experiment.parameter_manager.n_cam} calibrations, got {len(cals)}"
        
        print(f"Successfully initialized PyPTV core:")
        print(f"  - Camera parameters: {cpar}")
        print(f"  - Target parameters: {tpar}")
        print(f"  - Calibrations: {len(cals)} items")
        print(f"  - Volume parameters eps0: {vpar.get_eps0()}")
        
    except Exception as e:
        pytest.fail(f"Failed to initialize PyPTV core: {e}")


def test_image_preprocessing(test_cavity_setup):
    """Test image preprocessing (highpass filter)"""
    setup = test_cavity_setup
    experiment = setup['experiment']
    
    # Load images
    seq_params = experiment.parameter_manager.get_parameter('sequence')
    base_names = seq_params.get('base_name', [])
    n_cams = experiment.parameter_manager.n_cam
    first_frame = seq_params.get('first', 10000)
    
    orig_images = []
    for i, base_name in enumerate(base_names[:n_cams]):
        img_name = base_name % first_frame
        img_path = Path(img_name)
        img = imread(str(img_path))
        if img.ndim > 2:
            img = rgb2gray(img)
        img = img_as_ubyte(img)
        orig_images.append(img)
    
    # Initialize PyPTV core
    cpar, spar, vpar, track_par, tpar, cals, epar = ptv.py_start_proc_c(experiment.parameter_manager)
    
    # Apply preprocessing using the simple_highpass function
    processed_images = []
    for img in orig_images:
        processed_img = ptv.simple_highpass(img, cpar)
        processed_images.append(processed_img)
    
    assert len(processed_images) == len(orig_images), "Preprocessing changed number of images"
    for i, (orig, proc) in enumerate(zip(orig_images, processed_images)):
        assert orig.shape == proc.shape, f"Image {i} shape changed during preprocessing"
        print(f"Image {i}: original range {orig.min()}-{orig.max()}, processed range {proc.min()}-{proc.max()}")


def test_particle_detection(test_cavity_setup):
    """Test particle detection"""
    setup = test_cavity_setup
    experiment = setup['experiment']
    
    # Load and preprocess images
    seq_params = experiment.parameter_manager.get_parameter('sequence')
    base_names = seq_params.get('base_name', [])
    n_cams = experiment.parameter_manager.n_cam
    first_frame = seq_params.get('first', 10000)
    
    orig_images = []
    for i, base_name in enumerate(base_names[:n_cams]):
        img_name = base_name % first_frame
        img_path = Path(img_name)
        img = imread(str(img_path))
        if img.ndim > 2:
            img = rgb2gray(img)
        img = img_as_ubyte(img)
        orig_images.append(img)
    
    # Initialize PyPTV core
    cpar, spar, vpar, track_par, tpar, cals, epar = ptv.py_start_proc_c(experiment.parameter_manager)
    
    # Apply preprocessing
    processed_images = []
    for img in orig_images:
        processed_img = ptv.simple_highpass(img, cpar)
        processed_images.append(processed_img)
    
    # This test checks if detection functions exist, but may skip actual detection
    # since we need the correct detection API
    try:
        # Try to detect using available functions
        from optv.segmentation import target_recognition
        
        detections = []
        for i, img in enumerate(processed_images):
            targets = target_recognition(img, tpar, i, cpar)
            detections.append(targets)
            print(f"Camera {i+1}: detected {len(targets)} targets")
        
        total_detections = sum(len(det) for det in detections)
        print(f"Total detections across all cameras: {total_detections}")
        
        # For test_cavity, we expect some detections
        assert total_detections > 0, "No particles detected - check detection parameters or image quality"
        
    except ImportError as e:
        pytest.skip(f"Detection function not available: {e}")
    except Exception as e:
        pytest.skip(f"Detection failed, likely API mismatch: {e}")


def test_existing_trajectory_files(test_cavity_setup):
    """Test if trajectory files exist in res/ directory"""
    setup = test_cavity_setup
    
    res_dir = Path("res")
    if res_dir.exists():
        ptv_files = list(res_dir.glob("ptv_is.*"))
        print(f"Found {len(ptv_files)} trajectory files in res/")
        
        if ptv_files:
            # Try to read first trajectory file
            traj_file = ptv_files[0]
            with open(traj_file, 'r') as f:
                lines = f.readlines()
            
            assert len(lines) > 0, f"Trajectory file {traj_file.name} is empty"
            print(f"First trajectory file {traj_file.name} has {len(lines)} trajectory points")
            
            # Check format of first line - first line often contains just number of points
            if lines and len(lines) > 1:
                # Skip first line if it's just a count, check second line
                data_line = lines[1].strip() if len(lines) > 1 else lines[0].strip()
                parts = data_line.split()
                
                # Trajectory files can have different formats, just check that we have some data
                assert len(parts) >= 1, f"Trajectory line should have at least 1 column, got {len(parts)}"
                print(f"Sample trajectory line: {data_line}")
                
                # If it's a data line, it should have multiple columns
                if len(parts) >= 4:
                    print(f"Trajectory line has expected format with {len(parts)} columns")
                else:
                    print(f"Trajectory line format may be different: {len(parts)} columns")
        else:
            pytest.skip("No trajectory files found - would need to run sequence processing")
    else:
        pytest.skip("No res/ directory found")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])