"""Pytest version of ext_sequence_splitter plugin test"""

import subprocess
import sys
from pathlib import Path


def test_ext_sequence_splitter_plugin():
    """Test that ext_sequence_splitter plugin runs without errors"""
    
    # Path to the batch script and test data
    script_path = Path(__file__).parent.parent / "pyptv" / "pyptv_batch_plugins.py"
    test_exp_path = Path(__file__).parent / "test_splitter"
    
    # Check if required files exist
    assert script_path.exists(), f"Batch script not found: {script_path}"
    assert test_exp_path.exists(), f"Test experiment not found: {test_exp_path}"
    
    # Run the batch command with ext_sequence_splitter plugin
    cmd = [
        sys.executable, 
        str(script_path), 
        str(test_exp_path), 
        "1000001", 
        "1000002",  # Just 2 frames for quick test
        "--sequence", "ext_sequence_splitter"
    ]
    
    # Execute the command
    result = subprocess.run(
        cmd, 
        capture_output=True, 
        text=True, 
        timeout=60
    )
    
    # Check that it completed successfully
    assert result.returncode == 0, f"Process failed with return code {result.returncode}. STDERR: {result.stderr}"
    
    # Check that expected output strings are present
    assert "Processing frame 1000001" in result.stdout, "Frame 1000001 not processed"
    assert "Processing frame 1000002" in result.stdout, "Frame 1000002 not processed"
    assert "correspondences" in result.stdout, "No correspondences found"
    assert "Sequence completed successfully" in result.stdout, "Sequence did not complete successfully"
    
    print("✅ ext_sequence_splitter plugin test passed")


if __name__ == "__main__":
    test_ext_sequence_splitter_plugin()
    print("🎉 Pytest-style test passed!")
