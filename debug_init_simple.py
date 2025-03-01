#!/usr/bin/env python
"""
Simple debugging script for PyPTV initialization procedure.
This script traces the initialization process without requiring user input.
"""

import os
import sys
from pathlib import Path
import traceback
import time

# Import PyPTV components
sys.path.insert(0, '.')

# Try to add log handler before importing PTVCore
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('debug_init')

# Import after setting up logging
from pyptv.ui.ptv_core import PTVCore
from pyptv.yaml_parameters import ParameterManager

def debug_init(exp_path=None):
    """Debug the initialization process step by step."""
    if exp_path is None:
        exp_path = Path("tests/test_cavity")
    
    logger.info(f"Debugging initialization for experiment at: {exp_path}")
    
    # STEP 1: Create PTVCore
    try:
        logger.info("STEP 1: Creating PTVCore instance...")
        start_time = time.time()
        core = PTVCore(exp_path)
        logger.info(f"PTVCore created in {time.time() - start_time:.2f} seconds")
        logger.info(f"Experiment path: {core.exp_path}")
    except Exception as e:
        logger.error(f"Error creating PTVCore: {e}")
        logger.error(traceback.format_exc())
        return None
    
    # STEP 2: Load parameters
    try:
        logger.info("\nSTEP 2: Loading YAML parameters...")
        start_time = time.time()
        params = core.load_yaml_parameters()
        logger.info(f"Parameters loaded in {time.time() - start_time:.2f} seconds")
        
        # Check key parameters
        if params:
            ptv_params = params.get("PtvParams")
            logger.info(f"Number of cameras: {ptv_params.n_img}")
            logger.info(f"Image dimensions: {ptv_params.imx}x{ptv_params.imy}")
            
            # Check sequence parameters
            seq_params = params.get("SequenceParams")
            logger.info(f"Frame range: {seq_params.Seq_First}-{seq_params.Seq_Last}")
            
            # Check tracking parameters
            track_params = params.get("TrackingParams")
            logger.info(f"Min/Max velocity: {track_params.dvxmin}/{track_params.dvxmax}")
    except Exception as e:
        logger.error(f"Error loading parameters: {e}")
        logger.error(traceback.format_exc())
    
    # STEP 3: Full initialization
    try:
        logger.info("\nSTEP 3: Performing full initialization...")
        start_time = time.time()
        images = core.initialize()
        logger.info(f"Initialization completed in {time.time() - start_time:.2f} seconds")
        
        if core.initialized:
            logger.info(f"Initialization successful with {len(images)} camera images")
            logger.info(f"Core components loaded:")
            logger.info(f"  - cpar: {'✓' if core.cpar else '✗'}")
            logger.info(f"  - vpar: {'✓' if core.vpar else '✗'}")
            logger.info(f"  - track_par: {'✓' if core.track_par else '✗'}")
            logger.info(f"  - spar: {'✓' if core.spar else '✗'}")
        else:
            logger.error("Initialization failed")
    except Exception as e:
        logger.error(f"Error during initialization: {e}")
        logger.error(traceback.format_exc())
    
    return core

def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        exp_path = Path(sys.argv[1])
    else:
        exp_path = Path("tests/test_cavity")
    
    core = debug_init(exp_path)
    
    if core and core.initialized:
        logger.info("\n===== INITIALIZATION SUCCESSFUL =====")
    else:
        logger.error("\n===== INITIALIZATION FAILED =====")

if __name__ == "__main__":
    main()