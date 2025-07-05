import pytest
from pathlib import Path
import shutil
import os


@pytest.fixture(scope="session")
def test_data_dir():
    """Fixture to set up test data directory"""
    # Get the absolute path to the test_cavity directory
    test_dir = Path(__file__).parent / "test_cavity"
    if not test_dir.exists():
        pytest.skip(f"Test data directory {test_dir} not found")
    return test_dir


@pytest.fixture(scope="session")
def clean_test_environment(test_data_dir):
    """Clean up test environment before and after tests"""
    # Clean up any existing test results
    results_dir = test_data_dir / "res"
    if results_dir.exists():
        shutil.rmtree(results_dir)

    # Create fresh directories
    results_dir.mkdir(exist_ok=True)

    yield

    # Cleanup after tests
    if results_dir.exists():
        shutil.rmtree(results_dir)


@pytest.fixture(autouse=True)
def ensure_clean_working_directory():
    """
    Autouse fixture that ensures each test starts with a clean working directory.

    This fixture runs before every test to ensure proper test isolation
    by restoring the working directory to the project root.
    """
    # Store the original working directory
    original_cwd = None
    try:
        original_cwd = os.getcwd()
    except (OSError, FileNotFoundError):
        # If current directory doesn't exist, default to project root
        pass

    # Ensure we're in the project root (where pyproject.toml is)
    project_root = Path(__file__).parent.parent
    if project_root.exists():
        os.chdir(project_root)

    # Run the test
    yield

    # Restore original directory if it still exists, otherwise stay in project root
    if original_cwd:
        try:
            if Path(original_cwd).exists():
                os.chdir(original_cwd)
            else:
                # Original directory was deleted, stay in project root
                os.chdir(project_root)
        except (OSError, FileNotFoundError):
            # If restoration fails, ensure we're in project root
            os.chdir(project_root)
