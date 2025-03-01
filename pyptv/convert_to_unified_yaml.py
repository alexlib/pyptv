#!/usr/bin/env python
"""
Utility script to convert individual YAML parameter files to a unified YAML file.

This script loads all individual YAML parameter files in the parameters directory
and combines them into a single unified YAML file.
"""

import os
import sys
import argparse
from pathlib import Path
import yaml

# Add parent directory to path to allow importing pyptv modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pyptv.yaml_parameters import ParameterManager, DEFAULT_PARAMS_DIR, UNIFIED_YAML_FILENAME


def convert_to_unified_yaml(experiment_path, force=False):
    """
    Convert individual YAML parameter files to a unified YAML file.
    
    Args:
        experiment_path: Path to experiment directory
        force: Whether to overwrite existing unified YAML file
        
    Returns:
        Path to unified YAML file
    """
    # Get parameters directory
    params_dir = Path(experiment_path) / DEFAULT_PARAMS_DIR
    
    # Check if unified YAML file already exists
    unified_path = params_dir / UNIFIED_YAML_FILENAME
    if unified_path.exists() and not force:
        print(f"Unified YAML file already exists: {unified_path}")
        print("Use --force to overwrite it")
        return unified_path
    
    # Create a parameter manager for loading from individual files
    param_manager_individual = ParameterManager(params_dir, unified=False)
    
    # Load all parameters from individual files
    params = param_manager_individual.load_all()
    
    # Create a parameter manager for saving to unified file
    param_manager_unified = ParameterManager(params_dir, unified=True)
    
    # Save all parameters to unified file
    param_manager_unified.save_all(params)
    
    print(f"Successfully converted parameters to unified YAML file: {unified_path}")
    return unified_path


def main():
    """Command-line interface for converting to unified YAML."""
    parser = argparse.ArgumentParser(
        description="Convert individual YAML parameter files to a unified YAML file."
    )
    parser.add_argument(
        "experiment_path",
        help="Path to experiment directory",
        type=str,
        default=".",
        nargs="?",  # Make it optional
    )
    parser.add_argument(
        "--force",
        help="Overwrite existing unified YAML file",
        action="store_true",
    )
    
    args = parser.parse_args()
    
    # Convert to unified YAML
    convert_to_unified_yaml(args.experiment_path, args.force)


if __name__ == "__main__":
    main()