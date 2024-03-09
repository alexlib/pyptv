from pathlib import Path
import numpy as np
from typing import List

from openptv_python.calibration import Calibration
from openptv_python.correspondences import py_correspondences, MatchedCoords
from openptv_python.image_processing import preprocess_image
from openptv_python.orientation import (
    point_positions,
    full_calibration,
)
from openptv_python.parameters import (
    ControlPar,
    VolumePar,
    TrackPar,
    SequencePar,
    TargetPar,
    OrientPar,
    PftVersionPar,
    read_control_par,
    read_volume_par,
    read_sequence_par,
    read_target_par,
    read_track_par,
    read_examine_par,
)
from openptv_python.segmentation import target_recognition
from openptv_python.tracking_frame_buf import (
    read_targets, 
    Target, 
    match_coords,
    write_targets
)
from openptv_python.track import Tracker, default_naming
from skimage.io import imread



def process_path(input_path):
    """ Process a file path, accepting either a pathlib.Path object or a string.
    
    Args:
        input_path (Union[pathlib.Path, str]): The input file path.
    
    Returns:
        pathlib.Path: A Path object representing the processed path.
    """
    if isinstance(input_path, Path):
        # If input_path is already a Path object, return it as is
        return input_path
    else:
        # Otherwise, convert the string to a Path object
        return Path(input_path)

# # Example usage:
# file_path1 = pathlib.Path('my_directory/my_file.txt')
# file_path2 = 'another_directory/another_file.txt'

# # Call the function with both Path objects and strings
# processed_path1 = process_path(file_path1)
# processed_path2 = process_path(file_path2)

# print(f"Processed path 1: {processed_path1}")
# print(f"Processed path 2: {processed_path2}")


def negative(img):
    """ Negative 8-bit image """
    return 255 - img

def simple_highpass(img, cpar):
    """ Simple highpass is using liboptv preprocess_image """
    return preprocess_image(img, 0, cpar, 25)


def py_set_img(img, i):
    """Not used anymore, was transferring images to the C"""
    pass


def py_start_proc_c(n_cams):
    """Read parameters"""

    # Control parameters
    # cpar = ControlPar(n_cams)
    cpar = read_control_par(process_path("parameters/ptv.par"))

    # Sequence parameters
    spar  = read_sequence_par(process_path("parameters/sequence.par"), n_cams)

    # Volume parameters
    vpar = read_volume_par(process_path("parameters/criteria.par"))

    # Tracking parameters
    track_par = read_track_par(process_path("parameters/track.par"))

    # Target parameters
    tpar = read_target_par(process_path("parameters/targ_rec.par"))

    # Examine parameters, multiplane (single plane vs combined calibration)
    epar = read_examine_par(process_path("parameters/examine.par"))


    # Calibration parameters
    cals = []
    for i_cam in range(n_cams):
        tmp = cpar.cal_img_base_name[i_cam]
        cal = Calibration().from_file(process_path(tmp + ".ori"), process_path(tmp + ".addpar"))
        cals.append(cal)

    return cpar, spar, vpar, track_par, tpar, cals, epar


def py_pre_processing_c(list_of_images: List[np.ndarray], cpar: ControlPar) -> List[np.ndarray]:
    """Image pre-processing, mostly highpass filter, could be extended in
    the future

    Inputs:
        list of images
        cpar ControlPar()
    """
    newlist = []
    for img in list_of_images:
        newlist.append(simple_highpass(img, cpar))
    return newlist


def py_detection_proc_c(list_of_images, cpar, tpar, cals):
    """Detection of targets"""
    pft = PftVersionPar().from_file("parameters/pft_version.par")

    detections, corrected = [], []
    for i_cam, img in enumerate(list_of_images):
        if pft.existing_target_flag:
            targs = read_targets(cpar.get_img_base_name(i_cam), 0)
        else:
            targs = target_recognition(img, tpar, i_cam, cpar)

        targs.sort(key=lambda t: t.y)
        
        detections.append(targs)
        # mc = MatchedCoords(targs, cpar, cals[i_cam])
        mc = match_coords(targs, cpar, cals[i_cam])
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
    sorted_pos, sorted_corresp, num_targs = py_correspondences(
        exp.detections, exp.corrected, exp.cals, exp.vpar, exp.cpar)
    
    # Save targets only after they've been modified:
    for i_cam in range(exp.n_cams):
        write_targets(exp.detections[i_cam],
                      len(exp.detections[i_cam]), 
                      exp.spar.get_img_base_name(i_cam), 
                      frame
                      ) 

    print("Frame " + str(frame) + " had " +
          repr([s.shape[1] for s in sorted_pos]) + " correspondences.")

    return sorted_pos, sorted_corresp, num_targs


