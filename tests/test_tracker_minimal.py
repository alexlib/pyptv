import os
import numpy as np
from pathlib import Path
from pyptv.ptv import (
    ControlParams, VolumeParams, TrackingParams, SequenceParams, TargetParams,
    Calibration, Tracker, TargetArray, write_targets, generate_short_file_bases
)

def make_dummy_targets(n=3):
    targs = TargetArray(n)
    for i in range(n):
        targs[i].set_pnr(i)
        # Set 3D position: x, y, z (z=0.5)
        targs[i].set_pos([10.0 + i, 20.0 + i, 0.5])
        targs[i].set_pixel_counts(5, 5, 5)
        targs[i].set_sum_grey_value(100)
        targs[i].set_tnr(i)
    return targs

def test_tracker_minimal(tmp_path):

    tmp_path = Path(tmp_path)
    # Ensure res/ directory exists and set working directory
    res_dir = tmp_path / "res"
    res_dir.mkdir(exist_ok=True)
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    num_cams = 2

    # Write minimal calibration files for both cameras (after num_cams is defined)
    cal_data = (
        "# Camera calibration file\n"
        "pos: 0.0 0.0 0.0\n"
        "angles: 0.0 0.0 0.0\n"
        "rot: 1.0 0.0 0.0 0.0 1.0 0.0 0.0 0.0 1.0\n"
        "xh: 50.0\n"
        "yh: 50.0\n"
        "cc: 100.0\n"
        "glass_vec: 0.0 0.0 1.0\n"
    )
    for i in range(num_cams):
        cal_file = tmp_path / f"cal{i}"
        with open(cal_file, "w") as f:
            f.write(cal_data)
    # Set up dummy parameter objects
    cpar = ControlParams(num_cams)
    cpar.set_image_size((100, 100))
    cpar.set_pixel_size((0.01, 0.01))
    cpar.set_hp_flag(0)
    cpar.set_allCam_flag(0)
    cpar.set_tiff_flag(0)
    cpar.set_chfield(0)
    mm_params = cpar.get_multimedia_params()
    mm_params.set_n1(1.0)
    mm_params.set_layers([1.0], [0.0])
    mm_params.set_n3(1.0)
    for i in range(num_cams):
        cpar.set_cal_img_base_name(i, str(tmp_path / f"cal{i}"))

    vpar = VolumeParams()
    # Only limit x and z, not y
    vpar.set_X_lay([0.0, 50.0])  # x from 0 to 50
    vpar.set_Zmin_lay([0.0, 0.0])
    vpar.set_Zmax_lay([1.0, 1.0])
    vpar.set_eps0(1.0)
    vpar.set_cn(1.0)
    vpar.set_cnx(1.0)
    vpar.set_cny(1.0)
    vpar.set_csumg(1.0)
    vpar.set_corrmin(1.0)

    track_par = TrackingParams()
    track_par.set_dvxmin(-2.0)
    track_par.set_dvxmax(2.0)
    track_par.set_dvymin(-2.0)
    track_par.set_dvymax(2.0)
    track_par.set_dvzmin(-1.0)
    track_par.set_dvzmax(1.0)
    track_par.set_dangle(1.0)
    track_par.set_dacc(1.0)
    track_par.set_add(1)

    spar = SequenceParams(num_cams=num_cams)
    spar.set_first(1)
    spar.set_last(4)
    img_base_names = [str(tmp_path / f"img{i}_%04d.tif") for i in range(num_cams)]
    short_file_bases = generate_short_file_bases(img_base_names)
    for i in range(num_cams):
        spar.set_img_base_name(i, short_file_bases[i]+'.')

    tpar = TargetParams(num_cams)
    tpar.set_grey_thresholds([10, 10, 10, 10])
    tpar.set_pixel_count_bounds((1, 10))
    tpar.set_xsize_bounds((1, 10))
    tpar.set_ysize_bounds((1, 10))
    tpar.set_min_sum_grey(1)
    tpar.set_max_discontinuity(1)

    cals = [Calibration() for _ in range(num_cams)]

    # Print calibration parameters for both cameras
    print("\n--- DEBUG: Camera Calibrations ---")
    for idx, cal in enumerate(cals):
        print(f"Camera {idx} calibration:")
        # Print all attributes of the calibration object
        for attr in dir(cal):
            if not attr.startswith("_") and not callable(getattr(cal, attr)):
                print(f"  {attr}: {getattr(cal, attr)}")

    # Write dummy targets for frames 1-4, two particles per frame, both cameras
    short_file_bases = generate_short_file_bases(img_base_names)
    for frame in range(1, 5):
        for i in range(num_cams):
            targs = make_dummy_targets(n=2)
            # Set 3D positions for each target (z=0.5)
            targs[0].set_pnr(1)
            targs[0].set_pos([10.0 + frame * 0.5, 20.0 + frame * 0.5, 0.5])
            targs[1].set_pnr(2)
            targs[1].set_pos([30.0 + frame * 0.5, 40.0 + frame * 0.5, 0.5])
            # Add period between base and frame number
            write_targets(targs, short_file_bases[i] + '.', frame)
    # Create correspondence files with two particles, both present in both cameras
    for frame in range(1, 5):
        rt_is_file = res_dir / f"rt_is.{frame}"
        with open(rt_is_file, "w") as f:
            f.write("2\n")
            # pnr, x, y, z, cam1, cam2, cam3, cam4 (dummy values for cams)
            f.write(f"1 {10.0 + frame * 0.5} {20.0 + frame * 0.5} 0.5 1 2 -1 -1\n")
            f.write(f"2 {30.0 + frame * 0.5} {40.0 + frame * 0.5} 0.5 1 2 -1 -1\n")

    # Print all parameter values for debugging
    print("\n--- DEBUG: ControlParams ---")
    print("image_size:", cpar.get_image_size())
    print("pixel_size:", cpar.get_pixel_size())
    print("hp_flag:", cpar.get_hp_flag())
    print("allCam_flag:", cpar.get_allCam_flag())
    print("tiff_flag:", cpar.get_tiff_flag())
    print("chfield:", cpar.get_chfield())
    print("cal_img_base_names:", [cpar.get_cal_img_base_name(i) for i in range(num_cams)])
    mm_params = cpar.get_multimedia_params()
    print("mm_params n1:", mm_params.get_n1())
    print("mm_params n3:", mm_params.get_n3())

    print("\n--- DEBUG: VolumeParams ---")
    print("X_lay:", vpar.get_X_lay())
    print("Zmin_lay:", vpar.get_Zmin_lay())
    print("Zmax_lay:", vpar.get_Zmax_lay())
    print("eps0:", vpar.get_eps0())
    print("cn:", vpar.get_cn())
    print("cnx:", vpar.get_cnx())
    print("cny:", vpar.get_cny())
    print("csumg:", vpar.get_csumg())
    print("corrmin:", vpar.get_corrmin())

    print("\n--- DEBUG: TrackingParams ---")
    print("dvxmin:", track_par.get_dvxmin())
    print("dvxmax:", track_par.get_dvxmax())
    print("dvymin:", track_par.get_dvymin())
    print("dvymax:", track_par.get_dvymax())
    print("dvzmin:", track_par.get_dvzmin())
    print("dvzmax:", track_par.get_dvzmax())
    print("dangle:", track_par.get_dangle())
    print("dacc:", track_par.get_dacc())
    print("add:", track_par.get_add())

    print("\n--- DEBUG: SequenceParams ---")
    print("first:", spar.get_first())
    print("last:", spar.get_last())
    print("img_base_names:", [spar.get_img_base_name(i) for i in range(num_cams)])

    print("\n--- DEBUG: TargetParams ---")
    print("grey_thresholds:", tpar.get_grey_thresholds())
    print("pixel_count_bounds:", tpar.get_pixel_count_bounds())
    print("xsize_bounds:", tpar.get_xsize_bounds())
    print("ysize_bounds:", tpar.get_ysize_bounds())
    print("min_sum_grey:", tpar.get_min_sum_grey())
    print("max_discontinuity:", tpar.get_max_discontinuity())

    # Print all target positions for all frames and cameras
    print("\n--- DEBUG: Target Positions ---")
    for frame in range(1, 5):
        for i in range(num_cams):
            fname = f"{short_file_bases[i]}.{frame:04d}_targets"
            if os.path.exists(fname):
                with open(fname, "r") as f:
                    print(f"Frame {frame}, Cam {i}: {fname}")
                    print(f.read())
            else:
                print(f"Frame {frame}, Cam {i}: {fname} (not found)")

    # Print all correspondence files
    print("\n--- DEBUG: Correspondence Files (rt_is) ---")
    for frame in range(1, 5):
        rt_is_file = res_dir / f"rt_is.{frame}"
        if rt_is_file.exists():
            print(f"rt_is.{frame}:")
            with open(rt_is_file, "r") as f:
                print(f.read())
        else:
            print(f"rt_is.{frame} (not found)")

    # Now run Tracker
    tracker = Tracker(cpar, vpar, track_par, spar, cals)
    tracker.full_forward()
    # Print output ptv_is files
    print("\n--- DEBUG: Output ptv_is Files ---")
    for frame in range(1, 5):
        ptv_is_file = res_dir / f"ptv_is.{frame}"
        if ptv_is_file.exists():
            print(f"ptv_is.{frame}:")
            with open(ptv_is_file, "r") as f:
                print(f.read())
        else:
            print(f"ptv_is.{frame} (not found)")
    # Check for output file in the correct location
    track_file = res_dir / "ptv_is.1"
    assert track_file.exists(), "Tracker did not create the expected output file in res/. Check parameter and file base setup."
    # Check that at least one track is present in the output file
    with open(track_file, "r") as f:
        lines = f.readlines()
    # The first line is the number of tracks
    num_tracks = int(lines[0].strip()) if lines else 0
    assert num_tracks > 0, "No tracks found in ptv_is.1. Tracker did not link any particles."
    os.chdir(old_cwd)

if __name__ == "__main__":
    import tempfile
    test_tracker_minimal(tempfile.TemporaryDirectory().name)
    print("Tracker minimal test ran.")
