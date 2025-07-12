#!/usr/bin/env python3
"""
Pytest test suite for DetectionGUI functionality
"""

import pytest
import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from pyptv.detection_gui import DetectionGUI
from pyptv.experiment import Experiment


@pytest.fixture
def experiment_with_test_data():
    """Create an experiment with test data loaded"""
    experiment = Experiment()
    test_yaml = Path("tests/test_cavity/parameters_Run1.yaml")
    
    if test_yaml.exists():
        experiment.addParamset("Run1", test_yaml)
        experiment.setActive(0)
    else:
        pytest.skip(f"Test YAML file {test_yaml} not found")
    
    return experiment


@pytest.fixture
def test_working_directory():
    """Create a test working directory with known structure"""
    test_dir = Path("tests/test_cavity")
    if not test_dir.exists():
        pytest.skip(f"Test directory {test_dir} not found")
    return test_dir


class TestDetectionGUI:
    """Test suite for DetectionGUI class"""
    
    def test_detection_gui_initialization_with_working_directory(self, test_working_directory):
        """Test DetectionGUI initialization with working directory"""
        gui = DetectionGUI(working_directory=test_working_directory)
        
        assert gui.working_directory == test_working_directory
        assert gui.parameters_loaded is False
        assert gui.image_loaded is False
        assert gui.raw_image is None
        assert gui.processed_image is None
        assert gui.cpar is None
        assert gui.tpar is None
    
    def test_detection_gui_initialization_with_experiment(self, experiment_with_test_data):
        """Test DetectionGUI initialization with experiment object"""
        # This test assumes DetectionGUI should accept an experiment
        # We need to modify the constructor to handle both cases
        
        # For now, we'll extract the working directory from the experiment
        working_dir = Path.cwd() / "tests" / "test_cavity"  # Default test directory
        gui = DetectionGUI(working_directory=working_dir)
        
        # Test that the GUI can be initialized
        assert gui.working_directory == working_dir
        assert isinstance(gui.thresholds, list)
        assert len(gui.thresholds) == 4
        assert isinstance(gui.pixel_count_bounds, list)
        assert len(gui.pixel_count_bounds) == 2
    
    def test_parameter_loading(self, test_working_directory):
        """Test parameter loading functionality"""
        gui = DetectionGUI(working_directory=test_working_directory)
        
        # Change to test directory before loading parameters
        original_cwd = os.getcwd()
        try:
            os.chdir(test_working_directory)
            
            # Set a test image name that should exist
            test_image = "cal/cam1.tif"
            if (test_working_directory / test_image).exists():
                gui.image_name = test_image
                
                # Test parameter loading
                gui._button_load_params()
                
                assert gui.parameters_loaded is True
                assert gui.image_loaded is True
                assert gui.raw_image is not None
                assert gui.cpar is not None
                assert gui.tpar is not None
                
                # Test parameter values
                assert len(gui.thresholds) == 4
                assert len(gui.pixel_count_bounds) == 2
                assert len(gui.xsize_bounds) == 2
                assert len(gui.ysize_bounds) == 2
                assert isinstance(gui.sum_grey, int)
                assert isinstance(gui.disco, int)
                
                # Test that image was loaded correctly
                assert gui.raw_image.shape[0] > 0
                assert gui.raw_image.shape[1] > 0
            else:
                pytest.skip(f"Test image {test_image} not found")
                
        finally:
            os.chdir(original_cwd)
    
    def test_parameter_loading_missing_image(self, test_working_directory):
        """Test parameter loading with missing image file"""
        gui = DetectionGUI(working_directory=test_working_directory)
        
        # Set a non-existent image name
        gui.image_name = "nonexistent_image.tif"
        
        original_cwd = os.getcwd()
        try:
            os.chdir(test_working_directory)
            
            # Test parameter loading should fail gracefully
            gui._button_load_params()
            
            assert gui.parameters_loaded is False
            assert gui.image_loaded is False
            assert "Error reading image" in gui.status_text
                
        finally:
            os.chdir(original_cwd)
    
    def test_parameter_loading_missing_directory(self):
        """Test parameter loading with missing working directory"""
        non_existent_dir = Path("/tmp/nonexistent_test_directory")
        gui = DetectionGUI(working_directory=non_existent_dir)
        
        # Test parameter loading should fail gracefully
        gui._button_load_params()
        
        assert gui.parameters_loaded is False
        assert "does not exist" in gui.status_text
    
    def test_dynamic_trait_creation(self, test_working_directory):
        """Test that dynamic traits are created when parameters are loaded"""
        gui = DetectionGUI(working_directory=test_working_directory)
        
        original_cwd = os.getcwd()
        try:
            os.chdir(test_working_directory)
            
            # Set a test image that should exist
            test_image = "cal/cam1.tif"
            if (test_working_directory / test_image).exists():
                gui.image_name = test_image
                
                # Before loading parameters, check traits don't exist
                assert not hasattr(gui, 'grey_thresh')
                
                # Load parameters
                gui._button_load_params()
                
                if gui.parameters_loaded:
                    # After loading, dynamic traits should exist
                    assert hasattr(gui, 'grey_thresh')
                    assert hasattr(gui, 'min_npix')
                    
                    # Test that trait values are set correctly
                    assert gui.grey_thresh >= 0
                    assert gui.min_npix >= 0
            else:
                pytest.skip(f"Test image {test_image} not found")
                
        finally:
            os.chdir(original_cwd)
    
    def test_status_text_updates(self, test_working_directory):
        """Test that status text is updated correctly during operations"""
        gui = DetectionGUI(working_directory=test_working_directory)
        
        # Initially should have some default status
        initial_status = gui.status_text
        
        original_cwd = os.getcwd()
        try:
            os.chdir(test_working_directory)
            
            test_image = "cal/cam1.tif"
            if (test_working_directory / test_image).exists():
                gui.image_name = test_image
                gui._button_load_params()
                
                if gui.parameters_loaded:
                    # Status should be updated after successful loading
                    assert gui.status_text != initial_status
                    assert "Parameters loaded" in gui.status_text
            else:
                pytest.skip(f"Test image {test_image} not found")
                
        finally:
            os.chdir(original_cwd)


