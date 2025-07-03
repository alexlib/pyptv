#!/usr/bin/env python3
"""
Debug script to check parameter translation from YAML to OptV objects
"""

import sys
sys.path.insert(0, '.')

from pathlib import Path
from pyptv.experiment import Experiment
from pyptv.ptv import py_start_proc_c

def debug_parameters():
    print("=== DEBUG: Parameter Translation ===")
    
    # Load the test experiment
    test_dir = Path("tests/test_cavity")
    experiment = Experiment()
    experiment.populate_runs(test_dir)
    
    # Get all parameters
    all_params = experiment.parameter_manager.parameters.copy()
    all_params['n_cam'] = experiment.get_n_cam()
    
    print(f"Global n_cam: {all_params['n_cam']}")
    print()
    
    # Check target recognition parameters in YAML
    print("=== Target Recognition Parameters in YAML ===")
    targ_rec = all_params.get('targ_rec', {})
    print(f"gvthres: {targ_rec.get('gvthres', [])}")
    print(f"nnmin: {targ_rec.get('nnmin', 0)}")
    print(f"nnmax: {targ_rec.get('nnmax', 0)}")
    print(f"nxmin: {targ_rec.get('nxmin', 0)}")
    print(f"nxmax: {targ_rec.get('nxmax', 0)}")
    print(f"nymin: {targ_rec.get('nymin', 0)}")
    print(f"nymax: {targ_rec.get('nymax', 0)}")
    print(f"sumg_min: {targ_rec.get('sumg_min', 0)}")
    print(f"disco: {targ_rec.get('disco', 0)}")
    print()
    
    # Initialize OptV parameters
    cpar, spar, vpar, track_par, tpar, cals, epar = py_start_proc_c(all_params)
    
    print("=== Target Recognition Parameters in OptV ===")
    print(f"Grey thresholds: {tpar.get_grey_thresholds()}")
    pixel_bounds = tpar.get_pixel_count_bounds()
    print(f"Pixel count bounds: min={pixel_bounds[0]}, max={pixel_bounds[1]}")
    xsize_bounds = tpar.get_xsize_bounds()
    print(f"X size bounds: min={xsize_bounds[0]}, max={xsize_bounds[1]}")
    ysize_bounds = tpar.get_ysize_bounds()
    print(f"Y size bounds: min={ysize_bounds[0]}, max={ysize_bounds[1]}")
    print(f"Min sum grey: {tpar.get_min_sum_grey()}")
    print(f"Max discontinuity: {tpar.get_max_discontinuity()}")
    print()
    
    # Check control parameters
    print("=== Control Parameters ===")
    print(f"Image size: {cpar.get_image_size()}")
    print(f"Pixel size: {cpar.get_pixel_size()}")
    print(f"HP flag: {cpar.get_hp_flag()}")
    print(f"Number of cameras: {cpar.get_num_cams()}")
    print()
    
    # Check sequence parameters  
    print("=== Sequence Parameters ===")
    print(f"First frame: {spar.get_first()}")
    print(f"Last frame: {spar.get_last()}")
    for i in range(cpar.get_num_cams()):
        print(f"Camera {i} base name: {spar.get_img_base_name(i)}")
    print()

if __name__ == "__main__":
    debug_parameters()
