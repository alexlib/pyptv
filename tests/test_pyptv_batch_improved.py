"""
Test suite for the improved pyptv_batch.py module.

This test suite covers:
- Command line argument parsing
- Directory validation
- Error handling
- Main processing function
- Logging functionality
"""

import pytest
import tempfile
import shutil
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import logging
from io import StringIO

# Add the pyptv module to the path for testing
sys.path.insert(0, str(Path(__file__).parent.parent))

from pyptv.pyptv_batch import (
    main, 
    run_batch, 
    validate_experiment_directory,
    parse_command_line_args,
    ProcessingError,
    AttrDict,
    logger
)


class TestAttrDict:
    """Test the AttrDict utility class."""
    
    def test_attr_dict_creation(self):
        """Test that AttrDict can be created and accessed as attributes."""
        data = {"key1": "value1", "key2": 42}
        attr_dict = AttrDict(data)
        
        assert attr_dict.key1 == "value1"
        assert attr_dict.key2 == 42
        assert attr_dict["key1"] == "value1"
        assert attr_dict["key2"] == 42
    
    def test_attr_dict_modification(self):
        """Test that AttrDict can be modified via attributes and dict access."""
        attr_dict = AttrDict()
        attr_dict.new_key = "new_value"
        attr_dict["dict_key"] = "dict_value"
        
        assert attr_dict.new_key == "new_value"
        assert attr_dict["new_key"] == "new_value"
        assert attr_dict.dict_key == "dict_value"
        assert attr_dict["dict_key"] == "dict_value"


class TestDirectoryValidation:
    """Test directory validation functionality."""
    
    def setup_method(self):
        """Set up temporary directories for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.exp_path = Path(self.temp_dir) / "test_experiment"
        self.exp_path.mkdir()
    
    def teardown_method(self):
        """Clean up temporary directories."""
        shutil.rmtree(self.temp_dir)
    
    def test_validate_nonexistent_directory(self):
        """Test validation fails for non-existent directory."""
        non_existent = Path(self.temp_dir) / "does_not_exist"
        
        with pytest.raises(ProcessingError, match="does not exist"):
            validate_experiment_directory(non_existent)
    
    def test_validate_file_instead_of_directory(self):
        """Test validation fails when path points to a file."""
        file_path = Path(self.temp_dir) / "test_file.txt"
        file_path.write_text("test")
        
        with pytest.raises(ProcessingError, match="not a directory"):
            validate_experiment_directory(file_path)
    
    def test_validate_missing_required_directories(self):
        """Test validation fails when required subdirectories are missing."""
        with pytest.raises(ProcessingError, match="Missing required directories"):
            validate_experiment_directory(self.exp_path)
    
    def test_validate_missing_ptv_par_file(self):
        """Test validation fails when ptv.par file is missing."""
        # Create required directories
        for dirname in ["parameters", "img", "cal"]:
            (self.exp_path / dirname).mkdir()
        
        with pytest.raises(ProcessingError, match="Required file not found"):
            validate_experiment_directory(self.exp_path)
    
    def test_validate_successful(self):
        """Test successful validation with all required structure."""
        # Create required directories
        for dirname in ["parameters", "img", "cal", "res"]:
            (self.exp_path / dirname).mkdir()
        
        # Create ptv.par file
        ptv_par = self.exp_path / "parameters" / "ptv.par"
        ptv_par.write_text("4\n")  # 4 cameras
        
        # Should not raise any exception
        validate_experiment_directory(self.exp_path)


class TestCommandLineArgsParsing:
    """Test command line arguments parsing."""
    
    def setup_method(self):
        """Set up test environment."""
        self.original_argv = sys.argv.copy()
    
    def teardown_method(self):
        """Restore original argv."""
        sys.argv = self.original_argv
    
    def test_insufficient_arguments_with_existing_test_dir(self):
        """Test fallback to default values when insufficient args and test dir exists."""
        sys.argv = ["pyptv_batch.py"]
        
        # Mock the test directory to exist
        with patch('pyptv.pyptv_batch.Path') as mock_path:
            mock_path.return_value.resolve.return_value.exists.return_value = True
            mock_path.return_value.resolve.return_value = Path("/mock/test/path")
            
            exp_path, first, last = parse_command_line_args()
            
            assert first == 10000
            assert last == 10004
    
    def test_insufficient_arguments_without_test_dir(self):
        """Test error when insufficient args and test dir doesn't exist."""
        sys.argv = ["pyptv_batch.py"]
        
        # Mock the test directory to not exist
        with patch('pyptv.pyptv_batch.Path') as mock_path:
            mock_path.return_value.resolve.return_value.exists.return_value = False
            
            with pytest.raises(ValueError, match="Default test directory not found"):
                parse_command_line_args()
    
    def test_valid_arguments(self):
        """Test parsing valid command line arguments."""
        sys.argv = ["pyptv_batch.py", "/test/path", "1000", "2000"]
        
        with patch('pyptv.pyptv_batch.Path') as mock_path:
            mock_path.return_value.resolve.return_value = Path("/test/path")
            
            exp_path, first, last = parse_command_line_args()
            
            assert str(exp_path) == "/test/path"
            assert first == 1000
            assert last == 2000
    
    def test_invalid_frame_numbers(self):
        """Test error handling for invalid frame numbers."""
        sys.argv = ["pyptv_batch.py", "/test/path", "invalid", "2000"]
        
        with pytest.raises(ValueError, match="Invalid command line arguments"):
            parse_command_line_args()


