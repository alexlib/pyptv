"""Pytest version of ext_sequence_splitter plugin test"""

import subprocess
import sys
import os
import pytest
from pathlib import Path

@pytest.mark.integration
def test_ext_sequence_splitter_plugin():
    """Test that ext_sequence_splitter plugin runs without errors"""
    script_path = Path(__file__).parent.parent / "pyptv" / "pyptv_batch_plugins.py"
    test_exp_path = Path(__file__).parent / "test_splitter"

    # Check if required files exist
    assert script_path.exists(), f"Batch script not found: {script_path}"
    assert test_exp_path.exists(), f"Test experiment not found: {test_exp_path}"

    # Set PYTHONPATH so subprocess can import local pyptv
    env = os.environ.copy()
    repo_root = str(Path(__file__).parent.parent)
    env["PYTHONPATH"] = repo_root + os.pathsep + env.get("PYTHONPATH", "")

    cmd = [
        sys.executable,
        str(script_path),
        str(test_exp_path),
        "1000001",
        "1000002",
        "--sequence", "ext_sequence_splitter"
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=60,
        env=env
    )

    # Print output for debugging if failed
    if result.returncode != 0:
        print("STDOUT:\n", result.stdout)
        print("STDERR:\n", result.stderr)

    assert result.returncode == 0, f"Process failed with return code {result.returncode}. STDERR: {result.stderr}"
    assert "Processing frame 1000001" in result.stdout, "Frame 1000001 not processed"
    assert "Processing frame 1000002" in result.stdout, "Frame 1000002 not processed"
    assert "correspondences" in result.stdout, "No correspondences found"
    assert "Sequence completed successfully" in result.stdout, "Sequence did not complete successfully"

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])