# PyPTV Tests

This directory contains tests for the PyPTV package. The tests are organized by functionality and can be run using pytest.

## Running Tests

To run all tests:

```bash
python -m pytest
```

To run a specific test file:

```bash
python -m pytest tests/test_file.py
```

To run tests with verbose output:

```bash
python -m pytest -v
```

## Test Structure

The tests are organized as follows:

- **test_calibration_utils.py**: Tests for calibration utilities
- **test_cli.py** and **test_cli_extended.py**: Tests for command-line interface
- **test_core_functionality.py**: Tests for core functionality
- **test_environment.py**: Tests for environment setup
- **test_gui_components.py**: Tests for GUI components
- **test_installation.py** and **test_installation_extended.py**: Tests for installation
- **test_numpy_compatibility.py**: Tests for NumPy compatibility
- **test_optv.py**: Tests for optv integration
- **test_parameters.py**: Tests for parameter handling
- **test_plugins.py**: Tests for plugins
- **test_ptv_core.py**: Tests for PTV core functionality
- **test_pyptv_batch.py** and **test_pyptv_batch_extended.py**: Tests for batch processing

## Test Data

The test data is located in the `test_cavity` directory, which contains:

- **img/**: Test images
- **parameters/**: Test parameter files

## Skipped Tests

Some tests are skipped under certain conditions:

1. **test_calibration_gui_creation**: Requires more complex setup
2. **test_sequence_rembg_plugin**: Requires the rembg package
3. **test_windows_environment**: Windows-specific tests

## Adding New Tests

When adding new tests:

1. Create a new test file in the tests directory
2. Import the necessary modules
3. Write test functions that start with `test_`
4. Use pytest fixtures for setup and teardown
5. Run the tests to ensure they pass

## Test Coverage

To run tests with coverage:

```bash
python -m pytest --cov=pyptv
```

This will show the test coverage for the PyPTV package.
