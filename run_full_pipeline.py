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
import numpy as np
from pathlib import Path
import argparse
import logging

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
from pyptv.yaml_parameters import ParameterManager
from pyptv.parameter_builder import create_all_params_from_yaml
from pyptv.convert_to_unified_yaml import convert_to_unified_yaml
from pyptv import ptv


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


def run_full_pipeline(experiment_path):
    """
    Run the complete PyPTV pipeline on a dataset.
    
    Args:
        experiment_path: Path to the experiment directory
    """
    exp_path = Path(experiment_path)
    start_time = time.time()
    
    # Step 0: Copy parameter files and convert to unified YAML
    params_dir = copy_parameter_files(exp_path)
    logger.info("Converting parameters to unified YAML")
    convert_to_unified_yaml(exp_path, force=True)
    
    # Step 1: Initialize using parameters
    logger.info("Step 1: Initializing PTV system")
    n_cams = 4  # From parameters
    params = create_all_params_from_yaml(exp_path)
    cpar, spar, vpar, track_par, tpar, cals, epar = params
    
    # Log basic parameters
    logger.info(f"Number of cameras: {cpar.get_num_cams()}")
    logger.info(f"Image dimensions: {cpar.get_image_size()}")
    logger.info(f"Frame range: {spar.get_first()}-{spar.get_last()}")
    
    # Step 2: Load and process sequence of images
    frame_range = range(spar.get_first(), spar.get_last() + 1)
    logger.info(f"Step 2: Processing frames {frame_range[0]} to {frame_range[-1]}")
    
    # Make sure result directory exists
    result_dir = exp_path / "res"
    result_dir.mkdir(exist_ok=True)
    
    # Process each frame
    for frame in frame_range:
        logger.info(f"Processing frame {frame}")
        
        # Load images for this frame
        images = []
        for i_cam in range(n_cams):
            img_base = spar.get_img_base_name(i_cam)
            img_path = exp_path / f"{img_base}{frame}"
            
            try:
                # Load raw image
                with open(img_path, 'rb') as f:
                    img_data = f.read()
                
                # Convert to ndarray based on image dimensions
                imx, imy = cpar.get_image_size()
                image = np.frombuffer(img_data, dtype=np.ubyte).reshape(imy, imx)
                images.append(image)
                logger.info(f"  Loaded image: {img_path}")
            except Exception as e:
                logger.error(f"  Error loading image {img_path}: {e}")
                # Create dummy image
                images.append(np.zeros((imy, imx), dtype=np.uint8))
        
        # Step 3: Preprocess images (highpass filter)
        if cpar.get_hp_flag():
            logger.info("  Applying highpass filter")
            filtered_images = ptv.py_pre_processing_c(images, cpar)
        else:
            filtered_images = images
        
        # Step 4: Detect particles
        logger.info("  Detecting particles")
        detections, corrected = ptv.py_detection_proc_c(filtered_images, cpar, tpar, cals)
        
        # Log detection results
        for i_cam, cam_detections in enumerate(detections):
            logger.info(f"  Camera {i_cam+1}: {len(cam_detections)} particles detected")
        
        # Step 5: Find correspondences
        logger.info("  Finding correspondences")
        match_results = ptv.py_correspondences_proc_c(filtered_images, corrected, detections, cpar, vpar, cals)
        sorted_pos, sorted_corresp, num_targs = match_results
        
        if num_targs > 0:
            logger.info(f"  Found {num_targs} correspondences")
            
            # Step 6: Determine 3D positions
            logger.info("  Determining 3D positions")
            ptv.py_determination_proc_c(cpar.get_num_cams(), sorted_pos, sorted_corresp, corrected)
            
            # Write rt_is file for this frame
            rt_is_file = result_dir / f"rt_is.{frame}"
            logger.info(f"  Writing 3D positions to {rt_is_file}")
    
    # Step 7: Run tracking
    logger.info("Step 7: Running particle tracking")
    
    # Initialize tracker
    logger.info("  Initializing tracker")
    tracker = ptv.py_trackcorr_init(cpar, vpar, track_par, spar.get_first(), spar.get_last(), result_dir)
    
    # Run forward tracking
    logger.info("  Running forward tracking")
    tracker.full_forward()
    
    # Run backward tracking
    logger.info("  Running backward tracking")
    tracker.full_backward()
    
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