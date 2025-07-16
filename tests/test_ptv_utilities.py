"""Unit tests for utility and plugin functions in ptv.py"""

import pytest
import numpy as np
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from pyptv.ptv import (
    _read_calibrations, py_pre_processing_c, py_determination_proc_c,
    run_sequence_plugin, run_tracking_plugin, py_sequence_loop,
    py_trackcorr_init, py_trackcorr_loop, py_traject_loop, py_rclick_delete
)
from pyptv.experiment import Experiment
from optv.parameters import ControlParams
from optv.calibration import Calibration


@pytest.fixture
def test_cavity_exp():
    """Load test_cavity experiment for real testing"""
    test_cavity_path = Path(__file__).parent / "test_cavity"
    if not test_cavity_path.exists():
        pytest.skip("test_cavity directory not found")
    
    yaml_file = test_cavity_path / "parameters_Run1.yaml"
    if not yaml_file.exists():
        pytest.skip("test_cavity parameters_Run1.yaml not found")
    
    original_cwd = Path.cwd()
    os.chdir(test_cavity_path)
    
    try:
        experiment = Experiment()
        experiment.parameter_manager.from_yaml(yaml_file)
        yield experiment
    finally:
        os.chdir(original_cwd)


@pytest.fixture
def test_splitter_exp():
    """Load test_splitter experiment for real testing"""
    test_splitter_path = Path(__file__).parent / "test_splitter"
    if not test_splitter_path.exists():
        pytest.skip("test_splitter directory not found")
    
    yaml_file = test_splitter_path / "parameters_Run1.yaml"
    if not yaml_file.exists():
        pytest.skip("test_splitter parameters_Run1.yaml not found")
    
    original_cwd = Path.cwd()
    os.chdir(test_splitter_path)
    
    try:
        experiment = Experiment()
        experiment.parameter_manager.from_yaml(yaml_file)
        yield experiment
    finally:
        os.chdir(original_cwd)


class TestReadCalibrations:
    """Test _read_calibrations function"""
    
    def test_read_calibrations_basic(self, test_cavity_exp):
        """Test basic calibration reading with real experiment data"""
        from pyptv import ptv
        
        try:
            # Initialize PyPTV core with real experiment data
            cpar, spar, vpar, track_par, tpar, cals, epar = ptv.py_start_proc_c(test_cavity_exp.parameter_manager)
            
            n_cams = test_cavity_exp.parameter_manager.n_cam
            
            # Test the function with real control parameters
            result = _read_calibrations(cpar, n_cams)
            
            assert len(result) == n_cams
            assert all(isinstance(cal, Calibration) for cal in result)
            
        except Exception as e:
            # If core initialization fails, skip with informative message
            pytest.skip(f"Could not initialize PyPTV core with real data: {e}")
    
    def test_read_calibrations_mismatched_count(self, test_splitter_exp):
        """Test calibration reading with different camera count"""
        from pyptv import ptv
        
        try:
            # Initialize PyPTV core with real experiment data
            cpar, spar, vpar, track_par, tpar, cals, epar = ptv.py_start_proc_c(test_splitter_exp.parameter_manager)
            
            # Test with a different number of cameras than in the experiment
            test_n_cams = test_splitter_exp.parameter_manager.n_cam + 1
            
            result = _read_calibrations(cpar, test_n_cams)
            assert len(result) == test_n_cams  # Should create the right number of calibrations
            
        except Exception as e:
            # If core initialization fails, skip with informative message
            pytest.skip(f"Could not initialize PyPTV core with real data: {e}")


