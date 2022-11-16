import pathlib
import os
import numpy as np
from optv.calibration import Calibration
from optv.correspondences import correspondences, MatchedCoords
from optv.image_processing import preprocess_image
from optv.orientation import (
    point_positions,
    external_calibration,
    full_calibration,
)
from optv.parameters import (
    ControlParams,
    VolumeParams,
    TrackingParams,
    SequenceParams,
    TargetParams,
)
from optv.segmentation import target_recognition
from optv.tracking_framebuf import CORRES_NONE, read_targets, TargetArray
from optv.tracker import Tracker, default_naming
from optv.epipolar import epipolar_curve
from skimage.io import imread
from pyptv import parameters as par


def simple_highpass(img, cpar):
    return preprocess_image(img, 0, cpar, 25)


def py_set_img(img, i):
    """Not used anymore, was transferring images to the C"""
    pass


def py_start_proc_c(n_cams):
    """Read parameters"""

    # Control parameters
    cpar = ControlParams(n_cams)
    cpar.read_control_par(b"parameters/ptv.par")

    # Sequence parameters
    spar = SequenceParams(num_cams=n_cams)
    spar.read_sequence_par(b"parameters/sequence.par", n_cams)

    # Volume parameters
    vpar = VolumeParams()
    vpar.read_volume_par(b"parameters/criteria.par")

    # Tracking parameters
    track_par = TrackingParams()
    track_par.read_track_par(b"parameters/track.par")

    # Target parameters
    tpar = TargetParams(n_cams)
    tpar.read(b"parameters/targ_rec.par")

    # Examine parameters, multiplane (single plane vs combined calibration)
    epar = par.ExamineParams()
    epar.read()

    # Calibration parameters
    cals = []
    for i_cam in range(n_cams):
        cal = Calibration()
        tmp = cpar.get_cal_img_base_name(i_cam)
        cal.from_file(tmp + b".ori", tmp + b".addpar")
        cals.append(cal)

    return cpar, spar, vpar, track_par, tpar, cals, epar


def py_pre_processing_c(list_of_images, cpar):
    """Image pre-processing, mostly highpass filter, could be extended in
    the future

    Inputs:
        list of images
        cpar ControlParams()
    """
    newlist = []
    for img in list_of_images:
        newlist.append(simple_highpass(img, cpar))
    return newlist


def py_detection_proc_c(list_of_images, cpar, tpar, cals):
    """Detection of targets"""

    pftVersionParams = par.PftVersionParams(path="./parameters")
    pftVersionParams.read()
    Existing_Target = bool(pftVersionParams.Existing_Target)

    detections, corrected = [], []
    for i_cam, img in enumerate(list_of_images):
        if Existing_Target:
            targs = read_targets(cpar.get_img_base_name(i_cam), 0)
        else:
            targs = target_recognition(img, tpar, i_cam, cpar)

        targs.sort_y()
        detections.append(targs)
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
        exp.detections[i_cam].write(exp.spar.get_img_base_name(i_cam), frame)

    print("Frame " + str(frame) + " had " +
          repr([s.shape[1] for s in sorted_pos]) + " correspondences.")

    return sorted_pos, sorted_corresp, num_targs


