# Working with PyPTV Batch Processing in the pyptv Conda Environment

## Environment Setup

### Activating the pyptv Environment

```bash
# Activate the pyptv conda environment
conda activate pyptv

# Verify the environment is active
which python
# Should show: /home/user/miniforge3/envs/pyptv/bin/python

# Check Python version
python --version
# Should show: Python 3.11.13

### Environment Details

PyPTV uses a modern `environment.yml` and `requirements-dev.txt` for reproducible environments. Most dependencies are installed via conda, but some (e.g., `optv`, `opencv-python-headless`, `rembg`, `flowtracks`) are installed via pip in the conda environment.

See the root `environment.yml` for the recommended setup.

### Testing: Headless vs GUI

PyPTV separates tests into two categories:

- **Headless tests** (no GUI): Located in `tests/`. These run in CI (GitHub Actions) and Docker, and do not require a display.
- **GUI-dependent tests**: Located in `tests_gui/`. These require a display and are run locally or with Xvfb.

To run all tests locally:
```bash
bash run_tests.sh
```
To run only headless tests (recommended for CI/Docker):
```bash
bash run_headless_tests.sh
```
```

### Running Commands in the pyptv Environment

You can run commands in the pyptv environment in two ways:

#### Option 1: Activate then run
```bash
conda activate pyptv
python your_script.py
```

#### Option 2: Use conda run (recommended for automation)
```bash
conda run -n pyptv python your_script.py
```

## Testing the Improved pyptv_batch.py

### Running the Comprehensive Test Suite

```bash
# Run all tests
conda run -n pyptv pytest tests/test_pyptv_batch_improved.py -v

# Run specific test classes
conda run -n pyptv pytest tests/test_pyptv_batch_improved.py::TestAttrDict -v
conda run -n pyptv pytest tests/test_pyptv_batch_improved.py::TestLoggingFunctionality -v

# Run with coverage
conda run -n pyptv pytest tests/test_pyptv_batch_improved.py --cov=pyptv.pyptv_batch
```

### Running the Logger Demonstration

```bash
# Run the logger demonstration script
conda run -n pyptv python logger_demo.py

# Run the simplified test demonstration
conda run -n pyptv python test_pyptv_batch_demo.py
```

## Using the Improved pyptv_batch.py

### Command Line Usage

```bash
# Basic usage with the pyptv environment
conda run -n pyptv python pyptv/pyptv_batch.py /path/to/experiment 1000 2000

# With default test values (if test directory exists)
conda run -n pyptv python pyptv/pyptv_batch.py
```

### Python API Usage

```python
# In a Python script or interactive session
from pyptv.pyptv_batch import main, ProcessingError

try:
    main("/path/to/experiment", 1000, 2000, repetitions=1)
except ProcessingError as e:
    print(f"Processing failed: {e}")
```

## Key Improvements Made

### 1. Fixed Critical Bugs
- ✅ Fixed variable scoping issue in `run_batch()` function
- ✅ Proper parameter passing between functions
- ✅ Better working directory management

### 2. Enhanced Error Handling
- ✅ Custom `ProcessingError` exception class
- ✅ Specific error messages for different failure scenarios
- ✅ Input validation for all parameters
- ✅ Graceful handling of interruptions

### 3. Improved Logging
- ✅ Replaced print statements with structured logging
- ✅ Configurable logging levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- ✅ Consistent timestamp and format across all messages
- ✅ Better progress tracking and performance reporting

### 4. Code Quality Enhancements
- ✅ Complete type hints for better IDE support
- ✅ Comprehensive docstrings with parameters and exceptions
- ✅ Modern Python features (f-strings, pathlib, etc.)
- ✅ Separation of concerns (command parsing, validation, processing)

### 5. Testing Infrastructure
- ✅ Comprehensive test suite with pytest
- ✅ Mocking for external dependencies
- ✅ Test coverage for all major functionality
- ✅ Logging output verification

## Logger Usage Guide

### Basic Logging Levels

```python
import logging
from pyptv.pyptv_batch import logger

# Different severity levels (from least to most severe)
logger.debug("Detailed diagnostic information")
logger.info("General information about program execution")  
logger.warning("Something unexpected happened, but continuing")
logger.error("A serious problem occurred")
logger.critical("A severe error occurred, program may not continue")
```

### Configuring Logging

```python
import logging

# Set logging level
logging.basicConfig(level=logging.DEBUG)  # Show all messages
logging.basicConfig(level=logging.INFO)   # Show INFO and above (default)
logging.basicConfig(level=logging.WARNING) # Show only warnings and errors

# Custom format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
```

### Logging Best Practices

```python
# ✅ Good: Include context
logger.error(f"Failed to process file {filename}: {error}")

# ✅ Good: Use f-strings for formatting
logger.info(f"Processing {count} items in {directory}")

# ✅ Good: Appropriate level for the message
logger.info("Starting batch processing")  # Normal operation
logger.warning("Using default values")    # Unexpected but not critical
logger.error("Directory not found")       # Problem occurred

# ❌ Avoid: Generic messages without context
logger.error("Something went wrong")

# ❌ Avoid: Logging sensitive information
logger.debug(f"Password: {password}")  # Security risk!
```

## Example Workflow

Here's a complete example of using the improved pyptv_batch.py:

```bash
# 1. Activate the environment
conda activate pyptv

# 2. Run with logging to see progress
python pyptv/pyptv_batch.py /path/to/experiment 1000 1010

# Example output:
# 2025-06-26 21:30:31,240 - INFO - Starting PyPTV batch processing
# 2025-06-26 21:30:31,240 - INFO - Command line arguments: ['pyptv/pyptv_batch.py', '/path/to/experiment', '1000', '1010']
# 2025-06-26 21:30:31,241 - INFO - Starting batch processing in directory: /path/to/experiment
# 2025-06-26 21:30:31,241 - INFO - Frame range: 1000 to 1010
# 2025-06-26 21:30:31,241 - INFO - Repetitions: 1
# 2025-06-26 21:30:31,241 - INFO - Creating 'res' directory
# 2025-06-26 21:30:31,241 - INFO - Starting batch processing: frames 1000 to 1010
# 2025-06-26 21:30:31,241 - INFO - Number of cameras: 4
# 2025-06-26 21:30:31,242 - INFO - Batch processing completed successfully
# 2025-06-26 21:30:31,242 - INFO - Total processing time: 1.25 seconds
```

## Troubleshooting

### Common Issues and Solutions

1. **ImportError**: Make sure you're in the pyptv environment
   ```bash
   conda activate pyptv
   ```

2. **Directory not found**: Ensure the experiment directory has the required structure:
   ```
   experiment_dir/
   ├── parameters/
   │   └── ptv.par
   ├── img/
   ├── cal/
   └── res/  # Created automatically if missing
   ```

3. **Logging not appearing**: Check the logging level
   ```python
   import logging
   logging.getLogger().setLevel(logging.DEBUG)  # Show all messages
   ```

4. **Tests failing**: Make sure pytest is installed in the pyptv environment
   ```bash
   conda run -n pyptv pip install pytest pytest-cov
   ```

This setup provides a robust, well-tested, and maintainable batch processing system for PyPTV with excellent logging and error handling capabilities.
