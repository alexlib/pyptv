"""
This module defines the Experiment class, which manages PyPTV experiments 
with YAML-centric parameter sets.

The new design focuses on:
- Single YAML file contains all parameters for an experiment
- Simple file operations for parameter set management
- Working directory determined by YAML file location
- Relative paths resolved relative to YAML file
"""

from pathlib import Path
from typing import List, Optional, Union, Dict, Any
import os
import shutil
from traits.api import HasTraits, List as TraitsList, Str, Instance

from pyptv.parameter_manager import ParameterManager


class Paramset(HasTraits):
    """A parameter set represented by a single YAML file"""
    name = Str()
    yaml_path = Str()  # Store as string to avoid Traits issues
    
    def __init__(self, name: str, yaml_path: Union[str, Path]):
        super().__init__()
        self.name = name
        self.yaml_path = str(Path(yaml_path))
    
    @property 
    def path(self) -> Path:
        """Get yaml_path as Path object"""
        return Path(self.yaml_path)


class Experiment(HasTraits):
    """Experiment management with YAML-centric parameter sets
    
    This class manages an experiment which consists of:
    - A working directory 
    - One or more YAML parameter files
    - Associated data files (images, calibrations, results)
    """
    
    paramsets = TraitsList()
    active_params = Instance(ParameterManager, allow_none=True)
    experiment_path = Str()  # Store as string to avoid Traits issues
    
    def __init__(self, yaml_path: Optional[Union[str, Path]] = None):
        """Initialize experiment
        
        Args:
            yaml_path: Path to a YAML parameter file. If provided, sets this as active.
                      If None, creates empty experiment.
        """
        super().__init__()
        self.paramsets = []
        self.changed_active_params = False
        
        if yaml_path is not None:
            yaml_file = Path(yaml_path).resolve()
            if not yaml_file.exists():
                raise FileNotFoundError(f"Parameter file not found: {yaml_file}")
            
            self.experiment_path = str(yaml_file.parent)
            self.active_params = ParameterManager(yaml_file)
            
            # Add this parameter set
            name = yaml_file.stem.replace('parameters_', '')
            self.add_paramset(name, yaml_file)
            
            print(f"Experiment initialized with {yaml_file}")
        else:
            self.experiment_path = str(Path.cwd())
            self.active_params = ParameterManager()

    @property
    def exp_path(self) -> Path:
        """Get experiment_path as Path object"""
        return Path(self.experiment_path)

    def add_paramset(self, name: str, yaml_path: Union[str, Path]):
        """Add a parameter set to the experiment"""
        yaml_file = Path(yaml_path)
        paramset = Paramset(name, yaml_file)
        self.paramsets.append(paramset)
        print(f"Added parameter set: {name} -> {yaml_file}")

    def load_yaml_file(self, yaml_path: Union[str, Path]) -> ParameterManager:
        """Load a YAML parameter file and set as active
        
        Args:
            yaml_path: Path to YAML parameter file
            
        Returns:
            ParameterManager instance
        """
        yaml_file = Path(yaml_path).resolve()
        if not yaml_file.exists():
            raise FileNotFoundError(f"Parameter file not found: {yaml_file}")
        
        # Update experiment path if needed
        self.experiment_path = yaml_file.parent
        
        # Create new parameter manager
        self.active_params = ParameterManager(yaml_file)
        
        # Add to paramsets if not already there
        name = yaml_file.stem.replace('parameters_', '')
        if not any(p.name == name for p in self.paramsets):
            self.add_paramset(name, yaml_file)
        
        print(f"Loaded parameter file: {yaml_file}")
        return self.active_params

    def set_active_paramset(self, paramset: Union[Paramset, int, str]):
        """Set a parameter set as active
        
        Args:
            paramset: Paramset object, index, or name string
        """
        target_paramset = None
        
        if isinstance(paramset, int):
            if 0 <= paramset < len(self.paramsets):
                target_paramset = self.paramsets[paramset]
            else:
                raise IndexError(f"Invalid paramset index: {paramset}")
        elif isinstance(paramset, str):
            # Find paramset by name
            for p in self.paramsets:
                if p.name == paramset:
                    target_paramset = p
                    break
            if target_paramset is None:
                raise ValueError(f"Parameter set not found: {paramset}")
        elif isinstance(paramset, Paramset):
            target_paramset = paramset
        else:
            raise TypeError(f"Invalid paramset type: {type(paramset)}")
        
        # Load the parameter file
        self.active_params = ParameterManager(target_paramset.path)
        self.changed_active_params = True
        print(f"Set active parameter set: {target_paramset.name}")

    def get_parameter(self, name: str, default: Any = None) -> Any:
        """Get parameter from active parameter set"""
        if self.active_params is None:
            return default
        return self.active_params.get_parameter(name, default)

    def set_parameter(self, name: str, value: Any):
        """Set parameter in active parameter set"""
        if self.active_params is not None:
            self.active_params.set_parameter(name, value)

    def save_parameters(self):
        """Save active parameters to YAML file"""
        if self.active_params is not None:
            return self.active_params.save_yaml()
        return False

    def get_n_cam(self) -> int:
        """Get number of cameras from active parameters"""
        if self.active_params is not None:
            return self.active_params.get_n_cam()
        return 4  # Default

    def copy_paramset(self, source_name: str, new_name: str) -> Paramset:
        """Copy a parameter set
        
        Args:
            source_name: Name of source parameter set
            new_name: Name for new parameter set
            
        Returns:
            New Paramset object
        """
        # Find source paramset
        source = None
        for p in self.paramsets:
            if p.name == source_name:
                source = p
                break
        
        if source is None:
            raise ValueError(f"Source parameter set not found: {source_name}")
        
        # Create new YAML path
        new_yaml_path = self.exp_path / f"parameters_{new_name}.yaml"
        
        # Copy the YAML file
        shutil.copy2(source.yaml_path, new_yaml_path)
        
        # Add new paramset
        self.add_paramset(new_name, new_yaml_path)
        
        print(f"Copied parameter set {source_name} to {new_name}")
        return self.paramsets[-1]

    def delete_paramset(self, paramset: Union[Paramset, str]):
        """Delete a parameter set
        
        Args:
            paramset: Paramset object or name string
        """
        target_paramset = None
        
        if isinstance(paramset, str):
            # Find paramset by name
            for p in self.paramsets:
                if p.name == paramset:
                    target_paramset = p
                    break
            if target_paramset is None:
                raise ValueError(f"Parameter set not found: {paramset}")
        elif isinstance(paramset, Paramset):
            target_paramset = paramset
        else:
            raise TypeError(f"Invalid paramset type: {type(paramset)}")
        
        # Remove YAML file
        if target_paramset.path.exists():
            target_paramset.path.unlink()
            print(f"Deleted parameter file: {target_paramset.path}")
        
        # Remove from list
        self.paramsets.remove(target_paramset)
        print(f"Deleted parameter set: {target_paramset.name}")

    def populate_runs(self, directory: Union[str, Path]):
        """Populate parameter sets from directory containing YAML files
        
        Args:
            directory: Directory to scan for YAML parameter files
        """
        dir_path = Path(directory).resolve()
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {dir_path}")
        
        self.experiment_path = str(dir_path)
        
        # Clear existing paramsets
        self.paramsets.clear()
        
        # Find all parameter YAML files
        yaml_files = list(dir_path.glob("parameters_*.yaml"))
        
        if not yaml_files:
            print(f"No parameter YAML files found in {dir_path}")
            print("Creating default parameter file...")
            from pyptv.parameter_manager import create_parameter_template
            default_yaml = dir_path / "parameters_Run1.yaml"
            create_parameter_template(default_yaml)
            yaml_files = [default_yaml]
        
        # Add each YAML file as a paramset
        for yaml_file in sorted(yaml_files):
            name = yaml_file.stem.replace('parameters_', '')
            self.add_paramset(name, yaml_file)
        
        # Set first one as active
        if self.paramsets:
            self.set_active_paramset(0)
        
        print(f"Found {len(self.paramsets)} parameter sets in {dir_path}")

    def new_run(self, directory: Union[str, Path]):
        """Initialize with a directory path - alias for populate_runs"""
        self.populate_runs(directory)

    def create_new_paramset(self, name: str, template: Optional[str] = None) -> Paramset:
        """Create a new parameter set
        
        Args:
            name: Name for new parameter set
            template: Optional template to copy from (paramset name)
            
        Returns:
            New Paramset object
        """
        new_yaml_path = self.exp_path / f"parameters_{name}.yaml"
        
        if template:
            # Copy from template
            return self.copy_paramset(template, name)
        else:
            # Create from scratch
            from pyptv.parameter_manager import create_parameter_template
            param_manager = create_parameter_template(new_yaml_path)
            self.add_paramset(name, new_yaml_path)
            return self.paramsets[-1]

    def get_working_directory(self) -> Path:
        """Get current working directory (experiment path)"""
        return self.exp_path

    def set_working_directory(self, directory: Union[str, Path]):
        """Set working directory and scan for parameter files
        
        Args:
            directory: Path to experiment directory
        """
        self.populate_runs(directory)

    def validate_experiment(self) -> List[str]:
        """Validate experiment and return list of issues
        
        Returns:
            List of validation error messages
        """
        issues = []
        
        if not self.paramsets:
            issues.append("No parameter sets found")
        
        if self.active_params is None:
            issues.append("No active parameter set")
        else:
            # Validate active parameters
            param_issues = self.active_params.validate_parameters()
            issues.extend(param_issues)
        
        return issues

    def __str__(self) -> str:
        """String representation"""
        return f"Experiment({self.experiment_path}, {len(self.paramsets)} paramsets)"

    def __repr__(self) -> str:
        return self.__str__()
