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
from optv.orientation import dumbbell_target_func
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
from optv.transforms import convert_arr_pixel_to_metric

"""
example from Tracker documentation: 
        dict naming - a dictionary with naming rules for the frame buffer 
            files. Keys: 'corres', 'linkage', 'prio'. Values can be either
            strings or bytes. Strings will be automatically encoded to UTF-8 bytes.
            If None, uses default_naming.

    default_naming = {
        'corres': b'res/rt_is',
        'linkage': b'res/ptv_is',
        'prio': b'res/added'
    }            
"""

# PyPTV imports
from pyptv.parameter_manager import ParameterManager

# Constants
NAMES = ["cc", "xh", "yh", "k1", "k2", "k3", "p1", "p2", "scale", "shear"]
DEFAULT_FRAME_NUM = 123456789
DEFAULT_HIGHPASS_FILTER_SIZE = 25
DEFAULT_NO_FILTER = 0
SHORT_BASE = "cam"  # Use this as the short base for camera file naming



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


def _populate_cpar(ptv_params: dict, num_cams: int) -> ControlParams:
    """Populate a ControlParams object from a dictionary containing full parameters.
    
    Args:
        params: Full parameter dictionary with global num_cams and ptv section
    """
    # ptv_params = params.get('ptv', {})

    img_cal_list = ptv_params.get('img_cal', [])
    if len([x for x in img_cal_list if x is not None]) < num_cams:
        raise ValueError("img_cal_list is too short")
    
    cpar = ControlParams(num_cams)
    # Set required parameters directly from the dictionary, no defaults
    cpar.set_image_size((ptv_params['imx'], ptv_params['imy']))
    cpar.set_pixel_size((ptv_params['pix_x'], ptv_params['pix_y']))
    cpar.set_hp_flag(ptv_params['hp_flag'])
    cpar.set_allCam_flag(ptv_params['allcam_flag'])
    cpar.set_tiff_flag(ptv_params['tiff_flag'])
    cpar.set_chfield(ptv_params['chfield'])

    mm_params = cpar.get_multimedia_params()
    mm_params.set_n1(ptv_params['mmp_n1'])
    mm_params.set_layers([ptv_params['mmp_n2']], [ptv_params['mmp_d']])
    mm_params.set_n3(ptv_params['mmp_n3'])

    img_cal_list = ptv_params['img_cal']
    
    for i in range(num_cams):  # Use global num_cams
        cpar.set_cal_img_base_name(i, img_cal_list[i])
    return cpar

def _populate_spar(seq_params: dict, num_cams: int) -> SequenceParams:
    """Populate a SequenceParams object from a dictionary.
    
    Raises ValueError if required sequence parameters are missing.
    No default values are provided to avoid silent failures.
    """
    required_params = ['first', 'last', 'base_name']
    missing_params = [param for param in required_params if param not in seq_params]
    
    if missing_params:
        raise ValueError(f"Missing required sequence parameters: {missing_params}. "
                        f"Available parameters: {list(seq_params.keys())}")
    
    base_name_list = seq_params['base_name']

    if len([x for x in base_name_list if x is not None]) < num_cams:
        raise ValueError(f"base_name_list length ({len(base_name_list)}) does not match num_cams ({num_cams})")

    spar = SequenceParams(num_cams=num_cams)
    spar.set_first(seq_params['first'])
    spar.set_last(seq_params['last'])
    
    # Set base names for each camera
    for i in range(num_cams):
        spar.set_img_base_name(i, base_name_list[i])
    
    return spar

def _populate_vpar(crit_params: dict) -> VolumeParams:
    """Populate a VolumeParams object from a dictionary."""
    vpar = VolumeParams()
    vpar.set_X_lay(crit_params['X_lay'])
    vpar.set_Zmin_lay(crit_params['Zmin_lay'])
    vpar.set_Zmax_lay(crit_params['Zmax_lay'])
    
    # Set correspondence parameters
    vpar.set_eps0(crit_params['eps0'])
    vpar.set_cn(crit_params['cn'])
    vpar.set_cnx(crit_params['cnx'])
    vpar.set_cny(crit_params['cny'])
    vpar.set_csumg(crit_params['csumg'])
    vpar.set_corrmin(crit_params['corrmin'])
    
    return vpar

