"""
YAML-centric parameter manager for PyPTV

This module implements the new design where a single YAML file contains
all parameters needed for an experiment. The YAML file location determines
the working directory and all relative paths are resolved relative to it.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
import os
import shutil


class ParameterManager:
    """YAML-centric parameter manager for PyPTV
    
    This class handles all parameter management through a single YAML file
    that contains all parameters needed for an experiment. The YAML file location
    determines the working directory and all relative paths are resolved relative
    to the YAML file location.
    """
    
    def __init__(self, yaml_path: Optional[Union[str, Path]] = None):
        """Initialize ParameterManager with a YAML file
        
        Args:
            yaml_path: Path to the YAML parameter file. If None, creates empty parameters.
        """
        if yaml_path is not None:
            self.yaml_path = Path(yaml_path).resolve()
            if not self.yaml_path.exists():
                raise FileNotFoundError(f"Parameter file not found: {self.yaml_path}")
            self.working_dir = self.yaml_path.parent
            self.parameters = self.load_yaml()
            print(f"Working directory: {self.working_dir}")
            print(f"Parameter file: {self.yaml_path.name}")
        else:
            self.yaml_path = None
            self.working_dir = Path.cwd()
            self.parameters = {}

    def load_yaml(self) -> Dict[str, Any]:
        """Load parameters from YAML file"""
        try:
            with open(str(self.yaml_path), 'r') as f:
                parameters = yaml.safe_load(f) or {}
            print(f"Loaded parameters from {self.yaml_path}")
            return parameters
        except Exception as e:
            print(f"Error loading YAML file {self.yaml_path}: {e}")
            return {}

    def save_yaml(self, yaml_path: Optional[Path] = None) -> bool:
        """Save parameters to YAML file
        
        Args:
            yaml_path: Optional path to save to. If None, uses self.yaml_path
        """
        save_path = yaml_path or self.yaml_path
        if save_path is None:
            print("No YAML path specified for saving")
            return False
            
        try:
            with open(save_path, 'w') as f:
                yaml.dump(self.parameters, f, default_flow_style=False, sort_keys=False)
            print(f"Parameters saved to {save_path}")
            return True
        except Exception as e:
            print(f"Error saving parameters to {save_path}: {e}")
            return False

    def get_parameter(self, name: str, default: Any = None) -> Any:
        """Get a parameter by name
        
        Args:
            name: Parameter name (can be nested with dots, e.g., 'ptv.n_cam')
            default: Default value if parameter not found
        """
        if '.' in name:
            # Handle nested parameters
            keys = name.split('.')
            value = self.parameters
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default
            return value
        else:
            return self.parameters.get(name, default)

    def set_parameter(self, name: str, value: Any):
        """Set a parameter value
        
        Args:
            name: Parameter name (can be nested with dots)
            value: Parameter value
        """
        if '.' in name:
            # Handle nested parameters
            keys = name.split('.')
            current = self.parameters
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            current[keys[-1]] = value
        else:
            self.parameters[name] = value

    def resolve_path(self, relative_path: Union[str, Path]) -> Path:
        """Convert relative path to absolute based on YAML location
        
        Args:
            relative_path: Path relative to YAML file location
            
        Returns:
            Absolute path
        """
        if Path(relative_path).is_absolute():
            return Path(relative_path)
        else:
            return (self.working_dir / relative_path).resolve()

    def resolve_image_paths(self, img_names: List[str]) -> List[str]:
        """Resolve image paths relative to working directory
        
        Args:
            img_names: List of image name patterns (may contain %d for frame numbers)
            
        Returns:
            List of resolved path patterns
        """
        resolved = []
        for name in img_names:
            if Path(name).is_absolute():
                resolved.append(name)
            else:
                # For relative paths, resolve relative to working directory
                resolved.append(str(self.working_dir / name))
        return resolved

    def get_n_cam(self) -> int:
        """Get number of cameras from parameters"""
        return self.get_parameter('n_cam', 4)

    def get_image_names(self, frame_num: Optional[int] = None) -> List[str]:
        """Get image file names for cameras
        
        Args:
            frame_num: Frame number to substitute in patterns
            
        Returns:
            List of image file names
        """
        img_names = self.get_parameter('ptv.img_name', [])
        if not img_names:
            # Fallback to default pattern
            n_cam = self.get_n_cam()
            img_names = [f"cam{i+1}.tif" for i in range(n_cam)]
        
        # Resolve paths and substitute frame numbers if provided
        resolved_names = self.resolve_image_paths(img_names)
        
        if frame_num is not None:
            resolved_names = [name % frame_num if '%d' in name else name 
                            for name in resolved_names]
        
        return resolved_names

    def get_calibration_files(self) -> Dict[str, List[str]]:
        """Get calibration file paths"""
        cal_params = self.get_parameter('cal_ori', {})
        
        files = {}
        if 'img_ori' in cal_params:
            files['ori'] = [str(self.resolve_path(f)) for f in cal_params['img_ori']]
        
        if 'img_cal_name' in cal_params:
            files['cal_images'] = [str(self.resolve_path(f)) for f in cal_params['img_cal_name']]
            
        return files

    def copy_parameter_set(self, new_yaml_path: Union[str, Path]) -> 'ParameterManager':
        """Copy this parameter set to a new YAML file
        
        Args:
            new_yaml_path: Path for the new parameter file
            
        Returns:
            New ParameterManager instance for the copied parameters
        """
        new_path = Path(new_yaml_path)
        
        # Copy the YAML file
        if self.yaml_path:
            shutil.copy2(self.yaml_path, new_path)
        else:
            # Save current parameters to new file
            with open(new_path, 'w') as f:
                yaml.dump(self.parameters, f, default_flow_style=False, sort_keys=False)
        
        print(f"Parameter set copied to {new_path}")
        return ParameterManager(new_path)

    def get_working_directory(self) -> Path:
        """Get the working directory (YAML file location)"""
        return self.working_dir

    def get_yaml_path(self) -> Optional[Path]:
        """Get the YAML file path"""
        return self.yaml_path

    def update_parameters(self, updates: Dict[str, Any]):
        """Update multiple parameters at once
        
        Args:
            updates: Dictionary of parameter updates
        """
        for key, value in updates.items():
            self.set_parameter(key, value)

    def validate_parameters(self) -> List[str]:
        """Validate parameter set and return list of issues
        
        Returns:
            List of validation error messages
        """
        issues = []
        
        # Check required parameters
        required = ['n_cam', 'ptv', 'cal_ori']
        for req in required:
            if not self.get_parameter(req):
                issues.append(f"Missing required parameter: {req}")
        
        # Check file paths exist
        try:
            cal_files = self.get_calibration_files()
            for file_type, files in cal_files.items():
                for file_path in files:
                    if not Path(file_path).exists():
                        issues.append(f"Missing {file_type} file: {file_path}")
        except Exception as e:
            issues.append(f"Error checking calibration files: {e}")
        
        return issues

    def __str__(self) -> str:
        """String representation"""
        if self.yaml_path:
            return f"ParameterManager({self.yaml_path.name})"
        else:
            return "ParameterManager(no file)"

    def __repr__(self) -> str:
        return self.__str__()


def create_parameter_template(yaml_path: Union[str, Path], n_cam: int = 4) -> ParameterManager:
    """Create a template parameter YAML file
    
    Args:
        yaml_path: Path for the new parameter file
        n_cam: Number of cameras
        
    Returns:
        ParameterManager instance for the new file
    """
    template = {
        'n_cam': n_cam,
        'ptv': {
            'img_name': [f'img/cam{i+1}.%04d' for i in range(n_cam)],
            'imx': 1024,
            'imy': 1024,
            'pix_x': 0.01,
            'pix_y': 0.01,
            'chfield': 0,
            'hp_flag': 1,
            'allCam_flag': 0,
            'tiff_flag': 1,
            'imag_flag': 0,
            'splitter': 0,
            'inverse': 0
        },
        'cal_ori': {
            'img_cal_name': [f'cal/cam{i+1}_cal' for i in range(n_cam)],
            'img_ori': [f'cal/cam{i+1}.ori' for i in range(n_cam)],
            'fixp_name': 'cal/fixp_name.dat',
            'cal_splitter': 0
        },
        'sequence': {
            'base_name': [f'img/cam{i+1}.%04d' for i in range(n_cam)],
            'first': 1,
            'last': 100
        },
        'targ_rec': {
            'gv_th_1': 50,
            'gv_th_2': 10,
            'gv_th_3': 5,
            'min_npix': 4,
            'max_npix': 20,
            'min_npix_x': 2,
            'max_npix_x': 10,
            'min_npix_y': 2,
            'max_npix_y': 10,
            'sum_grey_value': 20,
            'x_size': [0.2] * n_cam,
            'y_size': [0.2] * n_cam,
            'pixel_count_x': [3] * n_cam,
            'pixel_count_y': [3] * n_cam
        },
        'tracking': {
            'dvx_max': 20.0,
            'dvy_max': 20.0,
            'dvz_max': 20.0,
            'angle_max': 30.0,
            'dacc_max': 0.1
        },
        'calibration': {
            'n_planes': 1,
            'plane_name': ['plane1'],
            'examine_flag': 0,
            'combine_flag': 0
        }
    }
    
    path = Path(yaml_path)
    with open(path, 'w') as f:
        yaml.dump(template, f, default_flow_style=False, sort_keys=False)
    
    print(f"Parameter template created: {path}")
    return ParameterManager(path)


# Legacy conversion utilities - Use pyptv.parameter_util module for conversions
# Note: The conversion functions are implemented in parameter_util.py to avoid circular imports
