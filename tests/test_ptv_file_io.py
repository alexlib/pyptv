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
        # Format: first line is number of targets, then target data (8 columns each)
        mock_file_content = "2\n1 100.5 200.5 30 25 15 150 0\n2 110.5 210.5 25 20 10 140 1\n"
        
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
                with pytest.raises(ValueError):
                    read_targets('empty_file.txt')
    
    def test_read_targets_invalid_format(self):
        """Test reading targets from file with invalid format"""
        # First line should be number of targets, second line has wrong number of columns
        mock_file_content = "1\n1 100.5 200.5 30\n"  # Only 4 columns instead of 8
        
        with patch('builtins.open', mock_open(read_data=mock_file_content)):
            with patch('os.path.exists', return_value=True):
                with pytest.raises(ValueError, match="Bad format for file"):
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
            
            # The function creates filename using file_base_to_filename which appends frame and _targets
            expected_filename = 'output_file.123456789_targets'
            mock_file.assert_called_once_with(expected_filename, 'wt')
            assert result is not None
    
    def test_write_targets_empty_list(self):
        """Test writing empty target list"""
        targets = []
        
        with patch('builtins.open', mock_open()) as mock_file:
            result = write_targets(targets, 'output_file.txt')
            
            # The function creates filename using file_base_to_filename which appends frame and _targets
            expected_filename = 'output_file.123456789_targets'
            mock_file.assert_called_once_with(expected_filename, 'wt')
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
            result = write_targets(targets, '/root/protected_file.txt')
            # Function catches IOError and returns False instead of raising
            assert result is False
    
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
            result = write_targets(targets, '/nonexistent/path/file.txt')
            # Function catches IOError and returns False instead of raising
            assert result is False


class TestFileBaseToFilename:
    """Test file_base_to_filename function"""
    
    def test_file_base_to_filename_basic(self):
        """Test basic filename generation"""
        base_name = "img_%04d.tif"
        frame_num = 1001
        
        result = file_base_to_filename(base_name, frame_num)
        
        # Function appends _targets and returns a Path object
        assert str(result) == "img_1001_targets"
    
    def test_file_base_to_filename_no_format(self):
        """Test filename generation without format specifier"""
        base_name = "image.tif"
        frame_num = 1001
        
        result = file_base_to_filename(base_name, frame_num)
        
        # Should handle base names without format specifiers and append frame and _targets
        assert str(result) == "image.1001_targets"
    
    def test_file_base_to_filename_complex_format(self):
        """Test filename generation with complex format"""
        base_name = "exp_test_cam_01_frame_%04d.tif"
        frame_num = 1001
        
        result = file_base_to_filename(base_name, frame_num)
        
        # Function should handle this and append _targets
        assert str(result) == "exp_test_cam_01_frame_1001_targets"
    
    def test_file_base_to_filename_zero_padding(self):
        """Test filename generation with zero padding"""
        base_name = "data_%06d.jpg"
        frame_num = 42
        
        result = file_base_to_filename(base_name, frame_num)
        
        # Function converts %06d to %04d and appends _targets
        assert str(result) == "data_0042_targets"
    
    def test_file_base_to_filename_negative_frame(self):
        """Test filename generation with negative frame number"""
        base_name = "img_%04d.tif"
        frame_num = -1
        
        result = file_base_to_filename(base_name, frame_num)
        
        # Should handle negative numbers and append _targets
        assert str(result) == "img_-001_targets"


class TestReadRtIsFile:
    """Test read_rt_is_file function"""
    
    def test_read_rt_is_file_valid_content(self):
        """Test reading valid rt_is file content"""
        # Mock rt_is file content with proper format
        mock_content = """2
0 100.5 200.5 50.0 1 2 3 4
1 110.5 210.5 60.0 5 6 7 8
"""
        with patch('builtins.open', mock_open(read_data=mock_content)):
            result = read_rt_is_file('test.rt')
            
            assert len(result) == 2
            assert result[0] == [100.5, 200.5, 50.0, 1, 2, 3, 4]
            assert result[1] == [110.5, 210.5, 60.0, 5, 6, 7, 8]
    
    def test_read_rt_is_file_empty_file(self):
        """Test reading empty rt_is file raises ValueError"""
        mock_content = "0\n"
        with patch('builtins.open', mock_open(read_data=mock_content)):
            with pytest.raises(ValueError, match="Failed to read the number of rows"):
                read_rt_is_file('empty.rt')
    
    def test_read_rt_is_file_nonexistent_file(self):
        """Test reading nonexistent file raises IOError"""
        with pytest.raises(IOError):
            read_rt_is_file('nonexistent_file.rt')
    
    def test_read_rt_is_file_invalid_format(self):
        """Test reading file with invalid format"""
        # Missing values in line
        mock_content = """1
0 100.5 200.5
"""
        with patch('builtins.open', mock_open(read_data=mock_content)):
            with pytest.raises(ValueError, match="Incorrect number of values in line"):
                read_rt_is_file('invalid.rt')
    
    def test_read_rt_is_file_zero_rows_error(self):
        """Test file with zero rows raises ValueError"""
        mock_content = "0\n"
        with patch('builtins.open', mock_open(read_data=mock_content)):
            with pytest.raises(ValueError, match="Failed to read the number of rows"):
                read_rt_is_file('zero_rows.rt')


if __name__ == "__main__":
    pytest.main([__file__])
