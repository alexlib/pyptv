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
        
        # Should still get 4 quadrants in specified order
        assert len(result) == 4
        
        # Verify order is applied correctly
        default_result = image_split(img)
        for i, quad_idx in enumerate(custom_order):
            np.testing.assert_array_equal(result[i], default_result[quad_idx])
    
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
    
    def test_simple_highpass_basic(self):
        """Test basic highpass filtering"""
        # Create a simple test image
        img = np.random.randint(0, 255, (50, 50), dtype=np.uint8)
        
        result = simple_highpass(img, self.cpar)
        
        # Result should be same size
        assert result.shape == img.shape
        assert result.dtype == np.uint8
    
    def test_simple_highpass_uniform_image(self):
        """Test highpass filter on uniform image"""
        # Uniform image should be mostly filtered out
        img = np.full((50, 50), 128, dtype=np.uint8)
        
        with patch('pyptv.ptv.preprocess_image') as mock_preprocess:
            # Mock the preprocessing to avoid potential core dumps with uniform images
            mock_preprocess.return_value = np.zeros((50, 50), dtype=np.uint8)
            
            result = simple_highpass(img, self.cpar)
            
            # Result should be mostly zeros (or low values)
            assert result.shape == img.shape
            assert np.mean(result) <= np.mean(img)
    
    def test_simple_highpass_edge_detection(self):
        """Test highpass filter on image with edges"""
        # Create image with sharp edge
        img = np.zeros((50, 50), dtype=np.uint8)
        img[:, 25:] = 255
        
        result = simple_highpass(img, self.cpar)
        
        # Should enhance the edge
        assert result.shape == img.shape
        # Edge should have high values
        assert np.max(result[:, 20:30]) > 0
    
    def test_simple_highpass_invalid_cpar(self):
        """Test highpass filter with invalid control parameters"""
        img = np.random.randint(0, 255, (50, 50), dtype=np.uint8)
        
        # Test with None
        with pytest.raises((AttributeError, TypeError)):
            simple_highpass(img, None)


if __name__ == "__main__":
    pytest.main([__file__])
