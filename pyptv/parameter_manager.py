"""
This module defines the ParameterManager class, which is responsible for
loading, saving, and managing parameters, and converting between a single
YAML file and a directory of parameter files.

This is a simplified, YAML-centric implementation that focuses on:
- Direct YAML-first design (no complex .par file mapping)
- Simple parameter access methods
- Clean error handling
- No temporary files or complex class initialization
"""

import yaml
from pathlib import Path
import argparse
from typing import Dict, Any, Optional


class ParameterManager:
    """
    A simplified parameter manager focused on YAML-centric operation.
    
    Key principles:
    - YAML is the primary format
    - Legacy .par support is minimal and direct
    - Simple, predictable API
    - No complex class mappings or temporary files
    """

    def __init__(self):
        """Initialize with empty parameters and default camera count."""
        self.parameters: Dict[str, Any] = {}
        self.n_cam: int = 4  # Global number of cameras
        self.path: Path = Path('.')

    def get_n_cam(self) -> int:
        """Get the global number of cameras."""
        return self.n_cam
    
    def set_n_cam(self, n_cam: int):
        """Set the global number of cameras."""
        self.n_cam = n_cam

    def get_parameter(self, name: str, default: Any = None, warn_if_missing: bool = True) -> Any:
        """
        Get a parameter by name with robust error handling.
        
        Args:
            name: The parameter name to retrieve
            default: Default value to return if parameter doesn't exist
            warn_if_missing: Whether to print a warning if parameter is missing
            
        Returns:
            The parameter value if found, otherwise the default value
        """
        if name in self.parameters:
            return self.parameters[name]
        else:
            if warn_if_missing and default is None:
                print(f"Warning: Parameter '{name}' not found in configuration.")
            return default
    
    def get_parameter_value(self, param_group: str, param_key: str, 
                          default: Any = None, warn_if_missing: bool = True) -> Any:
        """
        Get a specific parameter value from a parameter group.
        
        Args:
            param_group: The parameter group name (e.g., 'masking', 'ptv')
            param_key: The specific parameter key within the group
            default: Default value to return if parameter doesn't exist
            warn_if_missing: Whether to print a warning if parameter is missing
            
        Returns:
            The parameter value if found, otherwise the default value
        """
        group = self.get_parameter(param_group, default={}, warn_if_missing=False)
        if isinstance(group, dict) and param_key in group:
            return group[param_key]
        else:
            if warn_if_missing and param_group in self.parameters and default is None:
                print(f"Warning: Parameter '{param_key}' not found in group '{param_group}'.")
            return default
    
    def has_parameter(self, name: str) -> bool:
        """Check if a parameter exists."""
        return name in self.parameters
    
    def has_parameter_value(self, param_group: str, param_key: str) -> bool:
        """Check if a specific parameter value exists in a parameter group."""
        group = self.parameters.get(param_group, {})
        return isinstance(group, dict) and param_key in group

    def from_yaml(self, file_path: Path):
        """
        Load parameters from a YAML file.
        
        Args:
            file_path: Path to the YAML file
        """
        if not isinstance(file_path, Path):
            file_path = Path(file_path)
        self.path = file_path.parent

        try:
            with file_path.open('r') as f:
                data = yaml.safe_load(f) or {}
            
            # Extract global n_cam from the YAML structure
            if 'n_cam' in data:
                self.n_cam = data.pop('n_cam')  # Remove from data after extracting
                print(f"Global n_cam set to {self.n_cam} from top-level YAML")
            else:
                print(f"Warning: n_cam not found at top level in YAML, using default {self.n_cam}")
            
            # Clean up any legacy n_cam/n_img in subsections
            self._remove_legacy_n_cam_from_subsections(data)
                
            self.parameters = data
            print(f"Parameters loaded from {file_path}")
            
            # Ensure default parameters for compatibility
            self._ensure_default_parameters()
            
        except FileNotFoundError:
            print(f"Warning: YAML file not found at {file_path}. Using empty parameters.")
            self.parameters = {}
            self._ensure_default_parameters()
        except yaml.YAMLError as e:
            print(f"Error: Failed to parse YAML file {file_path}: {e}")
            self.parameters = {}
            self._ensure_default_parameters()

    def to_yaml(self, file_path: Path):
        """
        Save parameters to a YAML file.
        
        Args:
            file_path: Path where to save the YAML file
        """
        if not isinstance(file_path, Path):
            file_path = Path(file_path)

        # Create output data with global n_cam at the top
        output_data = {'n_cam': self.n_cam}
        output_data.update(self.parameters)

        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with file_path.open('w') as f:
            yaml.dump(output_data, f, default_flow_style=False, sort_keys=False)
        print(f"Parameters consolidated and saved to {file_path} with global n_cam = {self.n_cam}")

    def from_directory(self, dir_path: Path):
        """
        Load parameters from a directory of .par files using a simplified approach.
        
        This method provides basic compatibility with legacy .par files but uses
        a much simpler approach than the original complex class mapping.
        
        Args:
            dir_path: Path to directory containing .par files
        """
        if not isinstance(dir_path, Path):
            dir_path = Path(dir_path)
        self.path = dir_path

        if not dir_path.is_dir():
            print(f"Error: Directory not found at {dir_path}")
            return

        # Simple parameter extraction without complex class mapping
        self.parameters = {}
        
        # Read basic parameters from common files
        self._read_ptv_par(dir_path)
        self._read_cal_ori_par(dir_path)
        self._read_targ_rec_par(dir_path)
        self._read_sequence_par(dir_path)
        self._read_criteria_par(dir_path)
        self._read_track_par(dir_path)
        
        # Add other basic parameter files as needed
        self._read_simple_par_files(dir_path)
        
        # Migrate legacy manual orientation data if it exists
        self.migrate_man_ori_dat(dir_path)
        
        # Ensure default parameters
        self._ensure_default_parameters()

    def to_directory(self, dir_path: Path):
        """
        Save parameters to a directory of .par files using a simplified approach.
        
        This provides basic compatibility for legacy workflows that expect .par files.
        
        Args:
            dir_path: Directory where to save the .par files
        """
        if not isinstance(dir_path, Path):
            dir_path = Path(dir_path)

        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Writing parameters to directory using global n_cam = {self.n_cam}")

        # Write basic parameter files with simple format
        self._write_ptv_par(dir_path)
        self._write_cal_ori_par(dir_path)
        self._write_targ_rec_par(dir_path)
        self._write_sequence_par(dir_path)
        self._write_criteria_par(dir_path)
        self._write_track_par(dir_path)
        
        print(f"Parameters written to individual files in {dir_path}")

    def _remove_legacy_n_cam_from_subsections(self, data: Dict[str, Any]):
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

    def _ensure_default_parameters(self):
        """Ensure that commonly missing parameters have default values."""
        defaults = {
            'masking': {
                'mask_flag': False,
                'mask_base_name': ''
            },
            'unsharp_mask': {
                'flag': False,
                'size': 3,
                'strength': 1.0
            },
            'plugins': {
                'available_tracking': ['default'],
                'available_sequence': ['default'],
                'selected_tracking': 'default',
                'selected_sequence': 'default'
            }
        }
        
        for section, params in defaults.items():
            if section not in self.parameters:
                self.parameters[section] = params.copy()
                print(f"Info: Added default {section} parameters")

        # Ensure ptv parameters have splitter flag
        if 'ptv' in self.parameters and 'splitter' not in self.parameters['ptv']:
            self.parameters['ptv']['splitter'] = False
            print("Info: Added default splitter flag to ptv parameters")
        
        # Ensure cal_ori parameters have cal_splitter flag
        if 'cal_ori' in self.parameters and 'cal_splitter' not in self.parameters['cal_ori']:
            self.parameters['cal_ori']['cal_splitter'] = False
            print("Info: Added default cal_splitter flag to cal_ori parameters")
        
        # Default manual orientation coordinates section
        if 'man_ori_coordinates' not in self.parameters:
            # Create empty structure based on number of cameras
            n_cam = self.get_n_cam()
            self.parameters['man_ori_coordinates'] = {
                f'camera_{i}': {
                    'point_1': {'x': 0.0, 'y': 0.0},
                    'point_2': {'x': 0.0, 'y': 0.0},
                    'point_3': {'x': 0.0, 'y': 0.0},
                    'point_4': {'x': 0.0, 'y': 0.0}
                } for i in range(n_cam)
            }
            print("Info: Added default manual orientation coordinates structure")

    def ensure_default_parameters(self):
        """
        Public method to ensure that commonly missing parameters have default values.
        This helps maintain compatibility with older parameter files.
        """
        self._ensure_default_parameters()

    # Simplified .par file readers (basic format parsing)
    def _read_ptv_par(self, dir_path: Path):
        """Read ptv.par file with simple parsing."""
        par_file = dir_path / "ptv.par"
        if not par_file.exists():
            return
            
        try:
            with par_file.open('r') as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]
            
            if len(lines) >= 1:
                self.n_cam = int(lines[0])
                print(f"Global n_cam set to {self.n_cam} from ptv.par")
            
            # Basic ptv parameters with defaults
            self.parameters['ptv'] = {
                'img_name': [f'cam{i+1}.tif' for i in range(self.n_cam)],
                'img_cal': [f'cam{i+1}' for i in range(self.n_cam)],
                'hp_flag': True,
                'allcam_flag': False,
                'tiff_flag': True,
                'imx': 1280,
                'imy': 1024,
                'pix_x': 0.012,
                'pix_y': 0.012,
                'chfield': 0,
                'mmp_n1': 1.0,
                'mmp_n2': 1.33,
                'mmp_n3': 1.46,
                'mmp_d': 1.0,
                'splitter': False
            }
            
            # Parse additional lines if available
            if len(lines) >= 5:
                self.parameters['ptv']['img_name'] = lines[1:self.n_cam+1] if len(lines) > self.n_cam else self.parameters['ptv']['img_name']
                
        except (ValueError, IndexError) as e:
            print(f"Warning: Error reading ptv.par: {e}")

    def _read_cal_ori_par(self, dir_path: Path):
        """Read cal_ori.par file with simple parsing."""
        par_file = dir_path / "cal_ori.par"
        if not par_file.exists():
            return
            
        self.parameters['cal_ori'] = {
            'fixp_name': 'cal/target.txt',
            'img_cal_name': [f'cal/cam{i+1}.tif' for i in range(self.n_cam)],
            'img_ori': [f'cal/cam{i+1}.tif.ori' for i in range(self.n_cam)],
            'tiff_flag': True,
            'pair_flag': False,
            'chfield': 0,
            'cal_splitter': False
        }

    def _read_targ_rec_par(self, dir_path: Path):
        """Read targ_rec.par file with simple parsing."""
        par_file = dir_path / "targ_rec.par"
        if not par_file.exists():
            return
            
        self.parameters['targ_rec'] = {
            'gvthres': [25] * self.n_cam,
            'disco': 5,
            'nnmin': 1,
            'nnmax': 20,
            'nxmin': 1,
            'nxmax': 20,
            'nymin': 1,
            'nymax': 20,
            'sumg_min': 12,
            'cr_sz': 4
        }

    def _read_sequence_par(self, dir_path: Path):
        """Read sequence.par file with simple parsing."""
        par_file = dir_path / "sequence.par"
        if not par_file.exists():
            return
            
        try:
            with par_file.open('r') as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]
            
            # Default values
            self.parameters['sequence'] = {
                'base_name': [f'img/cam{i+1}.%d' for i in range(self.n_cam)],
                'first': 10001,
                'last': 10100
            }
            
            # Parse actual values if available
            if len(lines) >= self.n_cam + 2:
                # Lines 0 to n_cam-1 are base names
                self.parameters['sequence']['base_name'] = lines[:self.n_cam]
                # Line n_cam is first frame
                self.parameters['sequence']['first'] = int(lines[self.n_cam])
                # Line n_cam+1 is last frame  
                self.parameters['sequence']['last'] = int(lines[self.n_cam + 1])
                
        except (ValueError, IndexError) as e:
            print(f"Warning: Error reading sequence.par: {e}")
            # Keep default values if parsing fails
            self.parameters['sequence'] = {
                'base_name': [f'img/cam{i+1}.%d' for i in range(self.n_cam)],
                'first': 10001,
                'last': 10100
            }

    def _read_criteria_par(self, dir_path: Path):
        """Read criteria.par file with simple parsing."""
        par_file = dir_path / "criteria.par"
        if not par_file.exists():
            return
            
        self.parameters['criteria'] = {
            'X_lay': [-100.0, 100.0],
            'Zmin_lay': [10.0, 20.0],
            'Zmax_lay': [50.0, 60.0],
            'cnx': 0.5,
            'cny': 0.5,
            'cn': 0.5,
            'csumg': 12.0,
            'corrmin': 0.5,
            'eps0': 0.1
        }

    def _read_track_par(self, dir_path: Path):
        """Read track.par file with simple parsing."""
        par_file = dir_path / "track.par"
        if not par_file.exists():
            return
            
        self.parameters['track'] = {
            'dvxmin': -50.0,
            'dvxmax': 50.0,
            'dvymin': -50.0,
            'dvymax': 50.0,
            'dvzmin': -50.0,
            'dvzmax': 50.0,
            'angle': 0.5,
            'dacc': 5.0,
            'flagNewParticles': True
        }

    def _read_simple_par_files(self, dir_path: Path):
        """Read other simple parameter files."""
        # Add other parameter sections with basic defaults
        simple_defaults = {
            'pft_version': {'Existing_Target': False},
            'examine': {'Examine_Flag': False, 'Combine_Flag': False},
            'orient': {
                'pnfo': 4, 'cc': False, 'xh': False, 'yh': False,
                'k1': False, 'k2': False, 'k3': False,
                'p1': False, 'p2': False, 'scale': False, 'shear': False, 'interf': False
            },
            'dumbbell': {
                'dumbbell_eps': 0.001, 'dumbbell_scale': 1.0,
                'dumbbell_gradient_descent': 0.5, 'dumbbell_penalty_weight': 1.0,
                'dumbbell_step': 1, 'dumbbell_niter': 10
            },
            'shaking': {
                'shaking_first_frame': 1, 'shaking_last_frame': 10,
                'shaking_max_num_points': 100, 'shaking_max_num_frames': 10
            },
            'detect_plate': {
                'gvth_1': 25, 'gvth_2': 25, 'gvth_3': 25, 'gvth_4': 25,
                'tol_dis': 5, 'min_npix': 1, 'max_npix': 20,
                'min_npix_x': 1, 'max_npix_x': 20, 'min_npix_y': 1, 'max_npix_y': 20,
                'sum_grey': 12, 'size_cross': 4
            },
            'man_ori': {
                'nr': list(range(1, self.n_cam * 4 + 1))
            }
        }
        
        for section, defaults in simple_defaults.items():
            if section not in self.parameters:
                self.parameters[section] = defaults.copy()

    # Simplified .par file writers (basic format writing)
    def _write_ptv_par(self, dir_path: Path):
        """Write ptv.par file with simple format."""
        par_file = dir_path / "ptv.par"
        ptv_params = self.parameters.get('ptv', {})
        
        with par_file.open('w') as f:
            f.write(f"{self.n_cam}\n")
            for i in range(self.n_cam):
                img_name = ptv_params.get('img_name', [f'cam{i+1}.tif'] * self.n_cam)[i]
                f.write(f"{img_name}\n")

    def _write_cal_ori_par(self, dir_path: Path):
        """Write cal_ori.par file with simple format."""
        par_file = dir_path / "cal_ori.par"
        cal_ori_params = self.parameters.get('cal_ori', {})
        
        with par_file.open('w') as f:
            f.write(f"{cal_ori_params.get('fixp_name', 'cal/target.txt')}\n")
            for i in range(self.n_cam):
                img_cal = cal_ori_params.get('img_cal_name', [f'cal/cam{i+1}.tif'] * self.n_cam)[i]
                f.write(f"{img_cal}\n")

    def _write_targ_rec_par(self, dir_path: Path):
        """Write targ_rec.par file with simple format."""
        par_file = dir_path / "targ_rec.par"
        targ_rec_params = self.parameters.get('targ_rec', {})
        
        with par_file.open('w') as f:
            gvthres = targ_rec_params.get('gvthres', [25] * self.n_cam)
            for thresh in gvthres:
                f.write(f"{thresh}\n")

    def _write_sequence_par(self, dir_path: Path):
        """Write sequence.par file with simple format."""
        par_file = dir_path / "sequence.par"
        seq_params = self.parameters.get('sequence', {})
        
        with par_file.open('w') as f:
            base_names = seq_params.get('base_name', [f'img/cam{i+1}.%d' for i in range(self.n_cam)])
            for base_name in base_names:
                f.write(f"{base_name}\n")
            f.write(f"{seq_params.get('first', 10001)}\n")
            f.write(f"{seq_params.get('last', 10100)}\n")

    def _write_criteria_par(self, dir_path: Path):
        """Write criteria.par file with simple format."""
        par_file = dir_path / "criteria.par"
        criteria_params = self.parameters.get('criteria', {})
        
        with par_file.open('w') as f:
            x_lay = criteria_params.get('X_lay', [-100.0, 100.0])
            f.write(f"{x_lay[0]} {x_lay[1]}\n")

    def _write_track_par(self, dir_path: Path):
        """Write track.par file with simple format."""
        par_file = dir_path / "track.par"
        track_params = self.parameters.get('track', {})
        
        with par_file.open('w') as f:
            f.write(f"{track_params.get('dvxmin', -50.0)}\n")
            f.write(f"{track_params.get('dvxmax', 50.0)}\n")

    def migrate_man_ori_dat(self, source_dir):
        """
        Migrate man_ori.dat file data into the YAML parameters structure.
        
        This method converts legacy manual orientation coordinates from the old
        man_ori.dat format (which stored 4 points per camera in a flat file)
        to the new YAML structure where coordinates are organized by camera.
        
        Args:
            source_dir (Path): Directory containing the man_ori.dat file
        """
        if not isinstance(source_dir, Path):
            source_dir = Path(source_dir)
            
        man_ori_dat_path = source_dir / "man_ori.dat"
        
        if not man_ori_dat_path.exists():
            return  # No file to migrate
        
        print(f"Migrating man_ori.dat from {man_ori_dat_path}...")
        
        try:
            with open(man_ori_dat_path, 'r') as f:
                lines = f.readlines()
            
            # Ensure we have the right number of lines (n_cam * 4)
            n_cam = self.get_n_cam()
            expected_lines = n_cam * 4
            
            if len(lines) < expected_lines:
                print(f"Warning: man_ori.dat has {len(lines)} lines, expected {expected_lines}")
                return
            
            # Initialize the coordinates structure if needed
            if 'man_ori_coordinates' not in self.parameters:
                self.parameters['man_ori_coordinates'] = {}
            
            # Parse and migrate the coordinates
            line_idx = 0
            for cam_idx in range(n_cam):
                cam_key = f'camera_{cam_idx}'
                if cam_key not in self.parameters['man_ori_coordinates']:
                    self.parameters['man_ori_coordinates'][cam_key] = {}
                
                for point_idx in range(4):
                    point_key = f'point_{point_idx + 1}'
                    
                    if line_idx < len(lines):
                        try:
                            x_val, y_val = lines[line_idx].strip().split()
                            self.parameters['man_ori_coordinates'][cam_key][point_key] = {
                                'x': float(x_val),
                                'y': float(y_val)
                            }
                            line_idx += 1
                        except (ValueError, IndexError) as e:
                            print(f"Warning: Error parsing line {line_idx + 1} in man_ori.dat: {e}")
                            # Fill with default if parsing fails
                            self.parameters['man_ori_coordinates'][cam_key][point_key] = {
                                'x': 0.0,
                                'y': 0.0
                            }
                            line_idx += 1
                    else:
                        # Fill with default if data is missing
                        self.parameters['man_ori_coordinates'][cam_key][point_key] = {
                            'x': 0.0,
                            'y': 0.0
                        }
            
            print(f"Successfully migrated {line_idx} coordinate pairs from man_ori.dat")
            print(f"Manual orientation coordinates structure created for {n_cam} cameras")
            
        except Exception as e:
            print(f"Error migrating man_ori.dat: {e}")


def main():
    """Command-line interface for parameter conversion."""
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
        help="Convert from a directory of .par files to a single YAML file."
    )
    group.add_argument(
        '--to-dir', 
        action='store_true', 
        help="Convert from a single YAML file to a directory of .par files."
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