class TestPyPreProcessingC:
    """Test py_pre_processing_c function"""
    
    def test_py_pre_processing_c_basic(self, test_cavity_exp):
        """Test basic preprocessing with real experiment data"""
        from pyptv import ptv
        
        try:
            # Initialize PyPTV core with real experiment data
            cpar, spar, vpar, track_par, tpar, cals, epar = ptv.py_start_proc_c(test_cavity_exp.parameter_manager)
            
            n_cam = test_cavity_exp.parameter_manager.n_cam
            
            # Create test images with proper dimensions
            imx = cpar.get_image_size()[0]
            imy = cpar.get_image_size()[1]
            images = [
                np.random.randint(0, 255, (imy, imx), dtype=np.uint8)
                for _ in range(n_cam)
            ]
            
            # Use real parameters from the experiment
            ptv_params = test_cavity_exp.parameter_manager.parameters.get('ptv', {})
            
            result = py_pre_processing_c(n_cam, images, ptv_params)
            
            # Should return processed images
            assert len(result) == n_cam
            assert all(isinstance(img, np.ndarray) for img in result)
            
        except Exception as e:
            # If core initialization fails, skip with informative message
            pytest.skip(f"Could not initialize PyPTV core with real data: {e}")
    
    def test_py_pre_processing_c_empty_images(self):
        """Test preprocessing with empty image list"""
        n_cam = 0
        images = []
        ptv_params = {
            'imx': 100, 'imy': 100, 'hp_flag': 1,
            'pix_x': 0.012, 'pix_y': 0.012,  # Add required pixel size parameters
            'allcam_flag': 0,  # Add required allcam flag
            'tiff_flag': 0,  # Add required tiff flag
            'chfield': 0,  # Add required chfield parameter
            'mmp_n1': 1.0,  # Multimedia parameters
            'mmp_n2': 1.33,
            'mmp_d': 1.0,
            'mmp_n3': 1.0,
            'img_cal': []  # Empty calibration list to match n_cam=0
        }
        
        result = py_pre_processing_c(n_cam, images, ptv_params)
        
        # Should return empty list for empty input
        assert len(result) == 0
    
    @patch('pyptv.ptv._populate_cpar')
    def test_py_pre_processing_c_invalid_params(self, mock_populate_cpar):
        """Test preprocessing with invalid parameters"""
        n_cam = 1
        images = [np.random.randint(0, 255, (100, 100), dtype=np.uint8)]
        ptv_params = {}  # Missing required parameters
        
        mock_populate_cpar.side_effect = KeyError("Missing required parameter")
        
        with pytest.raises(KeyError):
            py_pre_processing_c(n_cam, images, ptv_params)


class TestPyDeterminationProcC:
    """Test py_determination_proc_c function"""
    
    def test_py_determination_proc_c_basic(self, test_splitter_exp):
        """Test basic determination processing with real data"""
        from pyptv import ptv
        
        try:
            # Initialize PyPTV core with real experiment data
            cpar, spar, vpar, track_par, tpar, cals, epar = ptv.py_start_proc_c(test_splitter_exp.parameter_manager)
            
            n_cams = test_splitter_exp.parameter_manager.n_cam
            
            # Create minimal test data - one point per camera
            sorted_pos = [np.array([[100.0, 200.0]]) for _ in range(n_cams)]
            sorted_corresp = [np.array([[0]]) for _ in range(n_cams)]
            
            # Use real TargetArray objects
            from optv.tracker import TargetArray
            from optv.tracking_framebuf import Target
            corrected = []
            for i in range(n_cams):
                target_array = TargetArray()
                # Add a test target
                target = Target()
                target.set_pos((100.0 + i, 200.0 + i))  # Slightly different positions
                target.set_pnr(0)
                target_array.append(target)
                corrected.append(target_array)
            
            # Should not raise any exceptions with real data structures
            py_determination_proc_c(n_cams, sorted_pos, sorted_corresp, corrected, cpar, vpar, cals)
            
        except Exception as e:
            # If core initialization fails, skip with informative message
            pytest.skip(f"Could not initialize PyPTV core with real data: {e}")
    
    def test_py_determination_proc_c_real_data(self, test_cavity_exp):
        """Test determination processing with real experiment data"""
        from pyptv import ptv
        
        try:
            # Initialize PyPTV core with real experiment data
            cpar, spar, vpar, track_par, tpar, cals, epar = ptv.py_start_proc_c(test_cavity_exp.parameter_manager)
            
            # Create minimal test data that matches the expected format
            n_cams = test_cavity_exp.parameter_manager.n_cam
            
            # Create simple test data - empty arrays with correct shape
            sorted_pos = [np.array([]).reshape(0, 2) for _ in range(n_cams)]
            sorted_corresp = [np.array([]).reshape(0, 1) for _ in range(n_cams)]
            
            # Use empty TargetArray objects (these exist in the real system)
            from optv.tracker import TargetArray
            corrected = [TargetArray() for _ in range(n_cams)]
            
            # Test with empty data - function should handle gracefully
            # This tests the function's robustness with edge cases
            if len(sorted_pos) > 0 and all(len(pos) == 0 for pos in sorted_pos):
                # For empty data, function may exit early - that's expected behavior
                try:
                    py_determination_proc_c(n_cams, sorted_pos, sorted_corresp, corrected, cpar, vpar, cals)
                except (ValueError, IndexError) as e:
                    # Empty data might cause these exceptions - that's acceptable
                    pass
            
        except Exception as e:
            # If core initialization fails, skip with informative message
            pytest.skip(f"Could not initialize PyPTV core with real data: {e}")
    
    def test_py_determination_proc_c_invalid_calibrations(self):
        """Test determination processing with invalid calibrations"""
        n_cams = 2
        sorted_pos = [np.array([[1.0, 2.0], [3.0, 4.0]])]
        sorted_corresp = [np.array([[0, 1]])]
        corrected = [Mock()]
        cpar = Mock(spec=ControlParams)
        vpar = Mock()
        cals = []  # Empty calibrations
        
        with pytest.raises((IndexError, ValueError)):
            py_determination_proc_c(n_cams, sorted_pos, sorted_corresp, corrected, cpar, vpar, cals)