def py_determination_proc_c(n_cams, sorted_pos, sorted_corresp, corrected):
    """Returns 3d positions"""

    # Control parameters
    cpar = ControlParams(n_cams)
    cpar.read_control_par(b"parameters/ptv.par")

    # Volume parameters
    vpar = VolumeParams()
    vpar.read_volume_par(b"parameters/criteria.par")

    cals = []
    for i_cam in range(n_cams):
        cal = Calibration()
        tmp = cpar.get_cal_img_base_name(i_cam)
        cal.from_file(tmp + b".ori", tmp + b".addpar")
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
    fname = b"".join([default_naming["corres"],
                      b".123456789"])  # hard-coded frame number
    with open(fname, "w", encoding='utf8') as rt_is:
        rt_is.write(str(pos.shape[0]) + "\n")
        for pix, pt in enumerate(pos):
            pt_args = (pix + 1, ) + tuple(pt) + tuple(print_corresp[:, pix])
            rt_is.write("%4d %9.3f %9.3f %9.3f %4d %4d %4d %4d\n" % pt_args)
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

    pftVersionParams = par.PftVersionParams(path="./parameters")
    pftVersionParams.read()
    Existing_Target = np.bool(pftVersionParams.Existing_Target)

    # sequence loop for all frames
    for frame in range(spar.get_first(), spar.get_last() + 1):
        print(f"processing {frame} frame")

        detections = []
        corrected = []
        for i_cam in range(n_cams):
            if Existing_Target:
                targs = read_targets(spar.get_img_base_name(i_cam), frame)
            else:
                # imname = spar.get_img_base_name(i_cam) + str(frame).encode()
                imname = spar.get_img_base_name(i_cam).decode()
                imname = pathlib.Path(imname.replace('#',f'{frame}'))
                print(f'Image name {imname}')

                if not imname.exists():
                    print(f"{imname} does not exist")

                img = imread(imname)
                # time.sleep(.1) # I'm not sure we need it here
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
        for i_cam in range(n_cams):
            detections[i_cam].write(spar.get_img_base_name(i_cam), frame)

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


def py_rclick_delete(x, y, n):
    """a tool to delete clicked points

    def py_right_click(int coord_x, int coord_y, n_image):
    global rclick_intx1,rclick_inty1,rclick_intx2,rclick_inty2,rclick_points_x1, rclick_points_y1,rclick_count,rclick_points_intx1, rclick_points_inty1

    x2_points,y2_points,x1,y1,x2,y2=[],[],[],[],[],[]

    cdef volume_par *vpar = read_volume_par("parameters/criteria.par")
    r = mouse_proc_c (coord_x, coord_y, 3, n_image, vpar, cpar)
    free(vpar)

    if r == -1:
        return -1,-1,-1,-1,-1,-1,-1,-1
    for i in range(cpar[0].num_cams):
        x2_temp,y2_temp=[],[]
        for j in range(rclick_count[i]):
            x2_temp.append(rclick_points_x1[i][j])
            y2_temp.append(rclick_points_y1[i][j])

        x2_points.append(x2_temp)
        y2_points.append(y2_temp)
        x1.append(rclick_intx1[i])
        y1.append(rclick_inty1[i])
        x2.append(rclick_intx2[i])
        y2.append(rclick_inty2[i])

    return  x1,y1,x2,y2,x2_points,y2_points,rclick_points_intx1, rclick_points_inty1


    """
    pass


def py_get_pix_N(x, y, n):
    """
    def py_get_pix_N(x,y,n_image):
    global pix
    cdef int i,j
    i=n_image
    x1=[]
    y1=[]
    for j in range(num[i]):
        x1.append(pix[i][j].x)
        y1.append(pix[i][j].y)
        x.append(x1)
        y.append(y1)

    """
    pass


def py_get_pix(x, y):
    """
    Returns a list of lists of target positions

    def py_get_pix(x,y):
    global pix
    cdef int i,j
    for i in range(cpar[0].num_cams):
        x1=[]
        y1=[]
        for j in range(num[i]):
            x1.append(pix[i][j].x)
            y1.append(pix[i][j].y)
        x.append(x1)
        y.append(y1)

    """
    return x, y


def py_calibration(selection):
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


def py_multiplanecalibration(exp):
    """Performs multiplane calibration, in which for all cameras the pre-processed plane in multiplane.par al combined.
    Overwrites the ori and addpar files of the cameras specified in cal_ori.par of the multiplane parameter folder
    """

    for i_cam in range(exp.n_cams):  # iterate over all cameras
        all_known = []
        all_detected = []
        for i in range(exp.MultiParams.n_planes):  # combine all single planes

            c = exp.calParams.img_ori[i_cam][-9]  # Get camera id

            file_known = exp.MultiParams.plane_name[i] + str(c) + ".tif.fix"
            file_detected = exp.MultiParams.plane_name[i] + str(c) + ".tif.crd"

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

        targs = TargetArray(len(all_detected))
        for tix in range(len(all_detected)):
            targ = targs[tix]
            det = all_detected[tix]

            targ.set_pnr(tix)
            targ.set_pos(det[1:])

        # backup the ORI/ADDPAR files first
        exp.backup_ori_files()

        op = par.OrientParams()
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
