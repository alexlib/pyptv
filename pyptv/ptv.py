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
from typing import List, Tuple, Dict, Optional, Union, Any, Callable

# Third-party imports
import numpy as np
from scipy.optimize import minimize
from skimage.io import imread
from skimage import img_as_ubyte
from skimage.color import rgb2gray

# OptV imports
from optv.calibration import Calibration
from optv.correspondences import correspondences, MatchedCoords
from optv.image_processing import preprocess_image
from optv.orientation import point_positions, full_calibration
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
from pyptv import parameters as par

# Constants
NAMES = ["cc", "xh", "yh", "k1", "k2", "k3", "p1", "p2", "scale", "shear"]
DEFAULT_FRAME_NUM = 123456789  # Default frame number instead of magic number 123456789
DEFAULT_HIGHPASS_FILTER_SIZE = 25  # Default size for highpass filter


def negative(img: np.ndarray) -> np.ndarray:
    """Convert an 8-bit image to its negative.

    Args:
        img: Input 8-bit image as numpy array

    Returns:
        Negative of the input image
    """
    return 255 - img


def simple_highpass(img: np.ndarray, cpar: ControlParams) -> np.ndarray:
    """Apply a simple highpass filter to an image using liboptv preprocess_image.

    Args:
        img: Input image as numpy array
        cpar: Control parameters

    Returns:
        Highpass filtered image
    """
    return preprocess_image(img, 0, cpar, DEFAULT_HIGHPASS_FILTER_SIZE)

