# Python Logging Guide for PyPTV Batch Processing

## Overview
The improved `pyptv_batch.py` uses Python's built-in `logging` module instead of simple `print()` statements. This provides better control over output, formatting, and the ability to direct logs to different destinations.

## Logger Configuration in pyptv_batch.py

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
```

### What this configuration does:
- **level=logging.INFO**: Sets the minimum level of messages to display
- **format**: Defines how log messages appear (timestamp - level - message)
- **logger = logging.getLogger(__name__)**: Creates a logger specific to this module

## Logging Levels (from least to most severe)

1. **DEBUG**: Detailed information for diagnosing problems
2. **INFO**: General information about program execution
3. **WARNING**: Something unexpected happened, but the program continues
4. **ERROR**: A serious problem occurred, some functionality failed
5. **CRITICAL**: A severe error occurred, program may not continue

## How to Use the Logger

### Basic Usage Examples

```python
# Information messages (normal operation)
logger.info("Starting batch processing")
logger.info(f"Processing frames {seq_first} to {seq_last}")

# Warning messages (unexpected but not critical)
logger.warning("Insufficient command line arguments, using defaults")

# Error messages (something went wrong)
logger.error("Processing failed: invalid directory structure")

# Debug messages (detailed diagnostic info)
logger.debug(f"Camera count read from file: {n_cams}")

# Critical messages (severe problems)
logger.critical("System resources exhausted, cannot continue")
```

### Formatted Log Messages

```python
# Using f-strings (recommended)
logger.info(f"Processing {count} files in {directory}")

# Using .format() method
logger.info("Processing {} files in {}".format(count, directory))

# Using % formatting (older style)
logger.info("Processing %d files in %s", count, directory)
```

### Logging in Exception Handling

```python
try:
    risky_operation()
except SpecificError as e:
    logger.error(f"Specific error occurred: {e}")
    # Continue or handle gracefully
except Exception as e:
    logger.critical(f"Unexpected error: {e}")
    raise  # Re-raise if critical
```

## Advanced Logger Configuration

### 1. Different Log Levels for Different Environments

```python
# For development - show all messages
logging.basicConfig(level=logging.DEBUG)

# For production - show only important messages  
logging.basicConfig(level=logging.WARNING)

# For verbose operation - show info and above
logging.basicConfig(level=logging.INFO)
```

### 2. Multiple Output Destinations

```python
import logging
from pathlib import Path

# Create logger
logger = logging.getLogger('pyptv_batch')
logger.setLevel(logging.DEBUG)

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Create file handler
log_file = Path('pyptv_batch.log')
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.DEBUG)

# Create formatters
console_format = logging.Formatter('%(levelname)s - %(message)s')
file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Add formatters to handlers
console_handler.setFormatter(console_format)
file_handler.setFormatter(file_format)

# Add handlers to logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)
```

### 3. Conditional Logging

```python
# Only log in debug mode
if logger.isEnabledFor(logging.DEBUG):
    expensive_debug_info = compute_expensive_operation()
    logger.debug(f"Debug info: {expensive_debug_info}")

# Using lazy evaluation with lambda
logger.debug("Expensive operation result: %s", 
             lambda: expensive_operation())
```

## Logger Usage in pyptv_batch.py

### Examples from the improved code:

```python
# Startup information
logger.info("Starting PyPTV batch processing")
logger.info(f"Command line arguments: {sys.argv}")

# Progress tracking
logger.info(f"Starting batch processing in directory: {exp_path}")
logger.info(f"Frame range: {seq_first} to {seq_last}")
logger.info(f"Number of cameras: {n_cams}")

# Directory operations
logger.info("Creating 'res' directory")

# Repetition tracking
if repetitions > 1:
    logger.info(f"Starting repetition {i + 1} of {repetitions}")

# Success confirmation
logger.info("Batch processing completed successfully")

# Performance information
logger.info(f"Total processing time: {elapsed_time:.2f} seconds")

# Warnings for unexpected situations
logger.warning("Insufficient command line arguments, using default test values")

# Error reporting
logger.error(f"Processing failed: {e}")
logger.error(f"Batch processing failed: {e}")
```

## Benefits Over Print Statements

### 1. **Flexible Output Control**
```python
# Easy to disable all debug messages in production
logging.getLogger().setLevel(logging.INFO)

# vs print statements that would need to be commented out
# print("Debug info")  # Would need manual removal
```

### 2. **Consistent Formatting**
```python
# All log messages have consistent timestamps and levels
# 2024-01-15 10:30:45,123 - INFO - Starting processing
# 2024-01-15 10:30:45,234 - ERROR - Processing failed

# vs inconsistent print output
# Starting processing
# ERROR: Processing failed
```

### 3. **Multiple Destinations**
```python
# Can simultaneously log to console, file, email, etc.
logger.info("Important message")  # Goes to all configured handlers

# vs print that only goes to stdout
print("Important message")  # Only to console
```

### 4. **Easy Integration with Other Tools**
```python
# Works with log aggregation tools, monitoring systems
# Can be configured via config files
# Integrates with testing frameworks
```

## Testing Logger Output

In the test file, we demonstrate how to capture and verify log messages:

```python
def test_logger_messages(self):
    # Capture log output
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    logger.addHandler(handler)
    
    # Trigger logging
    logger.info("Test message")
    
    # Verify output
    log_output = log_stream.getvalue()
    assert "Test message" in log_output
    assert "INFO" in log_output
    
    # Cleanup
    logger.removeHandler(handler)
```

## Best Practices

### 1. **Use Appropriate Levels**
- `DEBUG`: Variable values, function entry/exit
- `INFO`: Major steps in processing, user actions
- `WARNING`: Recoverable errors, deprecated usage
- `ERROR`: Errors that prevent specific functionality
- `CRITICAL`: Errors that may crash the program

### 2. **Include Context in Messages**
```python
# Good - includes context
logger.error(f"Failed to read file {filename}: {error}")

# Less helpful - no context
logger.error("File read failed")
```

### 3. **Use f-strings for Formatting**
```python
# Recommended
logger.info(f"Processing {count} items")

# Avoid string concatenation in logs
logger.info("Processing " + str(count) + " items")
```

### 4. **Don't Log Sensitive Information**
```python
# Avoid logging passwords, API keys, personal data
logger.debug(f"User: {username}, Password: {password}")  # BAD!

# Instead, log non-sensitive identifiers
logger.debug(f"Authentication attempt for user: {username}")  # GOOD
```

## Running the Tests

To run the comprehensive test suite:

```bash
# Install pytest if not already installed
pip install pytest

# Run all tests with verbose output
pytest tests/test_pyptv_batch_improved.py -v

# Run specific test class
pytest tests/test_pyptv_batch_improved.py::TestLoggingFunctionality -v

# Run with captured output to see logs
pytest tests/test_pyptv_batch_improved.py -v -s
```

The test suite demonstrates:
- How to capture log output for testing
- Verifying that appropriate log messages are generated
- Testing different log levels
- Integration testing with logging

This logging approach makes the PyPTV batch processing more professional, debuggable, and maintainable.
