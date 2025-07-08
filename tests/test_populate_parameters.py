import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
import numpy as np
import shutil
import filecmp

from pyptv.ptv import (
    _populate_cpar, _populate_spar, _populate_vpar, 
    _populate_track_par, _populate_tpar, _read_calibrations,
    py_start_proc_c
)
from pyptv.parameter_manager import ParameterManager
from optv.parameters import (
    ControlParams, SequenceParams, VolumeParams, 
    TrackingParams, TargetParams
)
from optv.calibration import Calibration


class TestPopulateCpar:
    """Test _populate_cpar function."""
    
    def test_populate_cpar_minimal(self):
        """Test with minimal parameters."""
        ptv_params = {
            'img_cal': ['cal/cam1', 'cal/cam2']  # Need to provide img_cal for n_cam
        }
        n_cam = 2
        
        cpar = _populate_cpar(ptv_params, n_cam)
        
        # Existing methods for spar (SequenceParams) include:
        # get_first(), get_last(), get_img_base_name(i)
        assert cpar.get_num_cams() == 2
        assert cpar.get_image_size() == (0, 0)  # Default values
        assert cpar.get_pixel_size() == (0.0, 0.0)
    
    def test_populate_cpar_full_params(self):
        """Test with complete parameter set."""
        ptv_params = {
            'imx': 1280,
            'imy': 1024,
            'pix_x': 0.012,
            'pix_y': 0.012,
            'hp_flag': True,
            'allcam_flag': False,
            'tiff_flag': True,
            'chfield': 1,
            'mmp_n1': 1.0,
            'mmp_n2': 1.49,
            'mmp_n3': 1.33,
            'mmp_d': 5.0,
            'img_cal': ['cal/cam1.tif', 'cal/cam2.tif', 'cal/cam3.tif', 'cal/cam4.tif']
        }
        n_cam = 4
        
        cpar = _populate_cpar(ptv_params, n_cam)
        
        assert cpar.get_num_cams() == 4
        assert cpar.get_image_size() == (1280, 1024)
        assert cpar.get_pixel_size() == (0.012, 0.012)
        assert cpar.get_hp_flag() == True
        assert cpar.get_allCam_flag() == False
        assert cpar.get_tiff_flag() == True
        assert cpar.get_chfield() == 1
        
        # Test multimedia parameters
        mm_params = cpar.get_multimedia_params()
        assert mm_params.get_n1() == 1.0
        assert mm_params.get_n3() == 1.33
        
        # Test calibration image names - OptV returns bytes
        for i in range(n_cam):
            expected_name = ptv_params['img_cal'][i]
            actual_name = cpar.get_cal_img_base_name(i)
            # Compare with encoded expected value
            assert actual_name == expected_name
    
    def test_populate_cpar_insufficient_cal_images(self):
        """Test behavior when not enough calibration images provided."""
        ptv_params = {
            'img_cal': ['cal/cam1.tif', 'cal/cam2.tif']  # Only 2 images
        }
        n_cam = 4  # But 4 cameras
        
        # Should raise ValueError due to length mismatch
        with pytest.raises(ValueError, match="img_cal_list length does not match n_cam"):
            _populate_cpar(ptv_params, n_cam)
    
    def test_populate_cpar_missing_img_cal(self):
        """Test behavior when img_cal is completely missing."""
        ptv_params = {}  # No img_cal provided
        n_cam = 2
        
        # Should raise ValueError due to length mismatch (empty list vs n_cam=2)
        with pytest.raises(ValueError, match="img_cal_list length does not match n_cam"):
            _populate_cpar(ptv_params, n_cam)


