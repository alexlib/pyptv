"""
Experiment management for PyPTV

This module contains the Experiment class which manages parameter sets
and experiment configuration for PyPTV.
"""

import shutil
from pathlib import Path
from traits.api import HasTraits, Instance, List, Str, Bool, Any
from pyptv.parameter_manager import ParameterManager


class Paramset(HasTraits):
    """A parameter set with a name and YAML file path"""
    name = Str()
    yaml_path = Path()
    
    def __init__(self, name: str, yaml_path: Path, **traits):
        super().__init__(**traits)
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
    pm = Instance(ParameterManager)
    
    def __init__(self, pm: ParameterManager = None, **traits):
        super().__init__(**traits)
        self.paramsets = []
        self.pm = pm if pm is not None else ParameterManager()
        # If pm has a loaded YAML path, add it as a paramset and set active
        yaml_path = getattr(self.pm, 'yaml_path', None)
        if yaml_path is not None:
            paramset = Paramset(name=yaml_path.stem, yaml_path=yaml_path)
            self.paramsets.append(paramset)
            self.active_params = paramset
        else:
            self.active_params = None

    def get_parameter(self, key):
        """Get parameter with ParameterManager delegation"""
        return self.pm.get_parameter(key)
    
    def save_parameters(self):
        """Save current parameters to the active parameter set's YAML file"""
        if self.active_params is not None:
            self.pm.to_yaml(self.active_params.yaml_path)
            print(f"Parameters saved to {self.active_params.yaml_path}")

    def load_parameters_for_active(self):
        """Load parameters for the active parameter set"""
        try:
            print(f"Loading parameters from YAML: {self.active_params.yaml_path}")
            self.pm.from_yaml(self.active_params.yaml_path)
        except Exception as e:
            raise IOError(f"Failed to load parameters from {self.active_params.yaml_path}: {e}")

    def getParamsetIdx(self, paramset):
        """Get the index of a parameter set"""
        if isinstance(paramset, int):
            return paramset
        else:
            return self.paramsets.index(paramset)

    def addParamset(self, name: str, yaml_path: Path):
        """Add a new parameter set to the experiment"""
        # Ensure the YAML file exists, creating it from legacy directory if needed
        # if not yaml_path.exists():
        #     # Try to find legacy directory
        #     legacy_dir = yaml_path.parent / f"parameters{name}"
        #     if legacy_dir.exists() and legacy_dir.is_dir():
        #         print(f"Creating YAML from legacy directory: {legacy_dir}")
        #         pm = ParameterManager()
        #         pm.from_directory(legacy_dir)
        #         pm.to_yaml(yaml_path)
        #     else:
        #         print(f"Warning: Neither YAML file {yaml_path} nor legacy directory {legacy_dir} exists")

        # Create a simplified Paramset with just name and YAML path
        self.paramsets.append(Paramset(name=name, yaml_path=yaml_path))

    def removeParamset(self, paramset):
        """Remove a parameter set from the experiment"""
        paramset_idx = self.getParamsetIdx(paramset)
        
        paramset_obj = self.paramsets[paramset_idx]
        # Rename the YAML file to .bck
        yaml_path = getattr(paramset_obj, "yaml_path", None)
        if yaml_path and isinstance(yaml_path, Path) and yaml_path.exists():
            bck_path = yaml_path.with_suffix('.bck')
            yaml_path.rename(bck_path)
            print(f"Renamed YAML file to backup: {bck_path}")

        # Remove the corresponding legacy directory if it exists
        paramset_name = getattr(paramset_obj, 'name', '')
        if paramset_name and yaml_path:
            legacy_dir = yaml_path.parent / f"parameters{paramset_name}"
            if legacy_dir.exists() and legacy_dir.is_dir():
                shutil.rmtree(legacy_dir)
                print(f"Removed legacy directory: {legacy_dir}")

        self.paramsets.remove(self.paramsets[paramset_idx])

    def rename_paramset(self, old_name: str, new_name: str):
        """Rename a parameter set and its YAML file."""
        # Find the paramset by old_name
        paramset_obj = next((ps for ps in self.paramsets if ps.name == old_name), None)
        if paramset_obj is None:
            raise ValueError(f"No parameter set found with name '{old_name}'")

        old_yaml = paramset_obj.yaml_path
        if not old_yaml.exists():
            raise FileNotFoundError(f"YAML file for parameter set '{old_name}' does not exist: {old_yaml}")

        # Create new YAML file path
        new_yaml = old_yaml.parent / f"parameters_{new_name}.yaml"
        if new_yaml.exists():
            raise FileExistsError(f"YAML file for new name already exists: {new_yaml}")

        # Rename the YAML file
        old_yaml.rename(new_yaml)
        print(f"Renamed YAML file from {old_yaml} to {new_yaml}")

        # Update paramset object
        paramset_obj.name = new_name
        paramset_obj.yaml_path = new_yaml

        # # Optionally, rename legacy directory if it exists
        # old_legacy_dir = old_yaml.parent / f"parameters{old_name}"
        # new_legacy_dir = old_yaml.parent / f"parameters{new_name}"
        # if old_legacy_dir.exists() and old_legacy_dir.is_dir():
        #     old_legacy_dir.rename(new_legacy_dir)
        #     print(f"Renamed legacy directory from {old_legacy_dir} to {new_legacy_dir}")

        return paramset_obj, new_yaml

    def nParamsets(self):
        """Get the number of parameter sets"""
        return len(self.paramsets)

    def set_active(self, paramset):
        """Set the active parameter set"""
        paramset_idx = self.getParamsetIdx(paramset)
        self.active_params = self.paramsets[paramset_idx]
        self.paramsets.pop(paramset_idx)
        self.paramsets.insert(0, self.active_params)
        # Load parameters for the newly active set
        self.load_parameters_for_active()

    # def export_legacy_directory(self, output_dir: Path):
    #     """Export current parameters to legacy .par files directory (for compatibility)"""
    #     if self.active_params is not None:
    #         self.pm.to_directory(output_dir)
    #         print(f"Exported parameters to legacy directory: {output_dir}")
    #     else:
    #         print("No active parameter set to export")

    def populate_runs(self, exp_path: Path):
        """Populate parameter sets from an experiment directory"""
        self.paramsets = []
        
        # Look for YAML files with parameter naming patterns
        yaml_patterns = ['*parameters_*.yaml']
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
        if self.nParamsets() > 0 and self.active_params is None:
            self.set_active(0)


    def duplicate_paramset(self, run_name: str):
        """Duplicate a parameter set by copying its YAML file to a new file with '_copy' appended to the name."""
        # Find the paramset by name
        paramset_obj = next((ps for ps in self.paramsets if ps.name == run_name), None)
        if paramset_obj is None:
            raise ValueError(f"No parameter set found with name '{run_name}'")
        
        src_yaml = paramset_obj.yaml_path
        if not src_yaml.exists():
            raise FileNotFoundError(f"YAML file for parameter set '{run_name}' does not exist: {src_yaml}")
        
        # Create new name and path
        new_name = f"{run_name}_copy"
        new_yaml = src_yaml.parent / f"parameters_{new_name}.yaml"
        
        if new_yaml.exists():
            raise FileExistsError(f"Duplicate YAML file already exists: {new_yaml}")
        
        shutil.copy(src_yaml, new_yaml)
        print(f"Duplicated parameter set '{run_name}' to '{new_name}'")
        
        self.addParamset(new_name, new_yaml)
        return new_yaml

    def create_new_paramset(self, name: str, exp_path: Path, copy_from_active: bool = True):
        """Create a new parameter set YAML file"""
        yaml_file = exp_path / f"parameters_{name}.yaml"
        
        if yaml_file.exists():
            raise ValueError(f"Parameter set {name} already exists at {yaml_file}")
        
        if copy_from_active and self.active_params is not None:
            # Copy from active parameter set
            shutil.copy(self.active_params.yaml_path, yaml_file)
            print(f"Created new parameter set {name} by copying from {self.active_params.name}")
        
        self.addParamset(name, yaml_file)
        return yaml_file

    def delete_paramset(self, paramset):
        """Delete a parameter set, its YAML file, and corresponding legacy directory"""
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

        # Delete corresponding legacy directory if it exists
        paramset_name = getattr(paramset_obj, 'name', '')
        if paramset_name and yaml_path:
            legacy_dir = yaml_path.parent / f"parameters{paramset_name}"
            if legacy_dir.exists() and legacy_dir.is_dir():
                shutil.rmtree(legacy_dir)
                print(f"Deleted legacy directory: {legacy_dir}")

        # Remove from list
        self.paramsets.remove(paramset_obj)
        print(f"Removed parameter set: {paramset_name}")

    def get_n_cam(self):
        """Get the global number of cameras"""
        return self.pm.get_n_cam()