def _populate_track_par(track_params: dict) -> TrackingParams:
    """Populate a TrackingParams object from a dictionary.
    
    Raises ValueError if required tracking parameters are missing.
    No default values are provided to avoid silent tracking failures.
    """
    required_params = ['dvxmin', 'dvxmax', 'dvymin', 'dvymax', 'dvzmin', 'dvzmax', 'angle', 'dacc', 'flagNewParticles']
    missing_params = [param for param in required_params if param not in track_params]
    
    if missing_params:
        raise ValueError(f"Missing required tracking parameters: {missing_params}. "
                        f"Available parameters: {list(track_params.keys())}")
    
    track_par = TrackingParams()
    track_par.set_dvxmin(track_params['dvxmin'])
    track_par.set_dvxmax(track_params['dvxmax'])
    track_par.set_dvymin(track_params['dvymin'])
    track_par.set_dvymax(track_params['dvymax'])
    track_par.set_dvzmin(track_params['dvzmin'])
    track_par.set_dvzmax(track_params['dvzmax'])
    track_par.set_dangle(track_params['angle'])
    track_par.set_dacc(track_params['dacc'])
    track_par.set_add(track_params['flagNewParticles'])
    return track_par

def _populate_tpar(targ_params: dict, num_cams: int) -> TargetParams:
    """Populate a TargetParams object from a dictionary."""
    # targ_params = params.get('targ_rec', {})
    
    # Get global num_cams - the single source of truth
    # num_cams = params.get('num_cams', 0)
    
    tpar = TargetParams(num_cams)
    # Handle both 'targ_rec' and 'detect_plate' parameter variants
    if 'targ_rec' in targ_params:
        params = targ_params['targ_rec']
        tpar.set_grey_thresholds(params['gvthres'])
        tpar.set_pixel_count_bounds((params['nnmin'], params['nnmax']))
        tpar.set_xsize_bounds((params['nxmin'], params['nxmax']))
        tpar.set_ysize_bounds((params['nymin'], params['nymax']))
        tpar.set_min_sum_grey(params['sumg_min'])
        tpar.set_max_discontinuity(params['disco'])
    elif 'detect_plate' in targ_params:
        params = targ_params['detect_plate']
        # Convert detect_plate keys to TargetParams fields
        # Ensure all required grey thresholds are present
        required_gvth_keys = ['gvth_1', 'gvth_2', 'gvth_3', 'gvth_4']
        missing_keys = [k for k in required_gvth_keys if k not in params]
        if missing_keys:
            raise ValueError(f"Missing required grey threshold keys in detect_plate: {missing_keys}")
        tpar.set_grey_thresholds([
            params['gvth_1'],
            params['gvth_2'],
            params['gvth_3'],
            params['gvth_4'],
        ])
        # Remove default values - all parameters must be explicitly provided
        required_detect_keys = ['min_npix', 'max_npix', 'min_npix_x', 'max_npix_x', 
                               'min_npix_y', 'max_npix_y', 'sum_grey', 'tol_dis']
        missing_detect_keys = [k for k in required_detect_keys if k not in params]
        if missing_detect_keys:
            raise ValueError(f"Missing required detect_plate keys: {missing_detect_keys}")
            
        tpar.set_pixel_count_bounds((params['min_npix'], params['max_npix']))
        tpar.set_xsize_bounds((params['min_npix_x'], params['max_npix_x']))
        tpar.set_ysize_bounds((params['min_npix_y'], params['max_npix_y']))
        tpar.set_min_sum_grey(params['sum_grey'])
        tpar.set_max_discontinuity(params['tol_dis'])
    else:
        raise ValueError("Target parameters must contain either 'targ_rec' or 'detect_plate' section.")
    return tpar

