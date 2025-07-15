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
    def test_py_start_proc_c_basic(self, mock_tpar, mock_track_par, mock_vpar, mock_spar, mock_cpar):
        """Test basic start processing call"""
        parameter_manager = Mock()
        parameter_manager.get_ptv_params.return_value = {
            'imx': 1024, 'imy': 768, 'pix_x': 0.01, 'pix_y': 0.01,
            'hp_flag': 1, 'allcam_flag': 0, 'tiff_flag': 1, 'chfield': 0,
            'mmp_n1': 1.0, 'mmp_n2': 1.33, 'mmp_d': 5.0, 'mmp_n3': 1.49,
            'img_cal': ['cal1.tif', 'cal2.tif']
        }
        parameter_manager.get_sequence_params.return_value = {
            'first': 1000, 'last': 1010,
            'base_name': ['img1_%04d.tif', 'img2_%04d.tif']
        }
        parameter_manager.get_criteria_params.return_value = {
            'X_lay': [0, 10], 'Zmin_lay': [-5, -3], 'Zmax_lay': [3, 5],
            'eps0': 0.1, 'cn': 0.5, 'cnx': 0.3, 'cny': 0.3,
            'csumg': 0.02, 'corrmin': 33.0
        }
        parameter_manager.get_tracking_params.return_value = {
            'dvxmin': -2.0, 'dvxmax': 2.0, 'dvymin': -2.0, 'dvymax': 2.0,
            'dvzmin': -2.0, 'dvzmax': 2.0, 'angle': 0.5, 'dacc': 5.0,
            'flagNewParticles': 1
        }
        parameter_manager.get_target_params.return_value = {
            'detect_plate': {
                'gvth_1': 50, 'gvth_2': 50, 'gvth_3': 50, 'gvth_4': 50,
                'min_npix': 25, 'max_npix': 900, 'min_npix_x': 5, 'max_npix_x': 30,
                'min_npix_y': 5, 'max_npix_y': 30, 'sum_grey': 20, 'tol_dis': 20
            }
        }
        parameter_manager.get_n_cam.return_value = 2
        
        # Mock the parameter objects
        mock_cpar.return_value = Mock()
        mock_spar.return_value = Mock()
        mock_vpar.return_value = Mock()
        mock_track_par.return_value = Mock()
        mock_tpar.return_value = Mock()
        
        result = py_start_proc_c(parameter_manager)
        
        assert len(result) == 7  # Should return tuple of 7 elements
        mock_cpar.assert_called_once()
        mock_spar.assert_called_once()
        mock_vpar.assert_called_once()
        mock_track_par.assert_called_once()
        mock_tpar.assert_called_once()
    
    def test_py_start_proc_c_invalid_parameter_manager(self):
        """Test start processing with invalid parameter manager"""
        with pytest.raises(AttributeError):
            py_start_proc_c(None)


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
        ptv_params = {}
        target_params = {}
        
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
        
        mock_correspondences.return_value = ([Mock(), Mock()], [Mock(), Mock()], 2)
        mock_write_targets.return_value = None
        
        result = py_correspondences_proc_c(exp)
        
        # The function returns the experiment object with updated correspondences
        assert result is not None
        mock_correspondences.assert_called_once_with(
            exp.detections, exp.corrected, exp.cals, exp.vpar, exp.cpar
        )
    
    def test_py_correspondences_proc_c_no_detections(self):
        """Test correspondences processing with no detections"""
        exp = Mock()
        exp.detections = []
        exp.corrected = []
        exp.cals = [Mock(), Mock()]
        exp.vpar = Mock()
        exp.cpar = Mock()
        exp.spar = Mock()
        exp.spar.get_first.return_value = 1000
        
        with patch('pyptv.ptv.correspondences') as mock_correspondences:
            mock_correspondences.return_value = ([], [], 0)
            
            result = py_correspondences_proc_c(exp)
            
            assert result is not None
            mock_correspondences.assert_called_once()
    
    def test_py_correspondences_proc_c_invalid_experiment(self):
        """Test correspondences processing with invalid experiment object"""
        with pytest.raises(AttributeError):
            py_correspondences_proc_c(None)


if __name__ == "__main__":
    pytest.main([__file__])
