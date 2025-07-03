import os
import shutil
import tempfile
import pytest
from pathlib import Path
from pyptv.parameter_util import legacy_to_yaml, yaml_to_legacy

# Fixtures for test directories
def test_legacy_to_yaml_and_back(tmp_path):
    # Use the existing test_cavity/parameters directory as legacy input
    legacy_dir = Path("tests/test_cavity/parameters")
    yaml_file = tmp_path / "parameters.yaml"
    # Convert legacy to YAML
    out_yaml = legacy_to_yaml(legacy_dir, yaml_file)
    assert out_yaml.exists()
    # Convert YAML back to legacy in a new temporary directory
    roundtrip_dir = tmp_path / "roundtrip_parameters"
    out_dir = yaml_to_legacy(out_yaml, roundtrip_dir, overwrite=True)
    assert out_dir.exists()
    # Compare the original and roundtripped directories
    orig_files = set(f.name for f in legacy_dir.iterdir())
    roundtrip_files = set(f.name for f in out_dir.iterdir())
    assert orig_files == roundtrip_files
    for fname in orig_files:
        with open(legacy_dir / fname, "rb") as f1, open(out_dir / fname, "rb") as f2:
            assert f1.read() == f2.read()

if __name__ == "__main__":
    pytest.main([__file__])