def _read_calibrations(cpar: ControlParams, num_cams: int) -> List[Calibration]:
    """Read calibration files for all cameras.
    
    Returns empty/default calibrations if files don't exist, which is normal
    for the calibration GUI before calibrations have been created.
    """
    cals = []
    for i_cam in range(num_cams):
        cal = Calibration()
        base_name = cpar.get_cal_img_base_name(i_cam)
        ori_file = base_name + ".ori"
        addpar_file = base_name + ".addpar"

        # Check if calibration files exist and are readable
        ori_exists = os.path.isfile(ori_file) and os.access(ori_file, os.R_OK)
        addpar_exists = os.path.isfile(addpar_file) and os.access(addpar_file, os.R_OK)
        
        if ori_exists and addpar_exists:
            # Both files exist, load them
            cal.from_file(ori_file, addpar_file)
            print(f"Loaded calibration for camera {i_cam + 1} from {ori_file}")
        else:
            # Files don't exist yet - this is normal for calibration GUI
            # Create default/empty calibration
            print(f"Calibration files not found for camera {i_cam + 1} - using defaults")
            print(f"  Missing: {ori_file if not ori_exists else ''} {addpar_file if not addpar_exists else ''}")
            
        cals.append(cal)

    return cals


def py_start_proc_c(
    pm: ParameterManager,
) -> Tuple[
    ControlParams,
    SequenceParams,
    VolumeParams,
    TrackingParams,
    TargetParams,
    List[Calibration],
    dict,
]:
    """Read all parameters needed for processing using ParameterManager."""
    try:
        params = pm.parameters
        num_cams = pm.num_cams

        cpar = _populate_cpar(params['ptv'], num_cams)
        spar = _populate_spar(params['sequence'], num_cams)
        vpar = _populate_vpar(params['criteria'])
        track_par = _populate_track_par(params['track'])

        # Create a dict that contains targ_rec for _populate_tpar
        # Use targ_rec instead of detect_plate to match manual GUI operations
        target_params_dict = {'targ_rec': params['targ_rec']}
        tpar = _populate_tpar(target_params_dict, num_cams)

        epar = params.get('examine')
        
        cals = _read_calibrations(cpar, num_cams)

        return cpar, spar, vpar, track_par, tpar, cals, epar

    except IOError as e:
        raise IOError(f"Failed to read parameter files: {e}")


def py_pre_processing_c(
        num_cams: int,
        list_of_images: List[np.ndarray], 
        ptv_params: dict, 
) -> List[np.ndarray]:
    """Apply pre-processing to a list of images.
    """
    # num_cams = len(list_of_images)
    cpar = _populate_cpar(ptv_params, num_cams)
    processed_images = []
    for i, img in enumerate(list_of_images):
        img_lp = img.copy() 
        processed_images.append(simple_highpass(img_lp, cpar))

    return processed_images


def py_detection_proc_c(
    num_cams: int,
    list_of_images: List[np.ndarray],
    ptv_params: dict,
    target_params: dict,
    existing_target: bool = False,
) -> Tuple[List[TargetArray], List[MatchedCoords]]:
    """Detect targets in a list of images."""
    # num_cams = len(ptv_params.get('img_cal', []))
    
    if len(list_of_images) != num_cams:
        raise ValueError(f"Number of images ({len(list_of_images)}) must match number of cameras ({num_cams})")

    cpar = _populate_cpar(ptv_params, num_cams)
    
    # Create a dict that contains targ_rec for _populate_tpar
    # target_params_dict = {'targ_rec': target_params}
    tpar = _populate_tpar(target_params, num_cams)
    
    cals = _read_calibrations(cpar, num_cams)

    detections = []
    corrected = []

    for i_cam, img in enumerate(list_of_images):
        if existing_target:
            raise NotImplementedError("Existing targets are not implemented")
        else:
            im = img.copy()
            targs = target_recognition(im, tpar, i_cam, cpar)

        targs.sort_y()
        # print(f"Camera {i_cam} detected {len(targs)} targets.")
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

    # img_base_names = [exp.spar.get_img_base_name(i) for i in range(exp.num_cams)]
    short_file_bases = exp.target_filenames
    print(f"short_file_bases: {short_file_bases}")

    for i_cam in range(exp.num_cams):
        write_targets(exp.detections[i_cam], short_file_bases[i_cam], frame)
    else:
        print("Warning: No sequence parameters found, skipping target writing")

    print(
        "Frame "
        + str(frame)
        + " had "
        + repr([s.shape[1] for s in sorted_pos])
        + " correspondences."
    )
    
    return sorted_pos, sorted_corresp, num_targs


