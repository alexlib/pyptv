import os
import shutil
import tempfile
import pytest
from pathlib import Path
from pyptv.parameter_util import legacy_to_yaml, yaml_to_legacy

def make_minimal_legacy_dir(tmp_path):
    """Create a minimal legacy parameter folder for testing."""
    legacy_dir = tmp_path / "parameters"
    legacy_dir.mkdir()
    
    # Create ptv.par with proper line-by-line format (based on real test_cavity format)
    ptv_par = legacy_dir / "ptv.par"
    ptv_par.write_text("""4
img/cam1.tif
cal/cam1.tif
img/cam2.tif
cal/cam2.tif
img/cam3.tif
cal/cam3.tif
img/cam4.tif
cal/cam4.tif
1
0
1
1280
1024
0.012
0.012
0
1
1.33
1.46
6
""")
    
    # Create targ_rec.par with proper line-by-line format
    targ_rec_par = legacy_dir / "targ_rec.par"
    targ_rec_par.write_text("""9
9
9
11
100
4
500
2
100
2
100
2
10
5
""")
    
    # Create cal_ori.par
    cal_ori_par = legacy_dir / "cal_ori.par"
    cal_ori_par.write_text("""cal/target.txt
cal/cam1.tif
cal/cam1.tif.ori
cal/cam2.tif
cal/cam2.tif.ori
cal/cam3.tif
cal/cam3.tif.ori
cal/cam4.tif
cal/cam4.tif.ori
1
0
0
""")
    
    # Create sequence.par
    sequence_par = legacy_dir / "sequence.par"
    sequence_par.write_text("""img1_
img2_
img3_
img4_
10001
10100
""")
    
    # Create criteria.par
    criteria_par = legacy_dir / "criteria.par"
    criteria_par.write_text("""-100.0
100.0
-50.0
-50.0
50.0
50.0
0.5
0.5
10
50
0.1
0.01
""")
    
    # Create plugins.json
    plugins_json = legacy_dir / "plugins.json"
    plugins_json.write_text('{"tracking": {"available": ["default"], "selected": "default"}, "sequence": {"available": ["default"], "selected": "default"}}')
    
    # Create man_ori.dat with 4 cameras x 4 points each
    man_ori_dat = legacy_dir / "man_ori.dat"
    man_ori_dat.write_text("0.0 0.0\n1.0 0.0\n1.0 1.0\n0.0 1.0\n" * 4)
    
    return legacy_dir

def test_legacy_to_yaml_minimal(tmp_path):
    """Test basic legacy to YAML conversion with minimal data."""
    legacy_dir = make_minimal_legacy_dir(tmp_path)
    yaml_file = tmp_path / "parameters.yaml"
    
    # Convert legacy to YAML
    out_yaml = legacy_to_yaml(legacy_dir, yaml_file, backup_legacy=False)
    assert out_yaml.exists()
    assert out_yaml == yaml_file
    
    # Check YAML file has content
    yaml_content = yaml_file.read_text()
    assert "num_cams: 4" in yaml_content
    assert "ptv:" in yaml_content
    assert "targ_rec:" in yaml_content

def test_yaml_to_legacy_minimal(tmp_path):
    """Test basic YAML to legacy conversion."""
    # First create a legacy directory and convert to YAML
    legacy_dir = make_minimal_legacy_dir(tmp_path)
    yaml_file = tmp_path / "parameters.yaml"
    legacy_to_yaml(legacy_dir, yaml_file, backup_legacy=False)
    
    # Convert YAML back to legacy
    roundtrip_dir = tmp_path / "roundtrip_parameters"
    out_dir = yaml_to_legacy(yaml_file, roundtrip_dir, overwrite=True)
    assert out_dir.exists()
    
    # Check essential files exist
    assert (out_dir / "ptv.par").exists()
    assert (out_dir / "targ_rec.par").exists()
    # assert (out_dir / "plugins.json").exists()
    assert (out_dir / "man_ori.dat").exists()

def test_legacy_to_yaml_and_back(tmp_path):
    """Test round-trip conversion with real test_cavity data."""
    # Use the existing test_cavity/parameters directory as legacy input
    legacy_dir = Path("tests/test_cavity/parameters")
    if not legacy_dir.exists():
        pytest.skip("test_cavity/parameters directory not found")
    
    yaml_file = tmp_path / "parameters.yaml"
    
    # Convert legacy to YAML
    out_yaml = legacy_to_yaml(legacy_dir, yaml_file, backup_legacy=False)
    assert out_yaml.exists()
    
    # Convert YAML back to legacy in a new temporary directory
    roundtrip_dir = tmp_path / "roundtrip_parameters"
    out_dir = yaml_to_legacy(out_yaml, roundtrip_dir, overwrite=True)
    assert out_dir.exists()
    
    # Check that essential files were created
    essential_files = ["ptv.par", "targ_rec.par", "man_ori.dat"]
    for fname in essential_files:
        assert (out_dir / fname).exists(), f"Essential file {fname} missing from roundtrip"
    
    # Check that the number of .par files is reasonable (should be most of the original)
    orig_par_files = list(legacy_dir.glob("*.par"))
    roundtrip_par_files = list(out_dir.glob("*.par"))
    assert len(roundtrip_par_files) >= len(orig_par_files) - 2, "Too many .par files lost in roundtrip"

if __name__ == "__main__":
    pytest.main([__file__])
