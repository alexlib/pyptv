import os
import shutil
import tempfile
import pandas as pd
import numpy as np
import pytest
from pyptv.flowtracks_utils import export_ptv_is_to_paraview

def make_fake_ptv_is_files(tmpdir, n_frames=3, n_particles=2):
    """Create fake ptv_is.# files for testing export_ptv_is_to_paraview."""
    # We'll create a minimalistic trajectories_ptvis-compatible loader
    # But for this test, we patch the function in the module
    # Instead, we create a fake loader below
    # This is a placeholder for a real test with actual files
    pass  # The real test will patch trajectories_ptvis

def test_export_ptv_is_to_paraview(monkeypatch, tmp_path):
    # Prepare fake data to be returned by trajectories_ptvis
    fake_trajs = [
        [
            (1.0, 2.0, 3.0, 0.1, 0.2, 0.3, 0, 42),
            (1.1, 2.1, 3.1, 0.1, 0.2, 0.3, 0, 42),
        ],
        [
            (4.0, 5.0, 6.0, 0.4, 0.5, 0.6, 1, 43),
            (4.1, 5.1, 6.1, 0.4, 0.5, 0.6, 1, 43),
        ],
    ]
    def fake_trajectories_ptvis(pattern, xuap=False):
        return fake_trajs
    monkeypatch.setattr("pyptv.flowtracks_utils.trajectories_ptvis", fake_trajectories_ptvis)
    outdir = tmp_path
    export_ptv_is_to_paraview(ptv_is_pattern="doesnotmatter", output_dir=str(outdir), xuap=False)
    # Check that output files exist and have correct content
    files = list(outdir.glob("ptv_*.txt"))
    assert files, "No output files created"
    # Read and check content
    for f in files:
        df = pd.read_csv(f, sep=",|	", engine="python")
        assert set(["particle", "x", "y", "z", "dx", "dy", "dz"]).issubset(df.columns)
        assert not df.empty
