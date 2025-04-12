#!/usr/bin/env python
"""
Script to check the installed version of pyptv and warn if it's not the expected version.
"""
import sys
import importlib.metadata

EXPECTED_VERSION = "0.3.5"  # The version in the local repository

def check_version():
    """Check if the installed version matches the expected version."""
    try:
        installed_version = importlib.metadata.version("pyptv")
        print(f"Installed pyptv version: {installed_version}")
        
        if installed_version != EXPECTED_VERSION:
            print(f"\nWARNING: The installed version ({installed_version}) does not match "
                  f"the expected version ({EXPECTED_VERSION}).")
            print("\nPossible reasons:")
            
            if installed_version == "0.3.4":
                print("- You installed from PyPI, which has version 0.3.4")
                print("- To install the development version (0.3.5), run:")
                print("  pip install -e /path/to/pyptv/repository")
            else:
                print("- You might have a different version installed")
                print("- Check your installation source")
            
            return False
        else:
            print(f"Version check passed: {installed_version}")
            return True
    except importlib.metadata.PackageNotFoundError:
        print("ERROR: pyptv is not installed.")
        return False

if __name__ == "__main__":
    success = check_version()
    sys.exit(0 if success else 1)