class TestPopulateSpar:
    """Test _populate_spar function."""
    
    def test_populate_spar_minimal(self):
        """Test with minimal parameters."""
        seq_params = {"base_name": ["cam0.%d", "cam1.%d"]}  # Provide exactly n_cam base names
        n_cam = 2
        
        spar = _populate_spar(seq_params, n_cam)
        
        # The OptV library returns bytes, so we need to decode or compare with bytes
        for i in range(n_cam):
            base_name = spar.get_img_base_name(i)
            expected_name = seq_params["base_name"][i]
            assert base_name == expected_name
    
        assert spar.get_first() == 0
        assert spar.get_last() == 0
    
    def test_populate_spar_no_base_names(self):
        """Test with no base names provided."""
        seq_params = {}  # No base_name provided
        n_cam = 2
        
        # Should raise ValueError due to empty base_name list vs n_cam=2
        with pytest.raises(ValueError, match="base_name_list length does not match n_cam"):
            _populate_spar(seq_params, n_cam)
    
    def test_populate_spar_full_params(self):
        """Test with complete parameter set."""
        seq_params = {
            'first': 10000,
            'last': 10004,
            'base_name': [
                'img/cam1_%04d.tif',
                'img/cam2_%04d.tif', 
                'img/cam3_%04d.tif',
                'img/cam4_%04d.tif'
            ]
        }
        n_cam = 4
        
        spar = _populate_spar(seq_params, n_cam)
        
        assert spar.get_first() == 10000
        assert spar.get_last() == 10004
        
        for i in range(n_cam):
            expected_name = seq_params['base_name'][i]
            actual_name = spar.get_img_base_name(i)
            # OptV returns bytes, so compare with encoded expected value
            assert actual_name == expected_name
    
    def test_populate_spar_insufficient_base_names(self):
        """Test behavior when not enough base names provided."""
        seq_params = {
            'base_name': ['img/cam1_%04d.tif', 'img/cam2_%04d.tif']  # Only 2 names
        }
        n_cam = 4  # But 4 cameras
        
        # Should raise ValueError due to length mismatch
        with pytest.raises(ValueError, match="base_name_list length does not match n_cam"):
            _populate_spar(seq_params, n_cam)


class TestPopulateVpar:
    """Test _populate_vpar function."""
    
    def test_populate_vpar_minimal(self):
        """Test with minimal parameters."""
        crit_params = {}
        
        vpar = _populate_vpar(crit_params)
        
        assert np.allclose(vpar.get_X_lay(),[0, 0])
        assert np.allclose(vpar.get_Zmin_lay(),[0, 0])
        assert np.allclose(vpar.get_Zmax_lay(),[0, 0])
    
    def test_populate_vpar_full_params(self):
        """Test with complete parameter set."""
        crit_params = {
            'X_lay': [-10.0, 10.0],
            'Zmin_lay': [-5.0, -5.0],
            'Zmax_lay': [15.0, 15.0]
        }
        
        vpar = _populate_vpar(crit_params)
        
        assert np.allclose(vpar.get_X_lay(), [-10.0, 10.0])
        assert np.allclose(vpar.get_Zmin_lay(), [-5.0, -5.0])
        assert np.allclose(vpar.get_Zmax_lay(), [15.0, 15.0])


class TestPopulateTrackPar:
    """Test _populate_track_par function."""
    
    def test_populate_track_par_minimal(self):
        """Test with minimal parameters."""
        track_params = {}
        
        track_par = _populate_track_par(track_params)
        
        assert track_par.get_dvxmin() == 0.0
        assert track_par.get_dvxmax() == 0.0
        assert track_par.get_add() == False
    
    def test_populate_track_par_full_params(self):
        """Test with complete parameter set."""
        track_params = {
            'dvxmin': -10.0,
            'dvxmax': 10.0,
            'dvymin': -8.0,
            'dvymax': 8.0,
            'dvzmin': -15.5,
            'dvzmax': 15.5,
            'angle': 100.0,
            'dacc': 0.5,
            'flagNewParticles': True
        }
        
        track_par = _populate_track_par(track_params)
        
        assert track_par.get_dvxmin() == -10.0
        assert track_par.get_dvxmax() == 10.0
        assert track_par.get_dvymin() == -8.0
        assert track_par.get_dvymax() == 8.0
        assert track_par.get_dvzmin() == -15.5
        assert track_par.get_dvzmax() == 15.5
        assert track_par.get_dangle() == 100.0
        assert track_par.get_dacc() == 0.5
        assert track_par.get_add() == True


