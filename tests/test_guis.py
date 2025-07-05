#!/usr/bin/env python3

from pathlib import Path
import sys

# Add pyptv to path
sys.path.insert(0, str(Path.cwd()))

def test_guis():
    yaml_file = Path('test_yaml_simple/parameters_Test1.yaml')
    
    results = []
    results.append(f"Testing with {yaml_file}")
    results.append(f"File exists: {yaml_file.exists()}")
    
    # Test CalibrationGUI
    try:
        from pyptv.calibration_gui import CalibrationGUI
        gui = CalibrationGUI(yaml_file)
        results.append("✓ Calibration GUI initialized successfully")
        results.append(f"✓ Number of cameras: {gui.n_cams}")
        results.append("✓ Calibration GUI test passed!")
    except Exception as e:
        results.append(f"❌ Calibration GUI error: {e}")
        import traceback
        results.append(traceback.format_exc())
    
    # Test MainGUI basic import
    try:
        from pyptv.pyptv_gui import MainGUI
        results.append("✓ MainGUI import successful")
        
        # Test initialization (without showing GUI)
        gui = MainGUI(yaml_file=yaml_file)
        n_cam = gui.get_n_cam()
        results.append(f"✓ MainGUI initialized with {n_cam} cameras")
        
    except Exception as e:
        results.append(f"❌ MainGUI error: {e}")
        import traceback
        results.append(traceback.format_exc())
    
    # Write results
    with open('gui_test_results.txt', 'w') as f:
        for result in results:
            f.write(result + '\n')

if __name__ == "__main__":
    test_guis()
