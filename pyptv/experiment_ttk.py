"""
TTK-compatible Experiment management for PyPTV

This module provides a Traits-free version of the Experiment class
for use with the TTK GUI system. It maintains the same interface
as the original Experiment class but without Traits dependencies.
"""

import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any
from pyptv.parameter_manager import ParameterManager


class ParamsetTTK:
    """A parameter set with a name and YAML file path - TTK version without Traits"""
    
    def __init__(self, name: str, yaml_path: Path):
        self.name = name
        self.yaml_path = yaml_path


class ExperimentTTK:
    """
    TTK-compatible Experiment class that manages parameter sets and experiment configuration.

    This is the main model class that owns all experiment data and parameters.
    It delegates parameter management to ParameterManager while handling
    the organization of multiple parameter sets.
    
    This version is Traits-free and designed for use with the TTK GUI system.
    """
    
    def __init__(self, pm: ParameterManager = None):
        self.paramsets: List[ParamsetTTK] = []
        self.pm = pm if pm is not None else ParameterManager()
        self.active_params: Optional[ParamsetTTK] = None
        
        # If pm has a loaded YAML path, add it as a paramset and set active
        yaml_path = getattr(self.pm, 'yaml_path', None)
        if yaml_path is not None:
            paramset = ParamsetTTK(name=yaml_path.stem, yaml_path=yaml_path)
            self.paramsets.append(paramset)
            self.active_params = paramset
        else:
            self.active_params = None

    def get_parameter(self, key: str) -> Any:
        """Get parameter value by key"""
        return self.pm.parameters.get(key)
    
    def set_parameter(self, key: str, value: Any):
        """Set parameter value by key"""
        self.pm.parameters[key] = value
    
    def get_n_cam(self) -> int:
        """Get number of cameras"""
        return self.pm.parameters.get('num_cams', 0)
    
    def set_n_cam(self, n_cam: int):
        """Set number of cameras"""
        self.pm.parameters['num_cams'] = n_cam
    
    def save_parameters(self, yaml_path: Optional[Path] = None):
        """Save parameters to YAML file"""
        if yaml_path is None and self.active_params:
            yaml_path = self.active_params.yaml_path
        
        if yaml_path:
            self.pm.to_yaml(yaml_path)
            print(f"Parameters saved to {yaml_path}")
        else:
            raise ValueError("No YAML path specified for saving parameters")
    
    def load_parameters(self, yaml_path: Path):
        """Load parameters from YAML file"""
        self.pm.from_yaml(yaml_path)
        
        # Update or add paramset
        paramset = ParamsetTTK(name=yaml_path.stem, yaml_path=yaml_path)
        
        # Check if this paramset already exists
        existing_idx = None
        for i, ps in enumerate(self.paramsets):
            if ps.yaml_path.resolve() == yaml_path.resolve():
                existing_idx = i
                break
        
        if existing_idx is not None:
            self.paramsets[existing_idx] = paramset
        else:
            self.paramsets.append(paramset)
        
        self.active_params = paramset
        print(f"Parameters loaded from {yaml_path}")
    
    def set_active(self, index: int):
        """Set active parameter set by index"""
        if 0 <= index < len(self.paramsets):
            self.active_params = self.paramsets[index]
            # Load the parameters from the active paramset
            self.pm.from_yaml(self.active_params.yaml_path)
            print(f"Set active parameter set to: {self.active_params.name}")
        else:
            raise IndexError(f"Parameter set index {index} out of range")
    
    def set_active_by_name(self, name: str):
        """Set active parameter set by name"""
        for i, paramset in enumerate(self.paramsets):
            if paramset.name == name:
                self.set_active(i)
                return
        raise ValueError(f"Parameter set '{name}' not found")
    
    def add_paramset(self, name: str, yaml_path: Path):
        """Add a new parameter set"""
        paramset = ParamsetTTK(name=name, yaml_path=yaml_path)
        self.paramsets.append(paramset)
        return paramset
    
    def remove_paramset(self, index: int):
        """Remove parameter set by index"""
        if 0 <= index < len(self.paramsets):
            removed = self.paramsets.pop(index)
            if self.active_params == removed:
                self.active_params = self.paramsets[0] if self.paramsets else None
            return removed
        else:
            raise IndexError(f"Parameter set index {index} out of range")
    
    def copy_paramset(self, source_index: int, new_name: str, new_yaml_path: Path):
        """Copy parameter set to a new location"""
        if 0 <= source_index < len(self.paramsets):
            source_paramset = self.paramsets[source_index]
            
            # Copy the YAML file
            shutil.copy2(source_paramset.yaml_path, new_yaml_path)
            
            # Create new paramset
            new_paramset = ParamsetTTK(name=new_name, yaml_path=new_yaml_path)
            self.paramsets.append(new_paramset)
            
            return new_paramset
        else:
            raise IndexError(f"Parameter set index {source_index} out of range")
    
    def get_paramset_names(self) -> List[str]:
        """Get list of parameter set names"""
        return [ps.name for ps in self.paramsets]
    
    def get_active_paramset_name(self) -> Optional[str]:
        """Get name of active parameter set"""
        return self.active_params.name if self.active_params else None
    
    def update_parameter_nested(self, category: str, key: str, value: Any):
        """Update a nested parameter value"""
        if category not in self.pm.parameters:
            self.pm.parameters[category] = {}
        self.pm.parameters[category][key] = value
    
    def get_parameter_nested(self, category: str, key: str, default: Any = None) -> Any:
        """Get a nested parameter value"""
        return self.pm.parameters.get(category, {}).get(key, default)
    
    def get_all_parameters(self) -> Dict[str, Any]:
        """Get all parameters as a dictionary"""
        return self.pm.parameters.copy()
    
    def update_parameters(self, updates: Dict[str, Any]):
        """Update multiple parameters at once"""
        for key, value in updates.items():
            if isinstance(value, dict) and key in self.pm.parameters and isinstance(self.pm.parameters[key], dict):
                # Merge nested dictionaries
                self.pm.parameters[key].update(value)
            else:
                self.pm.parameters[key] = value


def create_experiment_from_yaml(yaml_path: Path) -> ExperimentTTK:
    """Create an ExperimentTTK instance from a YAML file"""
    pm = ParameterManager()
    pm.from_yaml(yaml_path)
    pm.yaml_path = yaml_path  # Store the path for reference
    
    experiment = ExperimentTTK(pm=pm)
    return experiment


def create_experiment_from_directory(dir_path: Path) -> ExperimentTTK:
    """Create an ExperimentTTK instance from a parameter directory"""
    pm = ParameterManager()
    pm.from_directory(dir_path)
    
    experiment = ExperimentTTK(pm=pm)
    return experiment