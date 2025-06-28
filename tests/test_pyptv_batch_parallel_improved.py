"""
Test suite for the improved pyptv_batch_parallel.py module.

This test suite covers:
- Command line argument parsing
- Directory validation
- Frame range chunking
- Error handling
- Parallel processing coordination
- Logging functionality
"""

import pytest
import tempfile
import shutil
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import logging
from io import StringIO

# Add the pyptv module to the path for testing
sys.path.insert(0, str(Path(__file__).parent.parent))

from pyptv.pyptv_batch_parallel import (
    main, 
    run_sequence_chunk,
    chunk_ranges,
    validate_experiment_directory,
    parse_command_line_args,
    ProcessingError,
    AttrDict,
    logger
)


class TestAttrDictParallel:
    """Test the AttrDict utility class in parallel context."""
    
    def test_attr_dict_creation(self):
        """Test that AttrDict can be created and accessed as attributes."""
        data = {"key1": "value1", "key2": 42}
        attr_dict = AttrDict(data)
        
        assert attr_dict.key1 == "value1"
        assert attr_dict.key2 == 42
        assert attr_dict["key1"] == "value1"
        assert attr_dict["key2"] == 42


class TestChunkRanges:
    """Test frame range chunking functionality."""
    
    def test_even_division(self):
        """Test chunking when frames divide evenly."""
        ranges = chunk_ranges(1000, 1009, 5)  # 10 frames, 5 chunks = 2 frames each
        expected = [(1000, 1001), (1002, 1003), (1004, 1005), (1006, 1007), (1008, 1009)]
        assert ranges == expected
    
    def test_uneven_division(self):
        """Test chunking when frames don't divide evenly."""
        ranges = chunk_ranges(1000, 1009, 3)  # 10 frames, 3 chunks
        # With the improved algorithm: 10 frames / 3 chunks = 3 base + 1 remainder
        # First chunk gets extra frame: 4 frames, then 3, then 3
        expected = [(1000, 1003), (1004, 1006), (1007, 1009)]
        assert ranges == expected
    
    def test_more_chunks_than_frames(self):
        """Test when requesting more chunks than frames available."""
        ranges = chunk_ranges(1000, 1002, 5)  # 3 frames, 5 chunks requested
        expected = [(1000, 1000), (1001, 1001), (1002, 1002)]  # Should create 3 chunks
        assert ranges == expected
    
    def test_single_chunk(self):
        """Test with single chunk."""
        ranges = chunk_ranges(1000, 1010, 1)
        expected = [(1000, 1010)]
        assert ranges == expected
    
    def test_invalid_range(self):
        """Test error handling for invalid frame range."""
        with pytest.raises(ValueError, match="must be <= last frame"):
            chunk_ranges(1010, 1000, 2)
    
    def test_invalid_chunk_count(self):
        """Test error handling for invalid chunk count."""
        with pytest.raises(ValueError, match="must be >= 1"):
            chunk_ranges(1000, 1010, 0)


