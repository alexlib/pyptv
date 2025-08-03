#!/usr/bin/env python3
"""
Test to reproduce the detection parameter bug between GUI and sequence processing.

This test demonstrates that:
1. The GUI tries to use 'targ_rec' parameters that don't exist
2. The sequence loop correctly uses 'detect_plate' parameters
3. This causes different detection results
"""

import numpy as np
from pathlib import Path
from pyptv.experiment import Experiment
from pyptv.ptv import py_detection_proc_c, _populate_tpar
from skimage.io import imread
from skimage.color import rgb2gray
from skimage.util import img_as_ubyte

def test_detection_parameters_bug():
    """Test that reproduces the detection parameters bug."""
    
    # Load test parameters
    test_dir = Path("tests/test_cavity")
    yaml_file = test_dir / "parameters_Run1.yaml"
    
    experiment = Experiment()
    # Add the paramset to experiment
    experiment.addParamset("Run1", yaml_file)
    experiment.set_active(0)
    
    print("=== Testing Detection Parameter Bug ===")
    print()
    
    # Check what parameters are available
    print("Available parameter sections:")
    for key in experiment.pm.parameters.keys():
        print(f"  - {key}")
    print()
    
    # Test GUI approach (wrong)
    print("1. GUI approach (looking for 'targ_rec'):")
    targ_rec_params = experiment.pm.parameters['targ_rec']
    print(f"   targ_rec parameters: {targ_rec_params}")
    if targ_rec_params is None:
        print("   ❌ GUI will fail - no 'targ_rec' section!")
        # Create empty target_params as GUI would - but we need to provide required params
        # to avoid the KeyError we implemented for safety
        target_params_gui = {
            'targ_rec': {
                'gvthres': [0, 0, 0, 0],  # Default/empty values
                'nnmin': 1,
                'nnmax': 1000,
                'nxmin': 1,
                'nxmax': 20,
                'nymin': 1,
                'nymax': 20,
                'sumg_min': 0,
                'disco': 10
            }
        }
        try:
            tpar_gui = _populate_tpar(target_params_gui, experiment.get_n_cam())
            print(f"   GUI TargetParams created with default values (likely all zeros)")
        except Exception as e:
            print(f"   GUI TargetParams creation failed: {e}")
    else:
        target_params_gui = {'targ_rec': targ_rec_params}
        tpar_gui = _populate_tpar(target_params_gui, experiment.get_n_cam())
        print(f"   GUI TargetParams will have values from targ_rec")
    print()
    
    # Test sequence approach (correct)
    print("2. Sequence approach (looking for 'detect_plate'):")
    detect_plate_params = experiment.get_parameter('detect_plate')
    print(f"   detect_plate parameters: {detect_plate_params}")
    target_params_seq = None
    tpar_seq = None
    
    if detect_plate_params is not None:
        print("   ✅ Sequence will work - 'detect_plate' section exists!")
        target_params_seq = {'detect_plate': detect_plate_params}
        tpar_seq = _populate_tpar(target_params_seq, experiment.get_n_cam())
        print(f"   Sequence TargetParams will have proper values")
        print(f"   Grey thresholds: {[tpar_seq.get_grey_thresholds()[i] for i in range(4)]}")
        print(f"   Min/max pixels: {tpar_seq.get_pixel_count_bounds()}")
    else:
        print("   ❌ Sequence will also fail - no 'detect_plate' section!")
    print()
    
    # Test with an actual image if available
    ptv_params = experiment.get_parameter('ptv')
    if ptv_params is None:
        print("3. Cannot test actual detection - no 'ptv' parameters found")
        return
        
    img_path = Path(ptv_params['img_name'][0])
    
    if img_path.exists():
        print("3. Testing actual detection with first image:")
        print(f"   Image: {img_path}")
        
        # Load image
        img = imread(img_path)
        if img.ndim > 2:
            img = rgb2gray(img)
        img = img_as_ubyte(img)
        
        num_cams = experiment.get_n_cam()
        images = [img]  # Just test with first camera
        
        # Test GUI detection (with wrong parameters)
        try:
            print("   Testing GUI detection (targ_rec - empty parameters):")
            detections_gui, _ = py_detection_proc_c(
                1,  # Just one camera for test
                images,
                ptv_params,
                target_params_gui
            )
            print(f"   GUI detections: {len(detections_gui[0])} targets")
        except Exception as e:
            print(f"   GUI detection failed: {e}")
        
        # Test sequence detection (with correct parameters)
        if target_params_seq is not None:
            try:
                print("   Testing sequence detection (detect_plate - proper parameters):")
                detections_seq, _ = py_detection_proc_c(
                    1,  # Just one camera for test
                    images,
                    ptv_params,
                    target_params_seq
                )
                print(f"   Sequence detections: {len(detections_seq[0])} targets")
            except Exception as e:
                print(f"   Sequence detection failed: {e}")
        else:
            print("   Cannot test sequence detection - no detect_plate parameters")
            
    else:
        print(f"3. Cannot test actual detection - image not found: {img_path}")
    
    print()
    print("=== Conclusion ===")
    print("The GUI should use 'detect_plate' parameters, not 'targ_rec'!")
    print("This explains why sequence processing gets more detections than manual GUI steps.")

if __name__ == "__main__":
    test_detection_parameters_bug()
