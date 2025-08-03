
import pytest
from pyptv.ptv import extract_cam_ids, generate_short_file_bases

@pytest.mark.parametrize("img_bases, expected_cam_ids", [
    (["cam1_%d.tif", "cam2_%03d.tif", "cam3.%d"], [1, 2, 3]),
    (["cam4", "c5_%%d", "cam6_%04d"], [4, 5, 6]),
    (["im7.%%03d", "cam8_%%d.tif", "cam9_%%05d"], [7, 8, 9]),
    (["cam10", "cam11_10000", "Cam12_extra", "c13"], [10, 11, 12, 13]),
])
def test_extract_cam_ids_param(img_bases, expected_cam_ids):
    cam_ids = extract_cam_ids(img_bases)
    assert cam_ids == expected_cam_ids, f"{img_bases} -> {cam_ids}, expected {expected_cam_ids}"


def test_generate_short_file_bases():
    img_bases = [
        "cam1_%d.tif",
        "cam2_%03d.tif",
        "cam3.%d",
        "cam4",
        "c5_%%d",
        "cam6_%04d",
        "im7.%%03d",
        "cam8_%%d.tif",
        "cam9_%%05d",
        "cam10",
        "cam11_10000",
        "Cam12_extra",
        "c13",
    ]
    short_bases = generate_short_file_bases(img_bases)
    assert len(short_bases) == len(img_bases)
    for i, base in enumerate(short_bases):
        assert base.startswith("cam"), f"Short base {base} does not start with 'cam'"