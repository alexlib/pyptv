#!/usr/bin/env python
"""
Interactive test script for PyPTV initialization.
This script allows manual debugging of the initialization process.
"""

import os
import sys
import traceback
from pathlib import Path

# Set up the directory structure
TEST_DIR = Path('tests/test_cavity')
if not TEST_DIR.exists():
    print(f"Test directory {TEST_DIR} not found")
    sys.exit(1)

# Import PyPTV components
from pyptv.ui.ptv_core import PTVCore

def step_by_step_init():
    """Step-by-step initialization for debugging."""
    print("\n==== Testing step-by-step initialization ====\n")
    
    # Step 1: Create PTVCore instance
    print("Step 1: Creating PTVCore instance...")
    core = PTVCore(TEST_DIR)
    print("✓ PTVCore instance created")
    
    # Step 2: Check paths
    print("\nStep 2: Checking paths...")
    print(f"Experiment path: {core.exp_path}")
    print(f"Software path: {core.software_path}")
    input("Press Enter to continue...")
    
    # Step 3: Load parameters
    print("\nStep 3: Loading YAML parameters...")
    try:
        params = core.load_yaml_parameters()
        print("✓ Parameters loaded successfully")
        print(f"Parameter types: {list(params.keys())}")
        
        # Print some key parameters
        ptv_params = params.get("PtvParams")
        print(f"Number of cameras: {ptv_params.n_img}")
        print(f"Image dimensions: {ptv_params.imx}x{ptv_params.imy}")
    except Exception as e:
        print(f"✗ Error loading parameters: {e}")
        traceback.print_exc()
    input("Press Enter to continue...")
    
    # Step 4: Full initialization
    print("\nStep 4: Performing full initialization...")
    try:
        images = core.initialize()
        if core.initialized:
            print("✓ Initialization successful")
            print(f"Got {len(images)} camera images")
        else:
            print("✗ Initialization failed")
    except Exception as e:
        print(f"✗ Error during initialization: {e}")
        traceback.print_exc()
    
    return core

def main():
    """Main function."""
    core = step_by_step_init()
    
    # Final report
    print("\n==== Initialization Test Report ====\n")
    if core.initialized:
        print("✅ Initialization completed successfully")
        
        # Print key components
        print(f"Number of cameras: {core.n_cams}")
        print(f"Core components loaded:")
        print(f"  - cpar: {'✓' if core.cpar else '✗'}")
        print(f"  - vpar: {'✓' if core.vpar else '✗'}")
        print(f"  - track_par: {'✓' if core.track_par else '✗'}")
        print(f"  - spar: {'✓' if core.spar else '✗'}")
    else:
        print("❌ Initialization failed")
    
    print("\nTest completed")

if __name__ == "__main__":
    main()