def _read_calibrations(cpar: ControlParams, n_cams: int) -> List[Calibration]:
    """Read calibration files for all cameras.

    Args:
        cpar: Control parameters
        n_cams: Number of cameras

    Returns:
        List of Calibration objects, one for each camera

    Raises:
        IOError: If calibration files cannot be read
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


def py_start_proc_c(n_cams: int) -> Tuple[ControlParams, SequenceParams, VolumeParams,
                                    TrackingParams, TargetParams, List[Calibration],
                                    par.ExamineParams]:
    """Read all parameters needed for processing.

    This function reads all parameter files from the parameters directory and initializes
    the necessary objects for processing.

    Args:
        n_cams: Number of cameras

    Returns:
        Tuple containing:
            - cpar: Control parameters
            - spar: Sequence parameters
            - vpar: Volume parameters
            - track_par: Tracking parameters
            - tpar: Target parameters
            - cals: List of calibration objects
            - epar: Examine parameters

    Raises:
        IOError: If any parameter file cannot be read
    """
    # Define parameter file paths
    param_dir = Path("parameters")
    ptv_par_path = param_dir / "ptv.par"
    sequence_par_path = param_dir / "sequence.par"
    criteria_par_path = param_dir / "criteria.par"
    track_par_path = param_dir / "track.par"
    targ_rec_par_path = param_dir / "targ_rec.par"

    try:
        # Control parameters
        cpar = ControlParams(n_cams)
        cpar.read_control_par(str(ptv_par_path))

        # Sequence parameters
        spar = SequenceParams(num_cams=n_cams)
        spar.read_sequence_par(str(sequence_par_path), n_cams)

        # Volume parameters
        vpar = VolumeParams()
        vpar.read_volume_par(str(criteria_par_path))

        # Tracking parameters
        track_par = TrackingParams()
        track_par.read_track_par(str(track_par_path))

        # Target parameters
        tpar = TargetParams(n_cams)
        tpar.read(str(targ_rec_par_path))

        # Examine parameters (multiplane vs single plane calibration)
        epar = par.ExamineParams()
        epar.read()

        # Read calibration files
        cals = _read_calibrations(cpar, n_cams)

        return cpar, spar, vpar, track_par, tpar, cals, epar

    except IOError as e:
        raise IOError(f"Failed to read parameter files: {e}")


def py_pre_processing_c(list_of_images: List[np.ndarray], cpar: ControlParams) -> List[np.ndarray]:
    """Apply pre-processing to a list of images.

    Currently applies a highpass filter to each image, but could be extended
    with additional processing steps in the future.

    Args:
        list_of_images: List of input images as numpy arrays
        cpar: Control parameters

    Returns:
        List of processed images
    """
    processed_images = []
    for img in list_of_images:
        processed_images.append(simple_highpass(img, cpar))
    return processed_images


def py_detection_proc_c(list_of_images: List[np.ndarray],
                      cpar: ControlParams,
                      tpar: TargetParams,
                      cals: List[Calibration]) -> Tuple[List[TargetArray], List[MatchedCoords]]:
    """Detect targets in a list of images.

    This function performs target detection on each image and returns the detected
    targets and their corrected coordinates.

    Args:
        list_of_images: List of input images as numpy arrays
        cpar: Control parameters
        tpar: Target parameters
        cals: List of calibration objects

    Returns:
        Tuple containing:
            - detections: List of TargetArray objects with detected targets
            - corrected: List of MatchedCoords objects with corrected coordinates

    Raises:
        NotImplementedError: If Existing_Target is True (not implemented yet)
    """
    # Read PFT version parameters
    param_dir = Path("parameters")
    pft_version_params = par.PftVersionParams(path=param_dir)
    pft_version_params.read()
    existing_target = bool(pft_version_params.Existing_Target)

    detections = []
    corrected = []

    for i_cam, img in enumerate(list_of_images):
        if existing_target:
            raise NotImplementedError("Existing targets are not implemented")
        else:
            # Detect targets in the image
            targs = target_recognition(img, tpar, i_cam, cpar)

        # Sort targets by y-coordinate
        targs.sort_y()
        detections.append(targs)

        # Create matched coordinates
        mc = MatchedCoords(targs, cpar, cals[i_cam])
        corrected.append(mc)

    return detections, corrected


def py_correspondences_proc_c(exp):
    """Provides correspondences
    Inputs:
        exp = info.object from the pyptv_gui
    Outputs:
        quadruplets, ... : four empty lists filled later with the
    correspondences of quadruplets, triplets, pairs, and so on
    """

    frame = 123456789  # just a temporary workaround. todo: think how to write

    #        if any([len(det) == 0 for det in detections]):
    #            return False

    # Corresp. + positions.
    sorted_pos, sorted_corresp, num_targs = correspondences(
        exp.detections, exp.corrected, exp.cals, exp.vpar, exp.cpar)

    # Save targets only after they've been modified:
    for i_cam in range(exp.n_cams):
        base_name = exp.spar.get_img_base_name(i_cam)
        write_targets(exp.detections[i_cam], base_name, frame)


    print("Frame " + str(frame) + " had " +
          repr([s.shape[1] for s in sorted_pos]) + " correspondences.")

    return sorted_pos, sorted_corresp, num_targs


def py_determination_proc_c(n_cams: int,
                         sorted_pos: List[np.ndarray],
                         sorted_corresp: np.ndarray,
                         corrected: List[MatchedCoords]) -> None:
    """Calculate 3D positions from 2D correspondences and save to file.

    Args:
        n_cams: Number of cameras
        sorted_pos: List of sorted positions for each camera
        sorted_corresp: Array of correspondence indices
        corrected: List of corrected coordinates
    """
    # Get parameters
    cpar, _, vpar, _, _, cals, _ = py_start_proc_c(n_cams)

    # Concatenate sorted positions (distinction between quad/trip irrelevant here)
    sorted_pos = np.concatenate(sorted_pos, axis=1)
    sorted_corresp = np.concatenate(sorted_corresp, axis=1)

    # Get corrected coordinates by point numbers
    flat = np.array([
        corrected[i].get_by_pnrs(sorted_corresp[i]) for i in range(n_cams)
    ])

    # Calculate 3D positions
    pos, _ = point_positions(flat.transpose(1, 0, 2), cpar, cals, vpar)

    # Format correspondence array for printing
    if n_cams < 4:
        print_corresp = -1 * np.ones((4, sorted_corresp.shape[1]))
        print_corresp[:len(cals), :] = sorted_corresp
    else:
        print_corresp = sorted_corresp

    # Save positions to a temporary file
    fname = (default_naming["corres"].decode() + '.' + str(DEFAULT_FRAME_NUM)).encode()

    print(f'Prepared {fname} to write positions')

    try:
        with open(fname, "w", encoding='utf-8') as rt_is:
            print(f'Opened {fname}')
            rt_is.write(str(pos.shape[0]) + "\n")
            for pix, pt in enumerate(pos):
                pt_args = (pix + 1, ) + tuple(pt) + tuple(print_corresp[:, pix])
                rt_is.write("%4d %9.3f %9.3f %9.3f %4d %4d %4d %4d\n" % pt_args)
    except FileNotFoundError as e:
        print(f"Error writing to file {fname}: {e}")

def run_plugin(exp) -> None:
    """Load and run plugins for sequence processing.

    This function searches for plugins in the 'plugins' directory and runs the
    appropriate plugin based on the experiment configuration.

    Args:
        exp: Experiment object containing configuration
    """
    # Get the plugin directory path
    plugin_dir = Path(os.getcwd()) / 'plugins'
    print(f"Plugin directory: {plugin_dir}")

    # Add the plugins directory to sys.path so that Python can find the modules
    if str(plugin_dir) not in sys.path:
        sys.path.append(str(plugin_dir))

    # Iterate over the files in the 'plugins' directory
    for filename in os.listdir(plugin_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            # Get the plugin name without the '.py' extension
            plugin_name = filename[:-3]

            # Check if the plugin name matches the sequence_alg
            if plugin_name == exp.plugins.sequence_alg:
                # Dynamically import the plugin
                try:
                    print(f"Loading plugin: {plugin_name}")
                    plugin = importlib.import_module(plugin_name)
                except ImportError as e:
                    print(f"Error loading {plugin_name}: {e}")
                    print("Check for missing packages or syntax errors.")
                    return

                # Check if the plugin has a Sequence class
                if hasattr(plugin, 'Sequence'):
                    print(f"Running sequence plugin: {exp.plugins.sequence_alg}")
                    try:
                        # Create a Sequence instance and run it
                        sequence = plugin.Sequence(exp=exp)
                        sequence.do_sequence()
                    except Exception as e:
                        print(f"Error running sequence plugin {plugin_name}: {e}")



def py_sequence_loop(exp) -> None:
    """Run a sequence of detection, stereo-correspondence, and determination.

    This function processes a sequence of frames, performing detection, stereo-correspondence,
    and 3D position determination. It stores the results in cam#.XXX_targets and rt_is.XXX files.
    It's similar to running pyptv_batch.py without tracking.

    Args:
        exp: Experiment object containing configuration and parameters
    """

    # Sequence parameters

    n_cams, cpar, spar, vpar, tpar, cals = (
        exp.n_cams,
        exp.cpar,
        exp.spar,
        exp.vpar,
        exp.tpar,
        exp.cals,
    )

    # # Sequence parameters
    # spar = SequenceParams(num_cams=n_cams)
    # spar.read_sequence_par(b"parameters/sequence.par", n_cams)


    pftVersionParams = par.PftVersionParams(path=Path("parameters"))
    pftVersionParams.read()
    Existing_Target = np.bool8(pftVersionParams.Existing_Target)

    # sequence loop for all frames
    first_frame = spar.get_first()
    last_frame = spar.get_last()
    print(f" From {first_frame = } to {last_frame = }")

    for frame in range(first_frame, last_frame + 1):
        # print(f"processing {frame = }")

        detections = []
        corrected = []
        for i_cam in range(n_cams):
            base_image_name = spar.get_img_base_name(i_cam)
            if Existing_Target:
                targs = read_targets(base_image_name, frame)
            else:
                # imname = spar.get_img_base_name(i_cam) + str(frame).encode()

                # imname = Path(imname.replace('#',f'{frame}'))
                imname = Path(base_image_name % frame) # works with jumps from 1 to 10
                # print(f'Image name {imname}')

                if not imname.exists():
                    print(f"{imname} does not exist")
                else:
                    img = imread(imname)
                    if img.ndim > 2:
                        img = rgb2gray(img)

                    if img.dtype != np.uint8:
                        img = img_as_ubyte(img)
                # time.sleep(.1) # I'm not sure we need it here

                if 'exp1' in exp.__dict__:
                    if exp.exp1.active_params.m_params.Inverse:
                        print("Invert image")
                        img = 255 - img

                    if exp.exp1.active_params.m_params.Subtr_Mask:
                        # print("Subtracting mask")
                        try:
                            # background_name = exp.exp1.active_params.m_params.Base_Name_Mask.replace('#',str(i_cam))
                            background_name = exp.exp1.active_params.m_params.Base_Name_Mask % (i_cam + 1)
                            background = imread(background_name)
                            img = np.clip(img - background, 0, 255).astype(np.uint8)

                        except ValueError:
                            print("failed to read the mask")


                high_pass = simple_highpass(img, cpar)
                targs = target_recognition(high_pass, tpar, i_cam, cpar)

            targs.sort_y()
            detections.append(targs)
            masked_coords = MatchedCoords(targs, cpar, cals[i_cam])
            pos, _ = masked_coords.as_arrays()
            corrected.append(masked_coords)

        #        if any([len(det) == 0 for det in detections]):
        #            return False

        # Corresp. + positions.
        sorted_pos, sorted_corresp, _ = correspondences(
            detections, corrected, cals, vpar, cpar)

        # Save targets only after they've been modified:
        # this is a workaround of the proper way to construct _targets name
        for i_cam in range(n_cams):
            base_name = spar.get_img_base_name(i_cam)
            # base_name = replace_format_specifiers(base_name) # %d to %04d
            write_targets(detections[i_cam], base_name, frame)

        print("Frame " + str(frame) + " had " +
              repr([s.shape[1] for s in sorted_pos]) + " correspondences.")

        # Distinction between quad/trip irrelevant here.
        sorted_pos = np.concatenate(sorted_pos, axis=1)
        sorted_corresp = np.concatenate(sorted_corresp, axis=1)

        flat = np.array([
            corrected[i].get_by_pnrs(sorted_corresp[i])
            for i in range(len(cals))
        ])
        pos, _ = point_positions(flat.transpose(1, 0, 2), cpar, cals, vpar)

        # if len(cals) == 1: # single camera case
        #     sorted_corresp = np.tile(sorted_corresp,(4,1))
        #     sorted_corresp[1:,:] = -1

        if len(cals) < 4:
            print_corresp = -1 * np.ones((4, sorted_corresp.shape[1]))
            print_corresp[:len(cals), :] = sorted_corresp
        else:
            print_corresp = sorted_corresp

        # Save rt_is
        rt_is_filename = default_naming["corres"].decode()
        # rt_is_filename = f'{rt_is_filename}.{frame:04d}'
        rt_is_filename = f'{rt_is_filename}.{frame}'
        with open(rt_is_filename, "w", encoding="utf8") as rt_is:
            rt_is.write(str(pos.shape[0]) + "\n")
            for pix, pt in enumerate(pos):
                pt_args = (pix + 1, ) + tuple(pt) + tuple(print_corresp[:, pix])
                rt_is.write("%4d %9.3f %9.3f %9.3f %4d %4d %4d %4d\n" % pt_args)
        # rt_is.close()
    # end of a sequence loop


def py_trackcorr_init(exp):
    """Reads all the necessary stuff into Tracker"""

    for cam_id in range(exp.cpar.get_num_cams()):
        img_base_name = exp.spar.get_img_base_name(cam_id)
        # print(img_base_name)
        short_name = img_base_name.split('%')[0]
        if short_name[-1] == '_':
            short_name = short_name[:-1]+'.'
        # print(short_name)
        print(f' Renaming {img_base_name} to {short_name} before C library tracker')
        exp.spar.set_img_base_name(cam_id, short_name)


    tracker = Tracker(exp.cpar, exp.vpar, exp.track_par, exp.spar, exp.cals,
                      default_naming)


    return tracker


def py_trackcorr_loop():
    """Supposedly returns some lists of the linked targets at every step of a tracker"""
    pass


def py_traject_loop():
    """Used to plot trajectories after the full run

    def py_traject_loop(seq):
    global intx1_tr,intx2_tr,inty1_tr,inty2_tr,m1_tr
    trajectories_c(seq, cpar)
    intx1,intx2,inty1,inty2=[],[],[],[]

    for i in range(cpar[0].num_cams):
        intx1_t,intx2_t,inty1_t,inty2_t=[],[],[],[]
        for j in range(m1_tr):
            intx1_t.append(intx1_tr[i][j])
            inty1_t.append(inty1_tr[i][j])
            intx2_t.append(intx2_tr[i][j])
            inty2_t.append(inty2_tr[i][j])
        intx1.append(intx1_t)
        inty1.append(inty1_t)
        intx2.append(intx2_t)
        inty2.append(inty2_t)
    return intx1,inty1,intx2,inty2,m1_tr

    """


# ------- Utilities ----------#


def py_rclick_delete(x: int, y: int, n: int) -> None:
    """Delete clicked points (stub function).

    This is a placeholder for a function that would delete points clicked by the user.
    The original C implementation would store clicked coordinates for later processing.

    Args:
        x: X-coordinate of the click
        y: Y-coordinate of the click
        n: Camera number
    """
    # This function is not implemented in the Python version
    # It was used in the C version to delete points clicked by the user
    pass


def py_get_pix_N(x: int, y: int, n: int) -> Tuple[List[int], List[int]]:
    """Get pixel coordinates (stub function).

    This is a placeholder for a function that would return pixel coordinates.
    The original C implementation would return lists of x and y coordinates.

    Args:
        x: X-coordinate
        y: Y-coordinate
        n: Camera number

    Returns:
        Empty lists of x and y coordinates (placeholder)
    """
    # This function is not implemented in the Python version
    # It was used in the C version to get pixel coordinates
    return [], []


def py_get_pix(x: List[List[int]], y: List[List[int]]) -> Tuple[List[List[int]], List[List[int]]]:
    """Get target positions (stub function).

    This function is supposed to return lists of target positions.
    In the original C implementation, it would fill the provided x and y lists
    with target positions from all cameras.

    Args:
        x: List to be filled with x-coordinates
        y: List to be filled with y-coordinates

    Returns:
        Tuple containing the input lists (unchanged in this implementation)
    """
    # This function is not fully implemented in the Python version
    # It was used in the C version to get target positions
    return x, y


def py_calibration(selection, exp):
    """Calibration
    def py_calibration(sel):
    calibration_proc_c(sel)"""
    if selection == 1:  # read calibration parameters into liboptv
        pass

    if selection == 2:  # run detection of targets
        pass

    if selection == 9:  # initial guess
        """Reads from a target file the 3D points and projects them on
        the calibration images
        It is the same function as show trajectories, just read from a different
        file
        """

    if selection == 10:
        """Run the calibration with particles """
        from optv.tracking_framebuf import Frame
        from pyptv.parameters import OrientParams, ShakingParams

        num_cams = exp.cpar.get_num_cams()

        # cpar, spar, vpar, track_par, tpar, calibs, epar = py_start_proc_c(num_cams)
        calibs = _read_calibrations(exp.cpar, num_cams)

        targ_files = [exp.spar.get_img_base_name(c).decode().split('%d')[0].encode() for c in \
    range(num_cams)]
        # recognized names for the flags:

        op = OrientParams()
        op.read()

        sp = ShakingParams()
        sp.read()

        flags = [name for name in NAMES if getattr(op, name) == 1]
        # Iterate over frames, loading the big lists of 3D positions and
        # respective detections.
        all_known = []
        all_detected = [[] for c in range(num_cams)]

        for frm_num in range(sp.shaking_first_frame, sp.shaking_last_frame + 1):
            frame = Frame(exp.cpar.get_num_cams(),
                corres_file_base = ('res/rt_is').encode(),
                linkage_file_base= ('res/ptv_is').encode(),
                target_file_base = targ_files,
                frame_num = frm_num)

            all_known.append(frame.positions())
            for cam in range(num_cams):
                all_detected[cam].append(frame.target_positions_for_camera(cam))

        # Make into the format needed for full_calibration.
        all_known = np.vstack(all_known)

        # Calibrate each camera accordingly.
        targ_ix_all = []
        residuals_all = []
        targs_all = []
        for cam in range(num_cams):
            detects = np.vstack(all_detected[cam])
            assert detects.shape[0] == all_known.shape[0]

            have_targets = ~np.isnan(detects[:,0])
            used_detects = detects[have_targets,:]
            used_known = all_known[have_targets,:]

            targs = TargetArray(len(used_detects))

            for tix in range(len(used_detects)):
                targ = targs[tix]
                targ.set_pnr(tix)
                targ.set_pos(used_detects[tix])



            residuals = full_scipy_calibration(
                calibs[cam],
                used_known,
                targs,
                exp.cpar,
                flags=flags
            )
            print(f"After scipy full calibration, {np.sum(residuals**2)}")

            print(("Camera %d" % (cam + 1)))
            print((calibs[cam].get_pos()))
            print((calibs[cam].get_angles()))

            # Save the results
            ori_filename = exp.cpar.get_cal_img_base_name(cam)
            addpar_filename = ori_filename + b".addpar"
            ori_filename = ori_filename + b".ori"
            calibs[cam].write(ori_filename, addpar_filename)
            # exp._write_ori(cam, addpar_flag=True)  # addpar_flag to save addpar file

            targ_ix = [t.pnr() for t in targs if t.pnr() != -999]

            targs_all.append(targs)
            targ_ix_all.append(targ_ix)
            residuals_all.append(residuals)


        print("End calibration with particles")
        return targs_all, targ_ix_all, residuals_all



# def py_multiplanecalibration(exp):
#     """Performs multiplane calibration, in which for all cameras the pre-processed plane in multiplane.par al combined.
#     Overwrites the ori and addpar files of the cameras specified in cal_ori.par of the multiplane parameter folder
#     """