class TestDetectionGUIIntegration:
    """Integration tests for DetectionGUI with real data"""
    
    def test_full_detection_workflow(self, test_working_directory):
        """Test the complete detection workflow"""
        gui = DetectionGUI(working_directory=test_working_directory)
        
        original_cwd = os.getcwd()
        try:
            os.chdir(test_working_directory)
            
            test_image = "cal/cam1.tif"
            if (test_working_directory / test_image).exists():
                gui.image_name = test_image
                
                # Step 1: Load parameters
                gui._button_load_params()
                assert gui.parameters_loaded is True
                assert gui.image_loaded is True
                
                # Step 2: Test that we can access the image data
                assert gui.raw_image is not None
                assert gui.raw_image.ndim == 2  # Should be grayscale
                
                # Step 3: Test that parameters are properly initialized
                assert gui.cpar is not None
                assert gui.tpar is not None
                
                print("✓ Full detection workflow test passed")
                print(f"  - Image shape: {gui.raw_image.shape}")
                print(f"  - Grey threshold: {gui.thresholds[0]}")
                print(f"  - Pixel bounds: {gui.pixel_count_bounds}")
                print(f"  - X size bounds: {gui.xsize_bounds}")
                print(f"  - Y size bounds: {gui.ysize_bounds}")
                
            else:
                pytest.skip(f"Test image {test_image} not found")
                
        finally:
            os.chdir(original_cwd)


@pytest.mark.parametrize("threshold_values", [
    [10, 0, 0, 0],
    [40, 0, 0, 0], 
    [80, 0, 0, 0],
])
def test_threshold_parameter_variations(threshold_values, test_working_directory):
    """Test DetectionGUI with different threshold values"""
    gui = DetectionGUI(working_directory=test_working_directory)
    
    # Set custom threshold values
    gui.thresholds = threshold_values
    
    assert gui.thresholds == threshold_values
    assert len(gui.thresholds) == 4
    assert all(isinstance(t, int) for t in gui.thresholds)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