def py_determination_proc_c(
    num_cams: int,
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
        [corrected[i].get_by_pnrs(concatenated_corresp[i]) for i in range(num_cams)]
    )

    pos, _ = point_positions(flat.transpose(1, 0, 2), cpar, cals, vpar)

    if num_cams < 4:
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

    # Check if plugin directory exists
    if not plugin_dir.exists():
        raise FileNotFoundError(f"Plugin directory not found: {plugin_dir}")

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

    # Check if plugin directory exists
    if not plugin_dir.exists():
        raise FileNotFoundError(f"Plugin directory not found: {plugin_dir}")

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
                    print(f"Running tracking plugin: {exp.plugins.track_alg}")
                    try:
                        tracker = plugin.Tracking(exp=exp)
                        tracker.do_tracking()
                    except Exception as e:
                        print(f"Error running tracking plugin {plugin_name}: {e}")



def py_sequence_loop(exp) -> None:
    """Run a sequence of detection, stereo-correspondence, and determination.
    
    Args:
        exp: Either an Experiment object with pm attribute,
             or a MainGUI object with exp1.pm and cached parameter objects
    """
    
    # Handle both Experiment objects and MainGUI objects
    if hasattr(exp, 'pm'):
        # Traditional experiment object
        pm = exp.pm
        num_cams = pm.num_cams
        cpar = exp.cpar
        spar = exp.spar
        vpar = exp.vpar
        tpar = exp.tpar
        cals = exp.cals
    elif hasattr(exp, 'exp1') and hasattr(exp.exp1, 'pm'):
        # MainGUI object - ensure parameter objects are initialized
        pm = exp.exp1.pm
        num_cams = exp.num_cams
        cpar = exp.cpar
        spar = exp.spar
        vpar = exp.vpar
        tpar = exp.tpar
        cals = exp.cals
    else:
        raise ValueError("Object must have either pm or exp1.pm attribute")

    existing_target = pm.get_parameter('pft_version').get('Existing_Target', False)

    first_frame = spar.get_first()
    last_frame = spar.get_last()
    # Generate short_file_bases once per experiment
    img_base_names = [spar.get_img_base_name(i) for i in range(num_cams)]
    short_file_bases = exp.target_filenames

    for frame in range(first_frame, last_frame + 1):
        detections = []
        corrected = []
        for i_cam in range(num_cams):
            if existing_target:
                targs = read_targets(short_file_bases[i_cam], frame)
            else:
                imname = Path(img_base_names[i_cam] % frame)
                if not imname.exists():
                    raise FileNotFoundError(f"{imname} does not exist")
                else:
                    img = imread(imname)
                    if img.ndim > 2:
                        img = rgb2gray(img)
                    if img.dtype != np.uint8:
                        img = img_as_ubyte(img)
                if pm.get_parameter('ptv').get('inverse', False):
                    print("Invert image")
                    img = negative(img)
                masking_params = pm.get_parameter('masking')
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

            if len(targs) > 0:
                targs.sort_y()

            detections.append(targs)
            matched_coords = MatchedCoords(targs, cpar, cals[i_cam])
            pos, _ = matched_coords.as_arrays()
            corrected.append(matched_coords)

        # AFter we finished all targs, we can move to correspondences    
        sorted_pos, sorted_corresp, _ = correspondences(
            detections, corrected, cals, vpar, cpar
        )
        for i_cam in range(num_cams):
            write_targets(detections[i_cam], short_file_bases[i_cam], frame)
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
            [corrected[i].get_by_pnrs(sorted_corresp[i]) for i in range(len(exp.cals))]
        )
        pos, _ = point_positions(flat.transpose(1, 0, 2), exp.cpar, exp.cals, exp.vpar)
        if len(exp.cals) < 4:
            print_corresp = -1 * np.ones((4, sorted_corresp.shape[1]))
            print_corresp[: len(exp.cals), :] = sorted_corresp
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

    # Generate short_file_bases once per experiment
    # img_base_names = [exp.spar.get_img_base_name(i) for i in range(exp.cpar.get_num_cams())]
    # exp.short_file_bases = exp.target_filenames
    for cam_id, short_name in enumerate(exp.target_filenames):
        # print(f"Setting tracker image base name for cam {cam_id+1}: {Path(short_name).resolve()}")
        exp.spar.set_img_base_name(cam_id, str(Path(short_name).resolve())+'.')

    # print("exp.spar.img_base_names:", [exp.spar.get_img_base_name(i) for i in range(exp.cpar.get_num_cams())])

    # print(
    #     exp.track_par.get_dvxmin(), exp.track_par.get_dvxmax(),
    #     exp.track_par.get_dvymin(), exp.track_par.get_dvymax(),
    #     exp.track_par.get_dvzmin(), exp.track_par.get_dvzmax(),
    #     exp.track_par.get_dangle(), exp.track_par.get_dacc(),
    #     exp.track_par.get_add()
    # )
    
    print("Initializing Tracker with parameters:")
    tracker = Tracker(
        exp.cpar, exp.vpar, exp.track_par, exp.spar, exp.cals, default_naming
    )

    return tracker

