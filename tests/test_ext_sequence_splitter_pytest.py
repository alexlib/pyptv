"""Pytest version of ext_sequence_splitter plugin test (simplified)"""

import pytest
from pathlib import Path

from pyptv.pyptv_batch_plugins import run_batch

@pytest.mark.integration
def test_ext_sequence_splitter_plugin():
    """Test that ext_sequence_splitter plugin runs without errors using direct call."""
    test_exp_path = Path(__file__).parent / "test_splitter"
    yaml_file = test_exp_path / "parameters_Run1.yaml"
    assert yaml_file.exists(), f"YAML file not found: {yaml_file}"

    # Frame range and plugin names
    start_frame = 1000001
    end_frame = 1000002
    sequence_plugin = "ext_sequence_splitter"
    tracking_plugin = "ext_tracker_splitter"  # Not used, but required by signature

    run_batch(
        yaml_file=yaml_file,
        seq_first=start_frame,
        seq_last=end_frame,
        tracking_plugin=tracking_plugin,
        sequence_plugin=sequence_plugin,
        mode="sequence"
    )

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])