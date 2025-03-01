#!/usr/bin/env python
"""
Simplified full PyPTV pipeline runner script.

This script demonstrates the unified YAML parameter approach without requiring
the optv module to be installed.

Usage:
    python run_full_pipeline_simple.py [experiment_path]

Example:
    python run_full_pipeline_simple.py tests/test_cavity
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


def process_frame_dummy(frame, base_names, res_dir):
    """
    Simulated frame processing for demonstration purposes.
    
    Args:
        frame: Frame number to process
        base_names: List of base names for image files
        res_dir: Directory to save results
    """
    logger.info(f"Processing frame {frame}")
    
    # Simulate loading images
    logger.info("  Loading images")
    for i, base in enumerate(base_names):
        logger.info(f"    Camera {i+1}: {base}{frame}")
    
    # Simulate preprocessing
    logger.info("  Applying high-pass filter")
    
    # Simulate detection
    logger.info("  Detecting particles")
    detections = [np.random.randint(50, 150) for _ in range(len(base_names))]
    for i, count in enumerate(detections):
        logger.info(f"    Camera {i+1}: {count} particles detected")
    
    # Simulate correspondence
    logger.info("  Finding correspondences")
    n_corresp = np.random.randint(20, 50)
    logger.info(f"    Found {n_corresp} correspondences")
    
    # Simulate writing results
    rt_is_file = res_dir / f"rt_is.{frame}"
    logger.info(f"    Writing 3D positions to {rt_is_file}")
    
    # Actually write a dummy file for demonstration
    with open(rt_is_file, 'w') as f:
        f.write(f"{n_corresp}\n")
        for i in range(n_corresp):
            x = np.random.uniform(-10, 10)
            y = np.random.uniform(-10, 10)
            z = np.random.uniform(-10, 10)
            f.write(f"{x:.6f} {y:.6f} {z:.6f}\n")


def run_full_pipeline(experiment_path):
    """
    Run the simplified PyPTV pipeline on a dataset.
    
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
    ptv_params = unified_params.get('PtvParams', {})
    logger.info(f"PTV Parameters:")
    logger.info(f"  Number of cameras: {ptv_params.get('n_img', 0)}")
    logger.info(f"  Image dimensions: {ptv_params.get('imx', 0)}x{ptv_params.get('imy', 0)}")
    logger.info(f"  Pixel size: {ptv_params.get('pix_x', 0)}x{ptv_params.get('pix_y', 0)} mm")
    logger.info(f"  High-pass filter: {'Enabled' if ptv_params.get('hp_flag', False) else 'Disabled'}")
    
    # SequenceParams
    seq_params = unified_params.get('SequenceParams', {})
    logger.info(f"Sequence Parameters:")
    logger.info(f"  Frame range: {seq_params.get('first', 0)}-{seq_params.get('last', 0)}")
    logger.info(f"  Base names: {seq_params.get('base_name', [])}")
    
    # TrackingParams
    track_params = unified_params.get('TrackingParams', {})
    logger.info(f"Tracking Parameters:")
    logger.info(f"  Velocity limits X: {track_params.get('dvxmin', 0)} to {track_params.get('dvxmax', 0)}")
    logger.info(f"  Velocity limits Y: {track_params.get('dvymin', 0)} to {track_params.get('dvymax', 0)}")
    logger.info(f"  Velocity limits Z: {track_params.get('dvzmin', 0)} to {track_params.get('dvzmax', 0)}")
    logger.info(f"  Angle limit: {track_params.get('angle', 0)}")
    logger.info(f"  Acceleration limit: {track_params.get('dacc', 0)}")
    
    # TargetParams
    target_params = unified_params.get('TargetParams', {})
    logger.info(f"Target Parameters:")
    logger.info(f"  Gray value thresholds: {[target_params.get(f'gvth_{i+1}', 0) for i in range(4)]}")
    logger.info(f"  Particle size limits: {target_params.get('nnmin', 0)} to {target_params.get('nnmax', 0)} pixels")
    
    # CriteriaParams
    criteria_params = unified_params.get('CriteriaParams', {})
    logger.info(f"Criteria Parameters:")
    logger.info(f"  Volume limits X: {criteria_params.get('Xmin_lay', 0)} to {criteria_params.get('Xmax_lay', 0)}")
    logger.info(f"  Volume limits Y: {criteria_params.get('Ymin_lay', 0)} to {criteria_params.get('Ymax_lay', 0)}")
    logger.info(f"  Volume limits Z: {criteria_params.get('Zmin_lay', 0) if isinstance(criteria_params.get('Zmin_lay'), (int, float)) else criteria_params.get('Zmin_lay')}"
               f" to {criteria_params.get('Zmax_lay', 0) if isinstance(criteria_params.get('Zmax_lay'), (int, float)) else criteria_params.get('Zmax_lay')}")
    
    logger.info("\nStarting simulated pipeline with the unified parameters")
    
    # Create results directory
    res_dir = exp_path / "res"
    res_dir.mkdir(exist_ok=True)
    
    # Get sequence information
    n_cams = ptv_params.get('n_img', 4)
    first_frame = seq_params.get('first', 10001)
    last_frame = seq_params.get('last', 10004)
    base_names = seq_params.get('base_name', [])
    
    # Process each frame (simulated)
    for frame in range(first_frame, last_frame + 1):
        process_frame_dummy(frame, base_names, res_dir)
    
    # Simulate tracking
    logger.info("\nRunning simulated tracking")
    logger.info("  Forward tracking completed")
    logger.info("  Backward tracking completed")
    
    # Simulate writing trajectory file
    trajectories = np.random.randint(10, 30)
    ptv_is_file = res_dir / "ptv_is"
    with open(ptv_is_file, 'w') as f:
        f.write(f"{trajectories}\n")
    
    logger.info(f"Found {trajectories} trajectories")
    
    # Report completion time
    elapsed_time = time.time() - start_time
    logger.info(f"\nPipeline completed in {elapsed_time:.2f} seconds")


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Run a simplified PyPTV pipeline on a dataset"
    )
    parser.add_argument(
        "experiment_path", 
        help="Path to the experiment directory", 
        nargs='?', 
        default="tests/test_cavity"
    )
    
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