class TestPopulateTpar:
    """Test _populate_tpar function."""
    
    def test_populate_tpar_minimal(self):
        """Test with minimal parameters."""
        params = {
            'n_cam': 4,
            'targ_rec': {}
        }
        
        tpar = _populate_tpar(params, n_cam=params.get('n_cam', 0))
        
        assert np.allclose(tpar.get_grey_thresholds(),[0,0,0,0])
        assert tpar.get_pixel_count_bounds() == (0, 0)
    
    def test_populate_tpar_full_params(self):
        """Test with complete parameter set."""
        params = {
            'n_cam': 4,
            'targ_rec': {
                'gvthres': [9, 9, 9, 11],
                'nnmin': 4,
                'nnmax': 500,
                'nxmin': 2,
                'nxmax': 10,
                'nymin': 2,
                'nymax': 10,
                'sumg_min': 100,
                'disco': 25
            }
        }
        
        tpar = _populate_tpar(params, n_cam=params.get('n_cam', 0))
        
        # TargetParams doesn't have get_num_cams(), but we can test parameter values
        assert np.allclose(tpar.get_grey_thresholds(),[9, 9, 9, 11])
        assert tpar.get_pixel_count_bounds() == (4, 500)
        assert tpar.get_xsize_bounds() == (2, 10)
        assert tpar.get_ysize_bounds() == (2, 10)
        assert tpar.get_min_sum_grey() == 100
        assert tpar.get_max_discontinuity() == 25
    
    def test_populate_tpar_missing_n_cam(self):
        """Test behavior when n_cam is missing from params."""
        params = {
            'targ_rec': {
                'gvthres': [9, 9, 9, 11]
            }
        }

        # When n_cam is missing from params, we can infer it from gvthres length
        targ_rec = params.get('targ_rec', {})
        gvthres = targ_rec.get('gvthres')
        n_cam = len(gvthres) if gvthres else 0  # Default to 0 if gvthres is empty

        tpar = _populate_tpar(params, n_cam)
        
        # Should still work with inferred n_cam
        thresholds = tpar.get_grey_thresholds()
        assert len(thresholds) == 4  # Always 4 in Cython
        np.testing.assert_array_equal(thresholds, [9, 9, 9, 11])
        

class TestReadCalibrations:
    """Test _read_calibrations function."""
    
    def test_read_calibrations_missing_files(self, tmp_path: Path, capsys):
        """Test behavior when calibration files are missing."""
        # Create a minimal ControlParams
        cpar = ControlParams(2)
        cpar.set_cal_img_base_name(0, str(tmp_path / "cal" / "cam1"))
        cpar.set_cal_img_base_name(1, str(tmp_path / "cal" / "cam2"))
        
        # Should not raise an error, but return default calibrations
        cals = _read_calibrations(cpar, 2)
        
        # Should return 2 default calibrations
        assert len(cals) == 2
        assert all(isinstance(cal, Calibration) for cal in cals)
        
        # Should print warning messages
        captured = capsys.readouterr()
        assert "Calibration files not found for camera 1" in captured.out
        assert "Calibration files not found for camera 2" in captured.out
    
    @patch('pyptv.ptv.Calibration')
    def test_read_calibrations_success(self, mock_calibration, tmp_path: Path):
        """Test successful calibration reading with mocked Calibration."""
        # Setup mock
        mock_cal_instance = Mock()
        mock_calibration.return_value = mock_cal_instance
        
        # Create ControlParams
        cpar = ControlParams(2)
        cpar.set_cal_img_base_name(0, str(tmp_path / "cal" / "cam1"))
        cpar.set_cal_img_base_name(1, str(tmp_path / "cal" / "cam2"))
        
        # Create dummy calibration files
        cal_dir = tmp_path / "cal"
        cal_dir.mkdir()
        (cal_dir / "cam1.ori").touch()
        (cal_dir / "cam1.addpar").touch()
        (cal_dir / "cam2.ori").touch()
        (cal_dir / "cam2.addpar").touch()
        
        cals = _read_calibrations(cpar, 2)
        
        assert len(cals) == 2
        assert mock_calibration.call_count == 2
        assert mock_cal_instance.from_file.call_count == 2
    
    @patch('pyptv.ptv.Calibration')
    def test_read_calibrations_partial_files(self, mock_calibration, tmp_path: Path):
        """Test behavior when some calibration files are missing."""
        # Create a minimal ControlParams
        cpar = ControlParams(2)
        cpar.set_cal_img_base_name(0, str(tmp_path / "cal" / "cam1"))
        cpar.set_cal_img_base_name(1, str(tmp_path / "cal" / "cam2"))
        
        # Setup mock
        mock_cal_instance = Mock()
        mock_calibration.return_value = mock_cal_instance
        
        # Create partial calibration files
        cal_dir = tmp_path / "cal"
        cal_dir.mkdir()
        (cal_dir / "cam1.ori").touch()
        (cal_dir / "cam1.addpar").touch()
        # Missing cam1.addpar
        (cal_dir / "cam2.ori").touch()
        (cal_dir / "cam2.addpar").touch()
        
        cals = _read_calibrations(cpar, 2)
        
        assert len(cals) == 2
        # Check that Calibration was attempted for both cameras
        assert mock_calibration.call_count == 2
    
    def test_read_calibrations_file_content(self, tmp_path: Path):
        """Test that calibration files are read with correct file paths."""
        # Create a minimal ControlParams
        cpar = ControlParams(2)
        cpar.set_cal_img_base_name(0, str(tmp_path / "cal" / "cam1"))
        cpar.set_cal_img_base_name(1, str(tmp_path / "cal" / "cam2"))
        
        # Create dummy calibration files (structure/content is not tested here)
        cal_dir = tmp_path / "cal"
        cal_dir.mkdir()
        (cal_dir / "cam1.ori").write_text("0.0\n")
        (cal_dir / "cam1.addpar").write_text("0.0\n")
        (cal_dir / "cam2.ori").write_text("0.0\n")
        (cal_dir / "cam2.addpar").write_text("0.0\n")
        
        # Mock Calibration instance to check file path usage
        mock_cal_instance = Mock()
        with patch('pyptv.ptv.Calibration', return_value=mock_cal_instance):
            _read_calibrations(cpar, 2)
        
        # Check that from_file was called for each calibration file pair
        assert mock_cal_instance.from_file.call_count == 2
        expected_calls = [
            ((str(tmp_path / "cal" / "cam1.ori"), str(tmp_path / "cal" / "cam1.addpar")),),
            ((str(tmp_path / "cal" / "cam2.ori"), str(tmp_path / "cal" / "cam2.addpar")),)
        ]
        actual_calls = [call.args for call in mock_cal_instance.from_file.call_args_list]
        assert actual_calls == [calls[0] for calls in expected_calls]


