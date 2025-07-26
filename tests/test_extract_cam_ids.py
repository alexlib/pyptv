import pytest
from pyptv.ptv import extract_cam_ids

def test_extract_cam_ids_basic():
    # Standard case: cam1, cam2, cam3
    file_bases = ['cam1', 'cam2', 'cam3']
    assert extract_cam_ids(file_bases) == [1, 2, 3]

def test_extract_cam_ids_with_prefix():
    # Prefixes: img01, img02, img03
    file_bases = ['img01', 'img02', 'img03']
    assert extract_cam_ids(file_bases) == [1, 2, 3]

def test_extract_cam_ids_with_suffix():
    # Suffixes: c1_base, c2_base, c3_base
    file_bases = ['c1_base', 'c2_base', 'c3_base']
    assert extract_cam_ids(file_bases) == [1, 2, 3]

def test_extract_cam_ids_mixed():
    # Mixed: camA1, camB2, camC3
    file_bases = ['camA1', 'camB2', 'camC3']
    assert extract_cam_ids(file_bases) == [1, 2, 3]

def test_extract_cam_ids_multiple_numbers():
    # Multiple numbers: cam1_img10, cam2_img20, cam3_img30
    file_bases = ['cam1_img10', 'cam2_img20', 'cam3_img30']
    # Should pick the number that varies most (cam id)
    assert extract_cam_ids(file_bases) == [1, 2, 3]

def test_extract_cam_ids_no_number():
    # No number: fallback to 0
    file_bases = ['foo', 'bar', 'baz']
    assert extract_cam_ids(file_bases) == [1, 2, 3]

def test_extract_cam_ids_last_number_fallback():
    # Only last number varies: fallback to last number
    file_bases = ['prefix_1', 'prefix_2', 'prefix_3']
    assert extract_cam_ids(file_bases) == [1, 2, 3]

def test_extract_cam_ids_complex():
    # Complex: cam01A, cam02B, cam03C
    file_bases = ['cam01A', 'cam02B', 'cam03C']
    assert extract_cam_ids(file_bases) == [1, 2, 3]

def test_extract_cam_ids_realistic():
    # Realistic: /data/cam1/img, /data/cam2/img, /data/cam3/img
    file_bases = ['/data/cam1/img', '/data/cam2/img', '/data/cam3/img']
    assert extract_cam_ids(file_bases) == [1, 2, 3]

if __name__ == "__main__":
    pytest.main([__file__])