#!/usr/bin/env python
"""
Full PyPTV pipeline runner script.

This script performs the complete PyPTV pipeline on a dataset:
1. Initialize using parameters
2. Read sequence of images
3. Detect particles in those images
4. Find correspondences
5. Run tracking forward and backward

Usage:
    python run_full_pipeline.py [experiment_path]

Example:
    python run_full_pipeline.py tests/test_cavity
"""

import os
import sys
import time
import shutil
import yaml
import numpy as np
from pathlib import Path
import argparse
import logging
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('pyptv_pipeline')

# Add current directory to path
sys.path.insert(0, os.path.abspath('.'))

# Import PyPTV modules
from pyptv.yaml_parameters import ParameterManager, UNIFIED_YAML_FILENAME
from pyptv.convert_to_unified_yaml import convert_to_unified_yaml

# Try to import optv modules
HAS_OPTV = False
try:
    from optv.parameters import ControlParams, VolumeParams, TrackingParams, SequenceParams, TargetParams
    from optv.calibration import Calibration
    from optv.imgcoord import image_coordinates
    from optv.tracking import trackback_c
    from optv.orientation import match_detection_to_ref
    import optv.correspondences as correspond
    import optv.image_processing as img_process
    import optv.tracker as tracker
    import optv.tracking_framebuf as tracking_fb
    HAS_OPTV = True
except ImportError:
    logger.warning("optv module not found. Only parameter display will be available.")


def copy_parameter_files(experiment_path, params_subdir="parametersRun1"):
    """
    Copy parameter files from the specified subdirectory to 'parameters'.
    
    Args:
        experiment_path: Path to the experiment directory
        params_subdir: Subdirectory containing parameter files to use
        
    Returns:
        Path to the parameters directory
    """
    exp_path = Path(experiment_path)
    source_params_dir = exp_path / params_subdir
    target_params_dir = exp_path / "parameters"
    
    # Check if source directory exists
    if not source_params_dir.exists():
        raise FileNotFoundError(f"Parameter directory {source_params_dir} not found")
    
    # Create target directory if it doesn't exist
    target_params_dir.mkdir(exist_ok=True)
    
    # Copy all files from source to target
    logger.info(f"Copying parameter files from {source_params_dir} to {target_params_dir}")
    for file_path in source_params_dir.glob("*.*"):
        target_file = target_params_dir / file_path.name
        shutil.copy2(file_path, target_file)
        logger.info(f"Copied {file_path.name}")
    
    return target_params_dir