class TestRunBatch:
    """Test the run_batch function."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.exp_path = Path(self.temp_dir) / "test_experiment"
        self.exp_path.mkdir()
        
        # Create required directory structure
        for dirname in ["parameters", "img", "cal", "res"]:
            (self.exp_path / dirname).mkdir()
        
        # Create ptv.par file
        ptv_par = self.exp_path / "parameters" / "ptv.par"
        ptv_par.write_text("4\n")
    
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    @patch('pyptv.pyptv_batch.py_start_proc_c')
    @patch('pyptv.pyptv_batch.py_sequence_loop')
    @patch('pyptv.pyptv_batch.py_trackcorr_init')
    def test_run_batch_successful(self, mock_trackcorr, mock_sequence, mock_start_proc):
        """Test successful batch processing."""
        # Mock the PyPTV functions
        mock_spar = MagicMock()
        mock_tracker = MagicMock()
        
        mock_start_proc.return_value = (
            "cpar", mock_spar, "vpar", "track_par", "tpar", "cals", "epar"
        )
        mock_trackcorr.return_value = mock_tracker
        
        # Should not raise any exception
        run_batch(1000, 2000, self.exp_path)
        
        # Verify that the PyPTV functions were called
        mock_start_proc.assert_called_once_with(n_cams=4)
        mock_spar.set_first.assert_called_once_with(1000)
        mock_spar.set_last.assert_called_once_with(2000)
        mock_sequence.assert_called_once()
        mock_trackcorr.assert_called_once()
        mock_tracker.full_forward.assert_called_once()
    
    def test_run_batch_invalid_ptv_par(self):
        """Test error handling when ptv.par file is invalid."""
        # Write invalid content to ptv.par
        ptv_par = self.exp_path / "parameters" / "ptv.par"
        ptv_par.write_text("invalid_number\n")
        
        with pytest.raises(ProcessingError, match="Error reading camera count"):
            run_batch(1000, 2000, self.exp_path)
    
    @patch('pyptv.pyptv_batch.py_start_proc_c')
    def test_run_batch_processing_error(self, mock_start_proc):
        """Test error handling when PyPTV processing fails."""
        mock_start_proc.side_effect = Exception("PyPTV processing failed")
        
        with pytest.raises(ProcessingError, match="Batch processing failed"):
            run_batch(1000, 2000, self.exp_path)


class TestMainFunction:
    """Test the main processing function."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.exp_path = Path(self.temp_dir) / "test_experiment"
        self.exp_path.mkdir()
        
        # Create required directory structure
        for dirname in ["parameters", "img", "cal"]:
            (self.exp_path / dirname).mkdir()
        
        # Create ptv.par file
        ptv_par = self.exp_path / "parameters" / "ptv.par"
        ptv_par.write_text("4\n")
    
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_main_invalid_frame_range(self):
        """Test error handling for invalid frame range."""
        with pytest.raises(ValueError, match="must be <= last frame"):
            main(self.exp_path, 2000, 1000)
    
    def test_main_invalid_repetitions(self):
        """Test error handling for invalid repetitions."""
        with pytest.raises(ValueError, match="must be >= 1"):
            main(self.exp_path, 1000, 2000, repetitions=0)
    
    @patch('pyptv.pyptv_batch.run_batch')
    def test_main_successful_single_run(self, mock_run_batch):
        """Test successful single run."""
        main(self.exp_path, 1000, 2000)
        
        mock_run_batch.assert_called_once_with(1000, 2000, self.exp_path)
        
        # Check that res directory was created
        assert (self.exp_path / "res").exists()
    
    @patch('pyptv.pyptv_batch.run_batch')
    def test_main_successful_multiple_runs(self, mock_run_batch):
        """Test successful multiple runs."""
        main(self.exp_path, 1000, 2000, repetitions=3)
        
        assert mock_run_batch.call_count == 3
        for call in mock_run_batch.call_args_list:
            args, kwargs = call
            assert args == (1000, 2000, self.exp_path)


