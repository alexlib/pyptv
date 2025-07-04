#!/usr/bin/env python3
"""
Debug script to investigate correspondence matching issues
"""

import os
import numpy as np
from pathlib import Path
from pyptv.experiment import Experiment
from pyptv.ptv import py_start_proc_c
from imageio.v3 import imread
from skimage.color import rgb2gray
from skimage.util import img_as_ubyte
from optv.image_processing import preprocess_image
from optv.segmentation import target_recognition
from optv.correspondences import MatchedCoords, correspondences

# Constants
DEFAULT_NO_FILTER = 0
DEFAULT_HIGHPASS_FILTER_SIZE = 25

def simple_highpass(img, cpar):
    return preprocess_image(img, DEFAULT_NO_FILTER, cpar, DEFAULT_HIGHPASS_FILTER_SIZE)

def debug_correspondences():
    # Change to test directory
    test_dir = Path("/home/user/Documents/GitHub/pyptv/tests/test_cavity")
    os.chdir(test_dir)
    
    # Load parameters
    yaml_file = test_dir / "parameters_Run1.yaml"
    experiment = Experiment()
    experiment.parameter_manager.from_yaml(yaml_file)
    
    print(f"Loaded parameters, n_cam = {experiment.parameter_manager.n_cam}")
    
    # Initialize processing
    cpar, spar, vpar, track_par, tpar, cals, epar = py_start_proc_c(experiment.parameter_manager)
    
    print(f"Initialized processing:")
    print(f"  Number of cameras: {cpar.get_num_cams()}")
    print(f"  Image size: {cpar.get_image_size()}")
    print(f"  Pixel size: {cpar.get_pixel_size()}")
    print(f"  Multimedia parameters: {cpar.get_multimedia_params()}")
    
    # Check calibrations
    print(f"\nCalibration info:")
    for i, cal in enumerate(cals):
        print(f"  Camera {i}: pos={cal.get_pos()}, angles={cal.get_angles()}")
    
    # Test one frame
    frame = 10000
    detections = []
    corrected = []
    
    print(f"\nProcessing frame {frame}:")
    
    for i_cam in range(cpar.get_num_cams()):
        base_image_name = spar.get_img_base_name(i_cam)
        imname = Path(base_image_name % frame)
        print(f"  Camera {i_cam}: Loading {imname}")
        
        if not imname.exists():
            print(f"    ERROR: Image {imname} does not exist")
            continue
            
        img = imread(imname)
        if img.ndim > 2:
            img = rgb2gray(img)
        if img.dtype != np.uint8:
            img = img_as_ubyte(img)
            
        print(f"    Image shape: {img.shape}, dtype: {img.dtype}")
        print(f"    Image stats: min={img.min()}, max={img.max()}, mean={img.mean():.1f}")
        
        # Apply high-pass filter
        high_pass = simple_highpass(img, cpar)
        print(f"    High-pass stats: min={high_pass.min()}, max={high_pass.max()}, mean={high_pass.mean():.1f}")
        
        # Target recognition
        targs = target_recognition(high_pass, tpar, i_cam, cpar)
        targs.sort_y()
        print(f"    Detected {len(targs)} targets")
        
        # Show some target examples
        if len(targs) > 0:
            for j in range(min(5, len(targs))):  # Show first 5 targets
                targ = targs[j]
                print(f"      Target {j}: pos=({targ.pos()[0]:.2f}, {targ.pos()[1]:.2f}), pnr={targ.pnr()}")
        
        detections.append(targs)
        
        # Create matched coords
        matched_coords = MatchedCoords(targs, cpar, cals[i_cam])
        pos, _ = matched_coords.as_arrays()
        print(f"    Matched coords shape: {pos.shape if pos.size > 0 else 'empty'}")
        
        corrected.append(matched_coords)
    
    # Try correspondence matching
    print(f"\nCorrespondence matching:")
    print(f"  Detection counts: {[len(d) for d in detections]}")
    print(f"  Volume parameters: X_lay={vpar.get_X_lay()}, Z_lay=({vpar.get_Zmin_lay()}, {vpar.get_Zmax_lay()})")
    print(f"  Criteria: eps0={vpar.get_eps0()}")
    
    try:
        sorted_pos, sorted_corresp, _ = correspondences(
            detections, corrected, cals, vpar, cpar
        )
        
        print(f"  Correspondence results:")
        for i, (pos, corresp) in enumerate(zip(sorted_pos, sorted_corresp)):
            print(f"    Camera {i}: {pos.shape[1] if pos.size > 0 else 0} correspondences")
            
        # Show total correspondences
        total_corresp = sum(pos.shape[1] if pos.size > 0 else 0 for pos in sorted_pos)
        print(f"  Total correspondences: {total_corresp}")
        
    except Exception as e:
        print(f"  ERROR in correspondence matching: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_correspondences()
