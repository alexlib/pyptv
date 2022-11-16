""" PyPTV_BATCH is the script for the 3D-PTV (http://ptv.origo.ethz.ch)
    written in Python with Enthought Traits GUI/Numpy/Chaco

Example:
>> python pyptv_batch.py experiments/exp1 10001 10022

where 10001 is the first file in sequence and 10022 is the last one
the present "active" parameters are kept intact except the sequence


"""


# from scipy.misc import imread
import os
import sys
import time

import numpy as np
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

# from optv.tracking_framebuf import CORRES_NONE
from optv.tracker import Tracker, default_naming
from skimage.io import imread


# project specific inputs
# import pdb; pdb.set_trace()


def simple_highpass(img, cpar):
    return preprocess_image(img, 0, cpar, 12)


def run_batch(new_seq_first, new_seq_last):
    """this file runs inside exp_path, so the other names are
    prescribed by the OpenPTV type of a folder:
        /parameters
        /img
        /cal
        /res
    """
    # read the number of cameras
    with open("parameters/ptv.par", "r") as f:
        n_cams = int(f.readline())

    # Control parameters
    cpar = ControlParams(n_cams)
    cpar.read_control_par(b"parameters/ptv.par")

    # Sequence parameters
    spar = SequenceParams(num_cams=n_cams)
    spar.read_sequence_par(b"parameters/sequence.par", n_cams)
    spar.set_first(new_seq_first)
    spar.set_last(new_seq_last)

    # Volume parameters
    vpar = VolumeParams()
    vpar.read_volume_par(b"parameters/criteria.par")

    # Tracking parameters
    track_par = TrackingParams()
    track_par.read_track_par(b"parameters/track.par")

    # Target parameters
    tpar = TargetParams()
    tpar.read(b"parameters/targ_rec.par")

    # Calibration parameters

    cals = []
    for i_cam in range(n_cams):
        cal = Calibration()
        tmp = cpar.get_cal_img_base_name(i_cam)
        cal.from_file(tmp + b".ori", tmp + b".addpar")
        cals.append(cal)

    # sequence loop for all frames
    for frame in range(new_seq_first, new_seq_last + 1):
        print("processing frame %d" % frame)

        detections = []
        corrected = []
        for i_cam in range(n_cams):
            imname = spar.get_img_base_name(i_cam) + str(frame)
            img = imread(imname)
            hp = simple_highpass(img, cpar)
            targs = target_recognition(hp, tpar, i_cam, cpar)
            print(targs)

            targs.sort_y()
            detections.append(targs)
            mc = MatchedCoords(targs, cpar, cals[i_cam])
            pos, pnr = mc.as_arrays()
            print(i_cam)
            corrected.append(mc)

        #        if any([len(det) == 0 for det in detections]):
        #            return False

        # Corresp. + positions.
        sorted_pos, sorted_corresp, num_targs = correspondences(
            detections, corrected, cals, vpar, cpar
        )

        # Save targets only after they've been modified:
        for i_cam in range(n_cams):
            detections[i_cam].write(spar.get_img_base_name(i_cam), frame)

        print(
            "Frame "
            + str(frame)
            + " had "
            + repr([s.shape[1] for s in sorted_pos])
            + " correspondences."
        )

        # Distinction between quad/trip irrelevant here.
        sorted_pos = np.concatenate(sorted_pos, axis=1)
        sorted_corresp = np.concatenate(sorted_corresp, axis=1)

        flat = np.array(
            [
                corrected[i].get_by_pnrs(sorted_corresp[i])
                for i in range(len(cals))
            ]
        )
        pos, rcm = point_positions(flat.transpose(1, 0, 2), cpar, cals, vpar)

        if len(cals) < 4:
            print_corresp = -1 * np.ones((4, sorted_corresp.shape[1]))
            print_corresp[: len(cals), :] = sorted_corresp
        else:
            print_corresp = sorted_corresp

        # Save rt_is
        rt_is = open(default_naming["corres"] + "." + str(frame), "w")
        rt_is.write(str(pos.shape[0]) + "\n")
        for pix, pt in enumerate(pos):
            pt_args = (pix + 1,) + tuple(pt) + tuple(print_corresp[:, pix])
            rt_is.write("%4d %9.3f %9.3f %9.3f %4d %4d %4d %4d\n" % pt_args)
        rt_is.close()
    # end of a sequence loop

    tracker = Tracker(cpar, vpar, track_par, spar, cals, default_naming)
    tracker.full_forward()


#


def main(exp_path, first, last, repetitions=1):
    """runs the batch
    Usage:
        main([exp_dir, first, last], [repetitions])

    Parameters:
        list of 3 parameters in this order:
        exp_dir : directory with the experiment data
        first, last : integer, number of a first and last frame
        repetitions : int, default = 1, optional
    """
    start = time.time()

    try:
        exp_path = os.path.abspath(exp_path)
        print("exp_path is %s" % exp_path)
        os.chdir(exp_path)
        print(os.getcwd())
    except Exception:
        raise ValueError("Wrong experimental directory %s" % exp_path)

    # RON - make a res dir if it not found

    if "res" not in os.listdir(exp_path):
        print(" 'res' folder not found. creating one")
        os.makedirs(os.path.join(exp_path, "res"))

    for i in range(repetitions):
        try:  # strings
            seq_first = eval(first)
            seq_last = eval(last)
        except Exception:  # integers
            seq_first = first
            seq_last = last

        try:
            print((seq_first, seq_last))
            run_batch(seq_first, seq_last)
        except Exception:
            print("something wrong with the batch or the folder")

    end = time.time()
    print("time lapsed %f sec" % (end - start))


if __name__ == "__main__":
    """pyptv_batch.py enables to run a sequence without GUI
    It can run from a command shell:
    python pyptv_batch.py ~/test_cavity 10000 10004

    or from Python:

    import sys, os
    sys.path.append(os.path.abspath('openptv/openptv-python/pyptv_gui'))
    from pyptv_batch import main
    batch_command = '/openptv/openptv-python/pyptv_gui/pyptv_batch.py'
    PyPTV_working_directory = '/openptv/Working_folder/'
    mi,mx = 65119, 66217
    main([batch_command,PyPTV_working_directory, mi, mx])
    """
    # directory from which we run the software
    print("inside pyptv_batch.py\n")
    print(sys.argv)

    if len(sys.argv) < 4:
        print(
            "Wrong number of inputs, usage: python pyptv_batch.py \
        experiments/exp1 seq_first seq_last"
        )
        raise ValueError("wrong number of inputs")

    exp_path = sys.argv[1]
    first = sys.argv[2]
    last = sys.argv[3]

    main(exp_path, first, last)
