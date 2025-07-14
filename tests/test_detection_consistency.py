"""
Test that GUI manual detection and sequence detection use the same parameters
and produce consistent results.
"""

import pytest
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

from pyptv.ptv import py_detection_proc_c, py_start_proc_c, _populate_tpar
from pyptv.parameter_manager import ParameterManager
from pyptv.experiment import Experiment


class TestDetectionConsistency:
    """Test that manual GUI detection and sequence detection are consistent."""
    
    @pytest.fixture
    def experiment(self):
        """Create an experiment with test cavity parameters."""
        experiment = Experiment()
        test_dir = Path(__file__).parent / "test_cavity"
        experiment.populate_runs(test_dir)
        experiment.setActive(0)  # Use first parameter set
        return experiment
    
    @pytest.fixture
    def test_images(self):
        """Create test images for detection."""
        # Create simple test images with some "particles" (bright spots)
        images = []
        for i in range(4):  # 4 cameras
            img = np.zeros((512, 512), dtype=np.uint8)
            # Add some bright spots as fake particles
            img[100:110, 100:110] = 255  # particle 1
            img[200:205, 200:205] = 200  # particle 2  
            img[300:308, 300:308] = 180  # particle 3
            images.append(img)
        return images
    
    def test_tpar_parameter_consistency(self, experiment):
        """Test that py_start_proc_c uses targ_rec parameters, not detect_plate."""
        
        # Get parameter manager
        pm = experiment.parameter_manager
        
        # Get both parameter sections
        targ_rec_params = pm.get_parameter('targ_rec')
        detect_plate_params = pm.get_parameter('detect_plate')
        
        print(f"targ_rec params: {targ_rec_params}")
        print(f"detect_plate params: {detect_plate_params}")
        
        # Verify they're different (this is the source of the bug)
        assert targ_rec_params != detect_plate_params, "Parameters should be different"
        
        # Test py_start_proc_c creates tpar from targ_rec
        cpar, spar, vpar, track_par, tpar, cals, epar = py_start_proc_c(pm)
        
        # Test manual GUI approach
        target_params_gui = {'targ_rec': targ_rec_params}
        tpar_gui = _populate_tpar(target_params_gui, pm.n_cam)
        
        # Compare the TargetParams objects - they should be identical
        np.testing.assert_array_equal(tpar.get_grey_thresholds(), tpar_gui.get_grey_thresholds())
        assert tpar.get_pixel_count_bounds() == tpar_gui.get_pixel_count_bounds()
        assert tpar.get_xsize_bounds() == tpar_gui.get_xsize_bounds()
        assert tpar.get_ysize_bounds() == tpar_gui.get_ysize_bounds()
        
        print("✅ py_start_proc_c now correctly uses targ_rec parameters")
    
    def test_detection_consistency(self, experiment):
        """Test that manual detection and sequence detection use same parameters."""
        
        # Get parameters
        pm = experiment.parameter_manager
        ptv_params = pm.get_parameter('ptv')
        targ_rec_params = pm.get_parameter('targ_rec')
        
        # Manual GUI approach (what img_coord_action does)
        target_params_gui = {'targ_rec': targ_rec_params}
        tpar_gui = _populate_tpar(target_params_gui, pm.n_cam)
        
        # Sequence approach (what py_start_proc_c creates for sequence)
        cpar, spar, vpar, track_par, tpar_seq, cals, epar = py_start_proc_c(pm)
        
        # Compare the TargetParams objects - they should be identical
        np.testing.assert_array_equal(tpar_seq.get_grey_thresholds(), tpar_gui.get_grey_thresholds())
        assert tpar_seq.get_pixel_count_bounds() == tpar_gui.get_pixel_count_bounds()
        assert tpar_seq.get_xsize_bounds() == tpar_gui.get_xsize_bounds()
        assert tpar_seq.get_ysize_bounds() == tpar_gui.get_ysize_bounds()
        
        print("✅ Manual GUI and sequence detection use identical target parameters")
    
    def test_parameter_sections_exist(self, experiment):
        """Test that both targ_rec and detect_plate sections exist in YAML."""
        
        pm = experiment.parameter_manager
        
        targ_rec = pm.get_parameter('targ_rec')
        detect_plate = pm.get_parameter('detect_plate')
        
        assert targ_rec is not None, "targ_rec section should exist"
        assert detect_plate is not None, "detect_plate section should exist"
        
        # Print the difference to understand why they're different
        print(f"targ_rec grey thresholds: {targ_rec.get('gvthres', 'NOT_FOUND')}")
        print(f"detect_plate grey thresholds: [gvth_1={detect_plate.get('gvth_1')}, gvth_2={detect_plate.get('gvth_2')}, gvth_3={detect_plate.get('gvth_3')}, gvth_4={detect_plate.get('gvth_4')}]")
        
        print(f"targ_rec pixel bounds: nnmin={targ_rec.get('nnmin')}, nnmax={targ_rec.get('nnmax')}")
        print(f"detect_plate pixel bounds: min_npix={detect_plate.get('min_npix')}, max_npix={detect_plate.get('max_npix')}")


if __name__ == "__main__":
    # Run a simple test manually
    test_case = TestDetectionConsistency()
    
    from pyptv.experiment import Experiment
    experiment = Experiment()
    test_dir = Path(__file__).parent / "test_cavity"
    experiment.populate_runs(test_dir)
    experiment.setActive(0)
    
    test_case.test_tpar_parameter_consistency(experiment)
    test_case.test_parameter_sections_exist(experiment)
    
    print("All tests passed!")
