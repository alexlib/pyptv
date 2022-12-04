""" PBI copy """
import numpy as np
from scipy.optimize import minimize

from optv.parameters import ControlParams
from optv.calibration import Calibration
from optv.imgcoord import image_coordinates
from optv.transforms import convert_arr_metric_to_pixel
from optv.segmentation import target_recognition


from functools import partial
import scipy.optimize
from pyptv.parameter_gui import Calib_Params
from build.lib.pyptv.detection_gui import DetectionGUI

# from pbi, see https://github.com/yosefm/pbi
def fitness(solution, calib_targs, calib_detect, cpar):
    """
    Checks the fitness of an evolutionary solution of calibration values to 
    target points. Fitness is the sum of squares of the distance from each 
    guessed point to the closest neighbor.
    
    Arguments:
    solution - array, concatenated: position of intersection with Z=0 plane; 3 
        angles of exterior calibration; primary point (xh,yh,cc); 3 radial
        distortion parameters; 2 decentering parameters.
    calib_targs - a (p,3) array of p known points on the calibration target.
    calib_detect - a (d,2) array of d detected points in the calibration 
        target.
    cpar - a ControlParams object with image data.
    """
    # Breakdown of of agregate solution vector:
    inters = np.zeros(3)
    inters[:2] = solution[:2]
    R = solution[2]
    angs = solution[3:6]
    prim_point = solution[6:9]
    rad_dist = solution[9:12]
    decent = solution[12:14]
    
    # Compare known points' projections to detections:
    cal = gen_calib(inters, R, angs, glass_vec, prim_point, rad_dist,
                    decent)
    known_proj = image_coordinates(calib_targs, cal,
                                    cpar.get_multimedia_params())
    known_2d = convert_arr_metric_to_pixel(known_proj, cpar)
    dists = np.linalg.norm(known_2d[None, :, :] - calib_detect[:, None, :],
                            axis=2).min(axis=0)

    return np.sum(dists**2)


def pbi_full_calibration(
                    cal: Calibration,
                    calib_detect: np.ndarray,
                    calib_targs: np.ndarray,
                    cpar: ControlParams,
                    flags,
                )-> Calibration:
    """ New full calibration using scipy minimize

    Returns:
        _type_: _description_
    """
    
    # define partial function to keep the arguments
    solution = parse_calib(cal)
    res = minimize(fitness, 
                            solution,
                            args = (
                                calib_targs, 
                                calib_detect, 
                                cpar)
    )
    
    res_cal = gen_calib(res)

    # res is the cal object that minimizes the fitness
    err_est = fitness(res_cal, calib_targs, calib_detect, cpar)
    

    return res_cal, err_est

def get_pos(inters, R, angs):
    # Transpose of http://planning.cs.uiuc.edu/node102.html
    # Also consider the angles are reversed when moving from camera frame to
    # global frame.
    s = np.sin(angs)
    c = np.cos(angs)
    pos = inters + R*np.r_[ s[1], -c[1]*s[0], c[1]*c[0] ]
    return pos

def get_polar_rep(pos, angs):
    """
    Returns the point of intersection with zero Z plane, and distance from it.
    """
    s = np.sin(angs)
    c = np.cos(angs)
    zdir = -np.r_[ s[1], -c[1]*s[0], c[1]*c[0] ]
    
    c = -pos[2]/zdir[2]
    inters = pos + c*zdir
    R = np.linalg.norm(inters - pos)
    
    return inters[:2], R
    
def gen_calib(inters, R, angs, glass_vec, prim_point, radial_dist, decent):
    pos = get_pos(inters, R, angs)
    return Calibration(pos, angs, prim_point, radial_dist, decent, 
        np.r_[1, 0], glass_vec)
    
def parse_calib(
    cal: Calibration
    )-> np.ndarray:
    """parse calibration to solution

    Args:
        cal (Calibration): _description_

    Returns:
        np.ndarray: solution array
    """
    
    # Inverse it: 
    
    # Breakdown of of agregate solution vector:
    # inters = np.zeros(3)
    # inters[:2] = solution[:2]
    # R = solution[2]
    # angs = solution[3:6]
    # prim_point = solution[6:9]
    # rad_dist = solution[9:12]
    # decent = solution[12:14]
    
    inters = cal.get_pos() # including R
    angs = cal.get_angles()
    primary_point = cal.get_primary_point()
    rad_dist = cal.get_radial_distortion()
    decent = cal.get_decentering()
    
    return np.r_[inters, angs, primary_point, rad_dist, decent]