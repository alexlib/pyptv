#!/usr/bin/env python3
"""
Demo script showing how parameters.yaml is created from legacy .par files
"""

import sys
sys.path.insert(0, '.')

from pathlib import Path
from pyptv.parameter_manager import ParameterManager

def demo_parameter_conversion():
    print("=== PyPTV Parameter Conversion Demo ===")
    print("This shows how a YAML file is created from a legacy parameters folder\n")
    
    # Check if we have a legacy parameters directory
    legacy_dir = Path("tests/test_cavity/parameters")
    if not legacy_dir.exists():
        print(f"Legacy parameters directory not found at {legacy_dir}")
        return
    
    print(f"🔍 Step 1: Examining legacy .par files in {legacy_dir}")
    par_files = list(legacy_dir.glob("*.par"))
    print(f"Found {len(par_files)} .par files:")
    for par_file in sorted(par_files):
        print(f"  - {par_file.name}")
    print()
    
    # Initialize parameter manager
    print("🔧 Step 2: Creating ParameterManager and loading from directory")
    manager = ParameterManager()
    
    print("📖 Step 3: Reading .par files and converting to internal structure")
    manager.from_directory(legacy_dir)
    
    print(f"✅ Loaded parameters with global n_cam = {manager.n_cam}")
    print(f"📊 Found {len(manager.parameters)} parameter sections:")
    for param_name in manager.parameters.keys():
        print(f"  - {param_name}")
    print()
    
    print("🔍 Step 4: Sample parameter sections:")
    # Show some key parameter sections
    if 'targ_rec' in manager.parameters:
        targ_rec = manager.parameters['targ_rec']
        print("Target Recognition (targ_rec):")
        print(f"  - gvthres: {targ_rec.get('gvthres', [])}")
        print(f"  - nnmin: {targ_rec.get('nnmin', 0)}, nnmax: {targ_rec.get('nnmax', 0)}")
        print(f"  - sumg_min: {targ_rec.get('sumg_min', 0)}")
        print()
    
    if 'sequence' in manager.parameters:
        seq = manager.parameters['sequence']
        print("Sequence parameters:")
        print(f"  - first: {seq.get('first', 0)}, last: {seq.get('last', 0)}")
        print(f"  - base_name: {seq.get('base_name', [])}")
        print()
    
    if 'ptv' in manager.parameters:
        ptv = manager.parameters['ptv']
        print("PTV Control parameters:")
        print(f"  - imx: {ptv.get('imx', 0)}, imy: {ptv.get('imy', 0)}")
        print(f"  - hp_flag: {ptv.get('hp_flag', False)}")
        print(f"  - tiff_flag: {ptv.get('tiff_flag', False)}")
        print()
    
    # Convert to YAML
    yaml_output = Path("demo_converted_parameters.yaml")
    print(f"💾 Step 5: Converting to YAML format: {yaml_output}")
    manager.to_yaml(yaml_output)
    
    print(f"✅ Conversion complete! YAML file created at {yaml_output}")
    print()
    
    # Show the YAML structure
    print("📄 Step 6: YAML file structure preview:")
    with open(yaml_output, 'r') as f:
        lines = f.readlines()
        for i, line in enumerate(lines[:30]):  # Show first 30 lines
            print(f"  {i+1:2d}: {line.rstrip()}")
        if len(lines) > 30:
            print(f"     ... ({len(lines) - 30} more lines)")
    
    print("\n🎯 Key Points:")
    print("1. n_cam is extracted from ptv.par and becomes the global parameter")
    print("2. Each .par file becomes a section in the YAML")
    print("3. Legacy n_img fields are removed from individual sections")
    print("4. Default parameters are added for compatibility")
    print("5. The YAML becomes the single source of truth for all parameters")

if __name__ == "__main__":
    demo_parameter_conversion()