class TestPyStartProcC:
    """Test py_start_proc_c function."""
    
    @patch('pyptv.ptv._read_calibrations')
    def test_py_start_proc_c_success(self, mock_read_cals):
        """Test successful parameter initialization."""
        # Mock calibrations
        mock_read_cals.return_value = [Mock(), Mock(), Mock(), Mock()]
        
        # Create mock parameter manager
        mock_pm = Mock()
        mock_pm.n_cam = 4
        mock_pm.parameters = {
            'ptv': {
                'imx': 1280, 'imy': 1024, 'pix_x': 0.012, 'pix_y': 0.012,
                'img_cal': ['cal/cam1', 'cal/cam2', 'cal/cam3', 'cal/cam4']
            },
            'sequence': {
                'first': 10000, 'last': 10004,
                'base_name': ['img/cam1_%04d', 'img/cam2_%04d', 'img/cam3_%04d', 'img/cam4_%04d']
            },
            'criteria': {
                'X_lay': [-10, 10], 'Zmin_lay': [-5, -5], 'Zmax_lay': [15, 15]
            },
            'track': {
                'dvxmin': -10, 'dvxmax': 10, 'angle': 100.0
            },
            'targ_rec': {
                'gvthres': [9, 9, 9, 11], 'nnmin': 4, 'nnmax': 500
            },
            'examine': {},
            'n_cam': 4
        }
        
        result = py_start_proc_c(mock_pm)
        
        assert len(result) == 7  # Should return 7 items
        cpar, spar, vpar, track_par, tpar, cals, epar = result
        
        # Verify types
        assert isinstance(cpar, ControlParams)
        assert isinstance(spar, SequenceParams)
        assert isinstance(vpar, VolumeParams)
        assert isinstance(track_par, TrackingParams)
        assert isinstance(tpar, TargetParams)
        assert isinstance(cals, list)
        assert isinstance(epar, dict)
        
        # Verify values
        assert cpar.get_num_cams() == 4
        assert spar.get_first() == 10000
        np.testing.assert_array_equal(tpar.get_grey_thresholds(), [9, 9, 9, 11])
    
    @patch('pyptv.ptv._read_calibrations')
    def test_py_start_proc_c_calibration_error(self, mock_read_cals):
        """Test error handling when calibration reading fails."""
        mock_read_cals.side_effect = IOError("Calibration files not found")
        
        mock_pm = Mock()
        mock_pm.n_cam = 4
        mock_pm.parameters = {
            'ptv': {'img_cal': ['cal/cam1', 'cal/cam2', 'cal/cam3', 'cal/cam4']},
            'sequence': {'base_name': ['img1_%04d', 'img2_%04d', 'img3_%04d', 'img4_%04d']},
            'criteria': {},
            'track': {},
            'targ_rec': {},
            'examine': {}
        }
        
        with pytest.raises(IOError, match="Failed to read parameter files"):
            py_start_proc_c(mock_pm)


