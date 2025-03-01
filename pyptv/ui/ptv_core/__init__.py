"""Core PTV functionality for the modernized UI."""

import os
import warnings
import importlib.util
import sys
from pathlib import Path

# Try to load the full PTVCore implementation first
ptv_core_path = Path(__file__).parent.parent.parent / "ui" / "ptv_core.py"

if ptv_core_path.exists():
    try:
        # Load the full implementation
        spec = importlib.util.spec_from_file_location("ptv_core_full", str(ptv_core_path))
        ptv_core_full = importlib.util.module_from_spec(spec)
        sys.modules["ptv_core_full"] = ptv_core_full
        spec.loader.exec_module(ptv_core_full)
        
        # Use the full implementation
        PTVCore = ptv_core_full.PTVCore
        print("Using full PTVCore implementation")
    except Exception as e:
        # Fall back to bridge if there's an error
        from pyptv.ui.ptv_core.bridge import PTVCoreBridge as PTVCore
        warnings.warn(f"Failed to load full PTVCore implementation, falling back to bridge: {e}")
else:
    # Fall back to bridge if full implementation not found
    from pyptv.ui.ptv_core.bridge import PTVCoreBridge as PTVCore
    warnings.warn("Full PTVCore implementation not found, using bridge")

__all__ = ['PTVCore']