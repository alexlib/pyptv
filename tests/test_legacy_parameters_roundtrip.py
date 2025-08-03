import filecmp
from pathlib import Path
from pyptv import legacy_parameters
import shutil

def test_legacy_parameters_roundtrip(tmp_path):
    # Source directory with original parameter files
    src_dir = Path(__file__).parent / "test_cavity" / "parameters"
    assert src_dir.exists(), f"Source directory {src_dir} does not exist!"

    # Destination directory for roundtrip
    dest_dir = tmp_path / "parameters_roundtrip"
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Read all parameter files into objects
    params = legacy_parameters.readParamsDir(src_dir)

    # Print all parameter objects before writing to disk
    print("\n--- Parameter objects before writing ---")
    for name, param_obj in params.items():
        print(f"[{name.__name__}] {vars(param_obj)}")

    # Write all parameter objects to the new directory
    for param_obj in params.values():
        param_obj.path = dest_dir  # Set path to destination
        param_obj.write()

    # Copy any .dat files (e.g., man_ori.dat) directly for comparison
    for dat_file in src_dir.glob("*.dat"):
        shutil.copy(dat_file, dest_dir / dat_file.name)

    # Compare all .par and .dat files in src_dir and dest_dir
    for ext in ("*.par", "*.dat"):
        for src_file in src_dir.glob(ext):
            dest_file = dest_dir / src_file.name
            if src_file.name == "unsharp_mask.par":
                continue
            assert dest_file.exists(), f"Missing file: {dest_file}"
            with open(src_file, "r") as f1, open(dest_file, "r") as f2:
                src_lines = [line.strip() for line in f1]
                dest_lines = [line.strip() for line in f2]
                assert src_lines == dest_lines, f"Mismatch in {src_file.name}:\n{src_lines}\n!=\n{dest_lines}"

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])
