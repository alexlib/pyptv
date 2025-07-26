#!/usr/bin/env python3
"""
Logger demonstration script for PyPTV batch processing.

This script demonstrates various logging features and how they work
in practice with the improved pyptv_batch.py module.
"""

import logging
import time
from io import StringIO

# Configure logging similar to pyptv_batch.py
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def demonstrate_basic_logging():
    """Demonstrate basic logging levels and messages."""
    print("=== Basic Logging Demonstration ===")
    
    logger.debug("This is a DEBUG message (won't show with INFO level)")
    logger.info("This is an INFO message - normal operation")
    logger.warning("This is a WARNING message - something unexpected")
    logger.error("This is an ERROR message - something failed")
    logger.critical("This is a CRITICAL message - severe problem")
    
    print()


def demonstrate_formatted_logging():
    """Demonstrate formatted log messages."""
    print("=== Formatted Logging Demonstration ===")
    
    # Simulate some processing parameters
    exp_path = "/path/to/experiment"
    seq_first = 1000
    seq_last = 2000
    num_cams = 4
    
    # Using f-strings (recommended)
    logger.info(f"Starting batch processing in: {exp_path}")
    logger.info(f"Frame range: {seq_first} to {seq_last}")
    logger.info(f"Number of cameras: {num_cams}")
    
    # Simulating progress
    for i in range(3):
        logger.info(f"Processing repetition {i + 1} of 3")
        time.sleep(0.5)  # Simulate work
    
    # Performance reporting
    elapsed_time = 1.5
    logger.info(f"Total processing time: {elapsed_time:.2f} seconds")
    
    print()


def demonstrate_error_logging():
    """Demonstrate error handling with logging."""
    print("=== Error Handling with Logging ===")
    
    def risky_operation(should_fail=False):
        if should_fail:
            raise ValueError("Simulated processing error")
        return "Success"
    
    # Successful operation
    try:
        result = risky_operation(should_fail=False)
        logger.info(f"Operation completed successfully: {result}")
    except Exception as e:
        logger.error(f"Operation failed: {e}")
    
    # Failed operation
    try:
        result = risky_operation(should_fail=True)
        logger.info(f"Operation completed successfully: {result}")
    except ValueError as e:
        logger.error(f"Validation error occurred: {e}")
    except Exception as e:
        logger.critical(f"Unexpected error: {e}")
    
    print()


def demonstrate_conditional_logging():
    """Demonstrate conditional and debug logging."""
    print("=== Conditional Logging (requires DEBUG level) ===")
    
    # Temporarily change logging level to DEBUG
    original_level = logger.level
    logger.setLevel(logging.DEBUG)
    
    # Now debug messages will show
    logger.debug("This DEBUG message will now be visible")
    
    # Conditional logging to avoid expensive operations
    def expensive_operation():
        return "Expensive computation result"
    
    if logger.isEnabledFor(logging.DEBUG):
        debug_info = expensive_operation()
        logger.debug(f"Debug info: {debug_info}")
    
    # Restore original level
    logger.setLevel(original_level)
    logger.debug("This DEBUG message won't show (back to INFO level)")
    
    print()


def demonstrate_log_capture():
    """Demonstrate how to capture log output for testing."""
    print("=== Log Capture Demonstration (for testing) ===")
    
    # Create a string stream to capture logs
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
    
    # Add handler to capture output
    logger.addHandler(handler)
    
    # Generate some log messages
    logger.info("This message will be captured")
    logger.warning("This warning will also be captured")
    logger.error("This error will be captured too")
    
    # Get the captured output
    captured_output = log_stream.getvalue()
    print("Captured log output:")
    print(captured_output)
    
    # Verify specific content
    if "captured" in captured_output:
        print("✓ Successfully captured log messages")
    
    # Clean up
    logger.removeHandler(handler)
    handler.close()
    
    print()


def demonstrate_different_configurations():
    """Demonstrate different logging configurations."""
    print("=== Different Logging Configurations ===")
    
    # Save original configuration
    root_logger = logging.getLogger()
    original_handlers = root_logger.handlers[:]
    original_level = root_logger.level
    
    try:
        # Clear existing handlers
        for handler in root_logger.handlers:
            root_logger.removeHandler(handler)
        
        # Configuration 1: Minimal console output
        print("1. Minimal console output (WARNING and above):")
        logging.basicConfig(
            level=logging.WARNING,
            format='%(levelname)s: %(message)s',
            force=True
        )
        
        test_logger = logging.getLogger('test1')
        test_logger.info("This INFO won't show")
        test_logger.warning("This WARNING will show")
        test_logger.error("This ERROR will show")
        
        # Configuration 2: Detailed output with timestamps
        print("\n2. Detailed output with timestamps:")
        # Clear handlers again
        for handler in logging.getLogger().handlers:
            logging.getLogger().removeHandler(handler)
        
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s [%(levelname)8s] %(name)s: %(message)s',
            force=True
        )
        
        test_logger2 = logging.getLogger('test2')
        test_logger2.debug("Detailed debug message")
        test_logger2.info("Detailed info message")
        
    finally:
        # Restore original configuration
        for handler in logging.getLogger().handlers:
            logging.getLogger().removeHandler(handler)
        for handler in original_handlers:
            root_logger.addHandler(handler)
        root_logger.setLevel(original_level)
    
    print()


def simulate_pyptv_batch_logging():
    """Simulate the logging that would occur in pyptv_batch.py."""
    print("=== Simulated PyPTV Batch Processing Logs ===")
    
    # Simulate command line arguments
    fake_argv = ["pyptv_batch.py", "/path/to/experiment", "1000", "2000"]
    logger.info("Starting PyPTV batch processing")
    logger.info(f"Command line arguments: {fake_argv}")
    
    # Simulate directory validation
    logger.info("Validating experiment directory structure...")
    logger.info("✓ Found required directories: parameters, img, cal")
    logger.info("✓ Found ptv.par file")
    
    # Simulate main processing
    exp_path = "/path/to/experiment"
    seq_first, seq_last = 1000, 2000
    logger.info(f"Starting batch processing in directory: {exp_path}")
    logger.info(f"Frame range: {seq_first} to {seq_last}")
    logger.info("Repetitions: 1")
    
    # Simulate processing steps
    logger.info("Creating 'res' directory")
    logger.info("Starting batch processing: frames 1000 to 2000")
    logger.info("Number of cameras: 4")
    
    # Simulate processing time
    time.sleep(1)
    
    logger.info("Batch processing completed successfully")
    logger.info("Total processing time: 1.00 seconds")
    logger.info("Batch processing completed successfully")
    
    print()


if __name__ == "__main__":
    print("PyPTV Batch Logging Demonstration")
    print("=" * 50)
    print()
    
    # Run all demonstrations
    demonstrate_basic_logging()
    demonstrate_formatted_logging()
    demonstrate_error_logging()
    demonstrate_conditional_logging()
    demonstrate_log_capture()
    demonstrate_different_configurations()
    simulate_pyptv_batch_logging()
    
    print("Demonstration complete!")
    print("\nKey takeaways:")
    print("1. Use appropriate log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
    print("2. Include context in log messages")
    print("3. Use f-strings for formatting")
    print("4. Configure logging at the start of your application")
    print("5. Capture logs in tests to verify behavior")
