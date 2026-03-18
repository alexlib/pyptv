#!/usr/bin/env python3
"""
PyPTV Parameter Utilities

    print(f"🔄 Converting legacy parameters from {parameters_dir}")
    print(f"📁 Looking for .par files in: {parameters_dir}")
    print(f"📄 Output YAML file: {yaml_file}") module provides utilities for converting between legacy parameter formats
(.par files, plugins.json, man_ori.dat) and the new YAML-based parameter system.

Functions:
- legacy_to_yaml: Convert legacy parameter directory to parameters.yaml
- yaml_to_legacy: Convert parameters.yaml back to legacy format
"""

import sys
import shutil
from pathlib import Path
from typing import Union, Optional
import argparse

from pyptv.parameter_manager import ParameterManager
from pyptv.experiment import Experiment


def legacy_to_yaml(parameters_dir: Union[str, Path], 
                   yaml_file: Optional[Union[str, Path]] = None,
                   backup_legacy: bool = True) -> Path:
    """
    Convert legacy parameter directory to parameters.yaml file.
    
    This function reads all .par files from the specified parameters folder,
    along with plugins.json and man_ori.dat if present, and creates 
    a single parameters.yaml file.
    
    Args:
        parameters_dir: Path to parameters folder containing .par files
        yaml_file: Output YAML file path (default: parameters.yaml in parent of parameters_dir)
        backup_legacy: Whether to backup the parameters directory before conversion
        
    Returns:
        Path to the created YAML file
        
    Example:
        >>> legacy_to_yaml("./tests/test_cavity/parameters", "new_params.yaml")
        Path("new_params.yaml")
    """
    parameters_dir = Path(parameters_dir)
    
    if not parameters_dir.exists() or not parameters_dir.is_dir():
        raise ValueError(f"Parameters directory not found: {parameters_dir}")
    
    # Default output file - put in parent directory of parameters folder
    if yaml_file is None:
        yaml_file = parameters_dir.parent / "parameters.yaml"
    else:
        yaml_file = Path(yaml_file)
    
    print(f"🔄 Converting legacy parameters from {parameters_dir}")
    print(f"� Looking for .par files in: {parameters_dir}")
    print(f"�📄 Output YAML file: {yaml_file}")
    
    # Check for required files in parameters/ subfolder
    par_files = list(parameters_dir.glob("*.par"))
    if not par_files:
        raise ValueError(f"No .par files found in {parameters_dir}")
    
    ptv_par = parameters_dir / "ptv.par"
    if not ptv_par.exists():
        raise ValueError(f"Required file ptv.par not found in {parameters_dir}")
    
    print(f"📁 Found {len(par_files)} .par files:")
    for par_file in sorted(par_files):
        print(f"   - {par_file.name}")
    
    # Backup parameters directory if requested
    if backup_legacy:
        backup_dir = parameters_dir.parent / f"{parameters_dir.name}_backup"
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
        shutil.copytree(parameters_dir, backup_dir)
        print(f"💾 Created backup at {backup_dir}")
    
    # Load legacy parameters from parameters folder
    print("📖 Reading legacy .par files...")
    manager = ParameterManager()
    manager.from_directory(parameters_dir)
    
    # Create experiment to handle plugins.json and man_ori.dat migration
    print("🔧 Processing plugins and manual orientation data...")
    experiment = Experiment()
    experiment.pm = manager
    
   
    # Migrate man_ori.dat if it exists in the parameters folder
    # man_ori_dat = parameters_dir / "man_ori.dat"
    # if man_ori_dat.exists():
    #     print(f"📍 Migrating manual orientation from {man_ori_dat}")
    #     manager.migrate_man_ori_dat(parameters_dir)
    # else:
    #     print("ℹ️  No man_ori.dat found - using defaults")
    
    # Save to YAML
    print(f"💾 Saving to YAML: {yaml_file}")
    manager.to_yaml(yaml_file)
    
    print("✅ Conversion complete!")
    print(f"📊 Summary:")
    print(f"   - Global num_cams: {manager.num_cams}")
    print(f"   - Parameter sections: {len(manager.parameters)}")
    print(f"   - YAML file: {yaml_file}")
    print()
    print("🎯 Next steps:")
    print("   - Use parameters.yaml as your single parameter file")
    print("   - Copy parameters.yaml to create different parameter sets")
    print("   - Edit parameters.yaml directly or through PyPTV GUI")
    
    return yaml_file


