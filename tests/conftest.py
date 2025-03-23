import pytest
from pathlib import Path
import shutil

@pytest.fixture(scope="session")
def test_data_dir():
    """Fixture to set up test data directory"""
    test_dir = Path("tests/test_cavity")
    if not test_dir.exists():
        test_dir.mkdir(parents=True)
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