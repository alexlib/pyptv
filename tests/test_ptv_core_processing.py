"""Unit tests for core processing functions in ptv.py"""

import pytest
import numpy as np
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from pyptv.ptv import (
    py_start_proc_c, py_detection_proc_c, py_correspondences_proc_c
)


class TestPyStartProcC:
    """Test py_start_proc_c function"""
    
    @patch('pyptv.ptv._populate_cpar')
    @patch('pyptv.ptv._populate_spar')
    @patch('pyptv.ptv._populate_vpar')
    @patch('pyptv.ptv._populate_track_par')
    @patch('pyptv.ptv._populate_tpar')
    @patch('pyptv.ptv._read_calibrations')
    def test_py_start_proc_c_basic(self, mock_read_cals, mock_tpar, mock_track_par, mock_vpar, mock_spar, mock_cpar):
        """Test basic start processing call"""
        parameter_manager = Mock()
        parameter_manager.parameters = {
            'ptv': {
                'imx': 1024, 'imy': 768, 'pix_x': 0.01, 'pix_y': 0.01,
                'hp_flag': 1, 'allcam_flag': 0, 'tiff_flag': 1, 'chfield': 0,
                'mmp_n1': 1.0, 'mmp_n2': 1.33, 'mmp_d': 5.0, 'mmp_n3': 1.49,
                'img_cal': ['cal1.tif', 'cal2.tif']
            },
            'sequence': {
                'first': 1000, 'last': 1010,
                'base_name': ['img1_%04d.tif', 'img2_%04d.tif']
            },
            'criteria': {
                'X_lay': [0, 10], 'Zmin_lay': [-5, -3], 'Zmax_lay': [3, 5],
                'eps0': 0.1, 'cn': 0.5, 'cnx': 0.3, 'cny': 0.3,
                'csumg': 0.02, 'corrmin': 33.0
            },
            'track': {
                'dvxmin': -2.0, 'dvxmax': 2.0, 'dvymin': -2.0, 'dvymax': 2.0,
                'dvzmin': -2.0, 'dvzmax': 2.0, 'angle': 0.5, 'dacc': 5.0,
                'flagNewParticles': 1
            },
            'targ_rec': {  # Changed from detect_plate to targ_rec as expected by py_start_proc_c
                'gvth_1': 50, 'gvth_2': 50, 'gvth_3': 50, 'gvth_4': 50,
                'min_npix': 25, 'max_npix': 900, 'min_npix_x': 5, 'max_npix_x': 30,
                'min_npix_y': 5, 'max_npix_y': 30, 'sum_grey': 20, 'tol_dis': 20
            },
            'examine': {}  # Add examine parameters as expected by py_start_proc_c
        }
        parameter_manager.n_cam = 2  # Set as attribute, not method return value
        
        # Mock the parameter objects
        mock_cpar_obj = Mock()
        mock_cpar_obj.get_cal_img_base_name.return_value = "cal_base"
        mock_cpar.return_value = mock_cpar_obj
        mock_spar.return_value = Mock()
        mock_vpar.return_value = Mock()
        mock_track_par.return_value = Mock()
        mock_tpar.return_value = Mock()
        mock_read_cals.return_value = [Mock(), Mock()]  # Mock calibrations
        
        result = py_start_proc_c(parameter_manager)
        
        assert len(result) == 7  # Should return tuple of 7 elements
        mock_cpar.assert_called_once()
        mock_spar.assert_called_once()
        mock_vpar.assert_called_once()
        mock_track_par.assert_called_once()
        mock_tpar.assert_called_once()
        mock_read_cals.assert_called_once()
    
    def test_py_start_proc_c_invalid_parameter_manager(self):
        """Test start processing with invalid parameter manager"""
        # Test with Mock that doesn't have required attributes
        invalid_param_manager = Mock()
        del invalid_param_manager.parameters  # Remove the parameters attribute
        
        with pytest.raises(AttributeError):
            py_start_proc_c(invalid_param_manager)


