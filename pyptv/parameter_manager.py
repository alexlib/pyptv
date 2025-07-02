"""
This module defines the ParameterManager class, which is responsible for
loading, saving, and managing parameters, and converting between a single
YAML file and a directory of parameter files.
"""

import yaml
from pathlib import Path
import argparse
from pyptv import legacy_parameters as legacy_params

class ParameterManager:
    """
    A centralized manager for handling experiment parameters. It can convert
    a directory of .par files into a single YAML file and vice-versa.
    
    Features robust error handling for missing parameters:
    
    Example usage:
        pm = ParameterManager()
        pm.from_yaml('parameters.yaml')
        
        # Safe parameter access with defaults
        masking_params = pm.get_parameter('masking', default={'mask_flag': False})
        mask_flag = pm.get_parameter_value('masking', 'mask_flag', default=False)
        
        # Check parameter existence
        if pm.has_parameter('masking'):
            print("Masking parameters available")
    """

    def __init__(self):
        """
        Initializes the ParameterManager.
        """
        self.parameters = {}
        self.n_cam = 4  # Global number of cameras - critical parameter that defines structure
        self._class_map = self._get_class_map()
        self.path = None

    def _get_class_map(self):
        """Builds a map from parameter file names to their corresponding classes."""
        dummy_path = Path('.')
        class_map = {}

        base_classes = [
            legacy_params.PtvParams, legacy_params.CriteriaParams,
            legacy_params.DetectPlateParams, legacy_params.OrientParams,
            legacy_params.TrackingParams, legacy_params.PftVersionParams,
            legacy_params.ExamineParams, legacy_params.DumbbellParams,
            legacy_params.ShakingParams
        ]
        for cls in base_classes:
            instance = cls(path=dummy_path)
            class_map[instance.filename()] = cls

        n_img_classes = [
            legacy_params.CalOriParams, legacy_params.SequenceParams,
            legacy_params.TargRecParams, legacy_params.MultiPlaneParams,
            legacy_params.SortGridParams
        ]
        for cls in n_img_classes:
            instance = cls(n_img=0, path=dummy_path)
            class_map[instance.filename()] = cls

        instance = legacy_params.ManOriParams(n_img=0, nr=[], path=dummy_path)
        class_map[instance.filename()] = legacy_params.ManOriParams

        return class_map

    def from_directory(self, dir_path: Path):
        """
        Loads parameters from a directory of .par files.
        First determines n_cam from ptv.par, then uses it globally.
        """
        if not isinstance(dir_path, Path):
            dir_path = Path(dir_path)
        self.path = dir_path

        if not dir_path.is_dir():
            print(f"Error: Directory not found at {dir_path}")
            return

        # First, read ptv.par to determine n_cam (global number of cameras)
        ptv_par_path = dir_path / "ptv.par"
        if ptv_par_path.exists():
            ptv_obj = legacy_params.PtvParams(path=dir_path)
            ptv_obj.read()
            self.n_cam = ptv_obj.n_img  # Extract global n_cam from ptv.par
            print(f"Global n_cam set to {self.n_cam} from ptv.par")
        else:
            print(f"Warning: ptv.par not found, using default n_cam = {self.n_cam}")

        # Now load all parameter files using the global n_cam
        for par_file in sorted(dir_path.glob('*.par')):
            filename = par_file.name
            if filename in self._class_map:
                param_class = self._class_map[filename]
                
                # Use global n_cam for classes that need it
                if filename in ["cal_ori.par", "sequence.par", "targ_rec.par", "man_ori.par", "multi_planes.par", "sortgrid.par"]:
                    if filename == 'man_ori.par':
                        param_obj = param_class(n_img=self.n_cam, nr=[], path=dir_path)
                    else:
                        param_obj = param_class(n_img=self.n_cam, path=dir_path)
                else:
                    param_obj = param_class(path=dir_path)

                param_obj.read()
                param_name = par_file.stem
                
                param_dict = {
                    key: self._clean_value(getattr(param_obj, key))
                    for key in dir(param_obj)
                    if not key.startswith('_') and not key.endswith('_')
                       and key not in ['path', 'exp_path', 'trait_added', 'trait_modified', 'wrappers', 'default_path']
                       and not callable(getattr(param_obj, key))
                }
                
                # Remove redundant n_img from all parameter groups
                if 'n_img' in param_dict:
                    del param_dict['n_img']
                    print(f"Removed redundant n_img from {param_name} parameters")
                
                # Don't add n_cam to individual groups - use global only
                if param_name == 'ptv':
                    param_dict['splitter'] = False
                
                if param_name == 'cal_ori':
                    param_dict['cal_splitter'] = False
                    
                self.parameters[param_name] = param_dict
        
        # Ensure default parameters for compatibility
        self.ensure_default_parameters()

    def _clean_value(self, value):
        if isinstance(value, Path):
            return str(value)
        if isinstance(value, list):
            return [self._clean_value(v) for v in value]
        return value

    def get_parameter(self, name, default=None, warn_if_missing=True):
        """
        Get a parameter by name with robust error handling.
        
        Args:
            name (str): The parameter name to retrieve
            default: Default value to return if parameter doesn't exist
            warn_if_missing (bool): Whether to print a warning if parameter is missing
            
        Returns:
            The parameter value if found, otherwise the default value
        """
        if name in self.parameters:
            return self.parameters[name]
        else:
            if warn_if_missing:
                print(f"Warning: Parameter '{name}' not found in configuration. Using default value: {default}")
            return default
    
    def get_parameter_value(self, param_group, param_key, default=None, warn_if_missing=True):
        """
        Get a specific parameter value from a parameter group.
        
        Args:
            param_group (str): The parameter group name (e.g., 'masking', 'ptv')
            param_key (str): The specific parameter key within the group
            default: Default value to return if parameter doesn't exist
            warn_if_missing (bool): Whether to print a warning if parameter is missing
            
        Returns:
            The parameter value if found, otherwise the default value
        """
        group = self.get_parameter(param_group, default={}, warn_if_missing=warn_if_missing)
        if isinstance(group, dict) and param_key in group:
            return group[param_key]
        else:
            if warn_if_missing and param_group in self.parameters:
                print(f"Warning: Parameter '{param_key}' not found in group '{param_group}'. Using default value: {default}")
            return default
    
    def has_parameter(self, name):
        """
        Check if a parameter exists.
        
        Args:
            name (str): The parameter name to check
            
        Returns:
            bool: True if parameter exists, False otherwise
        """
        return name in self.parameters
    
    def has_parameter_value(self, param_group, param_key):
        """
        Check if a specific parameter value exists in a parameter group.
        
        Args:
            param_group (str): The parameter group name
            param_key (str): The specific parameter key within the group
            
        Returns:
            bool: True if parameter value exists, False otherwise
        """
        group = self.parameters.get(param_group, {})
        return isinstance(group, dict) and param_key in group

    def to_yaml(self, file_path: Path):
        if not isinstance(file_path, Path):
            file_path = Path(file_path)

        # Create output data with global n_cam at the top
        output_data = {'n_cam': self.n_cam}
        output_data.update(self.parameters)

        with file_path.open('w') as f:
            yaml.dump(output_data, f, default_flow_style=False, sort_keys=False)
        print(f"Parameters consolidated and saved to {file_path} with global n_cam = {self.n_cam}")

    def from_yaml(self, file_path: Path):
        if not isinstance(file_path, Path):
            file_path = Path(file_path)
        self.path = file_path.parent

        try:
            with file_path.open('r') as f:
                data = yaml.safe_load(f) or {}
            
            # Extract global n_cam from the YAML structure - SINGLE SOURCE OF TRUTH
            if 'n_cam' in data:
                # Direct n_cam field (the ONLY way n_cam should be stored)
                self.n_cam = data.pop('n_cam')  # Remove from data after extracting
                print(f"Global n_cam set to {self.n_cam} from top-level YAML")
            else:
                print(f"Warning: n_cam not found at top level in YAML, using default {self.n_cam}")
            
            # Clean up any legacy n_cam/n_img in subsections - they should not exist
            self._remove_legacy_n_cam_from_subsections(data)
                
            self.parameters = data
            print(f"Parameters loaded from {file_path}")
            
            # Ensure default parameters for compatibility
            self.ensure_default_parameters()
            
        except FileNotFoundError:
            print(f"Warning: YAML file not found at {file_path}. Using empty parameters.")
            self.parameters = {}
            self.ensure_default_parameters()
        except yaml.YAMLError as e:
            print(f"Error: Failed to parse YAML file {file_path}: {e}")
            self.parameters = {}
            self.ensure_default_parameters()

    def _remove_legacy_n_cam_from_subsections(self, data):
        """Remove any legacy n_cam or n_img from parameter subsections."""
        sections_to_clean = ['ptv', 'cal_ori', 'sequence', 'targ_rec', 'multi_planes', 'sortgrid']
        
        for section in sections_to_clean:
            if section in data and isinstance(data[section], dict):
                if 'n_cam' in data[section]:
                    legacy_val = data[section].pop('n_cam')
                    print(f"Removed legacy n_cam={legacy_val} from {section} section")
                if 'n_img' in data[section]:
                    legacy_val = data[section].pop('n_img')
                    print(f"Removed legacy n_img={legacy_val} from {section} section")

    def to_directory(self, dir_path: Path):
        if not isinstance(dir_path, Path):
            dir_path = Path(dir_path)

        dir_path.mkdir(parents=True, exist_ok=True)

        # Use global n_cam for all parameter objects that need it
        print(f"Writing parameters to directory using global n_cam = {self.n_cam}")

        for name, data in self.parameters.items():
            filename = f"{name}.par"
            if filename in self._class_map:
                param_class = self._class_map[filename]
                
                # Create parameter object with global n_cam
                if filename in ["cal_ori.par", "sequence.par", "targ_rec.par", "man_ori.par", "multi_planes.par", "sortgrid.par"]:
                    if filename == 'man_ori.par':
                        param_obj = param_class(n_img=self.n_cam, nr=[], path=dir_path)
                    else:
                        param_obj = param_class(n_img=self.n_cam, path=dir_path)
                else:
                    param_obj = param_class(path=dir_path)

                # Set parameter values, handling special cases
                for key, value in data.items():
                    if hasattr(param_obj, key):
                        # For legacy compatibility, map n_cam back to n_img when writing to objects
                        if key == 'n_cam' and hasattr(param_obj, 'n_img'):
                            setattr(param_obj, 'n_img', value)
                        else:
                            setattr(param_obj, key, value)
                
                # Ensure n_img is set for objects that need it
                if hasattr(param_obj, 'n_img') and not hasattr(data, 'n_img'):
                    param_obj.n_img = self.n_cam
                
                try:
                    param_obj.write()
                except Exception as e:
                    print(f"Exception caught, message: {e}")
                    
        print(f"Parameters written to individual files in {dir_path}")

    def ensure_default_parameters(self):
        """
        Ensure that commonly missing parameters have default values.
        This helps maintain compatibility with older parameter files.
        """
        # Default masking parameters
        if 'masking' not in self.parameters:
            self.parameters['masking'] = {
                'mask_flag': False,
                'mask_base_name': ''
            }
            print("Info: Added default masking parameters")
        
        # Default unsharp mask parameters
        if 'unsharp_mask' not in self.parameters:
            self.parameters['unsharp_mask'] = {
                'flag': False,
                'size': 3,
                'strength': 1.0
            }
            print("Info: Added default unsharp mask parameters")
        
        # Ensure ptv parameters have splitter flag (but NOT n_cam)
        if 'ptv' in self.parameters:
            if 'splitter' not in self.parameters['ptv']:
                self.parameters['ptv']['splitter'] = False
                print("Info: Added default splitter flag to ptv parameters")
        
        # Ensure cal_ori parameters have cal_splitter flag
        if 'cal_ori' in self.parameters and 'cal_splitter' not in self.parameters['cal_ori']:
            self.parameters['cal_ori']['cal_splitter'] = False
            print("Info: Added default cal_splitter flag to cal_ori parameters")

    def get_default_value_for_parameter(self, param_group, param_key):
        """
        Get a sensible default value for a known parameter.
        
        Args:
            param_group (str): The parameter group name
            param_key (str): The parameter key
            
        Returns:
            A sensible default value based on the parameter type
        """
        # Define known defaults for common parameters
        defaults = {
            'masking': {
                'mask_flag': False,
                'mask_base_name': '',
            },
            'unsharp_mask': {
                'flag': False,
                'size': 3,
                'strength': 1.0,
            },
            'ptv': {
                'splitter': False,
                'hp_flag': True,
                'allcam_flag': False,
                'tiff_flag': True,
            },
            'cal_ori': {
                'cal_splitter': False,
                'pair_flag': False,
                'tiff_flag': True,
            }
        }
        
        if param_group in defaults and param_key in defaults[param_group]:
            return defaults[param_group][param_key]
        
        # Generic defaults based on common naming patterns
        if param_key.endswith('_flag') or param_key.startswith('flag'):
            return False
        elif param_key.endswith('_name') or param_key.startswith('name'):
            return ''
        elif 'min' in param_key.lower():
            return 0
        elif 'max' in param_key.lower():
            return 100
        elif 'size' in param_key.lower():
            return 1
        else:
            return None

    def get_n_cam(self):
        """
        Get the global number of cameras.
        
        Returns:
            int: The global number of cameras
        """
        return self.n_cam
    
    def set_n_cam(self, n_cam):
        """
        Set the global number of cameras.
        
        Args:
            n_cam (int): The number of cameras
        """
        self.n_cam = n_cam
        print(f"Global n_cam set to {self.n_cam}")
        # Note: We do NOT update any subsections - n_cam only exists at top level
    