def create_params_from_yaml(unified_params, exp_path):
    """
    Create optv parameter objects from unified YAML parameters.
    
    Args:
        unified_params: Dictionary with unified parameters
        exp_path: Path to experiment directory
        
    Returns:
        Tuple of parameter objects (cpar, spar, vpar, track_par, tpar, cals)
    """
    # Extract individual parameter sections
    ptv_params = unified_params.get('PtvParams', {})
    track_params = unified_params.get('TrackingParams', {})
    seq_params = unified_params.get('SequenceParams', {})
    criteria_params = unified_params.get('CriteriaParams', {})
    target_params = unified_params.get('TargetParams', {})
    
    # Create control parameters
    n_img = ptv_params.get('n_img', 4)
    cpar = ControlParams(n_img)
    
    # Set image dimensions
    imx = ptv_params.get('imx', 1280)
    imy = ptv_params.get('imy', 1024)
    cpar.set_image_size((imx, imy))
    
    # Set pixel size
    pix_x = ptv_params.get('pix_x', 0.012)
    pix_y = ptv_params.get('pix_y', 0.012)
    cpar.set_pixel_size((pix_x, pix_y))
    
    # Set flags
    cpar.set_hp_flag(ptv_params.get('hp_flag', True))
    cpar.set_allCam_flag(ptv_params.get('allcam_flag', False))
    cpar.set_tiff_flag(ptv_params.get('tiff_flag', True))
    cpar.set_chfield(ptv_params.get('chfield', 0))
    
    # Set calibration image paths
    cal_img_base_names = ptv_params.get('img_cal', [])
    for i in range(min(n_img, len(cal_img_base_names))):
        cpar.set_cal_img_base_name(i, cal_img_base_names[i])
    
    # Set multimedia parameters
    mm_params = cpar.get_multimedia_params()
    mm_params.set_n1(ptv_params.get('mmp_n1', 1.0))
    mm_params.set_n2([ptv_params.get('mmp_n2', 1.33)])
    mm_params.set_n3(ptv_params.get('mmp_n3', 1.46))
    mm_params.set_d([ptv_params.get('mmp_d', 6.0)])
    
    # Create sequence parameters
    spar = SequenceParams(n_img)
    
    # Set frame range
    first_frame = seq_params.get('first', 10001)
    last_frame = seq_params.get('last', 10004)
    spar.set_first(first_frame)
    spar.set_last(last_frame)
    
    # Set image base names
    base_names = seq_params.get('base_name', [])
    for i in range(min(n_img, len(base_names))):
        spar.set_img_base_name(i, base_names[i])
    
    # Create volume parameters
    vpar = VolumeParams()
    
    # Set volume limits
    vpar.set_X_lay([criteria_params.get('X_lay', [0])[0]])
    vpar.set_Zmin_lay([criteria_params.get('Zmin_lay', -10.0) if isinstance(criteria_params.get('Zmin_lay'), (int, float)) else criteria_params.get('Zmin_lay', [-10.0])[0]])
    vpar.set_Zmax_lay([criteria_params.get('Zmax_lay', 10.0) if isinstance(criteria_params.get('Zmax_lay'), (int, float)) else criteria_params.get('Zmax_lay', [10.0])[0]])
    vpar.set_Ymin_lay([criteria_params.get('Ymin_lay', -10.0)])
    vpar.set_Ymax_lay([criteria_params.get('Ymax_lay', 10.0)])
    vpar.set_Xmin_lay([criteria_params.get('Xmin_lay', -10.0)])
    vpar.set_Xmax_lay([criteria_params.get('Xmax_lay', 10.0)])
    
    # Set correspondence parameters
    vpar.set_cn(criteria_params.get('cn', 0.0))
    vpar.set_eps0(criteria_params.get('eps0', 0.1))
    
    # Create tracking parameters
    track_par = TrackingParams()
    
    # Set velocity limits
    track_par.set_dvxmin(track_params.get('dvxmin', -10.0))
    track_par.set_dvxmax(track_params.get('dvxmax', 10.0))
    track_par.set_dvymin(track_params.get('dvymin', -10.0))
    track_par.set_dvymax(track_params.get('dvymax', 10.0))
    track_par.set_dvzmin(track_params.get('dvzmin', -10.0))
    track_par.set_dvzmax(track_params.get('dvzmax', 10.0))
    
    # Set angle and acceleration limits
    track_par.set_dangle(track_params.get('angle', 0.0))
    track_par.set_dacc(track_params.get('dacc', 0.9))
    
    # Set add particle flag
    track_par.set_add(1 if track_params.get('flagNewParticles', True) else 0)
    
    # Create target parameters
    tpar = TargetParams(n_img)
    
    # Set gray value thresholds for each camera
    thresholds = []
    for i in range(n_img):
        thresh_key = f'gvth_{i+1}'
        thresholds.append(target_params.get(thresh_key, 10))
    
    tpar.set_grey_thresholds(thresholds)
    
    # Set size constraints
    nnmin = target_params.get('nnmin', 4)
    nnmax = target_params.get('nnmax', 500)
    tpar.set_pixel_count_bounds((nnmin, nnmax))
    
    nxmin = target_params.get('nxmin', 2)
    nxmax = target_params.get('nxmax', 100)
    tpar.set_xsize_bounds((nxmin, nxmax))
    
    nymin = target_params.get('nymin', 2)
    nymax = target_params.get('nymax', 100)
    tpar.set_ysize_bounds((nymin, nymax))
    
    # Set other parameters
    tpar.set_min_sum_grey(target_params.get('sumg_min', 150))
    tpar.set_cross_size(target_params.get('cr_sz', 2))
    
    # Create calibration objects
    cals = []
    cal_dir = exp_path / "cal"
    
    if cal_dir.exists():
        for i_cam in range(n_img):
            cal = Calibration()
            cal_img_name = cpar.get_cal_img_base_name(i_cam)
            
            # Check for orientation file
            ori_file = cal_dir / f"{cal_img_name}.ori"
            add_file = cal_dir / f"{cal_img_name}.addpar"
            
            # Convert to byte strings for C interface
            ori_file_str = str(ori_file)
            add_file_str = str(add_file)
            
            # Load calibration if files exist
            if ori_file.exists() and add_file.exists():
                try:
                    cal.from_file(ori_file_str.encode(), add_file_str.encode())
                    cals.append(cal)
                except Exception as e:
                    logger.error(f"Error loading calibration for camera {i_cam+1}: {e}")
                    cals.append(None)
            else:
                logger.warning(f"Calibration files not found for camera {i_cam+1}")
                cals.append(None)
    else:
        logger.warning(f"Calibration directory not found: {cal_dir}")
        for _ in range(n_img):
            cals.append(None)
    
    return cpar, spar, vpar, track_par, tpar, cals


