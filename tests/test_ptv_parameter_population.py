"""Unit tests for parameter population functions in ptv.py"""

import pytest
import numpy as np
from pyptv.ptv import _populate_cpar, _populate_spar, _populate_vpar, _populate_track_par, _populate_tpar
from optv.parameters import ControlParams, SequenceParams, VolumeParams, TrackingParams, TargetParams


class TestPopulateCpar:
    """Test _populate_cpar function"""
    
    def test_populate_cpar_basic(self):
        """Test basic control parameter population"""
        ptv_params = {
            'imx': 1024,
            'imy': 768,
            'pix_x': 0.01,
            'pix_y': 0.01,
            'hp_flag': 1,
            'allcam_flag': 0,
            'tiff_flag': 1,
            'chfield': 0,
            'mmp_n1': 1.0,
            'mmp_n2': 1.33,
            'mmp_d': 5.0,
            'mmp_n3': 1.49,
            'img_cal': ['cal1.tif', 'cal2.tif']
        }
        n_cam = 2
        
        result = _populate_cpar(ptv_params, n_cam)
        
        assert isinstance(result, ControlParams)
        assert result.get_image_size() == (1024, 768)
        assert result.get_pixel_size() == (0.01, 0.01)
        assert result.get_hp_flag() == 1
    
    def test_populate_cpar_missing_required_params(self):
        """Test control parameter population with missing required parameters"""
        ptv_params = {
            'imx': 1024,
            # Missing 'imy'
            'pix_x': 0.01,
            'pix_y': 0.01,
        }
        n_cam = 2
        
        with pytest.raises(KeyError):
            _populate_cpar(ptv_params, n_cam)
    
    def test_populate_cpar_invalid_img_cal_length(self):
        """Test with mismatched img_cal list length"""
        ptv_params = {
            'imx': 1024,
            'imy': 768,
            'pix_x': 0.01,
            'pix_y': 0.01,
            'hp_flag': 1,
            'allcam_flag': 0,
            'tiff_flag': 1,
            'chfield': 0,
            'mmp_n1': 1.0,
            'mmp_n2': 1.33,
            'mmp_d': 5.0,
            'mmp_n3': 1.49,
            'img_cal': ['cal1.tif']  # Only 1 camera, but n_cam = 2
        }
        n_cam = 2
        
        with pytest.raises(ValueError, match="img_cal_list length does not match n_cam"):
            _populate_cpar(ptv_params, n_cam)


class TestPopulateSpar:
    """Test _populate_spar function"""
    
    def test_populate_spar_basic(self):
        """Test basic sequence parameter population"""
        seq_params = {
            'first': 1000,
            'last': 1010,
            'base_name': ['img1_%04d.tif', 'img2_%04d.tif']
        }
        n_cam = 2
        
        result = _populate_spar(seq_params, n_cam)
        
        assert isinstance(result, SequenceParams)
        assert result.get_first() == 1000
        assert result.get_last() == 1010
    
    def test_populate_spar_missing_required_params(self):
        """Test sequence parameter population with missing required parameters"""
        seq_params = {
            'first': 1000,
            # Missing 'last' and 'base_name'
        }
        n_cam = 2
        
        with pytest.raises(ValueError, match="Missing required sequence parameters"):
            _populate_spar(seq_params, n_cam)
    
    def test_populate_spar_invalid_base_name_length(self):
        """Test with mismatched base_name list length"""
        seq_params = {
            'first': 1000,
            'last': 1010,
            'base_name': ['img1_%04d.tif']  # Only 1 camera, but n_cam = 2
        }
        n_cam = 2
        
        with pytest.raises(ValueError, match="base_name_list length"):
            _populate_spar(seq_params, n_cam)


class TestPopulateVpar:
    """Test _populate_vpar function"""
    
    def test_populate_vpar_basic(self):
        """Test basic volume parameter population"""
        crit_params = {
            'X_lay': [0, 10],
            'Zmin_lay': [-5, -3],
            'Zmax_lay': [3, 5],
            'eps0': 0.1,
            'cn': 0.5,
            'cnx': 0.3,
            'cny': 0.3,
            'csumg': 0.02,
            'corrmin': 33.0
        }
        
        result = _populate_vpar(crit_params)
        
        assert isinstance(result, VolumeParams)
        assert result.get_eps0() == 0.1
        assert result.get_cn() == 0.5
    
    def test_populate_vpar_missing_required_params(self):
        """Test volume parameter population with missing required parameters"""
        crit_params = {
            'X_lay': [0, 10],
            # Missing other required parameters
        }
        
        with pytest.raises(KeyError):
            _populate_vpar(crit_params)


