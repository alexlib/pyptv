#!/usr/bin/env python3
"""
Test script for the improved ParameterManager functionality
"""
import pytest

from pyptv.parameter_manager import ParameterManager


def test_man_ori_dat_roundtrip(tmp_path):
    # Create a fake parameter directory with man_ori.dat
    param_dir = tmp_path / "params"
    param_dir.mkdir()
    man_ori_dat = param_dir / "man_ori.dat"
    # 2 cameras, 4 points each
    man_ori_dat.write_text("0.0 0.0\n1.0 0.0\n1.0 1.0\n0.0 1.0\n" * 2)
    ptv_par = param_dir / "ptv.par"
    # Write a valid ptv.par file with all required fields (example: 2 cameras)
    ptv_par.write_text(
        "\n".join([
            "2",
            "img/cam1.10002",
            "cal/cam1.tif",
            "img/cam2.10002",
            "cal/cam2.tif",
            "1",
            "0",
            "1",
            "1280",
            "1024",
            "0.012",
            "0.012",
            "0",
            "1",
            "1.33",
            "1.46",
            "6"
        ]) + "\n"
    )


    pm = ParameterManager()
    pm.from_directory(param_dir)
    assert 'man_ori_coordinates' in pm.parameters
    coords = pm.parameters['man_ori_coordinates']
    assert 'camera_0' in coords and 'camera_1' in coords
    assert coords['camera_0']['point_1'] == {'x': 0.0, 'y': 0.0}
    assert coords['camera_1']['point_4'] == {'x': 0.0, 'y': 1.0}

    # Now test writing back to directory
    out_dir = tmp_path / "out"
    pm.to_directory(out_dir)
    out_man_ori = out_dir / "man_ori.dat"
    assert out_man_ori.exists()
    lines = out_man_ori.read_text().splitlines()
    assert lines[0] == "0.0 0.0"
    assert lines[3] == "0.0 1.0"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
    # Run the test directly if this script is executed
    # test_parameter_manager()
