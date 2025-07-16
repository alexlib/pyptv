import os
import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("DISPLAY") is None or os.environ.get("QT_QPA_PLATFORM") == "offscreen",
    reason="GUI/Qt tests require a display (DISPLAY or QT_QPA_PLATFORM)"
)
#!/usr/bin/env python3
"""
Test parameter_gui.py handlers with Experiment/Paramset API
"""

import sys
from pathlib import Path
import tempfile
import shutil

# Add the pyptv directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "pyptv"))

try:
    from pyptv.experiment import Experiment
    from pyptv.parameter_gui import Main_Params, Calib_Params, Tracking_Params, ParamHandler, CalHandler, TrackHandler
    print("✓ All imports successful")
except Exception as e:
    print(f"✗ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


class MockInfo:
    """Mock TraitsUI info object for testing handlers"""
    def __init__(self, obj):
        self.object = obj


def test_param_handlers():
    """Test that parameter GUI handlers correctly save to YAML via Experiment"""
    print("Starting parameter handler test...")
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Copy test YAML file
        test_yaml_src = Path("tests/test_cavity/parameters_Run1.yaml")
        test_yaml_dst = temp_path / "parameters_Run1.yaml"
        
        if not test_yaml_src.exists():
            print(f"Error: Test YAML file {test_yaml_src} not found")
            return False
            
        shutil.copy(test_yaml_src, test_yaml_dst)
        print(f"Copied test YAML: {test_yaml_src} -> {test_yaml_dst}")
        
        # Create experiment and load parameters
        experiment = Experiment()
        experiment.addParamset("Run1", test_yaml_dst)
        experiment.setActive(0)
        
        print(f"Original n_cam: {experiment.parameter_manager.get_n_cam()}")
        
        # Test ParamHandler
        print("\\nTesting ParamHandler...")
        try:
            main_params = Main_Params(experiment)
            print(f"✓ Main_Params created successfully")
            
            # Modify parameters
            main_params.Num_Cam = 3
            main_params.Name_1_Image = "test_modified_cam1.tif"
            main_params.HighPass = False
            main_params.Seq_First = 30001
            print(f"Modified: Num_Cam={main_params.Num_Cam}, Name_1_Image={main_params.Name_1_Image}")
            
            # Simulate handler
            handler = ParamHandler()
            mock_info = MockInfo(main_params)
            handler.closed(mock_info, is_ok=True)
            print("✓ ParamHandler.closed() executed successfully")
            
            # Verify changes were saved by reloading
            experiment2 = Experiment()
            experiment2.addParamset("Run1", test_yaml_dst)
            experiment2.setActive(0)
            
            saved_n_cam = experiment2.parameter_manager.get_n_cam()
            saved_img_name = experiment2.parameter_manager.parameters['ptv']['img_name'][0]
            saved_hp_flag = experiment2.parameter_manager.parameters['ptv']['hp_flag']
            saved_seq_first = experiment2.parameter_manager.parameters['sequence']['first']
            
            print(f"Verification: n_cam={saved_n_cam}, img_name[0]={saved_img_name}, hp_flag={saved_hp_flag}, seq_first={saved_seq_first}")
            
            assert saved_n_cam == 3, f"Expected n_cam=3, got {saved_n_cam}"
            assert saved_img_name == "test_modified_cam1.tif", f"Expected img_name='test_modified_cam1.tif', got '{saved_img_name}'"
            assert saved_hp_flag == False, f"Expected hp_flag=False, got {saved_hp_flag}"
            assert saved_seq_first == 30001, f"Expected seq_first=30001, got {saved_seq_first}"
            print("✓ ParamHandler correctly saved parameters")
            
        except Exception as e:
            print(f"✗ ParamHandler test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        print("\\n🎉 Parameter GUI handler test passed!")
        return True


if __name__ == "__main__":
    try:
        result = test_param_handlers()
        if result:
            print("\\n✅ Parameter GUI handlers work correctly with Experiment/Paramset API!")
        else:
            print("\\n❌ Test failed")
            sys.exit(1)
    except Exception as e:
        print(f"\\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
