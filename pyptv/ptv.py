"""PyPTV core functionality module.

This module provides the core functionality for the PyPTV package, including
image processing, calibration, tracking, and other utilities.
"""

# Standard library imports
import importlib
import os
import sys
import re
from pathlib import Path
from typing import List, Tuple

# Third-party imports
import numpy as np
from scipy.optimize import minimize
from imageio.v3 import imread
from skimage.util import img_as_ubyte
from skimage.color import rgb2gray

# OptV imports
from optv.calibration import Calibration
from optv.correspondences import correspondences, MatchedCoords
from optv.image_processing import preprocess_image
from optv.orientation import point_positions
from optv.parameters import (
    ControlParams,
    VolumeParams,
    TrackingParams,
    SequenceParams,
    TargetParams,
)
from optv.segmentation import target_recognition
from optv.tracking_framebuf import TargetArray
from optv.tracker import Tracker, default_naming

# PyPTV imports
from pyptv.parameter_manager import ParameterManager

# Constants
NAMES = ["cc", "xh", "yh", "k1", "k2", "k3", "p1", "p2", "scale", "shear"]
DEFAULT_FRAME_NUM = 123456789
DEFAULT_HIGHPASS_FILTER_SIZE = 25
DEFAULT_NO_FILTER = 0



def image_split(img: np.ndarray, order = [0,1,3,2]) -> List[np.ndarray]:
    """Split image into four quadrants.
    """
    list_of_images = [
        img[: img.shape[0] // 2, : img.shape[1] // 2],
        img[: img.shape[0] // 2, img.shape[1] // 2:],
        img[img.shape[0] // 2:, : img.shape[1] // 2],
        img[img.shape[0] // 2:, img.shape[1] // 2:],
    ]
    list_of_images = [list_of_images[i] for i in order]
    return list_of_images
    
def negative(img: np.ndarray) -> np.ndarray:
    """Convert an 8-bit image to its negative.
    """
    return 255 - img


def simple_highpass(img: np.ndarray, cpar: ControlParams) -> np.ndarray:
    """Apply a simple highpass filter to an image using liboptv preprocess_image.
    """
    return preprocess_image(img, DEFAULT_NO_FILTER, cpar, DEFAULT_HIGHPASS_FILTER_SIZE)


def _populate_cpar(params: dict) -> ControlParams:
    """Populate a ControlParams object from a dictionary containing full parameters.
    
    Args:
        params: Full parameter dictionary with global n_cam and ptv section
    """
    ptv_params = params.get('ptv', {})
    
    # Get global n_cam - the single source of truth
    n_cam = params.get('n_cam', 4)
    
    cpar = ControlParams(n_cam)
    cpar.set_image_size((ptv_params.get('imx', 0), ptv_params.get('imy', 0)))
    cpar.set_pixel_size((ptv_params.get('pix_x', 0.0), ptv_params.get('pix_y', 0.0)))
    cpar.set_hp_flag(ptv_params.get('hp_flag', False))
    cpar.set_allCam_flag(ptv_params.get('allcam_flag', False))
    cpar.set_tiff_flag(ptv_params.get('tiff_flag', False))
    cpar.set_chfield(ptv_params.get('chfield', 0))
    multimedia_params = cpar.get_multimedia_params()
    multimedia_params.set_n1(ptv_params.get('mmp_n1', 1.0))
    multimedia_params.set_layers([ptv_params.get('mmp_n2', 1.0)], [ptv_params.get('mmp_d', 0.0)])
    multimedia_params.set_n3(ptv_params.get('mmp_n3', 1.0))
    mm_params = cpar.get_multimedia_params()
    mm_params.set_n1(ptv_params.get('mmp_n1', 1.0))
    mm_params.set_layers([ptv_params.get('mmp_n2', 1.0)], [ptv_params.get('mmp_d', 0.0)])
    mm_params.set_n3(ptv_params.get('mmp_n3', 1.0))
    for i in range(n_cam):  # Use global n_cam
        img_cal_list = ptv_params.get('img_cal', [])
        if i < len(img_cal_list):
            cpar.set_cal_img_base_name(i, img_cal_list[i])
        else:
            print(f"Warning: No calibration image specified for camera {i}")
    return cpar

def _populate_spar(params: dict) -> SequenceParams:
    """Populate a SequenceParams object from a dictionary."""
    seq_params = params.get('sequence', {})
    
    # Get global n_cam - the single source of truth
    n_cam = params.get('n_cam', 4)
    
    spar = SequenceParams(num_cams=n_cam)
    spar.set_first(seq_params.get('first', 0))
    spar.set_last(seq_params.get('last', 0))
    for i in range(n_cam):  # Use global n_cam
        base_name_list = seq_params.get('base_name', [])
        if i < len(base_name_list):
            spar.set_img_base_name(i, base_name_list[i])
        else:
            print(f"Warning: No image base name specified for camera {i}")
    return spar

def _populate_vpar(params: dict) -> VolumeParams:
    """Populate a VolumeParams object from a dictionary."""
    crit_params = params.get('criteria', {})
    vpar = VolumeParams()
    vpar.set_X_lay(crit_params.get('X_lay', [0,0]))
    vpar.set_Zmin_lay(crit_params.get('Zmin_lay', [0,0]))
    vpar.set_Zmax_lay(crit_params.get('Zmax_lay', [0,0]))
    return vpar

def _populate_track_par(params: dict) -> TrackingParams:
    """Populate a TrackingParams object from a dictionary."""
    track_params = params.get('track', {})
    track_par = TrackingParams()
    track_par.set_dvxmin(track_params.get('dvxmin', 0.0))
    track_par.set_dvxmax(track_params.get('dvxmax', 0.0))
    track_par.set_dvymin(track_params.get('dvymin', 0.0))
    track_par.set_dvymax(track_params.get('dvymax', 0.0))
    track_par.set_dvzmin(track_params.get('dvzmin', 0.0))
    track_par.set_dvzmax(track_params.get('dvzmax', 0.0))
    track_par.set_dangle(track_params.get('angle', 0.0))
    track_par.set_dacc(track_params.get('dacc', 0.0))
    track_par.set_add(track_params.get('flagNewParticles', False))
    return track_par

def _populate_tpar(params: dict) -> TargetParams:
    """Populate a TargetParams object from a dictionary."""
    targ_params = params.get('targ_rec', {})
    
    # Get global n_cam - the single source of truth
    n_cam = params.get('n_cam', 4)
    
    tpar = TargetParams(n_cam)
    tpar.set_grey_thresholds(targ_params.get('gvthres', []))
    tpar.set_pixel_count_bounds((targ_params.get('nnmin', 0), targ_params.get('nnmax', 0)))
    tpar.set_xsize_bounds((targ_params.get('nxmin', 0), targ_params.get('nxmax', 0)))
    tpar.set_ysize_bounds((targ_params.get('nymin', 0), targ_params.get('nymax', 0)))
    tpar.set_min_sum_grey(targ_params.get('sumg_min', 0))
    tpar.set_max_discontinuity(targ_params.get('disco', 0))
    return tpar

def _read_calibrations(cpar: ControlParams, n_cams: int) -> List[Calibration]:
    """Read calibration files for all cameras.
    """
    cals = []
    for i_cam in range(n_cams):
        cal = Calibration()
        base_name = cpar.get_cal_img_base_name(i_cam)
        ori_file = base_name + ".ori"
        addpar_file = base_name + ".addpar"

        try:
            cal.from_file(ori_file, addpar_file)
            cals.append(cal)
        except IOError as e:
            raise IOError(f"Failed to read calibration files for camera {i_cam}: {e}")

    return cals


def py_start_proc_c(
    params: dict,
) -> Tuple[
    ControlParams,
    SequenceParams,
    VolumeParams,
    TrackingParams,
    TargetParams,
    List[Calibration],
    dict,
]:
    """Read all parameters needed for processing.
    """
    try:
        ptv_params = params.get('ptv', {})
        cpar = _populate_cpar(params)  # Pass full params, not just ptv_params

        seq_params = params.get('sequence', {})
        spar = _populate_spar(seq_params)

        volume_params = params.get('volume', {})
        vpar = _populate_vpar(volume_params)

        track_params = params.get('track', {})
        track_par = _populate_track_par(track_params)

        target_params = params.get('targ_rec', {})
        tpar = _populate_tpar(target_params)


        epar = params.get('examine', {})
        cals = _read_calibrations(cpar, params.get('n_cam', 4))  # Use global n_cam

        return cpar, spar, vpar, track_par, tpar, cals, epar

    except IOError as e:
        raise IOError(f"Failed to read parameter files: {e}")


def py_pre_processing_c(
    list_of_images: List[np.ndarray], ptv_params: dict, 
) -> List[np.ndarray]:
    """Apply pre-processing to a list of images.
    """
    cpar = _populate_cpar(ptv_params)
    processed_images = []
    for i, img in enumerate(list_of_images):
        img_lp = img.copy() 
        processed_images.append(simple_highpass(img_lp, cpar))

    return processed_images


def py_detection_proc_c(
    list_of_images: List[np.ndarray],
    ptv_params: dict,
    target_params: dict,
    cals: List[Calibration],
    existing_target: bool = False,
) -> Tuple[List[TargetArray], List[MatchedCoords]]:
    """Detect targets in a list of images."""
    cpar = _populate_cpar(ptv_params)
    tpar = _populate_tpar(target_params)

    detections = []
    corrected = []

    for i_cam, img in enumerate(list_of_images):
        if existing_target:
            raise NotImplementedError("Existing targets are not implemented")
        else:
            targs = target_recognition(img, tpar, i_cam, cpar)

        targs.sort_y()
        detections.append(targs)
        mc = MatchedCoords(targs, cpar, cals[i_cam])
        corrected.append(mc)

    return detections, corrected


def py_correspondences_proc_c(exp):
    """Provides correspondences
    """
    frame = 123456789
    sorted_pos, sorted_corresp, num_targs = correspondences(
        exp.detections, exp.corrected, exp.cals, exp.vpar, exp.cpar
    )

    for i_cam in range(exp.n_cams):
        base_name = exp.spar.get_img_base_name(i_cam)
        write_targets(exp.detections[i_cam], base_name, frame)

    print(
        "Frame "
        + str(frame)
        + " had "
        + repr([s.shape[1] for s in sorted_pos])
        + " correspondences."
    )

    return sorted_pos, sorted_corresp, num_targs


def py_determination_proc_c(
    n_cams: int,
    sorted_pos: List[np.ndarray],
    sorted_corresp: List[np.ndarray],
    corrected: List[MatchedCoords],
    cpar: ControlParams,
    vpar: VolumeParams,
    cals: List[Calibration],
) -> None:
    """Calculate 3D positions from 2D correspondences and save to file.
    """
    concatenated_pos = np.concatenate(sorted_pos, axis=1)
    concatenated_corresp = np.concatenate(sorted_corresp, axis=1)

    flat = np.array(
        [corrected[i].get_by_pnrs(concatenated_corresp[i]) for i in range(n_cams)]
    )

    pos, _ = point_positions(flat.transpose(1, 0, 2), cpar, cals, vpar)

    if n_cams < 4:
        print_corresp = -1 * np.ones((4, concatenated_corresp.shape[1]))
        print_corresp[: len(cals), :] = concatenated_corresp
    else:
        print_corresp = concatenated_corresp

    fname = (default_naming["corres"].decode() + "." + str(DEFAULT_FRAME_NUM)).encode()

    print(f"Prepared {fname} to write positions")

    try:
        with open(fname, "w", encoding="utf-8") as rt_is:
            print(f"Opened {fname}")
            rt_is.write(str(pos.shape[0]) + "\n")
            for pix, pt in enumerate(pos):
                pt_args = (pix + 1,) + tuple(pt) + tuple(print_corresp[:, pix])
                rt_is.write("%4d %9.3f %9.3f %9.3f %4d %4d %4d %4d\n" % pt_args)
    except FileNotFoundError as e:
        print(f"Error writing to file {fname}: {e}")


def run_sequence_plugin(exp) -> None:
    """Load and run plugins for sequence processing.
    """
    plugin_dir = Path(os.getcwd()) / "plugins"
    print(f"Plugin directory: {plugin_dir}")

    if str(plugin_dir) not in sys.path:
        sys.path.append(str(plugin_dir))

    for filename in os.listdir(plugin_dir):
        if filename.endswith(".py") and filename != "__init__.py":
            plugin_name = filename[:-3]
            if plugin_name == exp.plugins.sequence_alg:
                try:
                    print(f"Loading plugin: {plugin_name}")
                    plugin = importlib.import_module(plugin_name)
                except ImportError as e:
                    print(f"Error loading {plugin_name}: {e}")
                    return

                if hasattr(plugin, "Sequence"):
                    print(f"Running sequence plugin: {exp.plugins.sequence_alg}")
                    try:
                        sequence = plugin.Sequence(exp=exp)
                        sequence.do_sequence()
                    except Exception as e:
                        print(f"Error running sequence plugin {plugin_name}: {e}")


def run_tracking_plugin(exp) -> None:
    """Load and run plugins for sequence processing.
    """
    plugin_dir = Path(os.getcwd()) / "plugins"
    print(f"Plugin directory: {plugin_dir}")

    if str(plugin_dir) not in sys.path:
        sys.path.append(str(plugin_dir))

    for filename in os.listdir(plugin_dir):
        if filename.endswith(".py") and filename != "__init__.py":
            plugin_name = filename[:-3]
            if plugin_name == exp.plugins.track_alg:
                try:
                    print(f"Loading plugin: {plugin_name}")
                    plugin = importlib.import_module(plugin_name)
                except ImportError as e:
                    print(f"Error loading {plugin_name}: {e}")
                    return

                if hasattr(plugin, "Tracking"):
                    print(f"Running sequence plugin: {exp.plugins.track_alg}")
                    try:
                        tracker = plugin.Tracking(exp=exp)
                        tracker.do_tracking()
                    except Exception as e:
                        print(f"Error running sequence plugin {plugin_name}: {e}")



def py_sequence_loop(exp) -> None:
    """Run a sequence of detection, stereo-correspondence, and determination.
    """
    n_cams, cpar, spar, vpar, tpar, cals = (
        exp.n_cams,
        exp.cpar,
        exp.spar,
        exp.vpar,
        exp.tpar,
        exp.cals,
    )

    existing_target = exp.pm.get_parameter('pft_version').get('Existing_Target', False)

    first_frame = spar.get_first()
    last_frame = spar.get_last()
    print(f" From {first_frame = } to {last_frame = }")

    for frame in range(first_frame, last_frame + 1):
        detections = []
        corrected = []
        for i_cam in range(n_cams):
            base_image_name = spar.get_img_base_name(i_cam)
            if existing_target:
                targs = read_targets(base_image_name, frame)
            else:
                imname = Path(base_image_name % frame)
                if not imname.exists():
                    raise FileNotFoundError(f"{imname} does not exist")
                else:
                    img = imread(imname)
                    if img.ndim > 2:
                        img = rgb2gray(img)

                    if img.dtype != np.uint8:
                        img = img_as_ubyte(img)

                if exp.pm.get_parameter('ptv').get('inverse', False):
                    print("Invert image")
                    img = negative(img)

                masking_params = exp.pm.get_parameter('masking')
                if masking_params and masking_params.get('mask_flag', False):
                    try:
                        background_name = (
                            masking_params['mask_base_name']
                            % (i_cam + 1)
                        )
                        background = imread(background_name)
                        img = np.clip(img - background, 0, 255).astype(np.uint8)

                    except (ValueError, FileNotFoundError):
                        print("failed to read the mask")

                high_pass = simple_highpass(img, cpar)
                targs = target_recognition(high_pass, tpar, i_cam, cpar)

            targs.sort_y()
            detections.append(targs)
            masked_coords = MatchedCoords(targs, cpar, cals[i_cam])
            pos, _ = masked_coords.as_arrays()
            corrected.append(masked_coords)

        sorted_pos, sorted_corresp, _ = correspondences(
            detections, corrected, cals, vpar, cpar
        )

        for i_cam in range(n_cams):
            base_name = spar.get_img_base_name(i_cam)
            write_targets(detections[i_cam], base_name, frame)

        print(
            "Frame "
            + str(frame)
            + " had "
            + repr([s.shape[1] for s in sorted_pos])
            + " correspondences."
        )

        sorted_pos = np.concatenate(sorted_pos, axis=1)
        sorted_corresp = np.concatenate(sorted_corresp, axis=1)

        flat = np.array(
            [corrected[i].get_by_pnrs(sorted_corresp[i]) for i in range(len(cals))]
        )
        pos, _ = point_positions(flat.transpose(1, 0, 2), cpar, cals, vpar)

        if len(cals) < 4:
            print_corresp = -1 * np.ones((4, sorted_corresp.shape[1]))
            print_corresp[: len(cals), :] = sorted_corresp
        else:
            print_corresp = sorted_corresp

        rt_is_filename = default_naming["corres"].decode()
        rt_is_filename = f"{rt_is_filename}.{frame}"
        with open(rt_is_filename, "w", encoding="utf8") as rt_is:
            rt_is.write(str(pos.shape[0]) + "\n")
            for pix, pt in enumerate(pos):
                pt_args = (pix + 1,) + tuple(pt) + tuple(print_corresp[:, pix])
                rt_is.write("%4d %9.3f %9.3f %9.3f %4d %4d %4d %4d\n" % pt_args)


def py_trackcorr_init(exp):
    """Reads all the necessary stuff into Tracker"""

    for cam_id in range(exp.cpar.get_num_cams()):
        img_base_name = exp.spar.get_img_base_name(cam_id)
        short_name = Path(img_base_name).parent / f'cam{cam_id+1}.'
        print(f" Renaming {img_base_name} to {short_name} before C library tracker")
        exp.spar.set_img_base_name(cam_id, str(short_name))

    tracker = Tracker(
        exp.cpar, exp.vpar, exp.track_par, exp.spar, exp.cals, default_naming
    )

    return tracker


def py_trackcorr_loop():
    """Supposedly returns some lists of the linked targets at every step of a tracker"""
    pass


def py_traject_loop():
    """Used to plot trajectories after the full run
    """


# ------- Utilities ----------#


def py_rclick_delete(x: int, y: int, n: int) -> None:
    """Delete clicked points (stub function).
    """
    pass


def py_get_pix_N(x: int, y: int, n: int) -> Tuple[List[int], List[int]]:
    """Get pixel coordinates (stub function).
    """
    return [], []


def py_get_pix(
    x: List[List[int]], y: List[List[int]]
) -> Tuple[List[List[int]], List[List[int]]]:
    """Get target positions (stub function).
    """
    return x, y


def py_calibration(selection, exp):
    """Calibration
    """
    if selection == 1:
        pass

    if selection == 2:
        pass

    if selection == 9:
        pass

    if selection == 10:
        from optv.tracking_framebuf import Frame
        
        num_cams = exp.cpar.get_num_cams()
        calibs = _read_calibrations(exp.cpar, num_cams)

        targ_files = [
            exp.spar.get_img_base_name(c).split("%d")[0].encode('utf-8')
            for c in range(num_cams)
        ]
        
        orient_params = exp.pm.get_parameter('orient')
        shaking_params = exp.pm.get_parameter('shaking')
        
        flags = [name for name in NAMES if orient_params.get(name) == 1]
        all_known = []
        all_detected = [[] for c in range(num_cams)]

        for frm_num in range(shaking_params['shaking_first_frame'], shaking_params['shaking_last_frame'] + 1):
            frame = Frame(
                exp.cpar.get_num_cams(),
                corres_file_base=("res/rt_is").encode('utf-8'),
                linkage_file_base=("res/ptv_is").encode('utf-8'),
                target_file_base=targ_files,
                frame_num=frm_num,
            )

            all_known.append(frame.positions())
            for cam in range(num_cams):
                all_detected[cam].append(frame.target_positions_for_camera(cam))

        all_known = np.vstack(all_known)

        targ_ix_all = []
        residuals_all = []
        targs_all = []
        for cam in range(num_cams):
            detects = np.vstack(all_detected[cam])
            assert detects.shape[0] == all_known.shape[0]

            have_targets = ~np.isnan(detects[:, 0])
            used_detects = detects[have_targets, :]
            used_known = all_known[have_targets, :]

            targs = TargetArray(len(used_detects))

            for tix in range(len(used_detects)):
                targ = targs[tix]
                targ.set_pnr(tix)
                targ.set_pos(used_detects[tix])

            residuals = full_scipy_calibration(
                calibs[cam], used_known, targs, exp.cpar, flags=flags
            )
            print(f"After scipy full calibration, {np.sum(residuals**2)}")

            print(("Camera %d" % (cam + 1)))
            print((calibs[cam].get_pos()))
            print((calibs[cam].get_angles()))

            ori_filename = exp.cpar.get_cal_img_base_name(cam)
            addpar_filename = ori_filename + ".addpar"
            ori_filename = ori_filename + ".ori"
            calibs[cam].write(ori_filename.encode('utf-8'), addpar_filename.encode('utf-8'))

            targ_ix = [t.pnr() for t in targs if t.pnr() != -999]

            targs_all.append(targs)
            targ_ix_all.append(targ_ix)
            residuals_all.append(residuals)

        print("End calibration with particles")
        return targs_all, targ_ix_all, residuals_all


def read_targets(file_base: str, frame: int = 123456789) -> TargetArray:
    """Read targets from a file."""
    filename = file_base_to_filename(file_base, frame)
    print(f" filename: {filename}")

    try:
        with open(filename, "r", encoding="utf-8") as file:
            num_targets = int(file.readline().strip())
            targs = TargetArray(num_targets)

            for tix in range(num_targets):
                line = file.readline().strip().split()

                if len(line) != 8:
                    raise ValueError(f"Bad format for file: {filename}")

                targ = targs[tix]
                targ.set_pnr(int(line[0]))
                targ.set_pos([float(line[1]), float(line[2])])
                targ.set_pixel_counts(int(line[3]), int(line[4]), int(line[5]))
                targ.set_sum_grey_value(int(line[6]))
                targ.set_tnr(int(line[7]))

    except IOError as err:
        print(f"Can't open targets file: {filename}")
        raise err

    return targs


def write_targets(targets: TargetArray, file_base: str, frame: int = 123456789) -> bool:
    """Write targets to a file."""
    success = False
    filename = file_base_to_filename(file_base, frame)
    num_targets = len(targets)

    try:
        target_arr = np.array(
            [
                ([t.pnr(), *t.pos(), *t.count_pixels(), t.sum_grey_value(), t.tnr()])
                for t in targets
            ]
        )
        np.savetxt(
            filename,
            target_arr,
            fmt="%4d %9.4f %9.4f %5d %5d %5d %5d %5d",
            header=f"{num_targets}",
            comments="",
        )
        success = True
    except IOError:
        print(f"Can't open targets file: {filename}")

    return success


def file_base_to_filename(file_base, frame):
    """Convert file base name to a filename"""
    file_base = os.path.splitext(file_base)[0]
    file_base = re.sub(r"_\d*d", "", file_base)
    if re.search(r"%\d*d", file_base):
        _ = re.sub(r"%\d*d", "%04d", file_base)
        filename = Path(f"{_ % frame}_targets")
    else:
        filename = Path(f"{file_base}.{frame:04d}_targets")

    return filename


def read_rt_is_file(filename) -> List[List[float]]:
    """Read data from an rt_is file and return the parsed values."""
    try:
        with open(filename, "r", encoding="utf-8") as file:
            num_rows = int(file.readline().strip())
            if num_rows == 0:
                raise ValueError("Failed to read the number of rows")

            data = []
            for _ in range(num_rows):
                line = file.readline().strip()
                if not line:
                    break

                values = line.split()
                if len(values) != 8:
                    raise ValueError("Incorrect number of values in line")

                x = float(values[1])
                y = float(values[2])
                z = float(values[3])
                p1 = int(values[4])
                p2 = int(values[5])
                p3 = int(values[6])
                p4 = int(values[7])

                data.append([x, y, z, p1, p2, p3, p4])

            return data

    except IOError as e:
        print(f"Can't open ascii file: {filename}")
        raise e


def full_scipy_calibration(
    cal: Calibration, XYZ: np.ndarray, targs: TargetArray, cpar: ControlParams, flags=[]
):
    """Full calibration using scipy.optimize"""
    from optv.transforms import convert_arr_metric_to_pixel
    from optv.imgcoord import image_coordinates

    def _residuals_k(x, cal, XYZ, xy, cpar):
        cal.set_radial_distortion(x)
        targets = convert_arr_metric_to_pixel(
            image_coordinates(XYZ, cal, cpar.get_multimedia_params()), cpar
        )
        xyt = np.array([t.pos() if t.pnr() != -999 else [np.nan, np.nan] for t in xy])
        residuals = np.nan_to_num(xyt - targets)
        return np.sum(residuals**2)

    def _residuals_p(x, cal, XYZ, xy, cpar):
        cal.set_decentering(x)
        targets = convert_arr_metric_to_pixel(
            image_coordinates(XYZ, cal, cpar.get_multimedia_params()), cpar
        )
        xyt = np.array([t.pos() if t.pnr() != -999 else [np.nan, np.nan] for t in xy])
        residuals = np.nan_to_num(xyt - targets)
        return np.sum(residuals**2)

    def _residuals_s(x, cal, XYZ, xy, cpar):
        cal.set_affine_trans(x)
        targets = convert_arr_metric_to_pixel(
            image_coordinates(XYZ, cal, cpar.get_multimedia_params()), cpar
        )
        xyt = np.array([t.pos() if t.pnr() != -999 else [np.nan, np.nan] for t in xy])
        residuals = np.nan_to_num(xyt - targets)
        return np.sum(residuals**2)

    def _residuals_combined(x, cal, XYZ, xy, cpar):
        cal.set_radial_distortion(x[:3])
        cal.set_decentering(x[3:5])
        cal.set_affine_trans(x[5:])

        targets = convert_arr_metric_to_pixel(
            image_coordinates(XYZ, cal, cpar.get_multimedia_params()), cpar
        )
        xyt = np.array([t.pos() if t.pnr() != -999 else [np.nan, np.nan] for t in xy])
        residuals = np.nan_to_num(xyt - targets)
        return residuals

    if any(flag in flags for flag in ["k1", "k2", "k3"]):
        sol = minimize(
            _residuals_k,
            cal.get_radial_distortion(),
            args=(cal, XYZ, targs, cpar),
            method="Nelder-Mead",
            tol=1e-11,
            options={"disp": True},
        )
        radial = sol.x
        cal.set_radial_distortion(radial)
    else:
        radial = cal.get_radial_distortion()

    if any(flag in flags for flag in ["p1", "p2"]):
        sol = minimize(
            _residuals_p,
            cal.get_decentering(),
            args=(cal, XYZ, targs, cpar),
            method="Nelder-Mead",
            tol=1e-11,
            options={"disp": True},
        )
        decentering = sol.x
        cal.set_decentering(decentering)
    else:
        decentering = cal.get_decentering()

    if any(flag in flags for flag in ["scale", "shear"]):
        sol = minimize(
            _residuals_s,
            cal.get_affine(),
            args=(cal, XYZ, targs, cpar),
            method="Nelder-Mead",
            tol=1e-11,
            options={"disp": True},
        )
        affine = sol.x
        cal.set_affine_trans(affine)

    else:
        affine = cal.get_affine()

    residuals = _residuals_combined(
        np.r_[radial, decentering, affine], cal, XYZ, targs, cpar
    )

    residuals /= 100

    return residuals