# ------- Utilities ----------#


def py_get_pix(
    x: List[List[int]], y: List[List[int]]
) -> Tuple[List[List[int]], List[List[int]]]:
    """Get target positions (stub function).
    """
    return x, y


def py_calibration(selection, exp):
    """Calibration
    
    Args:
        selection: Calibration selection type
        exp: Either an Experiment object with pm attribute,
             or a MainGUI object with exp1.pm and cached parameter objects
    """
    if selection == 1:
        pass

    if selection == 2:
        pass

    if selection == 9:
        pass

    if selection == 12:
        """ Calibration with dumbbell ."""
        return calib_dumbbell(exp)

    if selection == 10:
        """ Calibration with particles ."""

        return calib_particles(exp)


def write_targets(targets: TargetArray, short_file_base: str, frame: int) -> bool:
    """Write targets to a file."""
    filename = f"{short_file_base}.{frame:04d}_targets"
    num_targets = len(targets)
    success = False
    if num_targets == 0:
        with open(filename, "w", encoding="utf-8") as file:
            file.write("0\n")
        return True  # No targets to write, but file created successfully

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
        print(f"Can't write to targets file: {filename}")
    return success

def read_targets(short_file_base: str, frame: int) -> TargetArray:
    """Read targets from a file."""
    filename = f"{short_file_base}.{frame:04d}_targets"
    print(f" Reading targets from: filename: {filename}")

    if not os.path.exists(filename):
        raise FileNotFoundError(f"Targets file does not exist: {filename}")

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


def extract_cam_ids(file_bases: list[str]) -> list[int]:
    """
    Given a list of file base strings, extract the camera identification number from each.
    The camera id is the digit or number that is the main difference between the names,
    typically close to 'cam', 'c', 'img', etc.
    Returns a list of integers, one for each file base.
    """
    # Try to find all numbers in each string, and their context
    if not file_bases:
        raise ValueError("file_bases list is empty")
    
    # If input is a string, convert to a list
    if isinstance(file_bases, str):
        file_bases = [file_bases]

    # Remove frame number patterns like %d, %04d, etc.
    clean_bases = [re.sub(r'%0?\d*d', '', s) for s in file_bases]
    file_bases = clean_bases

    # Helper to extract all (number, context) pairs from a string
    def extract_number_context(s):
        # Find all numbers with up to 4 chars before and after
        matches = []
        for m in re.finditer(r'([a-zA-Z]{0,4})?(\d+)', s):
            prefix = m.group(1) or ''
            number = m.group(2)
            start = m.start(2)
            matches.append((number, prefix.lower(), start))
        return matches

    # Build a list of all numbers and their context for each string
    all_matches = [extract_number_context(s) for s in file_bases]

    # Transpose to group by position in the list
    # Find which number position varies the most across the list
    # (i.e., the one that is different between the names)
    candidate_indices = []
    maxlen = max(len(m) for m in all_matches) if all_matches else 0
    for idx in range(maxlen):
        nums = []
        for m in all_matches:
            if len(m) > idx:
                nums.append(m[idx][0])
            else:
                nums.append(None)
        # Count unique numbers (ignoring None)
        unique = set(n for n in nums if n is not None)
        candidate_indices.append((idx, len(unique)))

    # Pick the index with the most unique numbers (should be the cam id)
    candidate_indices.sort(key=lambda x: -x[1])
    if not candidate_indices or candidate_indices[0][1] <= 1:
        # fallback: just use the last number in each string
        fallback_ids = []
        for idx, s in enumerate(file_bases):
            found = re.findall(r'(\d+)', s)
            if found:
                fallback_ids.append(int(found[-1]))
            else:
                # fallback to default SHORT_BASE+idx+1
                fallback_ids.append(None)
        # If any fallback_ids are None, use default SHORT_BASE+idx+1
        if any(x is None for x in fallback_ids):
            fallback_ids = list(range(1, len(file_bases)+1))
            print("fall back to default list", fallback_ids)
            
        return fallback_ids

    cam_idx = candidate_indices[0][0]

    # Now, for each string, get the number at cam_idx
    cam_ids = []
    for idx, m in enumerate(all_matches):
        if len(m) > cam_idx:
            cam_ids.append(int(m[cam_idx][0]))
        else:
            # fallback: last number or default SHORT_BASE+idx+1
            nums = re.findall(r'(\d+)', ''.join([x[0] for x in m]))
            if nums:
                cam_ids.append(int(nums[-1]))
            else:
                cam_ids.append(f"{SHORT_BASE}{idx+1}")
    # If any cam_ids are not int, fallback to default SHORT_BASE+idx+1
    if any(not isinstance(x, int) for x in cam_ids):
        cam_ids = list(range(1, len(file_bases)+1))
        print("Fallback to default list {cam_ids}")

    return cam_ids


