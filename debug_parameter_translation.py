#!/usr/bin/env python3
"""
Debug script to test parameter translation to Cython objects.
"""

import sys
from pathlib import Path
from pyptv.parameter_manager import ParameterManager
from pyptv.ptv import py_start_proc_c

def test_parameter_translation():
    """Test parameter translation from YAML to Cython objects."""
    
    # Test with test_cavity parameters
    test_dir = Path("tests/test_cavity")
    parameters_dir = test_dir / "parameters"
    
    if not parameters_dir.exists():
        print(f"❌ Test directory not found: {parameters_dir}")
        return False
    
    print(f"🔍 Testing parameter translation with {parameters_dir}")
    
    # Load parameters using ParameterManager
    manager = ParameterManager()
    manager.from_directory(parameters_dir)
    
    print(f"📊 Loaded parameters with global n_cam: {manager.n_cam}")
    print(f"📋 Parameter sections: {list(manager.parameters.keys())}")
    
    # Prepare full parameters for py_start_proc_c
    all_params = manager.parameters.copy()
    all_params['n_cam'] = manager.n_cam
    
    print(f"\n🔧 Testing Cython parameter translation...")
    
    try:
        cpar, spar, vpar, track_par, tpar, cals, epar = py_start_proc_c(all_params)
        
        print(f"✅ ControlParams created successfully")
        print(f"   - Image size: {cpar.get_image_size()}")
        print(f"   - Pixel size: {cpar.get_pixel_size()}")
        print(f"   - HP flag: {cpar.get_hp_flag()}")
        print(f"   - All-cam flag: {cpar.get_allCam_flag()}")
        
        print(f"✅ SequenceParams created successfully")
        print(f"   - First: {spar.get_first()}")
        print(f"   - Last: {spar.get_last()}")
        
        print(f"✅ TargetParams created successfully")
        print(f"   - Grey thresholds: {tpar.get_grey_thresholds()}")
        print(f"   - Pixel bounds: {tpar.get_pixel_count_bounds()}")
        
        print(f"✅ Calibrations loaded: {len(cals)} cameras")
        for i, cal in enumerate(cals):
            print(f"   - Camera {i}: {cal}")
            
        print(f"\n🎯 Parameter translation successful!")
        return True
        
    except Exception as e:
        print(f"❌ Parameter translation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_calibration_files():
    """Test calibration file reading specifically."""
    
    test_dir = Path("tests/test_cavity")
    cal_dir = test_dir / "cal"
    
    if not cal_dir.exists():
        print(f"❌ Calibration directory not found: {cal_dir}")
        return False
    
    print(f"\n🔍 Testing calibration files in {cal_dir}")
    
    # List calibration files
    ori_files = list(cal_dir.glob("*.ori"))
    addpar_files = list(cal_dir.glob("*.addpar"))
    
    print(f"📁 Found {len(ori_files)} .ori files:")
    for f in ori_files:
        print(f"   - {f.name}")
        
    print(f"📁 Found {len(addpar_files)} .addpar files:")
    for f in addpar_files:
        print(f"   - {f.name}")
    
    # Test loading calibrations directly
    from optv.calibration import Calibration
    
    for i in range(min(len(ori_files), len(addpar_files))):
        try:
            cal = Calibration()
            ori_file = str(ori_files[i])
            addpar_file = str(addpar_files[i])
            
            print(f"\n📖 Testing calibration {i+1}:")
            print(f"   - ORI: {ori_files[i].name}")
            print(f"   - ADDPAR: {addpar_files[i].name}")
            
            cal.from_file(ori_file, addpar_file)
            print(f"   ✅ Calibration loaded successfully")
            print(f"   - Position: {cal.get_pos()}")
            print(f"   - Angles: {cal.get_angles()}")
            
        except Exception as e:
            print(f"   ❌ Failed to load calibration {i+1}: {e}")
            return False
    
    return True

def main():
    """Main test function."""
    print("🧪 Testing PyPTV parameter translation and calibration loading\n")
    
    # Change to the right directory
    import os
    os.chdir("/home/user/Documents/GitHub/pyptv")
    
    success = True
    
    # Test parameter translation
    if not test_parameter_translation():
        success = False
    
    # Test calibration files
    if not test_calibration_files():
        success = False
    
    if success:
        print(f"\n🎉 All tests passed!")
    else:
        print(f"\n💥 Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