class TestLoggingFunctionality:
    """Test logging functionality and demonstrate logger usage."""
    
    def setup_method(self):
        """Set up logging test environment."""
        # Create a string stream to capture log output
        self.log_stream = StringIO()
        self.log_handler = logging.StreamHandler(self.log_stream)
        self.log_handler.setLevel(logging.DEBUG)
        
        # Add handler to the pyptv_batch logger
        logger.addHandler(self.log_handler)
        logger.setLevel(logging.DEBUG)
    
    def teardown_method(self):
        """Clean up logging test environment."""
        logger.removeHandler(self.log_handler)
        self.log_handler.close()
    
    def test_logger_info_messages(self):
        """Test that info messages are logged correctly."""
        logger.info("Test info message")
        
        log_output = self.log_stream.getvalue()
        assert "Test info message" in log_output
        # The exact format may vary, so just check that message was captured
        assert len(log_output.strip()) > 0
    
    def test_logger_error_messages(self):
        """Test that error messages are logged correctly."""
        logger.error("Test error message")
        
        log_output = self.log_stream.getvalue()
        assert "Test error message" in log_output
        assert len(log_output.strip()) > 0
    
    def test_logger_warning_messages(self):
        """Test that warning messages are logged correctly."""
        logger.warning("Test warning message")
        
        log_output = self.log_stream.getvalue()
        assert "Test warning message" in log_output
        assert len(log_output.strip()) > 0
    
    @patch('pyptv.pyptv_batch.validate_experiment_directory')
    @patch('pyptv.pyptv_batch.run_batch')
    def test_main_function_logging(self, mock_run_batch, mock_validate):
        """Test that main function produces expected log messages."""
        temp_dir = tempfile.mkdtemp()
        exp_path = Path(temp_dir)
        
        try:
            main(exp_path, 1000, 2000)
            
            log_output = self.log_stream.getvalue()
            
            # Check for expected log messages
            assert "Starting batch processing in directory" in log_output
            assert "Frame range: 1000 to 2000" in log_output
            assert "Repetitions: 1" in log_output
            assert "Total processing time" in log_output
            
        finally:
            shutil.rmtree(temp_dir)


# Integration test
class TestPyPTVBatchIntegration:
    """Integration tests for the complete workflow."""
    
    def setup_method(self):
        """Set up integration test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.exp_path = Path(self.temp_dir) / "integration_test"
        self.exp_path.mkdir()
        
        # Create complete directory structure
        for dirname in ["parameters", "img", "cal", "res"]:
            (self.exp_path / dirname).mkdir()
        
        # Create ptv.par file
        ptv_par = self.exp_path / "parameters" / "ptv.par"
        ptv_par.write_text("2\n")  # 2 cameras for test
    
    def teardown_method(self):
        """Clean up integration test environment."""
        shutil.rmtree(self.temp_dir)
    
    @patch('pyptv.pyptv_batch.py_start_proc_c')
    @patch('pyptv.pyptv_batch.py_sequence_loop')
    @patch('pyptv.pyptv_batch.py_trackcorr_init')
    def test_complete_workflow(self, mock_trackcorr, mock_sequence, mock_start_proc):
        """Test the complete workflow from directory validation to processing."""
        # Mock PyPTV functions
        mock_spar = MagicMock()
        mock_tracker = MagicMock()
        
        mock_start_proc.return_value = (
            "cpar", mock_spar, "vpar", "track_par", "tpar", "cals", "epar"
        )
        mock_trackcorr.return_value = mock_tracker
        
        # Run the complete workflow
        main(str(self.exp_path), "1000", "1005", repetitions=2)
        
        # Verify all components were called correctly
        assert mock_start_proc.call_count == 2  # Called for each repetition
        assert mock_sequence.call_count == 2
        assert mock_trackcorr.call_count == 2
        assert mock_tracker.full_forward.call_count == 2


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
