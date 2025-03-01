"""
Parameter builder for directly creating optv parameter objects from YAML parameters.

This module provides functions to create parameter objects for the optv library
directly from YAML parameter objects, avoiding the need to read from parameter files.
"""

from pathlib import Path
import numpy as np

# Import optv parameter classes
from optv.parameters import ControlParams, SequenceParams, VolumeParams, TrackingParams, TargetParams
from optv.calibration import Calibration
import optv.parameters as par

# Import parameter manager
from pyptv.yaml_parameters import ParameterManager


def create_control_params_from_yaml(yaml_params):
    """
    Create a ControlParams object directly from YAML parameters.
    
    Args:
        yaml_params: Dictionary of YAML parameter objects
        
    Returns:
        ControlParams object
    """
    ptv_params = yaml_params.get("PtvParams")
    
    # Create the control params object with the number of cameras
    cpar = ControlParams(ptv_params.n_img)
    
    # Set image properties
    cpar.set_image_size((ptv_params.imx, ptv_params.imy))
    cpar.set_pixel_size((ptv_params.pix_x, ptv_params.pix_y))
    
    # Set calibration image base names
    for i in range(ptv_params.n_img):
        cal_img_name = getattr(ptv_params, f"cal_img_base_name_{i+1}")
        cpar.set_cal_img_base_name(i, cal_img_name)
    
    # Set flags
    cpar.set_hp_flag(ptv_params.hp_flag)
    cpar.set_allCam_flag(ptv_params.allCam_flag)
    cpar.set_tiff_flag(ptv_params.tiff_flag)
    cpar.set_chfield(ptv_params.chfield)
    
    # Set multimedia parameters
    mm_params = cpar.get_multimedia_params()
    mm_params.set_n1(ptv_params.mmp_n1)
    mm_params.set_n3(ptv_params.mmp_n3)
    
    # Set layers
    n2_values = []
    d_values = []
    for i in range(4):  # Maximum of 4 layers in current implementation
        n2_attr = f"mmp_n2_{i+1}"
        d_attr = f"mmp_d_{i+1}"
        
        if hasattr(ptv_params, n2_attr) and hasattr(ptv_params, d_attr):
            n2_val = getattr(ptv_params, n2_attr)
            d_val = getattr(ptv_params, d_attr)
            
            if n2_val is not None and d_val is not None:
                n2_values.append(n2_val)
                d_values.append(d_val)
    
    if n2_values:
        mm_params.set_layers(n2_values, d_values)
    
    return cpar


def create_sequence_params_from_yaml(yaml_params):
    """
    Create a SequenceParams object directly from YAML parameters.
    
    Args:
        yaml_params: Dictionary of YAML parameter objects
        
    Returns:
        SequenceParams object
    """
    seq_params = yaml_params.get("SequenceParams")
    ptv_params = yaml_params.get("PtvParams")
    
    # Create sequence params with the number of cameras
    spar = SequenceParams(num_cams=ptv_params.n_img)
    
    # Set frame range
    spar.set_first(seq_params.Seq_First)
    spar.set_last(seq_params.Seq_Last)
    
    # Set image base names
    for i in range(ptv_params.n_img):
        img_name_attr = f"Name_{i+1}_Seq"
        if hasattr(seq_params, img_name_attr):
            img_name = getattr(seq_params, img_name_attr)
            spar.set_img_base_name(i, img_name)
    
    return spar


def create_volume_params_from_yaml(yaml_params):
    """
    Create a VolumeParams object directly from YAML parameters.
    
    Args:
        yaml_params: Dictionary of YAML parameter objects
        
    Returns:
        VolumeParams object
    """
    criteria_params = yaml_params.get("CriteriaParams")
    
    # Create volume params
    vpar = VolumeParams()
    
    # Set X_lay
    vpar.set_X_lay([criteria_params.X_lay])
    
    # Set Z bounds
    vpar.set_Zmin_lay([criteria_params.Zmin_lay])
    vpar.set_Zmax_lay([criteria_params.Zmax_lay])
    
    # Set Y bounds
    vpar.set_Ymin_lay([criteria_params.Ymin_lay])
    vpar.set_Ymax_lay([criteria_params.Ymax_lay])
    
    # Set X bounds
    vpar.set_Xmin_lay([criteria_params.Xmin_lay])
    vpar.set_Xmax_lay([criteria_params.Xmax_lay])
    
    # Set correspondence parameters
    vpar.set_cn(criteria_params.cn)
    vpar.set_cnx(criteria_params.cnx)
    vpar.set_cny(criteria_params.cny)
    vpar.set_csumg(criteria_params.csumg)
    vpar.set_eps0(criteria_params.eps0)
    vpar.set_corrmin(criteria_params.corrmin)
    
    return vpar