#     for i_cam in range(exp.n_cams):  # iterate over all cameras
#         all_known = []
#         all_detected = []
#         for i in range(exp.MultiParams.n_planes):  # combine all single planes

#             c = exp.calParams.img_ori[i_cam][-9]  # Get camera id

#             file_known = exp.MultiParams.plane_name[i] + str(c) + ".tif.fix"
#             file_detected = exp.MultiParams.plane_name[i] + str(c) + ".tif.crd"

#             # Load calibration point information from plane i
#             known = np.loadtxt(file_known)
#             detected = np.loadtxt(file_detected)

#             if np.any(detected == -999):
#                 raise ValueError(
#                     ("Using undetected points in {} will cause " +
#                      "silliness. Quitting.").format(file_detected))

#             num_known = len(known)
#             num_detect = len(detected)

#             if num_known != num_detect:
#                 raise ValueError(
#                     "Number of detected points (%d) does not match" +
#                     " number of known points (%d) for %s, %s" %
#                     (num_known, num_detect, file_known, file_detected))

#             if len(all_known) > 0:
#                 detected[:, 0] = (all_detected[-1][-1, 0] + 1 +
#                                   np.arange(len(detected)))

#             # Append to list of total known and detected points
#             all_known.append(known)
#             all_detected.append(detected)