def py_determination_proc_c(n_cams, sorted_pos, sorted_corresp, corrected):
    """Returns 3d positions"""

    # Control parameters
    cpar = ControlPar(n_cams)
    cpar.read_control_par("parameters/ptv.par")

    # Volume parameters
    vpar = VolumePar()
    vpar.read_volume_par("parameters/criteria.par")

    cals = []
    for i_cam in range(n_cams):
        cal = Calibration()
        tmp = cpar.get_cal_img_base_name(i_cam)
        cal.from_file(tmp + ".ori", tmp + ".addpar")
        cals.append(cal)

    # Distinction between quad/trip irrelevant here.
    sorted_pos = np.concatenate(sorted_pos, axis=1)
    sorted_corresp = np.concatenate(sorted_corresp, axis=1)

    flat = np.array([
        corrected[i].get_by_pnrs(sorted_corresp[i]) for i in range(len(cals))
    ])
    pos, rcm = point_positions(flat.transpose(1, 0, 2), cpar, cals, vpar)

    if len(cals) < 4:
        print_corresp = -1 * np.ones((4, sorted_corresp.shape[1]))
        print_corresp[:len(cals), :] = sorted_corresp
    else:
        print_corresp = sorted_corresp

    # Save rt_is in a temporary file
    fname = "".join([default_naming["corres"],
                      ".123456789"])  # hard-coded frame number
    print(f'Prepared {fname} to write positions\n')

    try:
        with open(fname, "w", encoding='utf-8') as rt_is:
            print(f'Opened {fname} \n')
            rt_is.write(str(pos.shape[0]) + "\n")
            for pix, pt in enumerate(pos):
                pt_args = (pix + 1, ) + tuple(pt) + tuple(print_corresp[:, pix])
                rt_is.write("%4d %9.3f %9.3f %9.3f %4d %4d %4d %4d\n" % pt_args)
    except FileNotFoundError:
        msg = "Sorry, the file "+ fname + "does not exist."
        print(msg) # Sorry, the file John.txt does not exist.

    # rt_is.close()



def py_sequence_loop(exp):
    """Runs a sequence of detection, stereo-correspondence, determination and stores
    the data in the cam#.XXX_targets (rewritten) and rt_is.XXX files. Basically
    it is to run the batch as in pyptv_batch.py without tracking
    """
    n_cams, cpar, spar, vpar, tpar, cals = (
        exp.n_cams,
        exp.cpar,
        exp.spar,
        exp.vpar,
        exp.tpar,
        exp.cals,
    )

    pftVersionPar = PftVersionPar().from_file("parameters/pft_version.par")
    Existing_Target = bool(pftVersionPar.existing_target_flag)

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
                targs = read_targets(spar.get_img_base_name(i_cam), frame)
            else:
                # imname = spar.get_img_base_name(i_cam) + str(frame).encode()
                
                # imname = Path(imname.replace('#',f'{frame}'))
                imname = Path(base_image_name % frame) # works with jumps from 1 to 10 
                # print(f'Image name {imname}')

                if not imname.exists():
                    print(f"{imname} does not exist")
                else:
                    img = imread(imname)
                # time.sleep(.1) # I'm not sure we need it here
                
                if 'exp1' in exp.__dict__:
                    if exp.exp1.active_params.m_params.Inverse:
                        print("Invert image")
                        img = 255 - img

                    if exp.exp1.active_params.m_params.Subtr_Mask:
                        # print("Subtracting mask")
                        try:
                            background_name = exp.exp1.active_params.m_params.Base_Name_Mask.replace('#',str(i_cam))
                            # background_name = exp.exp1.active_params.m_params.Base_Name_Mask % (i_cam + 1)
                            background = imread(background_name)
                            img = np.clip(img - background, 0, 255).astype(np.uint8)

                        except ValueError:
                            print("failed to read the mask")
                    
                
                high_pass = simple_highpass(img, cpar)
                targs = target_recognition(high_pass, tpar, i_cam, cpar)

            targs.sort(key=lambda t: t.y)
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
            detections[i_cam].write(
                spar.get_img_base_name(i_cam),
                frame
                )

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
        rt_is_filename = rt_is_filename + f'.{frame}'
        with open(rt_is_filename, "w", encoding="utf8") as rt_is:
            rt_is.write(str(pos.shape[0]) + "\n")
            for pix, pt in enumerate(pos):
                pt_args = (pix + 1, ) + tuple(pt) + tuple(print_corresp[:, pix])
                rt_is.write("%4d %9.3f %9.3f %9.3f %4d %4d %4d %4d\n" % pt_args)
        # rt_is.close()
    # end of a sequence loop


