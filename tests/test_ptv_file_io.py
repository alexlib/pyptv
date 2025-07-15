"""Unit tests for file I/O functions in ptv.py"""

import pytest
import numpy as np
import tempfile
import os
from unittest.mock import Mock, patch, mock_open
from pyptv.ptv import (
    read_targets, write_targets, file_base_to_filename, read_rt_is_file
)


class TestReadTargets:
    """Test read_targets function"""
    
    def test_read_targets_valid_file(self):
        """Test reading targets from a valid file"""
        mock_file_content = "1 100.5 200.5 30 150\n2 110.5 210.5 25 140\n"
        
        with patch('builtins.open', mock_open(read_data=mock_file_content)):
            with patch('os.path.exists', return_value=True):
                result = read_targets('dummy_file.txt')
                
                assert result is not None
    
    def test_read_targets_nonexistent_file(self):
        """Test reading targets from nonexistent file"""
        with patch('os.path.exists', return_value=False):
            with pytest.raises(FileNotFoundError):
                read_targets('nonexistent_file.txt')
    
    def test_read_targets_empty_file(self):
        """Test reading targets from empty file"""
        with patch('builtins.open', mock_open(read_data="")):
            with patch('os.path.exists', return_value=True):
                result = read_targets('empty_file.txt')
                
                # Should handle empty file gracefully
                assert result is not None
    
    def test_read_targets_invalid_format(self):
        """Test reading targets from file with invalid format"""
        mock_file_content = "invalid data format\n"
        
        with patch('builtins.open', mock_open(read_data=mock_file_content)):
            with patch('os.path.exists', return_value=True):
                with pytest.raises((ValueError, IndexError)):
                    read_targets('invalid_file.txt')


class TestWriteTargets:
    """Test write_targets function"""
    
    def test_write_targets_basic(self):
        """Test writing targets to file"""
        mock_target = Mock()
        mock_target.pnr.return_value = 1
        mock_target.pos.return_value = [100.5, 200.5]
        mock_target.count_pixels.return_value = [5, 6]
        mock_target.sum_grey_value.return_value = 150
        mock_target.tnr.return_value = 0
        
        targets = [mock_target]
        
        with patch('builtins.open', mock_open()) as mock_file:
            result = write_targets(targets, 'output_file.txt')
            
            mock_file.assert_called_once_with('output_file.txt', 'w')
            assert result is not None
    
    def test_write_targets_empty_list(self):
        """Test writing empty target list"""
        targets = []
        
        with patch('builtins.open', mock_open()) as mock_file:
            result = write_targets(targets, 'output_file.txt')
            
            mock_file.assert_called_once_with('output_file.txt', 'w')
            assert result is not None
    
    def test_write_targets_permission_error(self):
        """Test writing targets with permission error"""
        mock_target = Mock()
        mock_target.pnr.return_value = 1
        mock_target.pos.return_value = [100.5, 200.5]
        mock_target.count_pixels.return_value = [5, 6]
        mock_target.sum_grey_value.return_value = 150
        mock_target.tnr.return_value = 0
        
        targets = [mock_target]
        
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            with pytest.raises(PermissionError):
                write_targets(targets, '/root/protected_file.txt')
    
    def test_write_targets_invalid_path(self):
        """Test writing targets to invalid path"""
        mock_target = Mock()
        mock_target.pnr.return_value = 1
        mock_target.pos.return_value = [100.5, 200.5]
        mock_target.count_pixels.return_value = [5, 6]
        mock_target.sum_grey_value.return_value = 150
        mock_target.tnr.return_value = 0
        
        targets = [mock_target]
        
        with patch('builtins.open', side_effect=FileNotFoundError("No such file or directory")):
            with pytest.raises(FileNotFoundError):
                write_targets(targets, '/nonexistent/path/file.txt')


class TestFileBaseToFilename:
    """Test file_base_to_filename function"""
    
    def test_file_base_to_filename_basic(self):
        """Test basic filename generation"""
        base_name = "img_%04d.tif"
        frame_num = 1001
        
        result = file_base_to_filename(base_name, frame_num)
        
        assert result == "img_1001.tif"
    
    def test_file_base_to_filename_no_format(self):
        """Test filename generation without format specifier"""
        base_name = "image.tif"
        frame_num = 1001
        
        result = file_base_to_filename(base_name, frame_num)
        
        # Should handle base names without format specifiers
        assert result is not None
    
    def test_file_base_to_filename_complex_format(self):
        """Test filename generation with complex format"""
        base_name = "exp_%s_cam_%02d_frame_%04d.tif"
        frame_num = 1001
        
        # This should raise an error due to insufficient arguments
        with pytest.raises((TypeError, ValueError)):
            file_base_to_filename(base_name, frame_num)
    
    def test_file_base_to_filename_zero_padding(self):
        """Test filename generation with zero padding"""
        base_name = "data_%06d.jpg"
        frame_num = 42
        
        result = file_base_to_filename(base_name, frame_num)
        
        assert result == "data_000042.jpg"
    
    def test_file_base_to_filename_negative_frame(self):
        """Test filename generation with negative frame number"""
        base_name = "img_%04d.tif"
        frame_num = -1
        
        result = file_base_to_filename(base_name, frame_num)
        
        # Should handle negative numbers
        assert result is not None


class TestReadRtIsFile:
    """Test read_rt_is_file function"""
    
    def test_read_rt_is_file_existing_file(self):
        """Test checking if rt file exists"""
        with patch('os.path.exists', return_value=True):
            result = read_rt_is_file('existing_file.rt')
            
            assert result is True
    
    def test_read_rt_is_file_nonexistent_file(self):
        """Test checking if rt file exists when it doesn't"""
        with patch('os.path.exists', return_value=False):
            result = read_rt_is_file('nonexistent_file.rt')
            
            assert result is False
    
    def test_read_rt_is_file_invalid_extension(self):
        """Test checking file with invalid extension"""
        with patch('os.path.exists', return_value=True):
            # The function should still check existence regardless of extension
            result = read_rt_is_file('file.txt')
            
            assert result is True
    
    def test_read_rt_is_file_empty_filename(self):
        """Test checking with empty filename"""
        with patch('os.path.exists', return_value=False):
            result = read_rt_is_file('')
            
            assert result is False
    
    def test_read_rt_is_file_none_filename(self):
        """Test checking with None filename"""
        with pytest.raises((TypeError, AttributeError)):
            read_rt_is_file(None)


if __name__ == "__main__":
    pytest.main([__file__])