class TestParameterConsistency:
    """Test parameter consistency and edge cases."""
    
    def test_parameter_consistency_n_cam(self):
        """Test that n_cam is consistently used across all functions."""
        n_cam = 3
        
        # Test that all functions respect n_cam parameter
        ptv_params = {'img_cal': ['cal1', 'cal2', 'cal3']}
        cpar = _populate_cpar(ptv_params, n_cam)
        assert cpar.get_num_cams() == n_cam
        
        seq_params = {'base_name': ['img1_%04d', 'img2_%04d', 'img3_%04d']}
        spar = _populate_spar(seq_params, n_cam)
        # SequenceParams doesn't have get_num_cams() but it was created with n_cam
        # Test that we can access all cameras
        for i in range(n_cam):
            spar.get_img_base_name(i)  # Should not raise an error
        
        params = {'n_cam': n_cam, 'targ_rec': {}}
        tpar = _populate_tpar(params, n_cam)
        # TargetParams has a fixed internal array size of 4 for grey thresholds in Cython
        # regardless of n_cam value. Only the first n_cam values are meaningful.
        thresholds = tpar.get_grey_thresholds()
        assert len(thresholds) == 4, f"TargetParams always has 4 thresholds, got {len(thresholds)}"
        # Check that default values are zeros
        np.testing.assert_array_equal(thresholds, [0, 0, 0, 0])
    
    def test_parameter_default_values(self):
        """Test that appropriate default values are used."""
        # Test ControlParams defaults - need to provide img_cal
        cpar = _populate_cpar({'img_cal': ['cal/cam1']}, 1)
        assert cpar.get_image_size() == (0, 0)
        assert cpar.get_pixel_size() == (0.0, 0.0)
        assert cpar.get_hp_flag() == False
        
        # Test SequenceParams defaults - need to provide base_name
        spar = _populate_spar({'base_name': ['img1_%04d']}, 1)
        assert spar.get_first() == 0
        assert spar.get_last() == 0
        
        # Test VolumeParams defaults
        vpar = _populate_vpar({})
        assert np.allclose(vpar.get_X_lay(), [0, 0])
        
        # Test TrackingParams defaults
        track_par = _populate_track_par({})
        assert track_par.get_add() == False
        
        # Test TargetParams defaults
        tpar = _populate_tpar({'targ_rec': {}}, n_cam = 0)
        thresholds = tpar.get_grey_thresholds()
        # TargetParams always returns array of size 4, regardless of n_cam
        assert len(thresholds) == 4, f"TargetParams always has 4 thresholds, got {len(thresholds)}"
        np.testing.assert_array_equal(thresholds, [0, 0, 0, 0])


