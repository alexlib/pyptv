#!/usr/bin/env python
"""
Modified version of pyptv_batch.py that uses the PTVCoreBridge directly.
This is a workaround for initialization issues with optv.
"""

import os
import sys
import time
from pathlib import Path

# Import the bridge directly to avoid initialization issues
from pyptv.ui.ptv_core.bridge import PTVCoreBridge
from pyptv import ptv

def run_batch(exp_path, first, last):
    """Run the batch process using the PTVCoreBridge."""
    print(f"Running batch on {exp_path} from frame {first} to {last}")
    
    # Change to experiment directory
    os.chdir(exp_path)
    
    # Create the bridge
    bridge = PTVCoreBridge(exp_path)
    
    # Initialize the bridge
    print("Initializing bridge...")
    bridge.initialize()
    
    # Get the number of cameras
    n_cams = bridge.n_cams
    print(f"Working with {n_cams} cameras")
    
    # Read the parameter files directly using py_start_proc_c
    print("Loading parameters...")
    try:
        (
            cpar,
            spar,
            vpar,
            track_par,
            tpar,
            cals,
            epar,
        ) = ptv.py_start_proc_c(n_cams=n_cams)
        
        # Set sequence range
        spar.set_first(first)
        spar.set_last(last)
        
        # Create experiment dict
        exp = {
            'cpar': cpar,
            'spar': spar,
            'vpar': vpar,
            'track_par': track_par,
            'tpar': tpar,
            'cals': cals,
            'epar': epar,
            'n_cams': n_cams,
        }
        
        # Convert to object-like access
        class AttrDict(dict):
            def __init__(self, *args, **kwargs):
                super(AttrDict, self).__init__(*args, **kwargs)
                self.__dict__ = self
        
        exp = AttrDict(exp)
        
        # Run the sequence loop
        print("Running sequence loop...")
        ptv.py_sequence_loop(exp)
        
        # Initialize tracker and run tracking
        print("Running tracking...")
        tracker = ptv.py_trackcorr_init(exp)
        tracker.full_forward()
        
        print("Batch processing completed successfully")
        return True
        
    except Exception as e:
        print(f"Error in batch processing: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main entry point."""
    if len(sys.argv) > 3:
        exp_path = Path(sys.argv[1])
        first = int(sys.argv[2])
        last = int(sys.argv[3])
    else:
        exp_path = Path("tests/test_cavity")
        first = 10000
        last = 10004
    
    start_time = time.time()
    
    # Make sure the result directory exists
    os.makedirs(exp_path / "res", exist_ok=True)
    
    # Run the batch
    success = run_batch(exp_path, first, last)
    
    end_time = time.time()
    print(f"Total processing time: {end_time - start_time:.2f} seconds")
    
    if success:
        print("✅ Batch processing completed successfully")
    else:
        print("❌ Batch processing failed")

if __name__ == "__main__":
    main()