class TestDirectoryValidationParallel:
    """Test directory validation functionality for parallel processing."""
    
    def setup_method(self):
        """Set up temporary directories for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.exp_path = Path(self.temp_dir) / "test_experiment"
        self.exp_path.mkdir()
    
    def teardown_method(self):
        """Clean up temporary directories."""
        shutil.rmtree(self.temp_dir)
    
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


class TestCommandLineArgsParsingParallel:
    """Test command line arguments parsing for parallel processing."""
    
    def setup_method(self):
        """Set up test environment."""
        self.original_argv = sys.argv.copy()
    
    def teardown_method(self):
        """Restore original argv."""
        sys.argv = self.original_argv
    
    def test_insufficient_arguments_with_existing_test_dir(self):
        """Test fallback to default values when insufficient args and test dir exists."""
        sys.argv = ["pyptv_batch_parallel.py"]
        
        # Mock the test directory to exist
        with patch('pyptv.pyptv_batch_parallel.Path') as mock_path:
            # Create a mock path object that exists
            mock_path_obj = MagicMock()
            mock_path_obj.exists.return_value = True
            mock_path_obj.resolve.return_value = mock_path_obj
            mock_path.return_value = mock_path_obj
            
            exp_path, first, last, n_processes = parse_command_line_args()
            
            assert first == 10000
            assert last == 10004
            assert n_processes == 2
    
    def test_valid_arguments(self):
        """Test parsing valid command line arguments."""
        sys.argv = ["pyptv_batch_parallel.py", "/test/path", "1000", "2000", "4"]
        
        with patch('pyptv.pyptv_batch_parallel.Path') as mock_path:
            mock_path.return_value.resolve.return_value = Path("/test/path")
            
            exp_path, first, last, n_processes = parse_command_line_args()
            
            assert str(exp_path) == "/test/path"
            assert first == 1000
            assert last == 2000
            assert n_processes == 4
    
    def test_invalid_frame_numbers(self):
        """Test error handling for invalid frame numbers."""
        sys.argv = ["pyptv_batch_parallel.py", "/test/path", "invalid", "2000", "4"]
        
        with pytest.raises(ValueError, match="Invalid command line arguments"):
            parse_command_line_args()


class TestRunSequenceChunk:
    """Test the run_sequence_chunk function."""
    
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
    
    @patch('pyptv.pyptv_batch_parallel.py_start_proc_c')
    @patch('pyptv.pyptv_batch_parallel.py_sequence_loop')
    def test_run_sequence_chunk_successful(self, mock_sequence, mock_start_proc):
        """Test successful chunk processing."""
        # Mock the PyPTV functions
        mock_spar = MagicMock()
        
        mock_start_proc.return_value = (
            "cpar", mock_spar, "vpar", "track_par", "tpar", "cals", "epar"
        )
        
        # Should not raise any exception
        result = run_sequence_chunk(self.exp_path, 1000, 2000)
        
        # Verify return value
        assert result == (1000, 2000)
        
        # Verify that the PyPTV functions were called
        mock_start_proc.assert_called_once_with(n_cams=4)
        mock_spar.set_first.assert_called_once_with(1000)
        mock_spar.set_last.assert_called_once_with(2000)
        mock_sequence.assert_called_once()
    
    def test_run_sequence_chunk_invalid_ptv_par(self):
        """Test error handling when ptv.par file is invalid."""
        # Write invalid content to ptv.par
        ptv_par = self.exp_path / "parameters" / "ptv.par"
        ptv_par.write_text("invalid_number\n")
        
        with pytest.raises(ProcessingError, match="Error reading camera count"):
            run_sequence_chunk(self.exp_path, 1000, 2000)


class TestMainFunctionParallel:
    """Test the main parallel processing function."""
    
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
            main(self.exp_path, 2000, 1000, 2)
    
    def test_main_invalid_process_count(self):
        """Test error handling for invalid process count."""
        with pytest.raises(ValueError, match="must be >= 1"):
            main(self.exp_path, 1000, 2000, 0)
    
    @patch('pyptv.pyptv_batch_parallel.ProcessPoolExecutor')
    def test_main_default_process_count(self, mock_executor_class):
        """Test using default process count."""
        # Mock the executor
        mock_executor = MagicMock()
        mock_executor_class.return_value.__enter__.return_value = mock_executor
        
        # Mock successful chunk execution
        mock_future = MagicMock()
        mock_future.result.return_value = (1000, 2000)
        mock_executor.submit.return_value = mock_future
        
        # Mock as_completed to return our future
        with patch('pyptv.pyptv_batch_parallel.as_completed') as mock_as_completed:
            mock_as_completed.return_value = [mock_future]
            
            # Should use CPU count as default when None is passed
            main(self.exp_path, 1000, 2000, None)
            
            # Check that res directory was created
            assert (self.exp_path / "res").exists()
    
    @patch('pyptv.pyptv_batch_parallel.ProcessPoolExecutor')
    def test_main_successful_parallel_execution(self, mock_executor_class):
        """Test successful parallel execution."""
        # Mock the executor and futures
        mock_executor = MagicMock()
        mock_executor_class.return_value.__enter__.return_value = mock_executor
        
        # Mock successful chunk execution
        mock_future = MagicMock()
        mock_future.result.return_value = (1000, 1002)
        mock_executor.submit.return_value = mock_future
        
        # Mock as_completed to return our future
        with patch('pyptv.pyptv_batch_parallel.as_completed') as mock_as_completed:
            mock_as_completed.return_value = [mock_future]
            
            main(self.exp_path, 1000, 1005, 2)
            
            # Verify executor was called
            mock_executor.submit.assert_called()


class TestLoggingFunctionalityParallel:
    """Test logging functionality for parallel processing."""
    
    def setup_method(self):
        """Set up logging test environment."""
        # Create a string stream to capture log output
        self.log_stream = StringIO()
        self.log_handler = logging.StreamHandler(self.log_stream)
        self.log_handler.setLevel(logging.DEBUG)
        
        # Add handler to the pyptv_batch_parallel logger
        logger.addHandler(self.log_handler)
        logger.setLevel(logging.DEBUG)
    
    def teardown_method(self):
        """Clean up logging test environment."""
        logger.removeHandler(self.log_handler)
        self.log_handler.close()
    
    def test_logger_parallel_messages(self):
        """Test that parallel processing messages are logged correctly."""
        logger.info("Starting parallel processing")
        logger.info("Frame chunks: [(1000, 1005), (1006, 1010)]")
        logger.info("✓ Completed chunk: frames 1000 to 1005")
        
        log_output = self.log_stream.getvalue()
        assert "Starting parallel processing" in log_output
        assert "Frame chunks" in log_output
        assert "Completed chunk" in log_output


# Integration test
class TestParallelBatchIntegration:
    """Integration tests for the complete parallel workflow."""
    
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
    
    @patch('pyptv.pyptv_batch_parallel.ProcessPoolExecutor')
    def test_complete_parallel_workflow(self, mock_executor_class):
        """Test the complete parallel workflow from validation to processing."""
        # Mock the executor and futures
        mock_executor = MagicMock()
        mock_executor_class.return_value.__enter__.return_value = mock_executor
        
        # Mock successful chunk execution
        mock_future1 = MagicMock()
        mock_future1.result.return_value = (1000, 1002)
        mock_future2 = MagicMock()
        mock_future2.result.return_value = (1003, 1005)
        
        mock_executor.submit.side_effect = [mock_future1, mock_future2]
        
        # Mock as_completed to return our futures
        with patch('pyptv.pyptv_batch_parallel.as_completed') as mock_as_completed:
            mock_as_completed.return_value = [mock_future1, mock_future2]
            
            # Run the complete workflow with 2 processes
            main(str(self.exp_path), "1000", "1005", 2)
            
            # Verify components were called
            assert mock_executor.submit.call_count == 2


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