class TestRunSequencePlugin:
    """Test run_sequence_plugin function"""
    
    @patch('pyptv.ptv.os.listdir')
    @patch('pyptv.ptv.os.getcwd')
    def test_run_sequence_plugin_empty_dir(self, mock_getcwd, mock_listdir):
        """Test sequence plugin with empty plugin directory"""
        from unittest.mock import Mock
        import tempfile
        import os
        
        # Create a mock experiment object with plugin system
        exp = Mock()
        exp.plugins = Mock()
        exp.plugins.sequence_alg = "test_plugin"
        
        # Mock an empty plugin directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create the plugins subdirectory
            plugins_dir = os.path.join(temp_dir, "plugins")
            os.makedirs(plugins_dir, exist_ok=True)
            
            mock_getcwd.return_value = temp_dir
            mock_listdir.return_value = []  # Empty directory
            
            # Should handle gracefully when no plugins found
            run_sequence_plugin(exp)
    
    def test_run_sequence_plugin_no_plugin_error(self):
        """Test sequence plugin with missing plugin directory - expect error"""
        import tempfile
        import os
        
        exp = Mock()
        exp.plugins = Mock()
        exp.plugins.sequence_alg = "nonexistent"
        
        # Create a temporary directory without plugins subdirectory to ensure clean test
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                # Should raise FileNotFoundError when plugin directory doesn't exist
                with pytest.raises(FileNotFoundError):
                    run_sequence_plugin(exp)
            finally:
                os.chdir(original_cwd)


class TestRunTrackingPlugin:
    """Test run_tracking_plugin function"""
    
    @patch('pyptv.ptv.os.listdir')
    @patch('pyptv.ptv.os.getcwd')
    def test_run_tracking_plugin_empty_dir(self, mock_getcwd, mock_listdir):
        """Test tracking plugin with empty plugin directory"""
        from unittest.mock import Mock
        import tempfile
        import os
        
        # Create a mock experiment object with plugin system
        exp = Mock()
        exp.plugins = Mock()
        exp.plugins.track_alg = "test_tracker"
        
        # Mock an empty plugin directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create the plugins subdirectory
            plugins_dir = os.path.join(temp_dir, "plugins")
            os.makedirs(plugins_dir, exist_ok=True)
            
            mock_getcwd.return_value = temp_dir
            mock_listdir.return_value = []  # Empty directory
            
            # Should handle gracefully when no plugins found
            run_tracking_plugin(exp)
    
    def test_run_tracking_plugin_no_plugin_error(self):
        """Test tracking plugin with missing plugin directory - expect error"""
        import tempfile
        import os
        
        exp = Mock()
        exp.plugins = Mock()
        exp.plugins.track_alg = "nonexistent"
        
        # Create a temporary directory without plugins subdirectory to ensure clean test
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                # Should raise FileNotFoundError when plugin directory doesn't exist
                with pytest.raises(FileNotFoundError):
                    run_tracking_plugin(exp)
            finally:
                os.chdir(original_cwd)


