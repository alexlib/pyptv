import pytest
from pyptv.ptv import generate_short_file_bases

@pytest.mark.parametrize("img_base_names, expected", [
    (
        ["img0.tif", "img1.tif", "img2.tif"],
        ["cam0", "cam1", "cam2"]
    ),
])
def test_generate_short_file_bases(img_base_names, expected):
    assert generate_short_file_bases(img_base_names) == expected

if __name__ == "__main__":
    pytest.main([__file__])
