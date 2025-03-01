#!/usr/bin/env python
"""
Debugging script for PyPTV initialization procedure.
This script allows detailed inspection of the initialization process.
"""

import os
import sys
from pathlib import Path
import traceback
import time
import argparse
import logging

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('pyptv_debug')

# Import PyPTV components
sys.path.insert(0, '.')
from pyptv.ui.ptv_core import PTVCore
from pyptv.yaml_parameters import ParameterManager

def debug_parameters(param_path):
    """Debug the parameter loading process."""
    logger.info(f"Debugging parameters at: {param_path}")
    
    # Check if parameters directory exists
    if not os.path.isdir(param_path):
        logger.error(f"Parameters directory not found: {param_path}")
        return False
    
    # List files in parameters directory
    logger.info("Files in parameters directory:")
    for f in os.listdir(param_path):
        logger.info(f"  - {f}")
    
    # Try to load parameters
    try:
        param_manager = ParameterManager(param_path)
        logger.info("Parameter manager created successfully")
        
        # Try to load all parameters
        logger.info("Loading all parameters...")
        yaml_params = param_manager.load_all()
        
        # Log loaded parameter types
        logger.info(f"Successfully loaded parameter types: {list(yaml_params.keys())}")
        
        # Examine PTV parameters in detail
        if "PtvParams" in yaml_params:
            ptv_params = yaml_params.get("PtvParams")
            logger.info(f"PTV Parameters:")
            logger.info(f"  - Number of cameras: {ptv_params.n_img}")
            logger.info(f"  - Image dimensions: {ptv_params.imx}x{ptv_params.imy}")
            logger.info(f"  - Highpass filter: {'Enabled' if ptv_params.hp_flag else 'Disabled'}")
        
        # Examine sequence parameters
        if "SequenceParams" in yaml_params:
            seq_params = yaml_params.get("SequenceParams")
            logger.info(f"Sequence Parameters:")
            logger.info(f"  - Frame range: {seq_params.Seq_First}-{seq_params.Seq_Last}")
            
            # Check camera image names
            for i in range(1, 5):  # Assuming up to 4 cameras
                image_attr = f"Name_{i}_Image"
                seq_attr = f"Name_{i}_Seq"
                if hasattr(seq_params, image_attr):
                    logger.info(f"  - Camera {i} image: {getattr(seq_params, image_attr)}")
                if hasattr(seq_params, seq_attr):
                    logger.info(f"  - Camera {i} sequence: {getattr(seq_params, seq_attr)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error loading parameters: {e}")
        logger.error(traceback.format_exc())
        return False

def debug_initialization(exp_path, step_by_step=False):
    """Debug the initialization process."""
    logger.info(f"Debugging initialization for experiment at: {exp_path}")
    
    # Debug parameters first
    param_path = os.path.join(exp_path, "parameters")
    if not debug_parameters(param_path):
        logger.warning("Parameter debugging failed, but continuing with initialization")
    
    # Create PTVCore
    try:
        logger.info("Creating PTVCore instance...")
        start_time = time.time()
        core = PTVCore(exp_path)
        logger.info(f"PTVCore created in {time.time() - start_time:.2f} seconds")
        
        # Check plugin loading
        logger.info(f"Loaded plugins: {core.plugins}")
        
        if step_by_step:
            input("Press Enter to continue to parameter loading...")
        
        # Load YAML parameters
        try:
            logger.info("Loading YAML parameters...")
            start_time = time.time()
            yaml_params = core.load_yaml_parameters()
            logger.info(f"Parameters loaded in {time.time() - start_time:.2f} seconds")
            logger.info(f"Loaded parameter types: {list(yaml_params.keys())}")
        except Exception as e:
            logger.error(f"Error loading YAML parameters: {e}")
            logger.error(traceback.format_exc())
        
        if step_by_step:
            input("Press Enter to continue to full initialization...")
        
        # Full initialization
        try:
            logger.info("Starting full initialization...")
            start_time = time.time()
            images = core.initialize()
            logger.info(f"Initialization completed in {time.time() - start_time:.2f} seconds")
            logger.info(f"Got {len(images)} camera images")
            
            # Check if initialization was successful
            logger.info(f"Initialization flag: {core.initialized}")
            if core.initialized:
                logger.info(f"Number of cameras: {core.n_cams}")
                # Check core components
                logger.info("Core components loaded:")
                logger.info(f"  - cpar: {core.cpar is not None}")
                logger.info(f"  - vpar: {core.vpar is not None}")
                logger.info(f"  - track_par: {core.track_par is not None}")
                logger.info(f"  - spar: {core.spar is not None}")
            
        except Exception as e:
            logger.error(f"Error during initialization: {e}")
            logger.error(traceback.format_exc())
        
        return core
        
    except Exception as e:
        logger.error(f"Error creating PTVCore: {e}")
        logger.error(traceback.format_exc())
        return None

def main():
    parser = argparse.ArgumentParser(description='Debug PyPTV initialization')
    parser.add_argument('exp_path', help='Path to experiment directory')
    parser.add_argument('--step', action='store_true', help='Step through initialization')
    args = parser.parse_args()
    
    core = debug_initialization(args.exp_path, args.step)
    
    if core and core.initialized:
        print("\n===== INITIALIZATION SUCCESSFUL =====")
    else:
        print("\n===== INITIALIZATION FAILED =====")

if __name__ == "__main__":
    main()