#         # Make into the format needed for full_calibration.
#         all_known = np.vstack(all_known)[:, 1:]
#         all_detected = np.vstack(all_detected)

#         targs = TargetArray(len(all_detected))
#         for tix in range(len(all_detected)):
#             targ = targs[tix]
#             det = all_detected[tix]

#             targ.set_pnr(tix)
#             targ.set_pos(det[1:])

#         # backup the ORI/ADDPAR files first
#         exp.backup_ori_files()

#         op = par.OrientParams()
#         op.read()
#         flags = [name for name in NAMES if getattr(op, name) == 1]

#         # Run the multiplane calibration
#         residuals, targ_ix, err_est = full_calibration(exp.cals[i_cam], all_known,
#                                                        targs, exp.cpar, flags)

#         # Save the results
#         ori = exp.calParams.img_ori[i_cam]
#         addpar = ori + ".addpar"
#         ori = ori + ".ori"

#         exp.cals[i_cam].write(ori.encode(), addpar.encode())
#         print("End multiplane")


def read_targets(file_base: str, frame: int=123456789) -> TargetArray:
    """Read targets from a file."""
    # buffer = TargetArray()
    # buffer = []

    # # if file_base has an extension, remove it
    # file_base = file_base.split(".")[0]

    # file_base = replace_format_specifiers(file_base) # remove %d
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

    # print(f" read {len(buffer)} targets from {filename}")
    return targs


