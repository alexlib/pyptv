"""Unit tests for basic image processing functions in ptv.py"""

import pytest
import numpy as np
from unittest.mock import patch
from pyptv.ptv import image_split, negative, simple_highpass
from optv.parameters import ControlParams


class TestImageSplit:
    """Test image_split function"""
    
    def test_image_split_basic(self):
        """Test basic image splitting functionality"""
        # Create a test image 4x4
        img = np.arange(16).reshape(4, 4)
        result = image_split(img)
        
        # Check we get 4 quadrants
        assert len(result) == 4
        
        # Check quadrant shapes
        for quad in result:
            assert quad.shape == (2, 2)
    
    def test_image_split_custom_order(self):
        """Test image splitting with custom order"""
        img = np.arange(16).reshape(4, 4)
        custom_order = [3, 2, 1, 0]
        result = image_split(img, order=custom_order)
        
        # Should still get 4 quadrants
        assert len(result) == 4
        
        # Get the original quadrants (without custom ordering)
        original_quadrants = [
            img[: img.shape[0] // 2, : img.shape[1] // 2],  # top-left
            img[: img.shape[0] // 2, img.shape[1] // 2:],   # top-right
            img[img.shape[0] // 2:, : img.shape[1] // 2],   # bottom-left
            img[img.shape[0] // 2:, img.shape[1] // 2:],    # bottom-right
        ]
        
        # Verify the custom order is applied correctly
        for i, quad_idx in enumerate(custom_order):
            np.testing.assert_array_equal(result[i], original_quadrants[quad_idx])
    
    def test_image_split_different_sizes(self):
        """Test image splitting with different image sizes"""
        # Test with larger image
        img = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        result = image_split(img)
        
        assert len(result) == 4
        for quad in result:
            assert quad.shape == (50, 50)
    
    def test_image_split_invalid_input(self):
        """Test image splitting with invalid inputs"""
        # Test with 1D array
        img_1d = np.arange(16)
        with pytest.raises(IndexError):
            image_split(img_1d)


class TestNegative:
    """Test negative function"""
    
    def test_negative_basic(self):
        """Test basic negative conversion"""
        img = np.array([[0, 127, 255]], dtype=np.uint8)
        result = negative(img)
        
        expected = np.array([[255, 128, 0]], dtype=np.uint8)
        np.testing.assert_array_equal(result, expected)
    
    def test_negative_full_range(self):
        """Test negative with full intensity range"""
        img = np.arange(256, dtype=np.uint8)
        result = negative(img)
        
        expected = 255 - img
        np.testing.assert_array_equal(result, expected)
    
    def test_negative_2d_image(self):
        """Test negative with 2D image"""
        img = np.array([[0, 50, 100], 
                       [150, 200, 255]], dtype=np.uint8)
        result = negative(img)
        
        expected = np.array([[255, 205, 155], 
                            [105, 55, 0]], dtype=np.uint8)
        np.testing.assert_array_equal(result, expected)


class TestSimpleHighpass:
    """Test simple_highpass function"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.cpar = ControlParams(1)  # Single camera setup
        self.cpar.set_image_size((100, 100))
        self.cpar.set_pixel_size((0.01, 0.01))
    
    def test_simple_highpass_mocked(self):
        """Test basic highpass filtering with mocked preprocess_image to avoid segfaults"""
        img = np.random.randint(0, 255, (50, 50), dtype=np.uint8)
        
        with patch('pyptv.ptv.preprocess_image') as mock_preprocess:
            # Mock the preprocessing to return a safe result
            expected_result = np.zeros((50, 50), dtype=np.uint8)
            mock_preprocess.return_value = expected_result
            
            result = simple_highpass(img, self.cpar)
            
            # Verify the function was called correctly
            mock_preprocess.assert_called_once()
            # Check that our function returns what the mock returns
            np.testing.assert_array_equal(result, expected_result)
            assert result.shape == img.shape
            assert result.dtype == np.uint8
    
    def test_simple_highpass_function_signature(self):
        """Test that simple_highpass has the correct function signature"""
        img = np.random.randint(100, 150, (30, 30), dtype=np.uint8)
        
        with patch('pyptv.ptv.preprocess_image') as mock_preprocess:
            mock_preprocess.return_value = np.zeros((30, 30), dtype=np.uint8)
            
            # Test function can be called with expected arguments
            result = simple_highpass(img, self.cpar)
            
            # Verify preprocess_image was called with the right parameters
            args, kwargs = mock_preprocess.call_args
            assert len(args) == 4  # img, no_filter, cpar, filter_size
            assert args[0] is img
            assert args[2] is self.cpar
    
    def test_simple_highpass_constants_used(self):
        """Test that simple_highpass uses the expected constants"""
        img = np.zeros((20, 20), dtype=np.uint8)
        
        with patch('pyptv.ptv.preprocess_image') as mock_preprocess:
            with patch('pyptv.ptv.DEFAULT_NO_FILTER', 0) as mock_no_filter:
                with patch('pyptv.ptv.DEFAULT_HIGHPASS_FILTER_SIZE', 7) as mock_filter_size:
                    mock_preprocess.return_value = np.zeros((20, 20), dtype=np.uint8)
                    
                    simple_highpass(img, self.cpar)
                    
                    # Verify the constants are used as expected
                    args, kwargs = mock_preprocess.call_args
                    assert args[1] == 0  # DEFAULT_NO_FILTER
                    assert args[3] == 7  # DEFAULT_HIGHPASS_FILTER_SIZE


if __name__ == "__main__":
    pytest.main([__file__])