def load_image(img_path, imx, imy):
    """
    Load an image from a file.
    
    Args:
        img_path: Path to the image file
        imx: Image width
        imy: Image height
        
    Returns:
        numpy array with image data
    """
    try:
        # Try to load image as raw data
        with open(img_path, 'rb') as f:
            img_data = f.read()
        
        # Convert to numpy array with proper dimensions
        return np.frombuffer(img_data, dtype=np.ubyte).reshape(imy, imx)
    except Exception as e:
        logger.error(f"Error loading image {img_path}: {e}")
        return np.zeros((imy, imx), dtype=np.uint8)


def run_full_pipeline(experiment_path):
    """
    Run the complete PyPTV pipeline on a dataset.
    
    Args:
        experiment_path: Path to the experiment directory
    """
    exp_path = Path(experiment_path)
    start_time = time.time()
    
    # Step 0: Convert to unified YAML if needed
    params_dir = exp_path / "parameters"
    if not params_dir.exists():
        logger.error(f"Parameters directory not found: {params_dir}")
        return
    
    logger.info("Converting parameters to unified YAML")
    unified_yaml_path = convert_to_unified_yaml(exp_path, force=True)
    
    # Load and display the unified YAML file
    with open(unified_yaml_path, 'r') as f:
        unified_params = yaml.safe_load(f)
    
    # Log info about the loaded parameters
    logger.info("Successfully loaded unified YAML parameters")
    
    # PtvParams
    if 'PtvParams' in unified_params:
        ptv_params = unified_params['PtvParams']
        logger.info(f"PTV Parameters:")
        logger.info(f"  Number of cameras: {ptv_params.get('n_img', 0)}")
        logger.info(f"  Image dimensions: {ptv_params.get('imx', 0)}x{ptv_params.get('imy', 0)}")
        logger.info(f"  Pixel size: {ptv_params.get('pix_x', 0)}x{ptv_params.get('pix_y', 0)} mm")
        logger.info(f"  High-pass filter: {'Enabled' if ptv_params.get('hp_flag', False) else 'Disabled'}")
    
    # SequenceParams
    if 'SequenceParams' in unified_params:
        seq_params = unified_params['SequenceParams']
        logger.info(f"Sequence Parameters:")
        logger.info(f"  Frame range: {seq_params.get('first', 0)}-{seq_params.get('last', 0)}")
        logger.info(f"  Base names: {seq_params.get('base_name', [])}")
    
    # TrackingParams
    if 'TrackingParams' in unified_params:
        track_params = unified_params['TrackingParams']
        logger.info(f"Tracking Parameters:")
        logger.info(f"  Velocity limits X: {track_params.get('dvxmin', 0)} to {track_params.get('dvxmax', 0)}")
        logger.info(f"  Velocity limits Y: {track_params.get('dvymin', 0)} to {track_params.get('dvymax', 0)}")
        logger.info(f"  Velocity limits Z: {track_params.get('dvzmin', 0)} to {track_params.get('dvzmax', 0)}")
        logger.info(f"  Angle limit: {track_params.get('angle', 0)}")
        logger.info(f"  Acceleration limit: {track_params.get('dacc', 0)}")
    
    # TargetParams
    if 'TargetParams' in unified_params:
        target_params = unified_params['TargetParams']
        logger.info(f"Target Parameters:")
        logger.info(f"  Gray value thresholds: {[target_params.get(f'gvth_{i+1}', 0) for i in range(4)]}")
        logger.info(f"  Particle size limits: {target_params.get('nnmin', 0)} to {target_params.get('nnmax', 0)} pixels")
    
    # CriteriaParams
    if 'CriteriaParams' in unified_params:
        criteria_params = unified_params['CriteriaParams']
        logger.info(f"Criteria Parameters:")
        logger.info(f"  Volume limits X: {criteria_params.get('Xmin_lay', 0)} to {criteria_params.get('Xmax_lay', 0)}")
        logger.info(f"  Volume limits Y: {criteria_params.get('Ymin_lay', 0)} to {criteria_params.get('Ymax_lay', 0)}")
        logger.info(f"  Volume limits Z: {criteria_params.get('Zmin_lay', 0) if isinstance(criteria_params.get('Zmin_lay'), (int, float)) else criteria_params.get('Zmin_lay')}"
                   f" to {criteria_params.get('Zmax_lay', 0) if isinstance(criteria_params.get('Zmax_lay'), (int, float)) else criteria_params.get('Zmax_lay')}")
    
    # Check if optv module is available for full processing
    if not HAS_OPTV:
        logger.info("")
        logger.info("Note: optv module not available. Only parameter display is shown.")
        elapsed_time = time.time() - start_time
        logger.info(f"Pipeline completed in {elapsed_time:.2f} seconds")
        return
    
    # Create parameter objects from YAML
    try:
        logger.info("Creating parameter objects from YAML")
        cpar, spar, vpar, track_par, tpar, cals = create_params_from_yaml(unified_params, exp_path)
        
        # Get sequence information
        n_cams = cpar.get_num_cams()
        frame_range = range(spar.get_first(), spar.get_last() + 1)
        imx, imy = cpar.get_image_size()
        
        logger.info(f"Processing frames {frame_range[0]} to {frame_range[-1]}")
        
        # Ensure results directory exists
        res_dir = exp_path / "res"
        res_dir.mkdir(exist_ok=True)
        
        # Process each frame
        for frame in frame_range:
            logger.info(f"Processing frame {frame}")
            
            # Load images for this frame
            images = []
            for i_cam in range(n_cams):
                img_base = spar.get_img_base_name(i_cam)
                img_path = exp_path / f"{img_base}{frame}"
                
                # Load the image
                image = load_image(img_path, imx, imy)
                images.append(image)
            
            # Pre-process images (high-pass filter)
            filtered_images = []
            if cpar.get_hp_flag():
                logger.info("  Applying high-pass filter")
                for i_cam, image in enumerate(images):
                    filtered = img_process.preprocess(image, "highpass", cpar)
                    filtered_images.append(filtered)
            else:
                filtered_images = images
            
            # Detect particles
            logger.info("  Detecting particles")
            detections = []
            for i_cam, image in enumerate(filtered_images):
                # Create target array
                targs = img_process.detection(image, tpar, i_cam)
                logger.info(f"    Camera {i_cam+1}: {len(targs)} particles detected")
                detections.append(targs)
            
            # Find correspondences using the detected particles
            logger.info("  Finding correspondences")
            
            if all(cals[i] is not None for i in range(n_cams)):
                # Get corrected coordinates
                logger.info("    Converting to metric coordinates")
                flat_coords = []
                for i_cam, targs in enumerate(detections):
                    # Convert from image to flat coordinates
                    flat_targs = np.array([t.pos() for t in targs])
                    flat_coords.append(flat_targs)
                
                logger.info("    Finding correspondences")
                # Find correspondences
                match_pts, corresp = correspond.correspond(
                    flat_coords, cals, vpar
                )
                
                if len(match_pts) > 0:
                    logger.info(f"    Found {len(match_pts)} correspondences")
                    
                    # Write rt_is file
                    rt_is_file = res_dir / f"rt_is.{frame}"
                    logger.info(f"    Writing 3D positions to {rt_is_file}")
                    
                    with open(rt_is_file, 'w') as f:
                        f.write(f"{len(match_pts)}\n")
                        for pt in match_pts:
                            f.write(f"{pt[0]} {pt[1]} {pt[2]}\n")
                else:
                    logger.warning(f"    No correspondences found for frame {frame}")
            else:
                logger.error("    Skipping correspondences due to missing calibration")
        
        # Initialize tracking framebuffer
        logger.info("Initializing tracking")
        fb = tracking_fb.read_track_init(
            res_dir, frame_range[0], frame_range[-1], track_par
        )
        
        # Run tracking
        logger.info("Running tracking")
        tr = tracker.Tracker(fb, track_par)
        tr.full_forward()
        tr.full_backward()
        
        logger.info("Tracking completed")
        
        # Report statistics
        try:
            # Read ptv_is to get trajectory info
            trajfile = res_dir / "ptv_is"
            if trajfile.exists():
                with open(trajfile, 'r') as f:
                    num_traj = int(f.readline().strip())
                    logger.info(f"Found {num_traj} trajectories")
        except Exception as e:
            logger.error(f"Error reading trajectory file: {e}")
        
    except Exception as e:
        logger.error(f"Error in pipeline: {e}")
        logger.error(traceback.format_exc())
    
    # Report completion time
    elapsed_time = time.time() - start_time
    logger.info(f"Pipeline completed in {elapsed_time:.2f} seconds")


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(description="Run the complete PyPTV pipeline on a dataset")
    parser.add_argument("experiment_path", help="Path to the experiment directory", 
                      nargs='?', default="tests/test_cavity")
    
    args = parser.parse_args()
    
    try:
        run_full_pipeline(args.experiment_path)
    except Exception as e:
        logger.error(f"Error running pipeline: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()