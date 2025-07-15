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


def _populate_cpar(ptv_params: dict, n_cam: int) -> ControlParams:
    """Populate a ControlParams object from a dictionary containing full parameters.
    
    Args:
        params: Full parameter dictionary with global n_cam and ptv section
    """
    # ptv_params = params.get('ptv', {})
    
    cpar = ControlParams(n_cam)
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
    
    if len(img_cal_list) != n_cam:
        raise ValueError("img_cal_list length does not match n_cam; check your Yaml file.")

    for i in range(n_cam):  # Use global n_cam
        cpar.set_cal_img_base_name(i, img_cal_list[i])
    return cpar

def _populate_spar(seq_params: dict, n_cam: int) -> SequenceParams:
    """Populate a SequenceParams object from a dictionary.
    
    Raises ValueError if required sequence parameters are missing.
    No default values are provided to avoid silent failures.
    """
    required_params = ['first', 'last', 'base_name']
    missing_params = [param for param in required_params if param not in seq_params]
    
    if missing_params:
        raise ValueError(f"Missing required sequence parameters: {missing_params}. "
                        f"Available parameters: {list(seq_params.keys())}")
    
    spar = SequenceParams(num_cams=n_cam)
    spar.set_first(seq_params['first'])
    spar.set_last(seq_params['last'])
    
    base_name_list = seq_params['base_name']
    if len(base_name_list) != n_cam:
        raise ValueError(f"base_name_list length ({len(base_name_list)}) does not match n_cam ({n_cam}); check your Yaml file.")
    
    for i in range(len(base_name_list)):
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

def _populate_tpar(targ_params: dict, n_cam: int) -> TargetParams:
    """Populate a TargetParams object from a dictionary."""
    # targ_params = params.get('targ_rec', {})
    
    # Get global n_cam - the single source of truth
    # n_cam = params.get('n_cam', 0)
    
    tpar = TargetParams(n_cam)
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

def _read_calibrations(cpar: ControlParams, n_cams: int) -> List[Calibration]:
    """Read calibration files for all cameras.
    
    Returns empty/default calibrations if files don't exist, which is normal
    for the calibration GUI before calibrations have been created.
    """
    cals = []
    for i_cam in range(n_cams):
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
    parameter_manager: "ParameterManager",
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
        params = parameter_manager.parameters
        n_cam = parameter_manager.n_cam

        ptv_params = params.get('ptv', {})
        cpar = _populate_cpar(ptv_params, n_cam)

        sequence_params = params.get('sequence', {})
        spar = _populate_spar(sequence_params, n_cam)

        volume_params = params.get('criteria', {})
        vpar = _populate_vpar(volume_params)

        track_params = params.get('track', {})
        track_par = _populate_track_par(track_params)

        # Create a dict that contains targ_rec for _populate_tpar
        # Use targ_rec instead of detect_plate to match manual GUI operations
        target_params_dict = {'targ_rec': params.get('targ_rec', {})}
        tpar = _populate_tpar(target_params_dict, n_cam)

        epar = params.get('examine', {})
        
        cals = _read_calibrations(cpar, n_cam)

        return cpar, spar, vpar, track_par, tpar, cals, epar

    except IOError as e:
        raise IOError(f"Failed to read parameter files: {e}")


def py_pre_processing_c(
        n_cam: int,
        list_of_images: List[np.ndarray], 
        ptv_params: dict, 
) -> List[np.ndarray]:
    """Apply pre-processing to a list of images.
    """
    # n_cam = len(list_of_images)
    cpar = _populate_cpar(ptv_params, n_cam)
    processed_images = []
    for i, img in enumerate(list_of_images):
        img_lp = img.copy() 
        processed_images.append(simple_highpass(img_lp, cpar))

    return processed_images