def write_targets(
    targets: TargetArray, file_base: str, frame: int=123456789) -> bool:
    """Write targets to a file."""
    success = False

    # fix old-type names, that are like cam1.# or just cam1.
    # if '#' in file_base:
    #     file_base = file_base.replace('#', '%05d')
    # if "%" not in file_base:
    #     file_base = file_base + "%05d"

    # file_base = replace_format_specifiers(file_base) # remove %d
    filename = file_base_to_filename(file_base, frame)

    # print("Writing targets to file: ", filename)

    num_targets = len(targets)

    try:
        # Convert targets to a 2D numpy array
        target_arr = np.array(
            [([t.pnr(), *t.pos(), *t.count_pixels(), t.sum_grey_value(), t.tnr()]) for t in targets]
        )
        # Save the target array to file using savetxt
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
    """ Convert file base name to a filename """
    file_base = os.path.splitext(file_base)[0]
    file_base = re.sub(r"_%\d*d", "", file_base)
    if re.search(r"%\d*d", file_base):
        _ = re.sub(r"%\d*d", "%04d", file_base)
        filename = Path(f'{_ % frame}_targets')
    else:
        filename =  Path(f'{file_base}.{frame:04d}_targets')

    return filename


def read_rt_is_file(filename) -> List[List[float]]:
    """Read data from an rt_is file and return the parsed values."""
    try:
        with open(filename, "r", encoding="utf-8") as file:
            # Read the number of rows
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

                row_number = int(values[0])
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