def generate_short_file_bases(img_base_names: List[str]) -> List[str]:
    """
    Given a list of image base names (full paths) for all cameras, generate a list of short_file_base strings for targets.
    The short file base will be in the same directory as the original, but with the filename replaced by SHORT_BASE + index.
    """
    ids = extract_cam_ids(img_base_names)
    short_bases = []
    for idx, full_path in enumerate(img_base_names):
        parent = Path(full_path).parent
        short_name = f"{SHORT_BASE}{ids[idx]}"
        short_bases.append(str(parent / short_name))
    return short_bases


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


"""
Perform dumbbell calibration from existing target files, using a subset of
the camera set, assuming some cameras are known to have moved and some to have
remained relatively static (but we can alternate on subsequent runs).

Created on Tue Dec 15 13:39:40 2015
@author: yosef

Modified for PyPTV on 2025-08-01
@author: alexlib
"""

# These readers should go in a nice module, but I wait on Max to finish the 
# proper bindings.

def dumbbell_target_func(targets, cpar, calibs, db_length, db_weight):
    """
    Calculate the ray convergence error for a set of targets and calibrations.

    Arguments:
    targets : np.ndarray
        Array of shape (num_cams, num_targets, 2), where num_cams is the number of cameras,
        num_targets is the total number of dumbbell endpoints (should be even, typically 2 per frame),
        and 2 corresponds to the (x, y) metric coordinates for each target in each camera.
    cpar : ControlParams
        A ControlParams object describing the overall setting.
    calibs : list of Calibration
        An array of per-camera Calibration objects.
    db_length : float
        Expected distance between two dumbbell points.
    db_weight : float
        Weight of the distance error in the target function.

    Returns:
    float
        The weighted ray convergence + length error measure.
    """
    from optv.orientation import multi_cam_point_positions

    num_cams = cpar.get_num_cams()
    num_targs = targets.shape[1]
    multimed_pars = cpar.get_multimedia_params()

    # Prepare the result arrays
    res = [np.zeros((num_cams, 3)) for _ in range(2)]
    res_current = None
    dtot = 0.0
    len_err_tot = 0.0
    dist = 0.0

    # Iterate over pairs of targets
    if num_targs % 2 != 0:
        raise ValueError("Number of targets must be even for dumbbell calibration")
    
    # Process each target pair
    for pt in range(0, num_targs, 2):
        # For each pair of targets (dumbbell ends)
        # Get their 2D positions in all cameras for this pair
        pair_targets = targets[:, pt:pt+2, :]  # shape: (num_cams, 2, pos)
        # Compute their 3D positions using all cameras
        # Each column: [cam1_t1, cam2_t1, ..., camN_t1], [cam1_t2, ..., camN_t2]
        # So we need to transpose to (2, num_cams, pos)
        pair_targets = pair_targets.transpose(1, 0, 2)  # shape: (2, num_cams, pos)
        # Get 3D positions for each end
        xyz1, err1 = multi_cam_point_positions(pair_targets[0,np.newaxis], cpar, calibs)
        xyz2, err2 = multi_cam_point_positions(pair_targets[1,np.newaxis], cpar, calibs)
        # xyz1, xyz2 are (1, 3) arrays (single point)
        # Compute the distance between the two ends
        dist = np.linalg.norm(xyz1[0] - xyz2[0])
        # Accumulate the error between measured and expected dumbbell length
        len_err_tot += abs(dist - db_length)
        # Accumulate the ray convergence error (sum of distances from rays to intersection)
        # Use the error returned by point_positions
        dtot += err1 + err2


    # Calculate the total error
    len_err_tot /= 2.0  # since we counted pairs, divide by 2

    # Calculate the total error as a weighted sum of ray convergence and length error
    dtot /= num_targs / 2.0  # average over pairs
    if db_length <= 0:
        raise ValueError("Dumbbell length must be positive")
    
    if db_weight < 0:
        raise ValueError("Dumbbell weight must be non-negative")

    # Return the total error
    return dtot + db_weight * len_err_tot / (num_targs / 2.0)   



