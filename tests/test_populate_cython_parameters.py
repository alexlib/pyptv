import sys
sys.path.insert(0, '.')
import numpy as np
from pathlib import Path
from pyptv.experiment import Experiment
from pyptv.ptv import py_start_proc_c, _populate_cpar, _populate_tpar, _populate_spar
from pyptv.parameter_util import legacy_to_yaml

def test_parameter_translation_pipeline():
    """Test the complete parameter translation pipeline step by step."""
    print("=== COMPREHENSIVE PARAMETER TRANSLATION TEST ===\n")
    
    # Step 1: Load experiment and get raw parameters
    print("1. Loading experiment and raw parameters...")
    test_dir = Path("tests/test_cavity")
    experiment = Experiment()
    experiment.populate_runs(test_dir)
    
    if not experiment.paramsets:
        print("❌ No parameter sets found!")
        return False
    
    experiment.active_params = experiment.paramsets[0]
    print(f"✅ Loaded experiment with {len(experiment.paramsets)} parameter sets")
    print(f"   Active: {experiment.active_params.name}")
    
    # Step 2: Check raw YAML parameters
    print("\n2. Checking raw YAML parameters...")
    params = experiment.parameter_manager.parameters
    n_cam = experiment.parameter_manager.n_cam
    
    print(f"   Global n_cam: {n_cam}")
    print(f"   Available sections: {list(params.keys())}")
    
    # Check critical sections
    ptv_params = params.get('ptv', {})
    targ_params = params.get('targ_rec', {})
    # print targ_params grey thresholds: 
    print(targ_params.get('gvthres','Mistake'))


    seq_params = params.get('sequence', {})
    
    print(f"   PTV section keys: {list(ptv_params.keys())}")
    print(f"   Target recognition keys: {list(targ_params.keys())}")
    print(f"   Sequence section keys: {list(seq_params.keys())}")
    
    if not ptv_params or not targ_params:
        print("❌ Missing critical parameter sections!")
        return False
    
    # Step 3: Test individual parameter object creation
    print("\n3. Testing individual parameter object creation...")
    
    try:
        # Test ControlParams
        print("   Creating ControlParams...")
        cpar = _populate_cpar(ptv_params, n_cam)
        print(f"   ✅ ControlParams: {cpar.get_num_cams()} cameras, image size: {cpar.get_image_size()}")
        
        # Test TargetParams  
        print("   Creating TargetParams...")
        tpar = _populate_tpar(targ_params)
        print(f"   ✅ TargetParams: grey thresholds: {tpar.get_grey_thresholds()}")
        print(f"      Pixel bounds: {tpar.get_pixel_count_bounds()}")
        
        # Test SequenceParams
        print("   Creating SequenceParams...")
        spar = _populate_spar(seq_params, n_cam)
        print(f"   ✅ SequenceParams: frames {spar.get_first()}-{spar.get_last()}")
        
    except Exception as e:
        print(f"❌ Error creating parameter objects: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 4: Test full py_start_proc_c
    print("\n4. Testing complete parameter initialization...")
    try:
        cpar, spar, vpar, track_par, tpar, cals, epar = py_start_proc_c(experiment.parameter_manager)
        print("   ✅ py_start_proc_c completed successfully")
        print(f"   ControlParams cameras: {cpar.get_num_cams()}")
        print(f"   Calibrations loaded: {len(cals)}")
        
    except Exception as e:
        print(f"❌ Error in py_start_proc_c: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 5: Test target recognition with real image
    print("\n5. Testing target recognition with real image...")
    try:
        from imageio.v3 import imread
        from skimage.color import rgb2gray
        from skimage.util import img_as_ubyte
        from optv.segmentation import target_recognition
        
        # Find first image
        img_base = spar.get_img_base_name(0)
        print(f"   Image base name: {img_base}")
        
        # Try with frame 10000
        img_path = Path(img_base % 10000)
        if not img_path.exists():
            # Try other frames
            for frame in [10001, 10002, 10003, 10004]:
                img_path = Path(img_base % frame)
                if img_path.exists():
                    break
        
        if not img_path.exists():
            print(f"❌ No image found for pattern {img_base}")
            return False
            
        print(f"   Loading image: {img_path}")
        img = imread(img_path)
        
        if img.ndim > 2:
            img = rgb2gray(img)
        if img.dtype != np.uint8:
            img = img_as_ubyte(img)
            
        print(f"   Image shape: {img.shape}, dtype: {img.dtype}")
        print(f"   Image range: {img.min()}-{img.max()}")
        
        # Apply target recognition
        print("   Running target recognition...")
        targs = target_recognition(img, tpar, 0, cpar)
        
        print(f"   🎯 Found {len(targs)} targets!")
        
        if len(targs) == 0:
            print("   ⚠️  Zero targets found - this indicates a problem!")
            
            # Debug target parameters
            print("   DEBUG: Target recognition parameters:")
            print(f"      Grey thresholds: {tpar.get_grey_thresholds()}")
            print(f"      Pixel count bounds: {tpar.get_pixel_count_bounds()}")
            print(f"      X size bounds: {tpar.get_xsize_bounds()}")
            print(f"      Y size bounds: {tpar.get_ysize_bounds()}")
            print(f"      Min sum grey: {tpar.get_min_sum_grey()}")
            print(f"      Max discontinuity: {tpar.get_max_discontinuity()}")
            
            # Check if thresholds are reasonable
            thresholds = tpar.get_grey_thresholds()
            if not thresholds or max(thresholds) > 250:
                print("   ❌ Grey thresholds seem wrong!")
                print(f"      Raw targ_rec params: {targ_params}")
            
            return False
        else:
            print(f"   ✅ Target recognition working - found {len(targs)} targets")
            
    except Exception as e:
        print(f"❌ Error in target recognition test: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n✅ ALL TESTS PASSED - Parameter translation pipeline is working!")
    return True

if __name__ == "__main__":
    test_parameter_translation_pipeline()