def yaml_to_legacy(yaml_file: Union[str, Path], 
                   output_dir: Union[str, Path],
                   overwrite: bool = False) -> Path:
    """
    Convert parameters.yaml back to legacy parameter format.
    
    This function reads a parameters.yaml file and creates .par files,
    plugins.json, and man_ori.dat in the specified output directory.
    
    Args:
        yaml_file: Path to the parameters.yaml file
        output_dir: Directory to create legacy parameter files
        overwrite: Whether to overwrite existing directory
        
    Returns:
        Path to the created legacy directory
        
    Example:
        >>> yaml_to_legacy("params.yaml", "legacy_params/")
        Path("legacy_params")
    """
    yaml_file = Path(yaml_file)
    output_dir = Path(output_dir)
    
    if not yaml_file.exists():
        raise ValueError(f"YAML file not found: {yaml_file}")
    
    if output_dir.exists():
        if not overwrite:
            raise ValueError(f"Output directory already exists: {output_dir}. Use overwrite=True to replace.")
        shutil.rmtree(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"🔄 Converting YAML to legacy format")
    print(f"📄 Input YAML file: {yaml_file}")
    print(f"📁 Output directory: {output_dir}")
    
    # Load YAML parameters
    print("📖 Reading YAML parameters...")
    manager = ParameterManager()
    manager.from_yaml(yaml_file)
    
    # Save to legacy .par files
    print("💾 Creating .par files...")
    manager.to_directory(output_dir)
    
    # # Extract and save plugins.json if plugins section exists
    # plugins_params = manager.get_parameter('plugins')
    # if plugins_params:
    #     plugins_json_path = output_dir / "plugins.json"
    #     print(f"🔌 Creating plugins.json at {plugins_json_path}")
        
    #     # Create plugins.json structure
    #     plugins_data = {
    #         "tracking": {
    #             "available": plugins_params.get('available_tracking', ['default']),
    #             "selected": plugins_params.get('selected_tracking', 'default')
    #         },
    #         "sequence": {
    #             "available": plugins_params.get('available_sequence', ['default']),
    #             "selected": plugins_params.get('selected_sequence', 'default')
    #         }
    #     }
        
    #     import json
    #     with open(plugins_json_path, 'w') as f:
    #         json.dump(plugins_data, f, indent=2)
    
    # Extract and save man_ori.dat if manual orientation coordinates exist
    man_ori_coords = manager.get_parameter('man_ori_coordinates')
    if man_ori_coords:
        man_ori_path = output_dir / "man_ori.dat"
        print(f"📍 Creating man_ori.dat at {man_ori_path}")
        
        with open(man_ori_path, 'w') as f:
            num_cams = manager.get_n_cam()  # Use the num_cams attribute directly
            for cam_idx in range(num_cams):
                cam_key = f'camera_{cam_idx}'
                if cam_key in man_ori_coords:
                    for point_idx in range(4):
                        point_key = f'point_{point_idx + 1}'
                        if point_key in man_ori_coords[cam_key]:
                            coords = man_ori_coords[cam_key][point_key]
                            x = coords.get('x', 0.0)
                            y = coords.get('y', 0.0)
                            f.write(f"{x:.6f} {y:.6f}\n")
                        else:
                            f.write("0.000000 0.000000\n")
                else:
                    # Write default coordinates for missing cameras
                    for _ in range(4):
                        f.write("0.000000 0.000000\n")
    
    print("✅ Conversion complete!")
    print(f"📊 Summary:")
    print(f"   - Created {len(list(output_dir.glob('*.par')))} .par files")
    if (output_dir / "plugins.json").exists():
        print("   - Created plugins.json")
    if (output_dir / "man_ori.dat").exists():
        print("   - Created man_ori.dat")
    print(f"   - Legacy directory: {output_dir}")
    
    return output_dir


def main():
    """Command-line interface for parameter conversion utilities."""
    parser = argparse.ArgumentParser(
        description="PyPTV Parameter Conversion Utilities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert legacy parameters folder to YAML
  python parameter_util.py legacy-to-yaml ./tests/test_cavity/parameters
  
  # Convert legacy parameters to specific YAML file
  python parameter_util.py legacy-to-yaml ./tests/test_cavity/parameters --output params.yaml
  
  # Convert YAML back to legacy format
  python parameter_util.py yaml-to-legacy params.yaml legacy_output/
  
  # Convert with overwrite
  python parameter_util.py yaml-to-legacy params.yaml legacy_output/ --overwrite
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Legacy to YAML command
    legacy_parser = subparsers.add_parser(
        'legacy-to-yaml', 
        help='Convert legacy parameter directory to YAML'
    )
    legacy_parser.add_argument(
        'parameters_dir', 
        type=Path,
        help='Path to parameters folder containing .par files'
    )
    legacy_parser.add_argument(
        '--output', '-o',
        type=Path,
        help='Output YAML file (default: parameters.yaml in legacy_dir)'
    )
    legacy_parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Skip creating backup of legacy directory'
    )
    
    # YAML to legacy command
    yaml_parser = subparsers.add_parser(
        'yaml-to-legacy',
        help='Convert YAML file to legacy parameter format'
    )
    yaml_parser.add_argument(
        'yaml_file',
        type=Path,
        help='Input YAML file'
    )
    yaml_parser.add_argument(
        'output_dir',
        type=Path,
        help='Output directory for legacy files'
    )
    yaml_parser.add_argument(
        '--overwrite',
        action='store_true',
        help='Overwrite existing output directory'
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'legacy-to-yaml':
            yaml_file = legacy_to_yaml(
                args.parameters_dir,
                args.output,
                backup_legacy=not args.no_backup
            )
            print(f"\n🎉 Success! YAML file created: {yaml_file}")
            
        elif args.command == 'yaml-to-legacy':
            output_dir = yaml_to_legacy(
                args.yaml_file,
                args.output_dir,
                overwrite=args.overwrite
            )
            print(f"\n🎉 Success! Legacy files created in: {output_dir}")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
