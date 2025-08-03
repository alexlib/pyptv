
import shutil
from pathlib import Path
import pytest
from pyptv.parameter_manager import ParameterManager

@pytest.mark.parametrize("src_dir", [
    "tests/test_cavity/parameters",
    "tests/test_splitter/parameters",
])
def test_cal_ori_roundtrip(src_dir, tmp_path):
    work_dir = tmp_path / "par_files"
    work_dir.mkdir()
    for f in Path(src_dir).glob('*.par'):
        shutil.copy(f, work_dir / f.name)

    pm = ParameterManager()
    pm.from_directory(work_dir)
    yaml_path = tmp_path / "parameters.yaml"
    pm.to_yaml(yaml_path)

    out_dir = tmp_path / "parameters_from_yaml"
    pm2 = ParameterManager()
    pm2.from_yaml(yaml_path)
    pm2.to_directory(out_dir)

    # Only test cal_ori.par
    orig_file = work_dir / "cal_ori.par"
    out_file = out_dir / "cal_ori.par"
    assert orig_file.exists(), f"Missing original cal_ori.par in {src_dir}"
    assert out_file.exists(), f"Missing output cal_ori.par in {src_dir}"
    DEFAULT_STRING = '---'
    def normalize(line):
        # Treat both '' and DEFAULT_STRING as equivalent for splitter/virtual cameras
        return DEFAULT_STRING if line.strip() in ('', DEFAULT_STRING) else line.strip()

    with open(orig_file, 'r') as orig, open(out_file, 'r') as new:
        orig_lines = [normalize(line) for line in orig.readlines()]
        new_lines = [normalize(line) for line in new.readlines()]
        assert len(new_lines) <= len(orig_lines), f"Output file {out_file} has more lines than input!"
        assert len(new_lines) > 0, f"Output file {out_file} is empty!"
        assert orig_lines == new_lines, f"Mismatch between original and output cal_ori.par files"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
    # Run the test directly if this script is executed
    # test_cal_ori_roundtrip()