def main():
    parser = argparse.ArgumentParser(
        description="Convert between a directory of .par files and a single YAML file.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('source', type=Path, help="Source directory or YAML file.")
    parser.add_argument('destination', type=Path, help="Destination YAML file or directory.")
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--to-yaml', 
        action='store_true', 
        help="Convert from a directory of .par files to a single YAML file.\n"
             "Example: python pyptv/parameter_manager.py tests/test_cavity/parameters/ parameters.yaml --to-yaml"
    )
    group.add_argument(
        '--to-dir', 
        action='store_true', 
        help="Convert from a single YAML file to a directory of .par files.\n"
             "Example: python pyptv/parameter_manager.py parameters.yaml new_params_dir/ --to-dir"
    )

    args = parser.parse_args()
    manager = ParameterManager()

    if args.to_yaml:
        if not args.source.is_dir():
            parser.error("Source for --to-yaml must be an existing directory.")
        print(f"Converting directory '{args.source}' to YAML file '{args.destination}'...")
        manager.from_directory(args.source)
        manager.to_yaml(args.destination)

    elif args.to_dir:
        if not args.source.is_file():
            parser.error("Source for --to-dir must be an existing file.")
        print(f"Converting YAML file '{args.source}' to directory '{args.destination}'...")
        manager.from_yaml(args.source)
        manager.to_directory(args.destination)

if __name__ == '__main__':
    main()