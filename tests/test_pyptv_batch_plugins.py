"""Simple test for pyptv_batch_plugins.py - runs the actual code"""

import subprocess
import sys
from pathlib import Path


def test_batch_plugins_runs():
    """Test that pyptv_batch_plugins runs without errors"""
    
    # Path to the script
    script_path = Path(__file__).parent.parent / "pyptv" / "pyptv_batch_plugins.py"
    test_exp_path = Path(__file__).parent.parent / "tests" / "test_splitter"
    
    # Check if test experiment exists
    if not test_exp_path.exists():
        print(f"❌ Test experiment not found: {test_exp_path}")
        return False
    
    # Run the actual command
    cmd = [
        sys.executable, 
        str(script_path), 
        str(test_exp_path), 
        "1000001", 
        "1000005"
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=60
        )
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("✅ Batch processing completed successfully")
            return True
        else:
            print(f"❌ Process failed with return code: {result.returncode}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Process timed out")
        return False
    except Exception as e:
        print(f"❌ Error running process: {e}")
        return False


if __name__ == "__main__":
    success = test_batch_plugins_runs()
    if success:
        print("\n🎉 Test passed!")
    else:
        print("\n💥 Test failed!")
        sys.exit(1)