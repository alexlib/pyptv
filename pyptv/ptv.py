import time

import os
import numpy as np
from optv.calibration import Calibration
from optv.correspondences import correspondences, MatchedCoords
from optv.image_processing import preprocess_image
from optv.orientation import point_positions
from optv.parameters import ControlParams, VolumeParams, TrackingParams, \
    SequenceParams, TargetParams
from optv.segmentation import target_recognition
from optv.tracking_framebuf import CORRES_NONE
from optv.tracker import Tracker, default_naming
from optv.epipolar import epipolar_curve
from imageio import imread


def simple_highpass(img, cpar):
    return preprocess_image(img, 0, cpar, 25)

    
def py_set_img(img,i):
    """ Not used anymore, was transferring images to the C """
    pass
    
def py_start_proc_c(n_cams):
    """ Read parameters """
    
    # Control parameters
    cpar = ControlParams(n_cams)
    cpar.read_control_par('parameters/ptv.par')

    # Sequence parameters
    spar = SequenceParams(num_cams=n_cams)
    spar.read_sequence_par('parameters/sequence.par',n_cams)

    # Volume parameters
    vpar = VolumeParams()
    vpar.read_volume_par('parameters/criteria.par')

    # Tracking parameters
    track_par = TrackingParams()
    track_par.read_track_par('parameters/track.par')

    # Target parameters
    tpar = TargetParams(n_cams)
    tpar.read('parameters/targ_rec.par')

    # 

    # Calibration parameters

    cals =[]
    for i_cam in xrange(n_cams):
        cal = Calibration()
        tmp = cpar.get_cal_img_base_name(i_cam)
        print(tmp)
        cal.from_file(tmp+'.ori', tmp+'.addpar')
        cals.append(cal)
        
    return cpar, spar, vpar, track_par, tpar, cals
        