def calib_convergence(calib_vec, targets, calibs, active_cams, cpar,
    db_length, db_weight):
    """
    Mediated the ray_convergence function and the parameter format used by 
    SciPy optimization routines, by taking a vector of variable calibration
    parameters and pouring it into the Calibration objects understood by 
    OpenPTV.
    
    Arguments:
    calib_vec - 1D array. 3 elements: camera 1 position, 3 element: camera 1 
        angles, next 6 for camera 2 etc.
    targets - a (c,t,2) array, for t target metric positions in each of c 
        cameras.
    calibs - an array of per-camera Calibration objects. The permanent fields 
        are retained, the variable fields get overwritten.
    active_cams - a sequence of True/False values stating whether the 
        corresponding camera is free to move or just a parameter.
    cpar - a ControlParams object describing the overall setting.
    db_length - expected distance between two dumbbell points.
    db_weight - weight of the distance error in the target function.
    
    Returns:
    The weighted ray convergence + length error measure.
    """
    calib_pars = calib_vec.reshape(-1, 2, 3)
    
    for cam, cal in enumerate(calibs):
        if not active_cams[cam]:
            continue
        
        # Pop a parameters line:
        pars = calib_pars[0]
        calib_pars = calib_pars[1:]
        
        cal.set_pos(pars[0])
        cal.set_angles(pars[1])
    
    return dumbbell_target_func(targets, cpar, calibs, db_length, db_weight)


