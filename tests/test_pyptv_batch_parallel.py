import pytest
from pathlib import Path
from pyptv import pyptv_batch_parallel


def test_pyptv_batch_parallel(test_data_dir):
    """Test parallel batch processing with test cavity data using YAML parameters"""
    test_dir = test_data_dir
    assert test_dir.exists(), f"Test directory {test_dir} not found"

    # Path to YAML parameter file
    yaml_file = test_dir / "parameters_Run1.yaml"
    assert yaml_file.exists(), f"YAML parameter file {yaml_file} not found"

    # Test specific frame range
    start_frame = 10000
    end_frame = 10004  # Use fewer frames for parallel test (faster)
    n_processes = 4

    try:
        # Only 'both' and 'sequence' modes are valid for parallel batch; 'tracking' is serial only
        pyptv_batch_parallel.main(yaml_file, start_frame, end_frame, n_processes, mode="both")
        pyptv_batch_parallel.main(yaml_file, start_frame, end_frame, n_processes, mode="sequence")
    except Exception as e:
        pytest.fail(f"Parallel batch processing failed: {str(e)}")


def test_pyptv_batch_parallel_validation_errors():
    """Test that proper validation errors are raised for parallel processing"""
    from pyptv.pyptv_batch_parallel import ProcessingError
    
    # Test non-existent YAML file
    with pytest.raises(ProcessingError, match="YAML parameter file does not exist"):
        pyptv_batch_parallel.main("nonexistent.yaml", 1, 2, 2)
    
    # Test invalid frame range
    with pytest.raises(ValueError, match="First frame .* must be <= last frame"):
        pyptv_batch_parallel.main("any.yaml", 10, 5, 2)  # first > last
    
    # Test invalid number of processes
    with pytest.raises(ValueError, match="Number of processes must be >= 1"):
        pyptv_batch_parallel.main("any.yaml", 1, 2, 0)  # n_processes = 0


def test_pyptv_batch_parallel_single_process(test_data_dir):
    """Test parallel processing with single process (should work like regular batch)"""
    test_dir = test_data_dir
    yaml_file = test_dir / "parameters_Run1.yaml"
    
    # Test with single process
    start_frame = 10000
    end_frame = 10004  # Just one frame
    n_processes = 1

    try:
        pyptv_batch_parallel.main(yaml_file, start_frame, end_frame, n_processes)
    except Exception as e:
        pytest.fail(f"Single process parallel batch processing failed: {str(e)}")


if __name__ == "__main__":
    pytest.main([__file__])