def py_detection_proc_c(
    n_cam: int,
    list_of_images: List[np.ndarray],
    ptv_params: dict,
    target_params: dict,
    existing_target: bool = False,
) -> Tuple[List[TargetArray], List[MatchedCoords]]:
    """Detect targets in a list of images."""
    # n_cam = len(ptv_params.get('img_cal', []))
    
    if len(list_of_images) != n_cam:
        raise ValueError(f"Number of images ({len(list_of_images)}) must match number of cameras ({n_cam})")

    cpar = _populate_cpar(ptv_params, n_cam)
    
    # Create a dict that contains targ_rec for _populate_tpar
    # target_params_dict = {'targ_rec': target_params}
    tpar = _populate_tpar(target_params, n_cam)
    
    cals = _read_calibrations(cpar, n_cam)

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

    # Get sequence parameters to write targets
    if hasattr(exp, 'spar') and exp.spar is not None:
        # Traditional experiment object with spar
        for i_cam in range(exp.n_cams):
            base_name = exp.spar.get_img_base_name(i_cam)
            write_targets(exp.detections[i_cam], base_name, frame)
    elif hasattr(exp, 'get_parameter'):
        # MainGUI object - get sequence parameters from ParameterManager
        seq_params = exp.get_parameter('sequence')
        if seq_params and 'base_name' in seq_params:
            for i_cam in range(exp.n_cams):
                base_name = seq_params['base_name'][i_cam]
                write_targets(exp.detections[i_cam], base_name, frame)
        else:
            print("Warning: No sequence parameters found, skipping target writing")
    else:
        print("Warning: No way to determine base names, skipping target writing")

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
                    print(f"Running sequence plugin: {exp.plugins.track_alg}")
                    try:
                        tracker = plugin.Tracking(exp=exp)
                        tracker.do_tracking()
                    except Exception as e:
                        print(f"Error running sequence plugin {plugin_name}: {e}")



def py_sequence_loop(exp) -> None:
    """Run a sequence of detection, stereo-correspondence, and determination.
    
    Args:
        exp: Either an Experiment object with parameter_manager attribute,
             or a MainGUI object with exp1.parameter_manager and cached parameter objects
    """
    
    # Handle both Experiment objects and MainGUI objects
    if hasattr(exp, 'parameter_manager'):
        # Traditional experiment object
        parameter_manager = exp.parameter_manager
        n_cams = exp.n_cams
        cpar = exp.cpar
        spar = exp.spar
        vpar = exp.vpar
        tpar = exp.tpar
        cals = exp.cals
    elif hasattr(exp, 'exp1') and hasattr(exp.exp1, 'parameter_manager'):
        # MainGUI object - ensure parameter objects are initialized
        exp.ensure_parameter_objects()
        parameter_manager = exp.exp1.parameter_manager
        n_cams = exp.n_cams
        cpar = exp.cpar
        spar = exp.spar
        vpar = exp.vpar
        tpar = exp.tpar
        cals = exp.cals
    else:
        raise ValueError("Object must have either parameter_manager or exp1.parameter_manager attribute")

    existing_target = parameter_manager.get_parameter('pft_version', {}).get('Existing_Target', False)

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

                if parameter_manager.get_parameter('ptv', {}).get('inverse', False):
                    print("Invert image")
                    img = negative(img)

                masking_params = parameter_manager.get_parameter('masking')
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
            # print(len(targs))
            detections.append(targs)
            matched_coords = MatchedCoords(targs, cpar, cals[i_cam])
            pos, _ = matched_coords.as_arrays()
            corrected.append(matched_coords)

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
    
    Args:
        selection: Calibration selection type
        exp: Either an Experiment object with parameter_manager attribute,
             or a MainGUI object with exp1.parameter_manager and cached parameter objects
    """
    if selection == 1:
        pass

    if selection == 2:
        pass

    if selection == 9:
        pass

    if selection == 10:
        from optv.tracking_framebuf import Frame
        
        # Handle both Experiment objects and MainGUI objects
        if hasattr(exp, 'parameter_manager'):
            # Traditional experiment object
            parameter_manager = exp.parameter_manager
            cpar = exp.cpar
            spar = exp.spar
        elif hasattr(exp, 'exp1') and hasattr(exp.exp1, 'parameter_manager'):
            # MainGUI object - ensure parameter objects are initialized
            exp.ensure_parameter_objects()
            parameter_manager = exp.exp1.parameter_manager
            cpar = exp.cpar
            spar = exp.spar
        else:
            raise ValueError("Object must have either parameter_manager or exp1.parameter_manager attribute")
        
        num_cams = cpar.get_num_cams()
        calibs = _read_calibrations(cpar, num_cams)

        targ_files = [
            spar.get_img_base_name(c).split("%d")[0].encode('utf-8')
            for c in range(num_cams)
        ]
        
        orient_params = parameter_manager.get_parameter('orient')
        shaking_params = parameter_manager.get_parameter('shaking')
        
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