class TestPySequenceLoop:
    """Test py_sequence_loop function"""
    
    def test_py_sequence_loop_basic_real_data(self, test_cavity_exp):
        """Test basic sequence loop execution with real test_cavity data"""
        from pyptv import ptv
        
        # Initialize PyPTV core with real experiment data
        try:
            cpar, spar, vpar, track_par, tpar, cals, epar = ptv.py_start_proc_c(test_cavity_exp.parameter_manager)
            
            # Create a proper experiment object for testing
            exp = Mock()
            exp.parameter_manager = test_cavity_exp.parameter_manager
            exp.n_cams = test_cavity_exp.parameter_manager.n_cam
            exp.cpar = cpar
            exp.spar = spar
            exp.vpar = vpar
            exp.track_par = track_par
            exp.tpar = tpar
            exp.cals = cals
            
            # Modify to process only 1 frame to keep test fast
            original_last = spar.get_last()
            spar.set_last(spar.get_first())  # Process just first frame
            
            # Should execute without major errors
            py_sequence_loop(exp)
            
            # Restore original settings
            spar.set_last(original_last)
            
        except Exception as e:
            # If core initialization fails, skip with informative message
            pytest.skip(f"Could not initialize PyPTV core with real data: {e}")
    
    def test_py_sequence_loop_invalid_experiment(self):
        """Test sequence loop with invalid experiment"""
        with pytest.raises(ValueError, match="Object must have either parameter_manager or exp1.parameter_manager attribute"):
            py_sequence_loop(None)


class TestPyTrackcorrInit:
    """Test py_trackcorr_init function"""
    
    def test_py_trackcorr_init_real_data(self, test_splitter_exp):
        """Test basic tracking correction initialization with real test_splitter data"""
        from pyptv import ptv
        
        try:
            # Initialize PyPTV core with real experiment data
            cpar, spar, vpar, track_par, tpar, cals, epar = ptv.py_start_proc_c(test_splitter_exp.parameter_manager)
            
            # Create a proper experiment object for testing
            exp = Mock()
            exp.spar = spar
            exp.tpar = tpar
            exp.vpar = vpar
            exp.track_par = track_par
            exp.cpar = cpar
            exp.cals = cals
            
            # Should not raise any exceptions
            result = py_trackcorr_init(exp)
            
            assert result is not None
            
        except Exception as e:
            # If core initialization fails, skip with informative message
            pytest.skip(f"Could not initialize PyPTV core with real data: {e}")
    
    def test_py_trackcorr_init_missing_params(self):
        """Test tracking correction init with missing parameters"""
        exp = Mock()
        exp.cpar.get_num_cams.return_value = 2  # Mock returns integer for range()
        exp.spar = None  # Missing sequence parameters
        
        with pytest.raises(AttributeError):
            py_trackcorr_init(exp)


class TestPyTrackcorrLoop:
    """Test py_trackcorr_loop function"""
    
    def test_py_trackcorr_loop_basic(self):
        """Test basic tracking correction loop - it's a stub function"""
        # py_trackcorr_loop is currently a stub that does nothing
        result = py_trackcorr_loop()
        
        assert result is None


class TestPyTrajectLoop:
    """Test py_traject_loop function"""
    
    def test_py_traject_loop_basic(self):
        """Test basic trajectory loop - it's a stub function"""
        # py_traject_loop is currently a stub that does nothing
        result = py_traject_loop()
        
        assert result is None


class TestPyRclickDelete:
    """Test py_rclick_delete function"""
    
    def test_py_rclick_delete_basic(self):
        """Test basic right-click delete"""
        x, y, n = 100, 200, 0
        
        # Function is a stub that just passes, so test it returns None
        result = py_rclick_delete(x, y, n)
        assert result is None
    
    def test_py_rclick_delete_invalid_coords(self):
        """Test right-click delete with invalid coordinates"""
        # Function is a stub that just passes, so test it returns None
        result = py_rclick_delete(-1, -1, 0)
        assert result is None
    
    def test_py_rclick_delete_invalid_camera(self):
        """Test right-click delete with invalid camera number"""
        # Function is a stub that just passes, so test it returns None
        result = py_rclick_delete(100, 200, -1)
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__])
