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
        """
        if not isinstance(dir_path, Path):
            dir_path = Path(dir_path)
        self.path = dir_path

        if not dir_path.is_dir():
            print(f"Error: Directory not found at {dir_path}")
            return

        ptv_par_path = dir_path / "ptv.par"
        n_img = 4
        if ptv_par_path.exists():
            ptv_obj = legacy_params.PtvParams(path=dir_path)
            ptv_obj.read()
            n_img = ptv_obj.n_img

        for par_file in sorted(dir_path.glob('*.par')):
            filename = par_file.name
            if filename in self._class_map:
                param_class = self._class_map[filename]
                
                if filename in ["cal_ori.par", "sequence.par", "targ_rec.par", "man_ori.par", "multi_planes.par", "sortgrid.par"]:
                    if filename == 'man_ori.par':
                        param_obj = param_class(n_img=n_img, nr=[], path=dir_path)
                    else:
                        param_obj = param_class(n_img=n_img, path=dir_path)
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
                if param_name == 'ptv':
                    param_dict['splitter'] = False
                if param_name == 'cal_ori':
                    param_dict['cal_splitter'] = False
                self.parameters[param_name] = param_dict
        
        # Ensure default parameters for compatibility
        self.ensure_default_parameters()

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

        with file_path.open('w') as f:
            yaml.dump(self.parameters, f, default_flow_style=False, sort_keys=False)
        print(f"Parameters consolidated and saved to {file_path}")

    def from_yaml(self, file_path: Path):
        if not isinstance(file_path, Path):
            file_path = Path(file_path)
        self.path = file_path.parent

        try:
            with file_path.open('r') as f:
                self.parameters = yaml.safe_load(f) or {}
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

    def to_directory(self, dir_path: Path):
        if not isinstance(dir_path, Path):
            dir_path = Path(dir_path)

        dir_path.mkdir(parents=True, exist_ok=True)

        n_img = self.parameters.get('ptv', {}).get('n_img', 4)

        for name, data in self.parameters.items():
            filename = f"{name}.par"
            if filename in self._class_map:
                param_class = self._class_map[filename]
                
                if filename in ["cal_ori.par", "sequence.par", "targ_rec.par", "man_ori.par", "multi_planes.par", "sortgrid.par"]:
                    if filename == 'man_ori.par':
                        param_obj = param_class(n_img=n_img, nr=[], path=dir_path)
                    else:
                        param_obj = param_class(n_img=n_img, path=dir_path)
                else:
                    param_obj = param_class(path=dir_path)

                for key, value in data.items():
                    if hasattr(param_obj, key):
                        setattr(param_obj, key, value)
                
                param_obj.write()
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
        
        # Ensure ptv parameters have splitter flag
        if 'ptv' in self.parameters and 'splitter' not in self.parameters['ptv']:
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
                'n_img': 4,
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