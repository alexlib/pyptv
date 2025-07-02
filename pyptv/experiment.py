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
    """A parameter set with a name and path"""
    name = Str
    par_path = Path
    # Legacy GUI objects removed - now handled by ParameterManager
    m_params = Instance(object)  # Will be None
    c_params = Instance(object)  # Will be None  
    t_params = Instance(object)  # Will be None


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
        """Save current parameters to YAML"""
        if self.active_params is not None:
            yaml_path = self.active_params.par_path / 'parameters.yaml'
            self.parameter_manager.to_yaml(yaml_path)
            print(f"Parameters saved to {yaml_path}")

    def load_parameters_for_active(self):
        """Load parameters for the active parameter set"""
        if self.active_params is not None:
            yaml_path = self.active_params.par_path / 'parameters.yaml'
            if yaml_path.exists():
                print(f"Loading parameters from YAML: {yaml_path}")
                self.parameter_manager.from_yaml(yaml_path)
            else:
                print(f"Creating parameters from directory: {self.active_params.par_path}")
                self.parameter_manager.from_directory(self.active_params.par_path)
                # Save as YAML for future use
                self.parameter_manager.to_yaml(yaml_path)
                print(f"Saved parameters as YAML: {yaml_path}")

    def getParamsetIdx(self, paramset):
        """Get the index of a parameter set"""
        if isinstance(paramset, int):
            return paramset
        else:
            return self.paramsets.index(paramset)

    def addParamset(self, name: str, par_path: Path):
        """Add a new parameter set to the experiment"""
        # Create ParameterManager for this parameter set
        pm = ParameterManager()
        yaml_path = par_path / 'parameters.yaml'
        if yaml_path.exists():
            pm.from_yaml(yaml_path)
        else:
            pm.from_directory(par_path)
            pm.to_yaml(yaml_path)

        # Create a simplified Paramset without legacy GUI objects
        self.paramsets.append(
            Paramset(
                name=name,
                par_path=par_path,
                m_params=None,  # No longer needed
                c_params=None,  # No longer needed  
                t_params=None,  # No longer needed
            )
        )

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
        self.syncActiveDir()
        # Load parameters for the newly active set
        self.load_parameters_for_active()

    def syncActiveDir(self):
        """Sync the active parameter set to the default parameters directory"""
        default_parameters_path = Path('parameters').resolve()
        if not default_parameters_path.exists():
            default_parameters_path.mkdir()

        # Ensure active_params is set and has par_path attribute
        if self.active_params is not None and hasattr(self.active_params, "par_path"):
            src_dir = self.active_params.par_path
            for ext in ('*.par', '*.yaml', '*.dat'):
                for file in src_dir.glob(ext):
                    dest_file = default_parameters_path / file.name
                    shutil.copy(file, dest_file)
                    print(f"Copied {file} to {dest_file}")
        else:
            print("No active parameter set or invalid active_params; skipping syncActiveDir.")

    def populate_runs(self, exp_path: Path):
        """Populate parameter sets from an experiment directory"""
        self.paramsets = []
        dir_contents = [f for f in exp_path.iterdir() if f.is_dir() and f.stem.startswith('parameters')]

        if len(dir_contents) == 1 and str(dir_contents[0].stem) == 'parameters':
            exp_name = "Run1"
            new_name = str(dir_contents[0]) + exp_name
            new_path = Path(new_name).resolve()
            new_path.mkdir(exist_ok=True)
            
            pm = ParameterManager()
            pm.from_directory(dir_contents[0])
            pm.to_yaml(new_path / 'parameters.yaml')
            
            dir_contents.append(new_path)

        for dir_item in dir_contents:
            if str(dir_item.stem) != 'parameters':
                exp_name = str(dir_item.stem).rsplit("parameters", maxsplit=1)[-1]

                print(f"Experiment name is: {exp_name}")
                print(" adding Parameter set\n")
                self.addParamset(exp_name, dir_item)

        if not self.changed_active_params:
            if self.nParamsets() > 0:
                self.setActive(0)
