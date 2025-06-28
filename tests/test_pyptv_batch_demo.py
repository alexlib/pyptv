#!/usr/bin/env python3
"""
Simple test script to demonstrate using the improved pyptv_batch.py 
with proper logging in the pyptv conda environment.

This script shows how to:
1. Use the improved pyptv_batch module
2. Handle logging output  
3. Work with the pyptv conda environment
4. Test basic functionality
"""

import sys
import tempfile
import shutil
from pathlib import Path
import logging

# Import our improved pyptv_batch components
from pyptv.pyptv_batch import (
    validate_experiment_directory, 
    ProcessingError,
    AttrDict,
    logger
)

def create_test_experiment_directory():
    """Create a temporary test experiment directory with required structure."""
    temp_dir = tempfile.mkdtemp()
    exp_path = Path(temp_dir) / "test_experiment"
    exp_path.mkdir()
    
    # Create required directories
    for dirname in ["parameters", "img", "cal", "res"]:
        (exp_path / dirname).mkdir()
    
    # Create ptv.par file with camera count
    ptv_par = exp_path / "parameters" / "ptv.par"
    ptv_par.write_text("2\n")  # 2 cameras for test
    
    logger.info(f"Created test experiment directory: {exp_path}")
    return exp_path, temp_dir

def test_directory_validation():
    """Test the directory validation functionality."""
    logger.info("=== Testing Directory Validation ===")
    
    exp_path, temp_dir = create_test_experiment_directory()
    
    try:
        # This should succeed
        validate_experiment_directory(exp_path)
        logger.info("✓ Directory validation passed")
        
        # Test with missing directory
        missing_dir = Path(temp_dir) / "nonexistent"
        try:
            validate_experiment_directory(missing_dir)
            logger.error("✗ Should have failed for missing directory")
        except ProcessingError as e:
            logger.info(f"✓ Correctly caught missing directory error: {e}")
            
    finally:
        shutil.rmtree(temp_dir)

def test_attr_dict():
    """Test the AttrDict utility class."""
    logger.info("=== Testing AttrDict ===")
    
    # Test creation and access
    data = {"camera_count": 4, "frame_range": [1000, 2000]}
    config = AttrDict(data)
    
    # Test attribute access
    logger.info(f"Camera count: {config.camera_count}")
    logger.info(f"Frame range: {config.frame_range}")
    
    # Test dictionary access
    assert config["camera_count"] == 4
    assert config.camera_count == 4
    
    # Test modification
    config.new_parameter = "test_value"
    assert config["new_parameter"] == "test_value"
    
    logger.info("✓ AttrDict functionality verified")

def test_logging_levels():
    """Demonstrate different logging levels."""
    logger.info("=== Testing Different Logging Levels ===")
    
    # Save original level
    original_level = logger.level
    
    try:
        # Test with INFO level (default)
        logger.info("This INFO message should appear")
        logger.debug("This DEBUG message should NOT appear (level too low)")
        
        # Change to DEBUG level
        logger.setLevel(logging.DEBUG)
        logger.info("Changed to DEBUG level")
        logger.debug("This DEBUG message should now appear")
        
        # Test warning and error
        logger.warning("This is a WARNING message")
        logger.error("This is an ERROR message (simulated)")
        
    finally:
        # Restore original level
        logger.setLevel(original_level)
        logger.info("Restored original logging level")

def simulate_batch_processing():
    """Simulate the batch processing workflow with mocked PyPTV functions."""
    logger.info("=== Simulating Batch Processing Workflow ===")
    
    exp_path, temp_dir = create_test_experiment_directory()
    
    try:
        logger.info("Starting simulated batch processing...")
        
        # Validate directory (should succeed)
        validate_experiment_directory(exp_path)
        logger.info("✓ Directory validation completed")
        
        # Simulate parameter parsing
        seq_first, seq_last = 1000, 1005
        logger.info(f"Frame range: {seq_first} to {seq_last}")
        
        # Note: We can't actually run the full main() function without 
        # the PyPTV dependencies, but we can test the directory setup
        res_path = exp_path / "res"
        if not res_path.exists():
            logger.info("Creating 'res' directory")
            res_path.mkdir(parents=True, exist_ok=True)
        
        logger.info("✓ Simulated processing setup completed")
        
    except Exception as e:
        logger.error(f"Simulation failed: {e}")
    finally:
        shutil.rmtree(temp_dir)

def main_test():
    """Run all tests and demonstrations."""
    logger.info("Starting PyPTV Batch Testing and Logger Demonstration")
    logger.info("=" * 60)
    
    # Test basic functionality
    test_attr_dict()
    test_directory_validation()
    test_logging_levels()
    simulate_batch_processing()
    
    logger.info("=" * 60)
    logger.info("All tests completed successfully!")
    
    # Show environment information
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Running from: {sys.executable}")

if __name__ == "__main__":
    # Configure logging to show all messages
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    try:
        main_test()
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        sys.exit(1)