def py_trackcorr_init(exp):
    """Reads all the necessary stuff into Tracker"""
    tracker = Tracker(exp.cpar, exp.vpar, exp.track_par, exp.spar, exp.cals,
                      default_naming)
    return tracker


def py_multiplanecalibration(exp):
    """Performs multiplane calibration, in which for all cameras the pre-processed plane in multiplane.par al combined.
    Overwrites the ori and addpar files of the cameras specified in cal_ori.par of the multiplane parameter folder
    """

    for i_cam in range(exp.n_cams):  # iterate over all cameras
        all_known = []
        all_detected = []
        for i in range(exp.MultiPar.n_planes):  # combine all single planes

            c = exp.calPar.img_ori[i_cam][-9]  # Get camera id

            file_known = exp.MultiPar.plane_name[i] + str(c) + ".tif.fix"
            file_detected = exp.MultiPar.plane_name[i] + str(c) + ".tif.crd"

            # Load calibration point information from plane i
            known = np.loadtxt(file_known)
            detected = np.loadtxt(file_detected)

            if np.any(detected == -999):
                raise ValueError(
                    ("Using undetected points in {} will cause " +
                     "silliness. Quitting.").format(file_detected))

            num_known = len(known)
            num_detect = len(detected)

            if num_known != num_detect:
                raise ValueError(
                    "Number of detected points (%d) does not match" +
                    " number of known points (%d) for %s, %s" %
                    (num_known, num_detect, file_known, file_detected))

            if len(all_known) > 0:
                detected[:, 0] = (all_detected[-1][-1, 0] + 1 +
                                  np.arange(len(detected)))

            # Append to list of total known and detected points
            all_known.append(known)
            all_detected.append(detected)

        # Make into the format needed for full_calibration.
        all_known = np.vstack(all_known)[:, 1:]
        all_detected = np.vstack(all_detected)

        targs = [Target() for _ in range(len(all_detected))]
        for tix, detected in enumerate(all_detected):
            targ = targs[tix]
            targ.set_pnr(tix)
            targ.set_pos(detected[1:])

        # backup the ORI/ADDPAR files first
        exp.backup_ori_files()

        op = OrientPar()
        op.read()

        # recognized names for the flags:
        names = [
            "cc",
            "xh",
            "yh",
            "k1",
            "k2",
            "k3",
            "p1",
            "p2",
            "scale",
            "shear",
        ]
        op_names = [
            op.cc,
            op.xh,
            op.yh,
            op.k1,
            op.k2,
            op.k3,
            op.p1,
            op.p2,
            op.scale,
            op.shear,
        ]

        flags = []
        for name, op_name in zip(names, op_names):
            if op_name == 1:
                flags.append(name)

        # Run the multiplane calibration
        residuals, targ_ix, err_est = full_calibration(exp.cals[0], all_known,
                                                       targs, exp.cpar, flags)

        # Save the results
        exp._write_ori(i_cam,
                       addpar_flag=True)  # addpar_flag to save addpar file
        print("End multiplane")