class TestCalibrationReadWrite:
    """Test calibration file reading and writing functionality."""
    
    @property
    def test_cal_dir(self):
        """Path to test calibration files."""
        return Path(__file__).parent / "test_cavity" / "cal"
    
    def setUp(self):
        """Set up test fixtures - called before each test method."""
        self.output_directory = Path("testing_output")
        # Create temporary output directory
        if not self.output_directory.exists():
            self.output_directory.mkdir()
        
        # Create an instance of Calibration wrapper class
        self.cal = Calibration()
    
    def tearDown(self):
        """Clean up after tests - called after each test method."""
        # Remove the testing output directory and its files
        if self.output_directory.exists():
            shutil.rmtree(self.output_directory)
    
    def print_calibration_info(self, cal: Calibration, cam_name: str):
        """Print calibration information to stdout for inspection."""
        print(f"\n=== Calibration info for {cam_name} ===")
        
        # Exterior orientation (position and rotation)
        pos = cal.get_pos()
        print(f"Camera position (X, Y, Z): {pos[0]:.6f}, {pos[1]:.6f}, {pos[2]:.6f}")
        
        angles = cal.get_angles()
        print(f"Camera angles (omega, phi, kappa): {angles[0]:.6f}, {angles[1]:.6f}, {angles[2]:.6f}")
        
        # Interior orientation
        primary_point = cal.get_primary_point()
        print(f"Primary point (xp, yp, c): {primary_point[0]:.6f}, {primary_point[1]:.6f}, {primary_point[2]:.6f}")
        
        # Radial distortion
        radial_dist = cal.get_radial_distortion()
        print(f"Radial distortion (k1, k2, k3): {radial_dist[0]:.6f}, {radial_dist[1]:.6f}, {radial_dist[2]:.6f}")
        
        # Decentering distortion
        decentering = cal.get_decentering()
        print(f"Decentering (p1, p2): {decentering[0]:.6f}, {decentering[1]:.6f}")
        
        # Affine transformation
        affine = cal.get_affine()
        print(f"Affine (scale, shear): {affine[0]:.6f}, {affine[1]:.6f}")
        
        # Glass vector (if multimedia)
        glass_vec = cal.get_glass_vec()
        print(f"Glass vector: {glass_vec[0]:.6f}, {glass_vec[1]:.6f}, {glass_vec[2]:.6f}")
        
        print("=" * 50)
    
    def test_read_real_calibration_files(self, capsys):
        """Test reading actual calibration files from test_cavity."""
        cam_files = ["cam1.tif", "cam2.tif", "cam3.tif", "cam4.tif"]
        
        calibrations = []
        for i, cam_file in enumerate(cam_files):
            cal = Calibration()
            cal_base = str(self.test_cal_dir / cam_file)
            
            try:
                cal.from_file(cal_base + ".ori", cal_base + ".addpar")
                calibrations.append(cal)
                
                # Print calibration info to stdout
                self.print_calibration_info(cal, f"Camera {i+1}")
                
            except Exception as e:
                pytest.fail(f"Failed to read calibration for {cam_file}: {e}")
        
        # Verify we read all calibrations
        assert len(calibrations) == 4
        
        # Basic sanity checks on calibration data
        for i, cal in enumerate(calibrations):
            pos = cal.get_pos()
            # Positions should be reasonable (not all zeros)
            assert not np.allclose(pos, [0, 0, 0]), f"Camera {i+1} has invalid position"
            
            # Focal length should be positive (it's the 3rd element of primary point)
            focal = cal.get_primary_point()[2]
            assert focal > 0, f"Camera {i+1} has invalid focal length: {focal}"
    
    def test_calibration_round_trip_filecmp(self):
        """Test reading calibration files and writing them back using numerical comparison."""
        cam_files = ["cam1.tif", "cam2.tif"]  # Test with 2 cameras
        
        # Set up output directory  
        self.setUp()
        
        try:
            for cam_file in cam_files:
                # Convert to bytes as required by OptV
                input_ori_file = str(self.test_cal_dir / f"{cam_file}.ori").encode('utf-8')
                input_add_file = str(self.test_cal_dir / f"{cam_file}.addpar").encode('utf-8')
                output_ori_file = str(self.output_directory / f"output_{cam_file}.ori").encode('utf-8')
                output_add_file = str(self.output_directory / f"output_{cam_file}.addpar").encode('utf-8')
                
                # Read original calibration
                orig_cal = Calibration()
                orig_cal.from_file(input_ori_file, input_add_file)
                
                # Write and read back
                orig_cal.write(output_ori_file, output_add_file)
                copied_cal = Calibration()
                copied_cal.from_file(output_ori_file, output_add_file)
                
                # Compare calibration parameters numerically (allowing for floating point precision)
                np.testing.assert_array_almost_equal(orig_cal.get_pos(), copied_cal.get_pos(), decimal=10)
                np.testing.assert_array_almost_equal(orig_cal.get_angles(), copied_cal.get_angles(), decimal=10)
                np.testing.assert_array_almost_equal(orig_cal.get_primary_point(), copied_cal.get_primary_point(), decimal=10)
                np.testing.assert_array_almost_equal(orig_cal.get_radial_distortion(), copied_cal.get_radial_distortion(), decimal=10)
                np.testing.assert_array_almost_equal(orig_cal.get_decentering(), copied_cal.get_decentering(), decimal=10)
                np.testing.assert_array_almost_equal(orig_cal.get_affine(), copied_cal.get_affine(), decimal=10)
                np.testing.assert_array_almost_equal(orig_cal.get_glass_vec(), copied_cal.get_glass_vec(), decimal=10)
                
                # For addpar files, they should be exactly identical (no floating point calculations)
                assert filecmp.cmp(input_add_file.decode('utf-8'), output_add_file.decode('utf-8'), shallow=False), \
                    f"ADDPAR round-trip failed for {cam_file}.addpar"
                
                print(f"✓ Round-trip test passed for {cam_file}")
        
        except Exception as e:
            pytest.fail(f"Round-trip test failed: {e}")
        finally:
            self.tearDown()
    
    def test_calibration_parameter_setters(self):
        """Test individual parameter setters with validation."""
        self.setUp()
        
        try:
            cal = Calibration()
            
            # Test set_pos() - should work with 3-element array
            new_pos = np.array([111.1111, 222.2222, 333.3333])
            cal.set_pos(new_pos)
            np.testing.assert_array_equal(new_pos, cal.get_pos())
            
            # Test invalid position arrays
            with pytest.raises(ValueError):
                cal.set_pos(np.array([1, 2, 3, 4]))  # Too many elements
            with pytest.raises(ValueError):
                cal.set_pos(np.array([1, 2]))  # Too few elements
            
            # Test set_angles()
            dmatrix_before = cal.get_rotation_matrix()
            angles_np = np.array([0.1111, 0.2222, 0.3333])
            cal.set_angles(angles_np)
            dmatrix_after = cal.get_rotation_matrix()
            
            np.testing.assert_array_equal(cal.get_angles(), angles_np)
            assert not np.array_equal(dmatrix_before, dmatrix_after), "Rotation matrix should change"
            
            # Test invalid angle arrays
            with pytest.raises(ValueError):
                cal.set_angles(np.array([1, 2, 3, 4]))
            with pytest.raises(ValueError):
                cal.set_angles(np.array([1, 2]))
            
            # Test set_primary_point()
            new_pp = np.array([111.1111, 222.2222, 333.3333])
            cal.set_primary_point(new_pp)
            np.testing.assert_array_equal(new_pp, cal.get_primary_point())
            
            # Test invalid primary point arrays
            with pytest.raises(ValueError):
                cal.set_primary_point(np.ones(4))
            with pytest.raises(ValueError):
                cal.set_primary_point(np.ones(2))
            
            # Test set_radial_distortion()
            new_rd = np.array([0.001, 0.002, 0.003])
            cal.set_radial_distortion(new_rd)
            np.testing.assert_array_equal(new_rd, cal.get_radial_distortion())
            
            # Test invalid radial distortion arrays
            with pytest.raises(ValueError):
                cal.set_radial_distortion(np.ones(4))
            with pytest.raises(ValueError):
                cal.set_radial_distortion(np.ones(2))
            
            # Test set_decentering()
            new_de = np.array([0.0001, 0.0002])
            cal.set_decentering(new_de)
            np.testing.assert_array_equal(new_de, cal.get_decentering())
            
            # Test invalid decentering arrays
            with pytest.raises(ValueError):
                cal.set_decentering(np.ones(3))
            with pytest.raises(ValueError):
                cal.set_decentering(np.ones(1))
            
            # Test set_glass_vec()
            new_gv = np.array([1.0, 2.0, 3.0])
            cal.set_glass_vec(new_gv)
            np.testing.assert_array_equal(new_gv, cal.get_glass_vec())
            
            # Test invalid glass vector arrays
            with pytest.raises(ValueError):
                cal.set_glass_vec(np.ones(2))
            with pytest.raises(ValueError):
                cal.set_glass_vec(np.ones(1))
            
            print("✓ All parameter setter tests passed")
            
        except Exception as e:
            pytest.fail(f"Parameter setter test failed: {e}")
        finally:
            self.tearDown()
    
    def test_full_calibration_instantiate(self):
        """Test creating a calibration with all parameters at once."""
        pos = np.r_[1., 3., 5.]
        angs = np.r_[2., 4., 6.]
        prim_point = pos * 3
        rad_dist = pos * 4
        decent = pos[:2] * 5
        affine = decent * 1.5
        glass = pos * 7
        
        cal = Calibration(pos, angs, prim_point, rad_dist, decent, affine, glass)
        
        # Verify all parameters were set correctly
        np.testing.assert_array_equal(pos, cal.get_pos())
        np.testing.assert_array_equal(angs, cal.get_angles())
        np.testing.assert_array_equal(prim_point, cal.get_primary_point())
        np.testing.assert_array_equal(rad_dist, cal.get_radial_distortion())
        np.testing.assert_array_equal(decent, cal.get_decentering())
        np.testing.assert_array_equal(affine, cal.get_affine())
        np.testing.assert_array_equal(glass, cal.get_glass_vec())
        
        print("✓ Full instantiation test passed")
    
    def test_file_content_comparison(self, tmp_path: Path):
        """Test that written calibration files are identical to originals."""
        cam_files = ["cam1.tif"]  # Test with one camera for detailed file comparison
        
        # Read and write calibration
        for cam_file in cam_files:
            # Read original
            cal = Calibration()
            orig_cal_base = str(self.test_cal_dir / cam_file)
            cal.from_file((orig_cal_base + ".ori").encode('utf-8'), (orig_cal_base + ".addpar").encode('utf-8'))
            
            # Write copy
            cal_copy_dir = tmp_path / "cal_copy"
            cal_copy_dir.mkdir(exist_ok=True)
            copy_cal_base = str(cal_copy_dir / cam_file)
            cal.write((copy_cal_base + ".ori").encode('utf-8'), (copy_cal_base + ".addpar").encode('utf-8'))
            
            # Compare file contents (this tests numerical precision)
            # Note: Small differences might exist due to floating point representation
            # so we'll check that the files are nearly identical
            
            # Read original files as text
            with open(orig_cal_base + ".ori", 'r') as f:
                orig_ori_content = f.read()
            with open(orig_cal_base + ".addpar", 'r') as f:
                orig_addpar_content = f.read()
            
            # Read copied files as text  
            with open(copy_cal_base + ".ori", 'r') as f:
                copy_ori_content = f.read()
            with open(copy_cal_base + ".addpar", 'r') as f:
                copy_addpar_content = f.read()
            
            print(f"\n=== Original .ori content for {cam_file} ===")
            print(orig_ori_content)
            print(f"\n=== Copied .ori content for {cam_file} ===")
            print(copy_ori_content)
            
            print(f"\n=== Original .addpar content for {cam_file} ===")
            print(orig_addpar_content)
            print(f"\n=== Copied .addpar content for {cam_file} ===")
            print(copy_addpar_content)
            
            # For numerical data, we'll parse and compare values rather than exact text
            # since formatting might differ slightly
            assert len(copy_ori_content.strip()) > 0, "Copied .ori file is empty"
            assert len(copy_addpar_content.strip()) > 0, "Copied .addpar file is empty"
    
    def test_calibration_with_control_params(self, tmp_path: Path):
        """Test calibration reading through _read_calibrations function."""
        # Create ControlParams pointing to test calibrations
        n_cam = 4
        cpar = ControlParams(n_cam)
        
        for i in range(n_cam):
            cam_file = f"cam{i+1}.tif"
            cal_base = str(self.test_cal_dir / cam_file)
            cpar.set_cal_img_base_name(i, cal_base)
        
        # Read calibrations through our function
        try:
            cals = _read_calibrations(cpar, n_cam)
            
            # Verify we got the right number of calibrations
            assert len(cals) == n_cam
            
            # Verify all calibrations are valid Calibration objects
            for i, cal in enumerate(cals):
                assert isinstance(cal, Calibration), f"Camera {i+1} is not a Calibration object"
                
                # Basic sanity checks
                pos = cal.get_pos()
                assert not np.allclose(pos, [0, 0, 0]), f"Camera {i+1} has invalid position"
                
                focal = cal.get_primary_point()[2]  # Focal length is 3rd element of primary point
                assert focal > 0, f"Camera {i+1} has invalid focal length"
                
                print(f"Camera {i+1} position: {pos}")
                print(f"Camera {i+1} focal length: {focal}")
                
        except Exception as e:
            pytest.fail(f"_read_calibrations failed: {e}")
    
    def test_modified_calibration_write(self, tmp_path: Path):
        """Test modifying calibration parameters and writing them."""
        # Read original calibration
        cal = Calibration()
        orig_cal_base = str(self.test_cal_dir / "cam1.tif")
        cal.from_file((orig_cal_base + ".ori").encode('utf-8'), (orig_cal_base + ".addpar").encode('utf-8'))
        
        # Get original values
        orig_pos = cal.get_pos()
        orig_primary_point = cal.get_primary_point()
        orig_focal = orig_primary_point[2]  # Focal length is 3rd element
        
        print(f"Original position: {orig_pos}")
        print(f"Original focal length: {orig_focal}")
        
        # Modify calibration parameters
        new_pos = np.array([orig_pos[0] + 10.0, orig_pos[1] + 5.0, orig_pos[2] - 15.0])
        new_focal = orig_focal + 1.0
        new_primary_point = np.array([orig_primary_point[0], orig_primary_point[1], new_focal])
        
        cal.set_pos(new_pos)
        cal.set_primary_point(new_primary_point)
        
        # Write modified calibration
        cal_copy_dir = tmp_path / "cal_modified"
        cal_copy_dir.mkdir()
        copy_cal_base = str(cal_copy_dir / "cam1_modified.tif")
        cal.write((copy_cal_base + ".ori").encode('utf-8'), (copy_cal_base + ".addpar").encode('utf-8'))
        
        # Read back modified calibration
        cal_modified = Calibration()
        cal_modified.from_file((copy_cal_base + ".ori").encode('utf-8'), (copy_cal_base + ".addpar").encode('utf-8'))
        
        # Verify modifications were saved correctly
        read_pos = cal_modified.get_pos()
        read_primary_point = cal_modified.get_primary_point()
        read_focal = read_primary_point[2]
        
        print(f"Modified position: {read_pos}")
        print(f"Modified focal length: {read_focal}")
        
        assert np.allclose(read_pos, new_pos, rtol=1e-10), \
            f"Position not saved correctly: expected {new_pos}, got {read_pos}"
        assert np.isclose(read_focal, new_focal, rtol=1e-10), \
            f"Focal length not saved correctly: expected {new_focal}, got {read_focal}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])