class TestPyDetectionProcC:
    """Test py_detection_proc_c function"""
    
    @patch('pyptv.ptv._populate_tpar')
    @patch('pyptv.ptv._populate_cpar')
    @patch('pyptv.ptv._read_calibrations')
    @patch('pyptv.ptv.target_recognition')
    @patch('pyptv.ptv.MatchedCoords')
    def test_py_detection_proc_c_basic(self, mock_matched_coords, mock_target_recognition, 
                                      mock_read_cals, mock_populate_cpar, mock_tpar):
        """Test basic detection processing call"""
        n_cam = 2
        list_of_images = [
            np.random.randint(0, 255, (100, 100), dtype=np.uint8),
            np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        ]
        ptv_params = {'imx': 100, 'imy': 100}
        target_params = {
            'detect_plate': {
                'gvth_1': 50, 'gvth_2': 50,
                'min_npix': 25, 'max_npix': 900,
                'min_npix_x': 5, 'max_npix_x': 30,
                'min_npix_y': 5, 'max_npix_y': 30,
                'sum_grey': 20, 'tol_dis': 20
            }
        }
        
        # Mock the dependencies
        mock_cpar = Mock()
        mock_tpar_obj = Mock()
        mock_cals = [Mock(), Mock()]
        mock_targets = Mock()
        mock_targets.sort_y = Mock()
        mock_matched_coords_obj = Mock()
        
        mock_populate_cpar.return_value = mock_cpar
        mock_tpar.return_value = mock_tpar_obj
        mock_read_cals.return_value = mock_cals
        mock_target_recognition.return_value = mock_targets
        mock_matched_coords.return_value = mock_matched_coords_obj
        
        result = py_detection_proc_c(n_cam, list_of_images, ptv_params, target_params)
        
        assert len(result) == 2  # Should return tuple of (detections, corrected)
        assert len(result[0]) == 2  # detections for 2 cameras
        assert len(result[1]) == 2  # corrected for 2 cameras
        
        mock_populate_cpar.assert_called_once_with(ptv_params, n_cam)
        mock_tpar.assert_called_once_with(target_params, n_cam)
        mock_read_cals.assert_called_once_with(mock_cpar, n_cam)
        assert mock_target_recognition.call_count == 2  # Called for each camera
    
    def test_py_detection_proc_c_empty_images(self):
        """Test detection processing with empty image list"""
        n_cam = 0
        list_of_images = []
        ptv_params = {
            'imx': 1024,
            'imy': 768,
            'pix_x': 0.01,
            'pix_y': 0.01,
            'hp_flag': False,
            'allcam_flag': False,
            'tiff_flag': False,
            'chfield': 0,
            'mmp_n1': 1.0,
            'mmp_n2': 1.0,
            'mmp_d': 1.0,
            'mmp_n3': 1.0,
            'img_cal': []  # Empty for 0 cameras
        }
        target_params = {
            'targ_rec': {
                'gvthres': [50, 50, 50, 50],
                'nnmin': 1,
                'nnmax': 1000,
                'nxmin': 1,
                'nxmax': 20,
                'nymin': 1,
                'nymax': 20,
                'sumg_min': 200,
                'disco': 10
            }
        }
        
        # Should handle empty input gracefully
        result = py_detection_proc_c(n_cam, list_of_images, ptv_params, target_params)
        
        assert len(result) == 2
        assert len(result[0]) == 0  # No detections
        assert len(result[1]) == 0  # No corrected
    
    def test_py_detection_proc_c_mismatched_camera_count(self):
        """Test detection processing with mismatched camera count"""
        n_cam = 3
        list_of_images = [
            np.random.randint(0, 255, (100, 100), dtype=np.uint8),
            np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        ]  # Only 2 images but n_cam = 3
        ptv_params = {'imx': 100, 'imy': 100}
        target_params = {}
        
        with pytest.raises(ValueError, match="Number of images"):
            py_detection_proc_c(n_cam, list_of_images, ptv_params, target_params)


class TestPyCorrespondencesProcC:
    """Test py_correspondences_proc_c function"""
    
    @patch('pyptv.ptv.correspondences')
    @patch('pyptv.ptv.write_targets')
    def test_py_correspondences_proc_c_basic(self, mock_write_targets, mock_correspondences):
        """Test basic correspondences processing call"""
        exp = Mock()
        exp.detections = [Mock(), Mock()]
        exp.corrected = [Mock(), Mock()]
        exp.cals = [Mock(), Mock()]
        exp.vpar = Mock()
        exp.cpar = Mock()
        exp.spar = Mock()
        exp.spar.get_first.return_value = 1000
        exp.spar.get_img_base_name.return_value = "img_base"
        exp.n_cams = 2  # Add the missing n_cams attribute
        
        # Create mock numpy arrays with proper shape attributes
        mock_array1 = np.array([[1, 2], [3, 4]])  # shape = (2, 2)
        mock_array2 = np.array([[5, 6, 7], [8, 9, 10]])  # shape = (2, 3)
        mock_correspondences.return_value = ([mock_array1, mock_array2], [Mock(), Mock()], 2)
        mock_write_targets.return_value = None
        
        result = py_correspondences_proc_c(exp)
        
        # The function returns a tuple of (sorted_pos, sorted_corresp, num_targs)
        assert result is not None
        assert len(result) == 3
        mock_correspondences.assert_called_once_with(
            exp.detections, exp.corrected, exp.cals, exp.vpar, exp.cpar
        )
    
    def test_py_correspondences_proc_c_no_detections(self):
        """Test correspondences processing with no detections"""
        exp = Mock()
        exp.detections = [[], []]  # Empty detection lists for 2 cameras
        exp.corrected = [[], []]  # Empty corrected lists for 2 cameras
        exp.cals = [Mock(), Mock()]
        exp.vpar = Mock()
        exp.cpar = Mock()
        exp.spar = Mock()
        exp.spar.get_first.return_value = 1000
        exp.spar.get_img_base_name.return_value = "img_base"
        exp.n_cams = 2  # Add the missing n_cams attribute
        
        with patch('pyptv.ptv.correspondences') as mock_correspondences:
            with patch('pyptv.ptv.write_targets') as mock_write_targets:
                # Return empty numpy arrays with proper shape
                empty_array = np.array([]).reshape(0, 0)
                mock_correspondences.return_value = ([empty_array], [empty_array], 0)
                mock_write_targets.return_value = None
                
                result = py_correspondences_proc_c(exp)
                
                assert result is not None
                assert len(result) == 3
                mock_correspondences.assert_called_once()
                # Should call write_targets for each camera
                assert mock_write_targets.call_count == 2
    
    def test_py_correspondences_proc_c_invalid_experiment(self):
        """Test correspondences processing with invalid experiment object"""
        with pytest.raises(AttributeError):
            py_correspondences_proc_c(None)


if __name__ == "__main__":
    pytest.main([__file__])
