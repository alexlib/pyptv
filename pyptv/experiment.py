"""
Experiment management for PyPTV

This module contains the Experiment class which manages parameter sets
and experiment configuration for PyPTV.
"""

import shutil
from pathlib import Path
from traits.api import HasTraits, Instance, List, Str
from pyptv.parameter_manager import ParameterManager


class Paramset(HasTraits):
    """A parameter set with a name and YAML file path"""
    name = Str
    yaml_path = Path
    
    def __init__(self, name: str, yaml_path: Path):
        super().__init__()
        self.name = name
        self.yaml_path = yaml_path


class Experiment(HasTraits):
    """
    The Experiment class manages parameter sets and experiment configuration.
    
    This is the main model class that owns all experiment data and parameters.
    It delegates parameter management to ParameterManager while handling
    the organization of multiple parameter sets.
    """
    active_params = Instance(Paramset)
    paramsets = List(Instance(Paramset))

    def __init__(self):
        HasTraits.__init__(self)
        self.changed_active_params = False
        self.parameter_manager = ParameterManager()

    def get_parameter(self, key):
        """Get parameter with ParameterManager delegation"""
        return self.parameter_manager.get_parameter(key)
    
    def save_parameters(self):
        """Save current parameters to the active parameter set's YAML file"""
        if self.active_params is not None:
            self.parameter_manager.to_yaml(self.active_params.yaml_path)
            print(f"Parameters saved to {self.active_params.yaml_path}")

    def load_parameters_for_active(self):
        """Load parameters for the active parameter set"""
        if self.active_params is not None and isinstance(self.active_params, Paramset):
            if self.active_params.yaml_path.exists():
                print(f"Loading parameters from YAML: {self.active_params.yaml_path}")
                self.parameter_manager.from_yaml(self.active_params.yaml_path)
            else:
                # Try to create YAML from legacy directory if it exists
                legacy_dir = self.active_params.yaml_path.parent / f"parameters{self.active_params.name}"
                if legacy_dir.exists() and legacy_dir.is_dir():
                    print(f"Creating YAML from legacy directory: {legacy_dir}")
                    self.parameter_manager.from_directory(legacy_dir)
                    self.parameter_manager.to_yaml(self.active_params.yaml_path)
                    print(f"Saved parameters as YAML: {self.active_params.yaml_path}")
                else:
                    print(f"Warning: YAML file {self.active_params.yaml_path} does not exist and no legacy directory found")
        else:
            print("Warning: active_params is not set or is not a Paramset instance.")

    def getParamsetIdx(self, paramset):
        """Get the index of a parameter set"""
        if isinstance(paramset, int):
            return paramset
        else:
            return self.paramsets.index(paramset)

    def addParamset(self, name: str, yaml_path: Path):
        """Add a new parameter set to the experiment"""
        # Ensure the YAML file exists, creating it from legacy directory if needed
        if not yaml_path.exists():
            # Try to find legacy directory
            legacy_dir = yaml_path.parent / f"parameters{name}"
            if legacy_dir.exists() and legacy_dir.is_dir():
                print(f"Creating YAML from legacy directory: {legacy_dir}")
                pm = ParameterManager()
                pm.from_directory(legacy_dir)
                pm.to_yaml(yaml_path)
            else:
                print(f"Warning: Neither YAML file {yaml_path} nor legacy directory {legacy_dir} exists")

        # Create a simplified Paramset with just name and YAML path
        self.paramsets.append(Paramset(name=name, yaml_path=yaml_path))

    def removeParamset(self, paramset):
        """Remove a parameter set from the experiment"""
        paramset_idx = self.getParamsetIdx(paramset)
        self.paramsets.remove(self.paramsets[paramset_idx])

    def nParamsets(self):
        """Get the number of parameter sets"""
        return len(self.paramsets)

    def setActive(self, paramset):
        """Set the active parameter set"""
        paramset_idx = self.getParamsetIdx(paramset)
        self.active_params = self.paramsets[paramset_idx]
        self.paramsets.pop(paramset_idx)
        self.paramsets.insert(0, self.active_params)
        # Load parameters for the newly active set
        self.load_parameters_for_active()

    def export_legacy_directory(self, output_dir: Path):
        """Export current parameters to legacy .par files directory (for compatibility)"""
        if self.active_params is not None:
            self.parameter_manager.to_directory(output_dir)
            print(f"Exported parameters to legacy directory: {output_dir}")
        else:
            print("No active parameter set to export")

    def populate_runs(self, exp_path: Path):
        """Populate parameter sets from an experiment directory"""
        self.paramsets = []
        
        # Look for YAML files with parameter naming patterns
        yaml_patterns = ['*parameters*.yaml', '*run*.yaml', 'parameters*.yaml']
        yaml_files = []
        
        for pattern in yaml_patterns:
            yaml_files.extend(exp_path.glob(pattern))
        
        # Also look in subdirectories for legacy structure
        subdirs = [d for d in exp_path.iterdir() if d.is_dir() and d.name.startswith('parameters')]
        
        # Convert legacy directories to YAML files if needed
        for subdir in subdirs:
            run_name = subdir.name.replace('parameters', '') or 'Run1'
            yaml_file = exp_path / f"parameters_{run_name}.yaml"
            
            if not yaml_file.exists():
                print(f"Converting legacy directory {subdir} to {yaml_file}")
                pm = ParameterManager()
                pm.from_directory(subdir)
                pm.to_yaml(yaml_file)
                
            yaml_files.append(yaml_file)
        
        # Remove duplicates and sort
        yaml_files = list(set(yaml_files))
        yaml_files.sort()
        
        # Create parameter sets from YAML files
        for yaml_file in yaml_files:
            # Extract run name from filename
            filename = yaml_file.stem
            if 'parameters_' in filename:
                run_name = filename.split('parameters_', 1)[1]
            elif filename.startswith('parameters'):
                run_name = filename[10:] or 'Run1'  # Remove 'parameters' prefix
            elif '_parameters' in filename:
                run_name = filename.split('_parameters', 1)[0]
            else:
                run_name = filename
                
            print(f"Adding parameter set: {run_name} from {yaml_file}")
            self.addParamset(run_name, yaml_file)
        
        # Set the first parameter set as active if none is active
        if not self.changed_active_params and self.nParamsets() > 0:
            self.setActive(0)

    def create_new_paramset(self, name: str, exp_path: Path, copy_from_active: bool = True):
        """Create a new parameter set YAML file"""
        yaml_file = exp_path / f"parameters_{name}.yaml"
        
        if yaml_file.exists():
            raise ValueError(f"Parameter set {name} already exists at {yaml_file}")
        
        if copy_from_active and self.active_params is not None:
            # Copy from active parameter set
            shutil.copy(self.active_params.yaml_path, yaml_file)
            print(f"Created new parameter set {name} by copying from {self.active_params.name}")
        else:
            # Create with default parameters
            pm = ParameterManager()
            pm.to_yaml(yaml_file)
            print(f"Created new parameter set {name} with default parameters")
        
        self.addParamset(name, yaml_file)
        return yaml_file

    def delete_paramset(self, paramset):
        """Delete a parameter set and its YAML file"""
        paramset_idx = self.getParamsetIdx(paramset)
        paramset_obj = self.paramsets[paramset_idx]

        # Ensure paramset_obj is a Paramset instance
        if not isinstance(paramset_obj, Paramset):
            raise TypeError("paramset_obj is not a Paramset instance")

        if paramset_obj == self.active_params:
            raise ValueError("Cannot delete the active parameter set")

        # Delete the YAML file
        yaml_path = getattr(paramset_obj, "yaml_path", None)
        if yaml_path and isinstance(yaml_path, Path) and yaml_path.exists():
            yaml_path.unlink()
            print(f"Deleted YAML file: {yaml_path}")

        # Remove from list
        self.paramsets.remove(paramset_obj)
        print(f"Removed parameter set: {getattr(paramset_obj, 'name', str(paramset_obj))}")

    def get_n_cam(self):
        """Get the global number of cameras"""
        return self.parameter_manager.get_n_cam()
