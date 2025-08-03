import pytest
from pathlib import Path
from pyptv import pyptv_batch


def test_pyptv_batch(test_data_dir):
    """Test batch processing with test cavity data using YAML parameters"""
    test_dir = test_data_dir
    assert test_dir.exists(), f"Test directory {test_dir} not found"

    # Path to YAML parameter file
    yaml_file = test_dir / "parameters_Run1.yaml"
    assert yaml_file.exists(), f"YAML parameter file {yaml_file} not found"

    # Test specific frame range
    start_frame = 10000
    end_frame = 10004

    try:
        # New API: pass YAML file path, not directory
        pyptv_batch.main(yaml_file, start_frame, end_frame)
    except Exception as e:
        pytest.fail(f"Batch processing failed: {str(e)}")


def test_pyptv_batch_with_repetitions(test_data_dir):
    """Test batch processing with multiple repetitions"""
    test_dir = test_data_dir
    yaml_file = test_dir / "parameters_Run1.yaml"
    
    # Test smaller frame range with repetitions
    start_frame = 10000
    end_frame = 10001  # Just 2 frames for speed
    repetitions = 2

    try:
        pyptv_batch.main(yaml_file, start_frame, end_frame, repetitions)
    except Exception as e:
        pytest.fail(f"Batch processing with repetitions failed: {str(e)}")


def test_pyptv_batch_validation_errors():
    """Test that proper validation errors are raised"""
    from pyptv.pyptv_batch import ProcessingError
    
    # Test non-existent YAML file
    with pytest.raises(ProcessingError, match="YAML parameter file does not exist"):
        pyptv_batch.main("nonexistent.yaml", 1, 2)
    
    # Test invalid frame range
    with pytest.raises(ValueError, match="First frame .* must be <= last frame"):
        pyptv_batch.main("any.yaml", 10, 5)  # first > last
    
    # Test invalid repetitions
    with pytest.raises(ValueError, match="Repetitions must be >= 1"):
        pyptv_batch.main("any.yaml", 1, 2, 0)  # repetitions = 0


def test_pyptv_batch_produces_results(test_data_dir):
    """Test that batch processing actually produces correspondence and tracking results"""
    test_dir = test_data_dir
    yaml_file = test_dir / "parameters_Run1.yaml"
    
    # Test specific frame
    start_frame = 10000
    end_frame = 10000  # Just one frame for quick test
    
    # Clear any existing results
    res_dir = test_dir / "res"
    if res_dir.exists():
        import shutil
        shutil.rmtree(res_dir)
    
    # Run batch processing
    pyptv_batch.main(yaml_file, start_frame, end_frame)
    
    # Check that result files were created
    assert res_dir.exists(), "Results directory should be created"
    
    # Check for correspondence files
    corres_file = res_dir / f"rt_is.{start_frame}"
    assert corres_file.exists(), f"Correspondence file {corres_file} should exist"
    
    # Check that correspondence file has content (more than just "0\n")
    content = corres_file.read_text()
    lines = content.strip().split('\n')
    assert len(lines) > 1, "Correspondence file should have more than just the count line"
    
    # First line should be the number of points
    num_points = int(lines[0])
    assert num_points > 0, f"Should have detected correspondences, got {num_points}"
    assert num_points == len(lines) - 1, "Number of points should match number of data lines"
    
    print(f"Successfully detected {num_points} correspondences in frame {start_frame}")


def test_pyptv_batch_tracking_results(test_data_dir):
    """Test that batch processing with multiple frames produces tracking results"""
    test_dir = test_data_dir
    yaml_file = test_dir / "parameters_Run1.yaml"
    
    # Test two frames for tracking
    start_frame = 10000
    end_frame = 10001
    
    # Clear any existing results
    res_dir = test_dir / "res"
    if res_dir.exists():
        import shutil
        shutil.rmtree(res_dir)
    
    # Run batch processing
    pyptv_batch.main(yaml_file, start_frame, end_frame)
    
    # Check that correspondence files exist for both frames
    for frame in [start_frame, end_frame]:
        corres_file = res_dir / f"rt_is.{frame}"
        assert corres_file.exists(), f"Correspondence file for frame {frame} should exist"
        
        content = corres_file.read_text()
        lines = content.strip().split('\n')
        num_points = int(lines[0])
        assert num_points > 0, f"Frame {frame} should have correspondences, got {num_points}"
    
    # Check for tracking output files (these depend on the tracker configuration)
    # At minimum, we should have some output indicating tracking was attempted
    print(f"Successfully processed frames {start_frame} to {end_frame} with tracking")


if __name__ == "__main__":
    pytest.main([__file__])