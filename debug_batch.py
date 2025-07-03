#!/usr/bin/env python3
"""
Debug script for pyptv_batch using the modern API.
"""

import sys
import traceback
from pathlib import Path

def main():
    # Adjust these paths as needed
    test_dir = Path("tests/test_cavity")
    yaml_file = test_dir / "parameters_Run1.yaml"

    if not test_dir.exists():
        print(f"❌ Test directory not found: {test_dir}")
        return False

    if not yaml_file.exists():
        print(f"❌ YAML file not found: {yaml_file}")
        return False

    print(f"🔍 Debugging pyptv_batch in: {test_dir}")
    print(f"📄 Using YAML file: {yaml_file}")

    try:
        # Import here to avoid issues if pyptv_batch is not installed
        from pyptv.pyptv_batch import main as pyptv_batch_main

        print("\n🚀 Running pyptv_batch.main() ...")
        pyptv_batch_main(test_dir, 10000, 10004)
        print("\n✅ pyptv_batch completed successfully!")

        return True

    except Exception as e:
        print(f"\n❌ pyptv_batch failed with error: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 All debug steps passed!")
    else:
        print("\n💥 Debug found issues that need to be fixed.")
        sys.exit(1)
