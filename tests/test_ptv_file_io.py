"""Unit tests for file I/O functions in ptv.py"""

import pytest
import numpy as np
import tempfile
import os
from unittest.mock import Mock, patch, mock_open
from pyptv.ptv import (
    read_targets, write_targets, read_rt_is_file, generate_short_file_bases, extract_cam_ids
)


class TestReadTargets:
    """Test read_targets function"""
    
    def test_read_targets_valid_file(self):
        """Test reading targets from a valid file"""
        mock_file_content = "2\n1 100.5 200.5 30 25 15 150 0\n2 110.5 210.5 25 20 10 140 1\n"
        base_names = ['img_cam1_%04d.tif']
        short_file_bases = generate_short_file_bases(base_names)
        with patch('builtins.open', mock_open(read_data=mock_file_content)):
            with patch('os.path.exists', return_value=True):
                result = read_targets(short_file_bases[0], 10000)
                assert result is not None
    
    def test_read_targets_nonexistent_file(self):
        """Test reading targets from nonexistent file"""
        base_names = ['img_cam1_%04d.tif']
        short_file_bases = generate_short_file_bases(base_names)
        with patch('os.path.exists', return_value=False):
            with pytest.raises(FileNotFoundError):
                read_targets(short_file_bases[0], 10000)
    
    def test_read_targets_empty_file(self):
        """Test reading targets from empty file"""
        base_names = ['img_cam1_%04d.tif']
        short_file_bases = generate_short_file_bases(base_names)
        with patch('builtins.open', mock_open(read_data="")):
            with patch('os.path.exists', return_value=True):
                with pytest.raises(ValueError):
                    read_targets(short_file_bases[0], 10000)
    
    def test_read_targets_invalid_format(self):
        """Test reading targets from file with invalid format"""
        mock_file_content = "1\n1 100.5 200.5 30\n"  # Only 4 columns instead of 8
        base_names = ['img_cam1_%04d.tif']
        short_file_bases = generate_short_file_bases(base_names)
        with patch('builtins.open', mock_open(read_data=mock_file_content)):
            with patch('os.path.exists', return_value=True):
                with pytest.raises(ValueError, match="Bad format for file"):
                    read_targets(short_file_bases[0], 10000)


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
        base_names = ['img_cam1_%04d.tif']
        short_file_bases = generate_short_file_bases(clean_bases(base_names))
        # print(short_file_bases)
        with patch('builtins.open', mock_open()) as mock_file:
            result = write_targets(targets, short_file_bases[0], 123456789)
            expected_filename = f'cam1.123456789_targets'
            mock_file.assert_called_once_with(expected_filename, 'wt')
            assert result is not None
    
    def test_write_targets_empty_list(self):
        """Test writing empty target list"""
        targets = []
        base_names = ['img_cam1_%04d.tif']
        short_file_bases = generate_short_file_bases(base_names)
        with patch('builtins.open', mock_open()) as mock_file:
            result = write_targets(targets, short_file_bases[0], 123456789)
            expected_filename = f'cam1.123456789_targets'
            mock_file.assert_called_once_with(expected_filename, 'w', encoding='utf-8')
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
        base_names = ['img_cam1_%04d.tif']
        short_file_bases = generate_short_file_bases(base_names)
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            result = write_targets(targets, short_file_bases[0], 123456789)
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
        base_names = ['img_cam1_%04d.tif']
        short_file_bases = generate_short_file_bases(base_names)
        with patch('builtins.open', side_effect=FileNotFoundError("No such file or directory")):
            result = write_targets(targets, short_file_bases[0], 123456789)
            assert result is False


def clean_bases(file_bases):
    import re
    """Remove frame number patterns like %d, %04d, etc. from file bases"""
    return [re.sub(r'%0?\d*d', '', s) for s in file_bases]


