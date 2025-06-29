"""
This module defines the ParameterManager class, which is responsible for
loading, saving, and managing parameters, and converting between a single
YAML file and a directory of parameter files.
"""

import yaml
from pathlib import Path
import argparse
from pyptv import legacy_parameters as old_params

class ParameterManager:
    """
    A centralized manager for handling experiment parameters. It can convert
    a directory of .par files into a single YAML file and vice-versa.
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
            old_params.PtvParams, old_params.CriteriaParams,
            old_params.DetectPlateParams, old_params.OrientParams,
            old_params.TrackingParams, old_params.PftVersionParams,
            old_params.ExamineParams, old_params.DumbbellParams,
            old_params.ShakingParams
        ]
        for cls in base_classes:
            instance = cls(path=dummy_path)
            class_map[instance.filename()] = cls

        n_img_classes = [
            old_params.CalOriParams, old_params.SequenceParams,
            old_params.TargRecParams, old_params.MultiPlaneParams,
            old_params.SortGridParams
        ]
        for cls in n_img_classes:
            instance = cls(n_img=0, path=dummy_path)
            class_map[instance.filename()] = cls

        instance = old_params.ManOriParams(n_img=0, nr=[], path=dummy_path)
        class_map[instance.filename()] = old_params.ManOriParams

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
            ptv_obj = old_params.PtvParams(path=dir_path)
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

    def _clean_value(self, value):
        if isinstance(value, Path):
            return str(value)
        if isinstance(value, list):
            return [self._clean_value(v) for v in value]
        return value

    def get_parameter(self, name):
        return self.parameters.get(name)

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

        with file_path.open('r') as f:
            self.parameters = yaml.safe_load(f)
        print(f"Parameters loaded from {file_path}")

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