def py_pre_processing_c(list_of_images, cpar):
    """ Image pre-processing, mostly highpass filter, could be extended in 
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
    """ Detection of targets """

    detections, corrected = [],[]
    for i_cam, img in enumerate(list_of_images):
        targs = target_recognition(img, tpar, i_cam, cpar)
        targs.sort_y()
        detections.append(targs)
        mc = MatchedCoords(targs, cpar, cals[i_cam])
        corrected.append(mc)
        
    return detections, corrected
    
def py_correspondences_proc_c(exp):
    """ Provides correspondences 
    Inputs: 
        exp = info.object from the pyptv_gui
    Outputs:
        quadruplets, ... : four empty lists filled later with the 
    correspondences of quadruplets, triplets, pairs, and so on
    """
    
    frame = 123456789 # just a temporary workaround. todo: think how to write


#        if any([len(det) == 0 for det in detections]):
#            return False

    # Corresp. + positions.
    sorted_pos, sorted_corresp, num_targs = correspondences(
        exp.detections, exp.corrected, exp.cals, exp.vpar, exp.cpar)

    # Save targets only after they've been modified:
    for i_cam in xrange(exp.n_cams):
        exp.detections[i_cam].write(exp.spar.get_img_base_name(i_cam),frame)

    print("Frame " + str(frame) + " had " \
          + repr([s.shape[1] for s in sorted_pos]) + " correspondences.")
              
    return sorted_pos, sorted_corresp, num_targs
    
def py_determination_proc_c(n_cams, sorted_pos, sorted_corresp, corrected):
    """ Returns 3d positions """
    
    # Control parameters
    cpar = ControlParams(n_cams)
    cpar.read_control_par('parameters/ptv.par')

    # Volume parameters
    vpar = VolumeParams()
    vpar.read_volume_par('parameters/criteria.par')    
        
    cals =[]
    for i_cam in xrange(n_cams):
        cal = Calibration()
        tmp = cpar.get_cal_img_base_name(i_cam)
        cal.from_file(tmp+'.ori', tmp+'.addpar')
        cals.append(cal)

    
    # Distinction between quad/trip irrelevant here.
    sorted_pos = np.concatenate(sorted_pos, axis=1)
    sorted_corresp = np.concatenate(sorted_corresp, axis=1)


    flat = np.array([corrected[i].get_by_pnrs(sorted_corresp[i]) \
                     for i in xrange(len(cals))])
    pos, rcm = point_positions(
        flat.transpose(1,0,2), cpar, cals, vpar)

    if len(cals) == 1: # single camera case
        sorted_corresp = np.tile(sorted_corresp,(4,1))
        sorted_corresp[1:,:] = -1

    # Save rt_is in a temporary file 
    frame = 123456789 # just a temporary workaround. todo: think how to write
    with open(default_naming['corres']+'.'+str(frame), 'w') as rt_is:
        rt_is.write(str(pos.shape[0]) + '\n')
        for pix, pt in enumerate(pos):
            pt_args = (pix + 1,) + tuple(pt) + tuple(sorted_corresp[:,pix])
            rt_is.write("%4d %9.3f %9.3f %9.3f %4d %4d %4d %4d\n" % pt_args)
    # rt_is.close()
 
 
def py_sequence_loop(exp):
    """ Runs a sequence of detection, stereo-correspondence, determination and stores
        the data in the cam#.XXX_targets (rewritten) and rt_is.XXX files. Basically 
        it is to run the batch as in pyptv_batch.py without tracking
    """
    n_cams, cpar, spar, vpar, tpar, cals = \
        exp.n_cams, exp.cpar, exp.spar, exp.vpar, exp.tpar, exp.cals
    # sequence loop for all frames
    for frame in xrange(spar.get_first(), spar.get_last()+1):
        print("processing frame %d" % frame)

        detections = []
        corrected = []
        for i_cam in xrange(n_cams):
            imname = spar.get_img_base_name(i_cam) + str(frame)
            if not os.path.exists(imname):
                print(os.path.abspath(os.path.curdir))
                print('{0} does not exist'.format(imname))

            img = imread(imname)
            # import pdb; pdb.set_trace()
            print(imname,img.shape)
            time.sleep(.1)
            hp = simple_highpass(img, cpar)
            targs = target_recognition(hp, tpar, i_cam, cpar)
            # print(targs)

            targs.sort_y()
            detections.append(targs)
            mc = MatchedCoords(targs, cpar, cals[i_cam])
            pos, pnr = mc.as_arrays()
            # print(i_cam)
            corrected.append(mc)


        #        if any([len(det) == 0 for det in detections]):
        #            return False

        # Corresp. + positions.
        sorted_pos, sorted_corresp, num_targs = correspondences(
            detections, corrected, cals, vpar, cpar)

        # Save targets only after they've been modified:
        for i_cam in xrange(n_cams):
            detections[i_cam].write(spar.get_img_base_name(i_cam),frame)


        print("Frame " + str(frame) + " had " \
              + repr([s.shape[1] for s in sorted_pos]) + " correspondences.")

        # Distinction between quad/trip irrelevant here.
        sorted_pos = np.concatenate(sorted_pos, axis=1)
        sorted_corresp = np.concatenate(sorted_corresp, axis=1)

        flat = np.array([corrected[i].get_by_pnrs(sorted_corresp[i]) \
                         for i in xrange(len(cals))])
        pos, rcm = point_positions(
            flat.transpose(1,0,2), cpar, cals, vpar)

        if len(cals) == 1: # single camera case
            sorted_corresp = np.tile(sorted_corresp,(4,1))
            sorted_corresp[1:,:] = -1

        # Save rt_is
        rt_is = open(default_naming['corres']+'.'+str(frame), 'w')
        rt_is.write(str(pos.shape[0]) + '\n')
        for pix, pt in enumerate(pos):
            pt_args = (pix + 1,) + tuple(pt) + tuple(sorted_corresp[:,pix])
            rt_is.write("%4d %9.3f %9.3f %9.3f %4d %4d %4d %4d\n" % pt_args)
        rt_is.close()
    # end of a sequence loop    
           

def py_trackcorr_init(exp):
    """ Reads all the necessary stuff into Tracker """
    tracker = Tracker(exp.cpar, exp.vpar, exp.track_par, exp.spar, exp.cals, \
                                                                        default_naming)
    return tracker

def py_trackcorr_loop():
    """ Supposedly returns some lists of the linked targets at every step of a tracker """
    pass

def py_traject_loop():
    """ Used to plot trajectories after the full run 
    
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
    
def py_rclick_delete():
    """ a tool to delete clicked points 
    
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
    
def py_get_pix_N():
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
    
    
def py_get_pix(x,y):
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
    return x,y 
    
def py_calibration(selection):
    """ Calibration 
    def py_calibration(sel):
    calibration_proc_c(sel) 
"""
    if selection == 1: # read calibration parameters into liboptv
        pass
    
    if selection == 2: # run detection of targets
        pass

    if selection == 9: # initial guess
        """ Reads from a target file the 3D points and projects them on 
        the calibration images
        It is the same function as show trajectories, just read from a different
        file 
        """

    
    
    

    
    