def full_scipy_calibration(cal: Calibration,
                           XYZ: np.ndarray,
                           targs: TargetArray,
                           cpar: ControlParams,
                           flags=[]
                           ):

    """ Full calibration using scipy.optimize """
    from scipy.optimize import minimize
    from optv.transforms import convert_arr_metric_to_pixel
    from optv.imgcoord import image_coordinates

    def _residuals_k(x, cal, XYZ, xy, cpar):
        """Residuals due to radial distortion

        Args:
            x (array-like): Array of parameters.
            cal (Calibration): Calibration object.
            XYZ (array-like): 3D coordinates.
            xy (array-like): 2D image coordinates.
            cpar (CPar): Camera parameters.


            args=(calibs[i_cam],
                self.cal_points["pos"],
                targs,
                self.cpar
                )


        Returns:
            residuals: Distortion in pixels
        """

        cal.set_radial_distortion(x)
        targets = convert_arr_metric_to_pixel(
            image_coordinates(XYZ, cal, cpar.get_multimedia_params()),
            cpar
        )
        xyt = np.array([t.pos() if t.pnr() != -999 else [np.nan, np.nan] for t in xy])
        residuals = np.nan_to_num(xyt - targets)
        # residuals = xy[:,1:] - targets
        return np.sum(residuals**2)

    def _residuals_p(x, cal, XYZ, xy, cpar):
        """Residuals due to decentering """
        cal.set_decentering(x)
        targets = convert_arr_metric_to_pixel(
            image_coordinates(XYZ, cal, cpar.get_multimedia_params()),
            cpar
        )
        xyt = np.array([t.pos() if t.pnr() != -999 else [np.nan, np.nan] for t in xy])
        residuals = np.nan_to_num(xyt - targets)
        return np.sum(residuals**2)

    def _residuals_s(x, cal, XYZ, xy, cpar):
        """Residuals due to decentering """
        cal.set_affine_trans(x)
        targets = convert_arr_metric_to_pixel(
            image_coordinates(XYZ, cal, cpar.get_multimedia_params()),
            cpar
        )
        xyt = np.array([t.pos() if t.pnr() != -999 else [np.nan, np.nan] for t in xy])
        residuals = np.nan_to_num(xyt - targets)
        return np.sum(residuals**2)

    def _residuals_combined(x, cal, XYZ, xy, cpar):
        """Combined residuals  """

        cal.set_radial_distortion(x[:3])
        cal.set_decentering(x[3:5])
        cal.set_affine_trans(x[5:])

        targets = convert_arr_metric_to_pixel(
            image_coordinates(XYZ, cal, cpar.get_multimedia_params()),
            cpar
        )
        xyt = np.array([t.pos() if t.pnr() != -999 else [np.nan, np.nan] for t in xy])
        residuals = np.nan_to_num(xyt - targets)
        return residuals


    # Main loop

    if any(flag in flags for flag in ['k1', 'k2', 'k3']):
        sol = minimize(_residuals_k,
                    cal.get_radial_distortion(),
                    args=(cal,
                            XYZ,
                            targs,
                            cpar
                            ),
                            method='Nelder-Mead',
                            tol=1e-11,
                            options={'disp':True},
                            )
        radial = sol.x
        cal.set_radial_distortion(radial)
    else:
        radial = cal.get_radial_distortion()

    if any(flag in flags for flag in ['p1', 'p2']):
        # now decentering
        sol = minimize(_residuals_p,
                    cal.get_decentering(),
                    args=(cal,
                            XYZ,
                            targs,
                            cpar
                            ),
                            method='Nelder-Mead',
                            tol=1e-11,
                            options={'disp':True},
                            )
        decentering = sol.x
        cal.set_decentering(decentering)
    else:
        decentering = cal.get_decentering()

    if any(flag in flags for flag in ['scale', 'shear']):
        # now affine
        sol = minimize(_residuals_s,
                    cal.get_affine(),
                    args=(cal,
                            XYZ,
                            targs,
                            cpar
                            ),
                            method='Nelder-Mead',
                            tol=1e-11,
                            options={'disp':True},
                            )
        affine = sol.x
        cal.set_affine_trans(affine)

    else:
        affine = cal.get_affine()


    residuals = _residuals_combined(
                    np.r_[radial, decentering, affine],
                    cal,
                    XYZ,
                    targs,
                    cpar
                    )

    residuals /= 100

    return residuals