class TestPopulateTrackPar:
    """Test _populate_track_par function"""
    
    def test_populate_track_par_basic(self):
        """Test basic tracking parameter population"""
        track_params = {
            'dvxmin': -2.0,
            'dvxmax': 2.0,
            'dvymin': -2.0,
            'dvymax': 2.0,
            'dvzmin': -2.0,
            'dvzmax': 2.0,
            'angle': 0.5,
            'dacc': 5.0,
            'flagNewParticles': 1
        }
        
        result = _populate_track_par(track_params)
        
        assert isinstance(result, TrackingParams)
        assert result.get_dvxmin() == -2.0
        assert result.get_dvxmax() == 2.0
        assert result.get_dacc() == 5.0
    
    def test_populate_track_par_missing_required_params(self):
        """Test tracking parameter population with missing required parameters"""
        track_params = {
            'dvxmin': -2.0,
            'dvxmax': 2.0,
            # Missing other required parameters
        }
        
        with pytest.raises(ValueError, match="Missing required tracking parameters"):
            _populate_track_par(track_params)
    
    def test_populate_track_par_all_missing(self):
        """Test tracking parameter population with empty dict"""
        track_params = {}
        
        with pytest.raises(ValueError, match="Missing required tracking parameters"):
            _populate_track_par(track_params)


class TestPopulateTpar:
    """Test _populate_tpar function"""
    
    def test_populate_tpar_detect_plate(self):
        """Test target parameter population with detect_plate format"""
        targ_params = {
            'detect_plate': {
                'gvth_1': 50,
                'gvth_2': 50,
                'gvth_3': 50,
                'gvth_4': 50,
                'min_npix': 25,
                'max_npix': 900,
                'min_npix_x': 5,
                'max_npix_x': 30,
                'min_npix_y': 5,
                'max_npix_y': 30,
                'sum_grey': 20,
                'tol_dis': 20
            }
        }
        n_cam = 4
        
        result = _populate_tpar(targ_params, n_cam)
        
        assert isinstance(result, TargetParams)
        grey_thresholds = result.get_grey_thresholds()
        assert len(grey_thresholds) == 4
        assert all(th == 50 for th in grey_thresholds)
    
    def test_populate_tpar_targ_rec(self):
        """Test target parameter population with targ_rec format"""
        targ_params = {
            'targ_rec': {
                'gvthres': [50, 50, 50, 50],
                'nnmin': 25,
                'nnmax': 900,
                'nxmin': 5,
                'nxmax': 30,
                'nymin': 5,
                'nymax': 30,
                'sumg_min': 20,
                'disco': 20
            }
        }
        n_cam = 4
        
        result = _populate_tpar(targ_params, n_cam)
        
        assert isinstance(result, TargetParams)
        grey_thresholds = result.get_grey_thresholds()
        assert len(grey_thresholds) == 4
        assert all(th == 50 for th in grey_thresholds)
    
    def test_populate_tpar_missing_detect_plate_params(self):
        """Test target parameter population with missing detect_plate parameters"""
        targ_params = {
            'detect_plate': {
                'gvth_1': 50,
                'gvth_2': 50,
                # Missing required parameters
            }
        }
        n_cam = 4
        
        with pytest.raises(ValueError):
            _populate_tpar(targ_params, n_cam)
    
    def test_populate_tpar_missing_section(self):
        """Test target parameter population with missing section"""
        targ_params = {
            'invalid_section': {}
        }
        n_cam = 4
        
        with pytest.raises(ValueError, match="Target parameters must contain either"):
            _populate_tpar(targ_params, n_cam)
    
    def test_populate_tpar_missing_grey_thresholds(self):
        """Test target parameter population with missing grey thresholds"""
        targ_params = {
            'detect_plate': {
                'gvth_1': 50,
                'gvth_2': 50,
                # Missing gvth_3 and gvth_4
                'min_npix': 25,
                'max_npix': 900,
                'min_npix_x': 5,
                'max_npix_x': 30,
                'min_npix_y': 5,
                'max_npix_y': 30,
                'sum_grey': 20,
                'tol_dis': 20
            }
        }
        n_cam = 4
        
        with pytest.raises(ValueError, match="Missing required grey threshold keys"):
            _populate_tpar(targ_params, n_cam)


if __name__ == "__main__":
    pytest.main([__file__])
