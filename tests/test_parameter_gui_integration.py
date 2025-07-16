import os
import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("DISPLAY") is None or os.environ.get("QT_QPA_PLATFORM") == "offscreen",
    reason="GUI/Qt tests require a display (DISPLAY or QT_QPA_PLATFORM)"
)
#!/usr/bin/env python3
"""
Test parameter_gui.py integration with Experiment/Paramset API
"""

import sys
from pathlib import Path
import tempfile
import shutil

# Add the pyptv directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "pyptv"))

from pyptv.experiment import Experiment
from pyptv.parameter_gui import Main_Params, Calib_Params, Tracking_Params


def test_parameter_gui_experiment_integration():
    """Test that parameter GUI classes work with Experiment objects"""
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Copy test YAML file
        test_yaml_src = Path("tests/test_cavity/parameters_Run1.yaml")
        test_yaml_dst = temp_path / "parameters_Run1.yaml"
        
        if test_yaml_src.exists():
            shutil.copy(test_yaml_src, test_yaml_dst)
            print(f"Copied test YAML: {test_yaml_src} -> {test_yaml_dst}")
        else:
            print(f"Error: Test YAML file {test_yaml_src} not found")
            return False
        
        # Create experiment and load parameters
        experiment = Experiment()
        experiment.addParamset("Run1", test_yaml_dst)
        experiment.setActive(0)
        
        print(f"Experiment active params: {getattr(experiment.active_params, 'name', 'Unknown')}")
        print(f"Number of cameras: {experiment.parameter_manager.get_n_cam()}")
        
        # Test Main_Params initialization
        print("\\nTesting Main_Params...")
        try:
            main_params = Main_Params(experiment)
            print(f"✓ Main_Params created successfully")
            print(f"  - Number of cameras: {main_params.Num_Cam}")
            print(f"  - Image names: {[main_params.Name_1_Image, main_params.Name_2_Image, main_params.Name_3_Image, main_params.Name_4_Image]}")
            print(f"  - High pass filter: {main_params.HighPass}")
            print(f"  - Gray thresholds: {[main_params.Gray_Tresh_1, main_params.Gray_Tresh_2, main_params.Gray_Tresh_3, main_params.Gray_Tresh_4]}")
            
            # Test parameter modification
            original_num_cam = main_params.Num_Cam
            main_params.Num_Cam = 3
            main_params.HighPass = False
            print(f"  - Modified parameters: Num_Cam={main_params.Num_Cam}, HighPass={main_params.HighPass}")
            
        except Exception as e:
            print(f"✗ Main_Params failed: {e}")
            raise
        
        # Test Calib_Params initialization
        print("\\nTesting Calib_Params...")
        try:
            calib_params = Calib_Params(experiment)
            print(f"✓ Calib_Params created successfully")
            print(f"  - Number of cameras: {calib_params.n_cam}")
            print(f"  - Image size: {calib_params.h_image_size}x{calib_params.v_image_size}")
            print(f"  - Calibration images: {[calib_params.cam_1, calib_params.cam_2, calib_params.cam_3, calib_params.cam_4]}")
            print(f"  - Gray value thresholds: {[calib_params.grey_value_treshold_1, calib_params.grey_value_treshold_2, calib_params.grey_value_treshold_3, calib_params.grey_value_treshold_4]}")
            
        except Exception as e:
            print(f"✗ Calib_Params failed: {e}")
            raise
        
        # Test Tracking_Params initialization
        print("\\nTesting Tracking_Params...")
        try:
            tracking_params = Tracking_Params(experiment)
            print(f"✓ Tracking_Params created successfully")
            print(f"  - dvxmin/dvxmax: {tracking_params.dvxmin}/{tracking_params.dvxmax}")
            print(f"  - dvymin/dvymax: {tracking_params.dvymin}/{tracking_params.dvymax}")
            print(f"  - dvzmin/dvzmax: {tracking_params.dvzmin}/{tracking_params.dvzmax}")
            print(f"  - angle: {tracking_params.angle}")
            print(f"  - flagNewParticles: {tracking_params.flagNewParticles}")
            
        except Exception as e:
            print(f"✗ Tracking_Params failed: {e}")
            raise
        
        # Test parameter saving through experiment
        print("\\nTesting parameter saving...")
        try:
            # Modify some parameters
            main_params.Name_1_Image = "test_cam1.tif"
            main_params.Seq_First = 20001
            calib_params.grey_value_treshold_1 = 30
            tracking_params.dvxmin = -60.0
            
            # Simulate what the handlers would do
            print("Simulating ParamHandler save...")
            
            # Update parameters in experiment (simulate ParamHandler)
            img_name = [main_params.Name_1_Image, main_params.Name_2_Image, main_params.Name_3_Image, main_params.Name_4_Image]
            experiment.parameter_manager.parameters['ptv']['img_name'] = img_name
            experiment.parameter_manager.parameters['sequence']['first'] = main_params.Seq_First
            experiment.parameter_manager.parameters['detect_plate']['gvth_1'] = calib_params.grey_value_treshold_1
            experiment.parameter_manager.parameters['track']['dvxmin'] = tracking_params.dvxmin
            
            # Save to YAML
            experiment.save_parameters()
            print("✓ Parameters saved successfully")
            
            # Verify save by reloading
            experiment2 = Experiment()
            experiment2.addParamset("Run1", test_yaml_dst)
            experiment2.setActive(0)
            
            saved_img_name = experiment2.parameter_manager.parameters['ptv']['img_name'][0]
            saved_seq_first = experiment2.parameter_manager.parameters['sequence']['first']
            saved_gvth_1 = experiment2.parameter_manager.parameters['detect_plate']['gvth_1']
            saved_dvxmin = experiment2.parameter_manager.parameters['track']['dvxmin']
            
            print(f"✓ Verification: img_name[0] = {saved_img_name}")
            print(f"✓ Verification: seq_first = {saved_seq_first}")
            print(f"✓ Verification: gvth_1 = {saved_gvth_1}")
            print(f"✓ Verification: dvxmin = {saved_dvxmin}")
            
            assert saved_img_name == "test_cam1.tif"
            assert saved_seq_first == 20001
            assert saved_gvth_1 == 30
            assert saved_dvxmin == -60.0
            
        except Exception as e:
            print(f"✗ Parameter saving failed: {e}")
            raise
        
        print("\\n🎉 All parameter_gui integration tests passed!")
        return True


if __name__ == "__main__":
    try:
        test_parameter_gui_experiment_integration()
        print("\\n✅ Parameter GUI integration with Experiment/Paramset API is working correctly!")
    except Exception as e:
        print(f"\\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
