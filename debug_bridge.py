#!/usr/bin/env python
"""
Debug script to investigate PTVCoreBridge issues.
This script examines what happens during the PTVCore transformation.
"""

import os
import sys
from pathlib import Path
import inspect
import traceback

# Import PyPTV components
sys.path.insert(0, '.')

# Add logging
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('debug_bridge')

# Import the PTVCore class
from pyptv.ui.ptv_core import PTVCore

# Let's examine the PTVCore class
logger.info(f"PTVCore type: {type(PTVCore)}")
logger.info(f"PTVCore base classes: {PTVCore.__bases__}")
logger.info(f"PTVCore module: {PTVCore.__module__}")

# Let's also check the import chain
logger.info("\nImport chain from pyptv.ui.ptv_core:")
module = sys.modules["pyptv.ui.ptv_core"]
logger.info(f"Module: {module}")

# Check if there's a PTVCoreBridge in any of the imported modules
for name, module in sys.modules.items():
    if "pyptv" in name and hasattr(module, "PTVCoreBridge"):
        logger.info(f"Found PTVCoreBridge in module: {name}")
        bridge = getattr(module, "PTVCoreBridge")
        logger.info(f"PTVCoreBridge type: {type(bridge)}")
        logger.info(f"PTVCoreBridge bases: {bridge.__bases__}")

# Try to create a PTVCore instance and see what happens
try:
    logger.info("\nCreating PTVCore instance...")
    core = PTVCore(Path("tests/test_cavity"))
    
    # Check what we got
    logger.info(f"Created instance of type: {type(core)}")
    
    # Examine the instance's attributes and methods
    logger.info("\nInstance attributes:")
    for attr in dir(core):
        if not attr.startswith("__"):
            try:
                value = getattr(core, attr)
                if not callable(value):
                    logger.info(f"  - {attr}: {type(value)}")
                else:
                    logger.info(f"  - {attr}(): {type(value)} (method)")
            except Exception as e:
                logger.info(f"  - {attr}: ERROR - {e}")
    
    # Check if initialize exists and try to call it
    if hasattr(core, "initialize"):
        logger.info("\nCalling initialize()...")
        try:
            result = core.initialize()
            logger.info(f"Initialize result type: {type(result)}")
            logger.info(f"Instance type after initialize: {type(core)}")
        except Exception as e:
            logger.error(f"Error in initialize: {e}")
            logger.error(traceback.format_exc())
    
except Exception as e:
    logger.error(f"Error creating PTVCore: {e}")
    logger.error(traceback.format_exc())