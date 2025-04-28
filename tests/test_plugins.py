"""
Tests for the plugin system
"""
import pytest
import os
import sys
import tempfile
from pathlib import Path
import shutil
import importlib

# Import plugin modules
from pyptv.plugins.ext_sequence_denis import Sequence
from pyptv.plugins.ext_tracker_denis import Tracking
from pyptv.plugins.ext_sequence_contour import Sequence as Sequence_Contour

# Conditionally import rembg-dependent modules
import importlib.util
if importlib.util.find_spec("rembg") is not None:
    from pyptv.plugins.ext_sequence_rembg import Sequence as Sequence_Rembg

@pytest.fixture
def mock_experiment_dir():
    """Create a mock experiment directory structure with plugin files"""
    temp_dir = tempfile.mkdtemp()
    exp_dir = Path(temp_dir) / "test_experiment"
    exp_dir.mkdir(exist_ok=True)

    # Create required subdirectories
    params_dir = exp_dir / "parameters"
    params_dir.mkdir(exist_ok=True)

    img_dir = exp_dir / "img"
    img_dir.mkdir(exist_ok=True)

    cal_dir = exp_dir / "cal"
    cal_dir.mkdir(exist_ok=True)

    res_dir = exp_dir / "res"
    res_dir.mkdir(exist_ok=True)

    plugins_dir = exp_dir / "plugins"
    plugins_dir.mkdir(exist_ok=True)

    # Create plugin files
    with open(exp_dir / "sequence_plugins.txt", "w") as f:
        f.write("ext_sequence_denis\n")
        f.write("ext_sequence_contour\n")
        f.write("ext_sequence_rembg\n")

    with open(exp_dir / "tracking_plugins.txt", "w") as f:
        f.write("ext_tracker_denis\n")

    # Copy plugin files to the plugins directory
    for plugin_file in ["ext_sequence_denis.py", "ext_tracker_denis.py",
                        "ext_sequence_contour.py", "ext_sequence_rembg.py"]:
        src_path = Path("/home/user/Documents/repos/pyptv/pyptv/plugins") / plugin_file
        if src_path.exists():
            shutil.copy(src_path, plugins_dir / plugin_file)

    yield exp_dir
    shutil.rmtree(temp_dir)

def test_sequence_denis_plugin():
    """Test the Sequence plugin from ext_sequence_denis"""
    plugin = Sequence()
    assert hasattr(plugin, "do_sequence")
    assert callable(plugin.do_sequence)

def test_tracker_denis_plugin():
    """Test the Tracking plugin from ext_tracker_denis"""
    plugin = Tracking()
    assert hasattr(plugin, "do_tracking")
    assert callable(plugin.do_tracking)

def test_sequence_contour_plugin():
    """Test the Sequence_Contour plugin"""
    plugin = Sequence_Contour()
    assert hasattr(plugin, "do_sequence")
    assert callable(plugin.do_sequence)

@pytest.mark.skipif(not importlib.util.find_spec("rembg"),
                   reason="rembg package not installed")
def test_sequence_rembg_plugin():
    """Test the Sequence_Rembg plugin"""
    if importlib.util.find_spec("rembg") is None:
        pytest.skip("rembg package not installed")

    try:
        plugin = Sequence_Rembg()
        assert hasattr(plugin, "do_sequence")
        assert callable(plugin.do_sequence)
    except ImportError:
        pytest.skip("rembg package not installed")

def test_plugin_loading(mock_experiment_dir):
    """Test loading plugins from files"""
    # Change to the mock experiment directory
    original_dir = os.getcwd()
    os.chdir(mock_experiment_dir)

    try:
        # Add the plugins directory to sys.path
        sys.path.insert(0, str(mock_experiment_dir / "plugins"))

        # Read the plugin list
        with open("sequence_plugins.txt", "r") as f:
            sequence_plugins = [line.strip() for line in f if line.strip()]

        with open("tracking_plugins.txt", "r") as f:
            tracking_plugins = [line.strip() for line in f if line.strip()]

        # Try to import each plugin
        for plugin_name in sequence_plugins:
            # Skip rembg plugin if rembg is not installed
            if plugin_name == "ext_sequence_rembg" and importlib.util.find_spec("rembg") is None:
                continue

            try:
                module = importlib.import_module(plugin_name)
                # For sequence plugins, the class is always named 'Sequence'
                plugin_class = getattr(module, 'Sequence')
                plugin = plugin_class()
                assert hasattr(plugin, "do_sequence")
                assert callable(plugin.do_sequence)
            except (ImportError, AttributeError) as e:
                # If the error is about rembg, skip it
                if "No module named 'rembg'" in str(e):
                    continue
                # If the plugin file doesn't exist in the test environment, skip it
                if not (mock_experiment_dir / "plugins" / f"{plugin_name}.py").exists():
                    pytest.skip(f"Plugin file {plugin_name}.py not found")
                else:
                    raise

        for plugin_name in tracking_plugins:
            try:
                module = importlib.import_module(plugin_name)
                # For tracking plugins, the class is always named 'Tracking'
                plugin_class = getattr(module, 'Tracking')
                plugin = plugin_class()
                assert hasattr(plugin, "do_tracking")
                assert callable(plugin.do_tracking)
            except (ImportError, AttributeError):
                # If the plugin file doesn't exist in the test environment, skip it
                if not (mock_experiment_dir / "plugins" / f"{plugin_name}.py").exists():
                    pytest.skip(f"Plugin file {plugin_name}.py not found")
                else:
                    raise
    finally:
        # Remove the plugins directory from sys.path
        if str(mock_experiment_dir / "plugins") in sys.path:
            sys.path.remove(str(mock_experiment_dir / "plugins"))

        # Change back to the original directory
        os.chdir(original_dir)
