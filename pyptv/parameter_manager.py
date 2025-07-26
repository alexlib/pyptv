import yaml
from pathlib import Path
from pyptv import legacy_parameters as legacy_params

# Minimal ParameterManager for converting between .par directories and YAML files.

class ParameterManager:
    def __init__(self):
        self.parameters = {}
        self.num_cams = 0
        self._class_map = self._get_class_map()
        self.plugins_info = {}  # Initialize plugins_info

    def _get_class_map(self):
        dummy_path = Path('.')
        class_map = {}
        # Map .par filenames to legacy parameter classes
        for cls in [
            legacy_params.PtvParams, legacy_params.CriteriaParams, legacy_params.DetectPlateParams,
            legacy_params.OrientParams, legacy_params.TrackingParams, legacy_params.PftVersionParams,
            legacy_params.ExamineParams, legacy_params.DumbbellParams, legacy_params.ShakingParams
        ]:
            class_map[cls(path=dummy_path).filename] = cls
        for cls in [
            legacy_params.CalOriParams, legacy_params.SequenceParams, legacy_params.TargRecParams,
            legacy_params.MultiPlaneParams, legacy_params.SortGridParams
        ]:
            class_map[cls(n_img=0, path=dummy_path).filename] = cls
        class_map[legacy_params.ManOriParams(n_img=0, nr=[], path=dummy_path).filename] = legacy_params.ManOriParams
        return class_map

    def from_directory(self, dir_path) -> dict:
        """Load parameters from a directory containing .par files."""
        dir_path = Path(dir_path)
        self.parameters = {}
        ptv_par = dir_path / "ptv.par"
        if ptv_par.exists():
            ptv = legacy_params.PtvParams(path=dir_path)
            ptv.read()
            self.num_cams = ptv.n_img
        # print(f"[DEBUG] num_cams after reading ptv.par: {self.num_cams}")
        for par_file in sorted(dir_path.glob("*.par")):
            filename = par_file.name
            if filename in self._class_map:
                cls = self._class_map[filename]
                if filename in ["cal_ori.par", "sequence.par", "targ_rec.par", "man_ori.par", "multi_planes.par", "sortgrid.par"]:
                    if filename == "man_ori.par":
                        obj = cls(n_img=self.num_cams, nr=[], path=dir_path)
                    else:
                        obj = cls(n_img=self.num_cams, path=dir_path)
                else:
                    obj = cls(path=dir_path)
                obj.read()
                # Only include attributes that are actual parameters (not class/static fields)
                # Use the class's 'fields' property if available, else filter by excluding known non-parameter fields
                if hasattr(obj, 'fields') and isinstance(obj.fields, (list, tuple)):
                    d = {k: getattr(obj, k) for k in obj.fields if hasattr(obj, k)}
                else:
                    d = {k: getattr(obj, k) for k in dir(obj)
                         if not k.startswith('_') and not callable(getattr(obj, k))
                         and k not in ['path', 'exp_path', 'default_path', 'filename', 'fields', 'n_img']}
                self.parameters[par_file.stem] = d

        # # Debug print for tracking parameters after loading from directory
        # if 'track' in self.parameters:
        #     print("[DEBUG] 'track' parameters after from_directory:", self.parameters['track'])
        # else:
        #     print("[DEBUG] 'track' section missing after from_directory!")

        # Debug print for cam_id expectations
        # print(f"[DEBUG] Expected cam_id values after from_directory: {list(range(self.num_cams))}")

        # Read man_ori.dat if present and add to parameters as 'man_ori_coordinates'
        man_ori_dat = dir_path / "man_ori.dat"
        if man_ori_dat.exists():
            coords = {}
            try:
                with man_ori_dat.open('r') as f:
                    lines = [line.strip() for line in f if line.strip()]
                num_cams = self.num_cams
                for cam_idx in range(num_cams):
                    cam_key = f'camera_{cam_idx}'
                    coords[cam_key] = {}
                    for pt_idx in range(4):
                        line_idx = cam_idx * 4 + pt_idx
                        if line_idx < len(lines):
                            x_str, y_str = lines[line_idx].split()
                            coords[cam_key][f'point_{pt_idx+1}'] = {'x': float(x_str), 'y': float(y_str)}
                        else:
                            coords[cam_key][f'point_{pt_idx+1}'] = {'x': 0.0, 'y': 0.0}
                self.parameters['man_ori_coordinates'] = coords
            except Exception as e:
                print(f"Warning: Failed to read man_ori.dat: {e}")

        # Ensure splitter and cal_splitter are present in ptv and cal_ori after reading
        if 'ptv' in self.parameters:
            self.parameters['ptv']['splitter'] = getattr(self, 'splitter', False)
        if 'cal_ori' in self.parameters:
            self.parameters['cal_ori']['cal_splitter'] = getattr(self, 'cal_splitter', False)

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

        # Default plugins parameters or scan plugins directory
        plugins_dir = dir_path / 'plugins'
        if not plugins_dir.exists() or not plugins_dir.is_dir():
            if 'plugins' not in self.parameters:
                self.parameters['plugins'] = {
                    'available_tracking': ['default'],
                    'available_sequence': ['default'],
                    'selected_tracking': 'default',
                    'selected_sequence': 'default'
                }
                print("Info: Added default plugins parameters")
        else:
            available_tracking = ['default']
            available_sequence = ['default']
            for entry in plugins_dir.iterdir():
                if entry.is_file() and entry.suffix == '.py':
                    name = entry.stem
                    if 'sequence' in name:
                        available_sequence.append(name)
                    if 'track' in name or 'tracker' in name:
                        available_tracking.append(name)
            self.parameters['plugins'] = {
                'available_tracking': sorted(available_tracking),
                'available_sequence': sorted(available_sequence),
                'selected_tracking': 'default',
                'selected_sequence': 'default'
            }
            print("Info: Populated plugins from plugins directory")

    def scan_plugins(self, plugins_dir=None):
        """Scan the plugins directory and update self.plugins_info with available plugins."""
        if plugins_dir is None:
            plugins_dir = Path('plugins')
        else:
            plugins_dir = Path(plugins_dir)
        plugins = []
        if plugins_dir.exists() and plugins_dir.is_dir():
            for entry in plugins_dir.iterdir():
                if entry.is_dir() or (entry.is_file() and entry.suffix in {'.py', '.so', '.dll'}):
                    plugins.append(entry.stem)
        # Always include 'default' in both available lists
        available_sequence = ['default']
        available_tracking = ['default']
        for plugin in plugins:
            if plugin != 'default':
                available_sequence.append(plugin)
                available_tracking.append(plugin)
        self.plugins_info = {
            'available_sequence': sorted(available_sequence),
            'available_tracking': sorted(available_tracking),
            'selected_sequence': 'default',
            'selected_tracking': 'default'
        }

    def to_yaml(self, file_path) -> dict:
        """Write parameters to a YAML file."""
        file_path = Path(file_path)
        out = {'num_cams': self.num_cams}
        # Remove 'default_path' and 'filename' from all parameter dicts (all classes)
        filtered_params = {}
        for k, v in self.parameters.items():
            if isinstance(v, dict):
                filtered_params[k] = {ik: iv for ik, iv in v.items() if ik not in ('default_path', 'filename')}
            else:
                filtered_params[k] = v

        # Insert splitter under ptv, cal_splitter under cal_ori only if not already present
        if 'ptv' in filtered_params and 'splitter' not in filtered_params['ptv']:
            filtered_params['ptv']['splitter'] = False
        if 'cal_ori' in filtered_params and 'cal_splitter' not in filtered_params['cal_ori']:
            filtered_params['cal_ori']['cal_splitter'] = False

        # Add plugins section if available
        if hasattr(self, 'plugins_info'):
            out['plugins'] = self.plugins_info
        out.update(filtered_params)
        
        def convert(obj):
            if isinstance(obj, dict):
                return {k: convert(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert(i) for i in obj]
            elif isinstance(obj, Path):
                return str(obj)
            else:
                return obj
            
        data = convert(out)
        
        # import traceback

        with file_path.open('w') as f:
            print(f"[DEBUG] Writing to {file_path} at step:")
            # traceback.print_stack(limit=5)
            yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)

    def from_yaml(self, file_path):
        """Load parameters from a YAML file."""

        file_path = Path(file_path)
        with file_path.open('r') as f:
            data = yaml.safe_load(f)

        self.num_cams = data.get('num_cams')
        self.parameters = data


    def to_directory(self, dir_path):
        """Write parameters to a legacy directory as .par files."""
        dir_path = Path(dir_path)
        dir_path.mkdir(parents=True, exist_ok=True)
        # Do NOT write splitter or cal_splitter to directory (par) files; they are YAML-only
        for name, data in self.parameters.items():
            filename = f"{name}.par"
            if filename in self._class_map:
                cls = self._class_map[filename]
                if filename in ["cal_ori.par", "sequence.par", "targ_rec.par", "man_ori.par", "multi_planes.par", "sortgrid.par"]:
                    if filename == "man_ori.par":
                        obj = cls(n_img=self.num_cams, nr=[], path=dir_path)
                    else:
                        obj = cls(n_img=self.num_cams, path=dir_path)
                else:
                    obj = cls(path=dir_path)
                # Special handling for cal_ori.par to ensure correct list lengths and repeat last value if needed
                if filename == "cal_ori.par":
                    if 'img_cal_name' in data and isinstance(data['img_cal_name'], list):
                        L = data['img_cal_name']
                        if len(L) < self.num_cams:
                            last = L[-1] if L else ""
                            L = L + [last for _ in range(self.num_cams - len(L))]
                        data['img_cal_name'] = L[:self.num_cams]
                    if 'img_ori' in data and isinstance(data['img_ori'], list):
                        L = data['img_ori']
                        if len(L) < self.num_cams:
                            last = L[-1] if L else ""
                            L = L + [last for _ in range(self.num_cams - len(L))]
                        data['img_ori'] = L[:self.num_cams]
                for k, v in data.items():
                    if hasattr(obj, k):
                        setattr(obj, k, v)
                if hasattr(obj, 'n_img'):
                    obj.n_img = self.num_cams
                obj.write()

        # Write man_ori.dat if 'man_ori_coordinates' is present in parameters
        coords = self.parameters.get('man_ori_coordinates')
        if coords:
            man_ori_dat = dir_path / "man_ori.dat"
            try:
                with man_ori_dat.open('w') as f:
                    num_cams = self.num_cams
                    for cam_idx in range(num_cams):
                        cam_key = f'camera_{cam_idx}'
                        for pt_idx in range(4):
                            pt_key = f'point_{pt_idx+1}'
                            pt = coords.get(cam_key, {}).get(pt_key, {'x': 0.0, 'y': 0.0})
                            f.write(f"{pt['x']} {pt['y']}\n")
            except Exception as e:
                print(f"Warning: Failed to write man_ori.dat: {e}")

    def get_n_cam(self):
        return self.num_cams
    
    def get_parameter(self, name):
        """Get a specific parameter by name, returning None if not found."""
        parameter = self.parameters.get(name, None)
        if parameter is None:
            raise ValueError(f'{name} returns None')
        return parameter

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Convert between .par directory and YAML file.")
    parser.add_argument('source', type=Path, help="Source directory or YAML file.")
    parser.add_argument('destination', type=Path, help="Destination YAML file or directory.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--to-yaml', action='store_true', help="Convert directory to YAML.")
    group.add_argument('--to-dir', action='store_true', help="Convert YAML to directory.")
    args = parser.parse_args()
    pm = ParameterManager()
    if args.to_yaml:
        pm.from_directory(args.source)
        pm.to_yaml(args.destination)
    elif args.to_dir:
        pm.from_yaml(args.source)
        pm.to_directory(args.destination)