def create_tracking_params_from_yaml(yaml_params):
    """
    Create a TrackingParams object directly from YAML parameters.
    
    Args:
        yaml_params: Dictionary of YAML parameter objects
        
    Returns:
        TrackingParams object
    """
    track_params = yaml_params.get("TrackingParams")
    
    # Create tracking params
    tpar = TrackingParams()
    
    # Set velocity limits
    tpar.set_dvxmin(track_params.dvxmin)
    tpar.set_dvxmax(track_params.dvxmax)
    tpar.set_dvymin(track_params.dvymin)
    tpar.set_dvymax(track_params.dvymax)
    tpar.set_dvzmin(track_params.dvzmin)
    tpar.set_dvzmax(track_params.dvzmax)
    
    # Set angle and acceleration limits
    tpar.set_dangle(track_params.angle)
    tpar.set_dacc(track_params.dacc)
    
    # Set add particle flag
    tpar.set_add(1 if track_params.flagNewParticles else 0)
    
    return tpar


def create_target_params_from_yaml(yaml_params):
    """
    Create a TargetParams object directly from YAML parameters.
    
    Args:
        yaml_params: Dictionary of YAML parameter objects
        
    Returns:
        TargetParams object
    """
    targ_rec_params = yaml_params.get("TargetParams")
    ptv_params = yaml_params.get("PtvParams")
    
    # Create target params object
    target_par = TargetParams(ptv_params.n_img)
    
    # Set threshold for each camera
    thresholds = []
    for i in range(ptv_params.n_img):
        threshold_attr = f"gvth_{i+1}"
        if hasattr(targ_rec_params, threshold_attr):
            thresholds.append(getattr(targ_rec_params, threshold_attr))
        else:
            # Use a default if not found
            thresholds.append(0)
    
    target_par.set_grey_thresholds(thresholds)
    
    # Set size constraints
    target_par.set_pixel_count_bounds((targ_rec_params.nnmin, targ_rec_params.nnmax))
    target_par.set_xsize_bounds((targ_rec_params.nxmin, targ_rec_params.nxmax))
    target_par.set_ysize_bounds((targ_rec_params.nymin, targ_rec_params.nymax))
    
    # Set other parameters
    target_par.set_max_discontinuity(targ_rec_params.discont)
    target_par.set_min_sum_grey(targ_rec_params.sumg_min)
    target_par.set_cross_size(targ_rec_params.cr_sz)
    
    return target_par


def create_calibration_from_files(cpar, exp_path):
    """
    Create calibration objects for each camera from calibration files.
    
    Args:
        cpar: ControlParams object
        exp_path: Path to experiment directory
        
    Returns:
        List of Calibration objects
    """
    cals = []
    exp_path = Path(exp_path)
    
    for i_cam in range(cpar.get_num_cams()):
        cal = Calibration()
        cal_img_base = cpar.get_cal_img_base_name(i_cam)
        
        # Full path to calibration files
        ori_path = exp_path / "cal" / f"{cal_img_base}.ori"
        addpar_path = exp_path / "cal" / f"{cal_img_base}.addpar"
        
        # Convert to byte strings for the C interface
        ori_path_bytes = str(ori_path).encode()
        addpar_path_bytes = str(addpar_path).encode()
        
        # Load calibration from files
        cal.from_file(ori_path_bytes, addpar_path_bytes)
        cals.append(cal)
    
    return cals


def create_examine_params():
    """
    Create examine parameters.
    
    Returns:
        ExamineParams object
    """
    # For now, we still need to use the file reading for ExamineParams
    # as it doesn't have a complete Python wrapper
    epar = par.ExamineParams()
    epar.read()
    
    return epar


def create_all_params_from_yaml(exp_path):
    """
    Create all parameter objects directly from YAML parameters.
    
    Args:
        exp_path: Path to experiment directory
        
    Returns:
        Tuple of parameter objects (cpar, spar, vpar, track_par, tpar, cals, epar)
    """
    # Load YAML parameters from unified YAML file
    params_dir = Path(exp_path) / "parameters"
    param_manager = ParameterManager(params_dir, unified=True)
    yaml_params = param_manager.load_all()
    
    # Create parameter objects
    cpar = create_control_params_from_yaml(yaml_params)
    spar = create_sequence_params_from_yaml(yaml_params)
    vpar = create_volume_params_from_yaml(yaml_params)
    track_par = create_tracking_params_from_yaml(yaml_params)
    tpar = create_target_params_from_yaml(yaml_params)
    
    # Create calibration objects
    cals = create_calibration_from_files(cpar, exp_path)
    
    # Create examine parameters
    epar = create_examine_params()
    
    return cpar, spar, vpar, track_par, tpar, cals, epar