def calib_dumbbell(cal_gui)-> None:
    """Calibration with dumbbell targets.

    Args:
        exp: Either an Experiment object with pm attribute,
             or a MainGUI object with exp1.pm and cached parameter objects
    """
    pm = cal_gui.experiment.pm
    cpar, spar, vpar, track_par, tpar, cals, epar = py_start_proc_c(pm)
    num_cams = cpar.get_num_cams()
    target_filenames = pm.get_target_filenames()

    # Get dumbbell length from parameters (or set default)
    db_length = pm.get_parameter('dumbbell').get('dumbbell_scale')
    db_weight = pm.get_parameter('dumbbell').get('dumbbell_penalty_weight')

    # Get frame range
    first_frame = spar.get_first()
    last_frame = spar.get_last()

    num_frames = last_frame - first_frame + 1
    # all_targs = [[] for pt in range(num_frames*2)] # 2 targets per fram
    all_targs = []
    for frame in range(num_frames):
        frame_targets = []
        valid = True
        for cam in range(num_cams):
            targs = read_targets(target_filenames[cam], first_frame + frame)
            if len(targs) != 2:
                valid = False
                break
            frame_targets.append([targ.pos() for targ in targs])
        if valid:
            # Only add targets if all cameras have exactly two targets
            # for tix in range(2):
            #     all_targs[frame*2 + tix].extend([frame_targets[cam][tix] for cam in range(num_cams)])
            all_targs.append(frame_targets)
    
    all_targs = np.array(all_targs)
    assert(all_targs.shape[1] == num_cams and all_targs.shape[2] == 2)
    num_frames, n_cams, num_targs, num_pos = all_targs.shape
    all_targs = all_targs.transpose(1,0,2,3).reshape(n_cams, num_frames*num_targs, num_pos)

    all_targs = np.array([convert_arr_pixel_to_metric(np.array(targs), cpar) \
        for targs in all_targs])
    
    # Generate initial guess vector and bounds for optimization:
    active = np.ones(num_cams) # 1 means camera can move
    num_active = int(np.sum(active))
    calib_vec = np.empty((num_active, 2, 3))
    active_ptr = 0
    for cam in range(num_cams):
        if active[cam]:
            calib_vec[active_ptr,0] = cals[cam].get_pos()
            calib_vec[active_ptr,1] = cals[cam].get_angles()
            active_ptr += 1
        
        # Positions within a neighbourhood of the initial guess, so we don't 
        # converge to the trivial solution where all cameras are in the same 
        # place.
    calib_vec = calib_vec.flatten()
    
    # Test optimizer-ready target function:
    print("Initial values (1 row per camera, pos, then angle):")
    print(calib_vec.reshape(num_cams,-1))
    print("Current target function (to minimize):", end=' ')
    print(calib_convergence(calib_vec, all_targs, cals, active, cpar,
        db_length, db_weight))
    
    # Optimization:
    res = minimize(calib_convergence, calib_vec, 
                args=(all_targs, cals, active, cpar, db_length, db_weight),
                tol=1, options={'maxiter': 1000})
        
    print("Result of dumbbell calibration")
    print(res.x.reshape(num_cams,-1))
    print("Success:", res.success, res.message)
    print("Final target function:", end=' ')
    print(calib_convergence(res.x, all_targs, cals, active, cpar,
        db_length, db_weight))


    # convert calib_vec back to Calibration objects:
    calib_pars = res.x.reshape(-1, 2, 3)
    
    for cam, cal in enumerate(cals):
        if not active[cam]:
            continue
        
        # Pop a parameters line:
        pars = calib_pars[0]
        calib_pars = calib_pars[1:]
        
        cal.set_pos(pars[0])
        cal.set_angles(pars[1])


        # Write the calibration results to files:
        ori_filename = cpar.get_cal_img_base_name(cam)
        addpar_filename = ori_filename + ".addpar"
        ori_filename = ori_filename + ".ori"
        cal.write(ori_filename.encode('utf-8'), addpar_filename.encode('utf-8'))



def calib_particles(exp):
    """Calibration with particles."""

    from optv.tracking_framebuf import Frame
    
    # Handle both Experiment objects and MainGUI objects
    if hasattr(exp, 'pm'):
        # Traditional experiment object
        pm = exp.pm
        num_cams = pm.num_cams
        cpar = exp.cpar
        spar = exp.spar
        vpar = exp.vpar
        tpar = exp.tpar
        cals = exp.cals
    elif hasattr(exp, 'exp1') and hasattr(exp.exp1, 'pm'):
        # MainGUI object - ensure parameter objects are initialized
        pm = exp.exp1.pm
        num_cams = exp.num_cams
        cpar = exp.cpar
        spar = exp.spar
        vpar = exp.vpar
        tpar = exp.tpar
        cals = exp.cals
    else:
        raise ValueError("Object must have either pm or exp1.pm attribute")
    
    num_cams = cpar.get_num_cams()
    calibs = _read_calibrations(cpar, num_cams)

    targ_files = [
        spar.get_img_base_name(c).split("%d")[0].encode('utf-8')
        for c in range(num_cams)
    ]
    
    orient_params = pm.get_parameter('orient')
    shaking_params = pm.get_parameter('shaking')
    
    flags = [name for name in NAMES if orient_params.get(name) == 1]
    all_known = []
    all_detected = [[] for c in range(num_cams)]

    for frm_num in range(shaking_params['shaking_first_frame'], shaking_params['shaking_last_frame'] + 1):
        frame = Frame(
            cpar.get_num_cams(),
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