class TestExtractCamIds:
    """Test extract_cam_ids function"""

    def test_extract_cam_ids_basic(self):
        """Test extraction of camera ids from typical file base names"""
        file_bases = [
            "cam1_%04d.tif",
            "img_cam2_%03d.tif",
            "exp_test_cam_01_frame_%04d.tif",
            "c5_%d",
            "Cam12_extra",
            "c13",
            "C001H001S0001000001.tif"
        ]
        expected = [1, 2, 1, 5, 12, 13, 1]
        result = extract_cam_ids(file_bases)
        assert result == expected

    def test_extract_cam_ids_multiple_numbers(self):
        """Test extraction when multiple numbers are present in base names"""
        file_bases = [
            "prefix_cam1_img2_%04d.tif",
            "prefix_cam2_img3_%04d.tif",
            "prefix_cam3_img4_%04d.tif"
        ]
        # The cam id should be the one that varies (cam1, cam2, cam3 -> 1,2,3)
        expected = [1, 2, 3]
        result = extract_cam_ids(file_bases)
        assert result == expected

    def test_extract_cam_ids_no_numbers(self):
        """Test extraction when no numbers are present"""
        file_bases = [
            "camera0_%d.tif",
            "camera1_%d.tif"
        ]
        expected = [0, 1]
        result = extract_cam_ids(file_bases)
        assert result == expected

    def test_extract_cam_ids_single_entry(self):
        """Test extraction with a single file base"""
        file_bases = ["cam7_%04d.tif"]
        expected = [7]
        result = extract_cam_ids(file_bases)
        assert result == expected

    def test_extract_cam_ids_empty_list(self):
        """Test extraction with empty list should raise ValueError"""
        file_bases = []
        with pytest.raises(ValueError):
            extract_cam_ids(file_bases)

    def test_extract_cam_ids_trailing_number(self):
        """Test extraction when only trailing number is present"""
        file_bases = ["foo_bar_99"]
        expected = [99]
        result = extract_cam_ids(file_bases)
        assert result == expected

    def test_extract_cam_ids_varied_patterns(self):
        """Test extraction with varied patterns and leading zeros"""
        file_bases = [
            "cam01_%04d.tif",
            "cam02_%04d.tif",
            "cam03_%04d.tif"
        ]
        expected = [1, 2, 3]
        result = extract_cam_ids(file_bases)
        assert result == expected

    def test_extract_cam_ids_with_percent_d(self):
        """Test extraction with percent-d patterns"""
        file_bases = [
            "img_c1_%d",
            "img_c2_%d",
            "img_c3_%d"
        ]
        expected = [1, 2, 3]
        result = extract_cam_ids(file_bases)
        assert result == expected

    def test_extract_cam_ids_fallback(self):
        """Test fallback to last number if no varying position"""
        file_bases = [
            "foo_1_bar_2",
            "foo_1_bar_2"
        ]
        expected = [2, 2]
        result = extract_cam_ids(file_bases)
        assert result == expected

class TestCleanBases:
    """Test clean_bases utility function"""

    def test_clean_bases_removes_percent_d(self):
        file_bases = [
            "cam1_%04d.tif",
            "img_cam2_%03d.tif",
            "exp_test_cam_01_frame_%04d.tif",
            "c5_%d"
        ]
        expected = [
            "cam1_.tif",
            "img_cam2_.tif",
            "exp_test_cam_01_frame_.tif",
            "c5_"
        ]
        result = clean_bases(file_bases)
        assert result == expected

    def test_clean_bases_no_pattern(self):
        file_bases = [
            "cam1.tif",
            "img_cam2.tif"
        ]
        expected = [
            "cam1.tif",
            "img_cam2.tif"
        ]
        result = clean_bases(file_bases)
        assert result == expected

    def test_clean_bases_empty(self):
        file_bases = []
        expected = []
        result = clean_bases(file_bases)
        assert result == expected

class TestFileBaseToFilename:
    """Test file_base_to_short_file_base function"""
    
    def test_extract_cam_id(self):
        """Test extraction of cam_id from various base names"""
        test_cases = [
            ("cam1_%04d.tif", [1]),
            ("img_cam2_%03d.tif", [2]),
            ("exp_test_cam_01_frame_%04d.tif", [1]),
            ("c5_%%d", [5]),
            ("Cam12_extra", [12]),
            ("c13", [13]),
            ("C001H001S0001%05d.tif",[1])
        ]


        for base_name, expected_id in test_cases:
            cam_id = extract_cam_ids(base_name)
            assert cam_id == expected_id, f"{base_name} -> {cam_id}, expected {expected_id}"

    # def test_generate_short_file_bases(self):
    #     """Test generation of short file bases from a list of base names"""
    #     base_names = [s
    #         "cam1_%04d.tif",
    #         "img_cam2_%03d.tif",
    #         "exp_test_cam_01_frame_%04d.tif",
    #         "c5_%%d",
    #         "Cam12_extra",
    #         "c13",
    #     ]
    #     short_bases = generate_short_file_bases(base_names)
    #     assert len(short_bases) == len(base_names)
    #     for base, short in zip(base_names, short_bases):
    #         cam_id = extract_cam_id(base)
    #         assert short.startswith(f"cam{cam_id}"), f"Short base {short} does not start with cam{cam_id}"


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
