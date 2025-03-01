"""Modern parameter handling for PyPTV using YAML.

This module provides a new parameter handling system based on YAML files
rather than the legacy ASCII parameter files. It maintains compatibility
with the old system while providing a more flexible and maintainable approach.

This module now supports a unified YAML file approach, where all parameters
are stored in a single multi-level YAML file rather than multiple separate files.
"""

import os
from pathlib import Path
import yaml
from typing import Dict, List, Any, Optional, Union, TypeVar, Generic, Type
import json
from dataclasses import dataclass, field, asdict, is_dataclass

# Default locations and filenames
DEFAULT_PARAMS_DIR = "parameters"
UNIFIED_YAML_FILENAME = "pyptv_config.yaml"

# Type variable for generic parameter classes
T = TypeVar('T')


def ensure_path(path: Union[str, Path]) -> Path:
    """Convert string to Path object if needed."""
    if isinstance(path, str):
        return Path(path)
    return path


@dataclass
class ParameterBase:
    """Base class for all parameter dataclasses."""
    
    path: Path = field(default_factory=lambda: Path(DEFAULT_PARAMS_DIR))
    
    def __post_init__(self):
        """Ensure path is a Path object after initialization."""
        self.path = ensure_path(self.path)
    
    @property
    def filename(self) -> str:
        """Return the parameter filename (must be implemented by subclasses)."""
        raise NotImplementedError("Subclasses must implement filename property")
    
    @property
    def legacy_filename(self) -> str:
        """Return the legacy parameter filename (defaults to yaml filename with .par)."""
        return self.filename.replace('.yaml', '.par')
    
    @property
    def filepath(self) -> Path:
        """Return the full path to the parameter file."""
        return self.path.joinpath(self.filename)
    
    @property
    def legacy_filepath(self) -> Path:
        """Return the full path to the legacy parameter file."""
        return self.path.joinpath(self.legacy_filename)
    
    def save(self) -> None:
        """Save parameters to YAML file."""
        # Create directory if it doesn't exist
        self.path.mkdir(parents=True, exist_ok=True)
        
        # Convert dataclass to dict, excluding path and private fields
        data = {k: v for k, v in asdict(self).items() 
                if not k.startswith('_') and k != 'path'}
        
        # Write to YAML
        with open(self.filepath, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)
    
    @classmethod
    def load(cls: Type[T], path: Union[str, Path] = DEFAULT_PARAMS_DIR) -> T:
        """Load parameters from YAML file.
        
        Args:
            path: Path to the parameters directory
            
        Returns:
            Initialized parameter object
        """
        path = ensure_path(path)
        # Create temporary instance to get filename
        temp_instance = cls(path=path)
        filepath = path.joinpath(temp_instance.filename)
        
        # Create instance with default values
        instance = cls(path=path)
        
        # If YAML exists, load it
        if filepath.exists():
            with open(filepath, 'r') as f:
                data = yaml.safe_load(f)
                
            # Update instance with loaded data
            for key, value in data.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
        # Otherwise try to load legacy format if available
        elif instance.legacy_filepath.exists():
            instance.load_legacy()
            # Save in new format
            instance.save()
        
        return instance
    
    def load_legacy(self) -> None:
        """Load parameters from legacy format (.par files).
        
        This method should be implemented by subclasses to handle
        the specific format of each parameter file.
        """
        raise NotImplementedError("Subclasses must implement load_legacy method")
    
    def save_legacy(self) -> None:
        """Save parameters to legacy format (.par files).
        
        This method should be implemented by subclasses to handle
        the specific format of each parameter file.
        """
        raise NotImplementedError("Subclasses must implement save_legacy method")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert parameters to dictionary, excluding private attributes."""
        return {k: v for k, v in asdict(self).items() 
                if not k.startswith('_') and k != 'path'}


@dataclass
class PtvParams(ParameterBase):
    """Main PTV parameters (ptv.par/ptv.yaml)."""
    
    n_img: int = 4  # Number of cameras
    img_name: List[str] = field(default_factory=lambda: [""] * 4)  # Image names
    img_cal: List[str] = field(default_factory=lambda: [""] * 4)  # Calibration image names
    hp_flag: bool = True  # Highpass filtering flag
    allcam_flag: bool = False  # Use only particles in all cameras
    tiff_flag: bool = True  # TIFF header flag
    imx: int = 1280  # Image width in pixels
    imy: int = 1024  # Image height in pixels
    pix_x: float = 0.012  # Pixel size horizontal [mm]
    pix_y: float = 0.012  # Pixel size vertical [mm]
    chfield: int = 0  # Field flag (0=frame, 1=odd, 2=even)
    mmp_n1: float = 1.0  # Refractive index air
    mmp_n2: float = 1.33  # Refractive index water
    mmp_n3: float = 1.46  # Refractive index glass
    mmp_d: float = 6.0  # Thickness of glass [mm]
    
    @property
    def filename(self) -> str:
        return "ptv.yaml"
    
    def load_legacy(self) -> None:
        """Load from legacy ptv.par format."""
        try:
            with open(self.legacy_filepath, "r") as f:
                lines = [line.strip() for line in f.readlines()]
                
                idx = 0
                self.n_img = int(lines[idx])
                idx += 1
                
                self.img_name = [""] * max(4, self.n_img)
                self.img_cal = [""] * max(4, self.n_img)
                
                for i in range(self.n_img):
                    self.img_name[i] = lines[idx]
                    idx += 1
                    self.img_cal[i] = lines[idx]
                    idx += 1
                
                self.hp_flag = int(lines[idx]) != 0
                idx += 1
                self.allcam_flag = int(lines[idx]) != 0
                idx += 1
                self.tiff_flag = int(lines[idx]) != 0
                idx += 1
                self.imx = int(lines[idx])
                idx += 1
                self.imy = int(lines[idx])
                idx += 1
                self.pix_x = float(lines[idx])
                idx += 1
                self.pix_y = float(lines[idx])
                idx += 1
                self.chfield = int(lines[idx])
                idx += 1
                self.mmp_n1 = float(lines[idx])
                idx += 1
                self.mmp_n2 = float(lines[idx])
                idx += 1
                self.mmp_n3 = float(lines[idx])
                idx += 1
                self.mmp_d = float(lines[idx])
                
        except Exception as e:
            print(f"Error loading legacy PTV parameters: {e}")
    
    def save_legacy(self) -> None:
        """Save to legacy ptv.par format."""
        try:
            with open(self.legacy_filepath, "w") as f:
                f.write(f"{self.n_img}\n")
                
                for i in range(self.n_img):
                    f.write(f"{self.img_name[i]}\n")
                    f.write(f"{self.img_cal[i]}\n")
                
                f.write(f"{int(self.hp_flag)}\n")
                f.write(f"{int(self.allcam_flag)}\n")
                f.write(f"{int(self.tiff_flag)}\n")
                f.write(f"{self.imx}\n")
                f.write(f"{self.imy}\n")
                f.write(f"{self.pix_x}\n")
                f.write(f"{self.pix_y}\n")
                f.write(f"{self.chfield}\n")
                f.write(f"{self.mmp_n1}\n")
                f.write(f"{self.mmp_n2}\n")
                f.write(f"{self.mmp_n3}\n")
                f.write(f"{self.mmp_d}\n")
                
        except Exception as e:
            print(f"Error saving legacy PTV parameters: {e}")


@dataclass
class TrackingParams(ParameterBase):
    """Tracking parameters (track.par/track.yaml)."""
    
    dvxmin: float = -10.0  # Min velocity in x
    dvxmax: float = 10.0   # Max velocity in x
    dvymin: float = -10.0  # Min velocity in y
    dvymax: float = 10.0   # Max velocity in y
    dvzmin: float = -10.0  # Min velocity in z
    dvzmax: float = 10.0   # Max velocity in z
    angle: float = 0.0     # Angle for search cone
    dacc: float = 0.9      # Acceleration limit
    flagNewParticles: bool = True  # Flag for adding new particles
    
    @property
    def filename(self) -> str:
        return "track.yaml"
    
    def load_legacy(self) -> None:
        """Load from legacy track.par format."""
        try:
            with open(self.legacy_filepath, "r") as f:
                lines = [line.strip() for line in f.readlines()]
                
                idx = 0
                self.dvxmin = float(lines[idx])
                idx += 1
                self.dvxmax = float(lines[idx])
                idx += 1
                self.dvymin = float(lines[idx])
                idx += 1
                self.dvymax = float(lines[idx])
                idx += 1
                self.dvzmin = float(lines[idx])
                idx += 1
                self.dvzmax = float(lines[idx])
                idx += 1
                self.angle = float(lines[idx])
                idx += 1
                self.dacc = float(lines[idx])
                idx += 1
                self.flagNewParticles = int(lines[idx]) != 0
                
        except Exception as e:
            print(f"Error loading legacy tracking parameters: {e}")
    
    def save_legacy(self) -> None:
        """Save to legacy track.par format."""
        try:
            with open(self.legacy_filepath, "w") as f:
                f.write(f"{self.dvxmin}\n")
                f.write(f"{self.dvxmax}\n")
                f.write(f"{self.dvymin}\n")
                f.write(f"{self.dvymax}\n")
                f.write(f"{self.dvzmin}\n")
                f.write(f"{self.dvzmax}\n")
                f.write(f"{self.angle}\n")
                f.write(f"{self.dacc}\n")
                f.write(f"{int(self.flagNewParticles)}\n")
                
        except Exception as e:
            print(f"Error saving legacy tracking parameters: {e}")


@dataclass
class SequenceParams(ParameterBase):
    """Sequence parameters (sequence.par/sequence.yaml)."""
    
    first: int = 10001  # First frame in sequence
    last: int = 10004   # Last frame in sequence
    n_img: int = 4      # Number of cameras
    base_name: List[str] = field(default_factory=lambda: ["img/cam1.", "img/cam2.", "img/cam3.", "img/cam4."])  # Base names for sequence
    Zmin_lay: float = -10.0  # Min Z coordinate
    Zmax_lay: float = 10.0   # Max Z coordinate
    Ymin_lay: float = -10.0  # Min Y coordinate
    Ymax_lay: float = 10.0   # Max Y coordinate
    Xmin_lay: float = -10.0  # Min X coordinate
    Xmax_lay: float = 10.0   # Max X coordinate
    Cam_1_Reference: str = "img/cam1.10002"  # Background image for cam 1 (optional)
    Cam_2_Reference: str = "img/cam2.10002"  # Background image for cam 2 (optional)
    Cam_3_Reference: str = "img/cam3.10002"  # Background image for cam 3 (optional)
    Cam_4_Reference: str = "img/cam4.10002"  # Background image for cam 4 (optional)
    Inverse: bool = False    # Invert images
    Subtr_Mask: bool = False  # Subtract mask/background
    Base_Name_Mask: str = ""  # Base name for mask files
    
    @property
    def filename(self) -> str:
        return "sequence.yaml"
    
    def load_legacy(self) -> None:
        """Load from legacy sequence.par format."""
        try:
            with open(self.legacy_filepath, "r") as f:
                lines = [line.strip() for line in f.readlines()]
                
                idx = 0
                self.Seq_First = int(lines[idx])
                idx += 1
                self.Seq_Last = int(lines[idx])
                idx += 1
                
                # Basenames for sequences
                self.Basename_1_Seq = lines[idx]
                idx += 1
                self.Basename_2_Seq = lines[idx]
                idx += 1
                self.Basename_3_Seq = lines[idx]
                idx += 1
                self.Basename_4_Seq = lines[idx]
                idx += 1
                
                # Reference images
                self.Name_1_Image = lines[idx]
                idx += 1
                self.Name_2_Image = lines[idx]
                idx += 1
                self.Name_3_Image = lines[idx]
                idx += 1
                self.Name_4_Image = lines[idx]
                idx += 1
                
                # Volume coordinates
                self.Zmin_lay = float(lines[idx])
                idx += 1
                self.Zmax_lay = float(lines[idx])
                idx += 1
                self.Ymin_lay = float(lines[idx])
                idx += 1
                self.Ymax_lay = float(lines[idx])
                idx += 1
                self.Xmin_lay = float(lines[idx])
                idx += 1
                self.Xmax_lay = float(lines[idx])
                idx += 1
                
                # Optional parameters
                if idx < len(lines):
                    self.Cam_1_Reference = lines[idx]
                    idx += 1
                if idx < len(lines):
                    self.Cam_2_Reference = lines[idx]
                    idx += 1
                if idx < len(lines):
                    self.Cam_3_Reference = lines[idx]
                    idx += 1
                if idx < len(lines):
                    self.Cam_4_Reference = lines[idx]
                    idx += 1
                if idx < len(lines):
                    self.Inverse = int(lines[idx]) != 0
                    idx += 1
                if idx < len(lines):
                    self.Subtr_Mask = int(lines[idx]) != 0
                    idx += 1
                if idx < len(lines):
                    self.Base_Name_Mask = lines[idx]
                
        except Exception as e:
            print(f"Error loading legacy sequence parameters: {e}")
    
    def save_legacy(self) -> None:
        """Save to legacy sequence.par format."""
        try:
            with open(self.legacy_filepath, "w") as f:
                f.write(f"{self.Seq_First}\n")
                f.write(f"{self.Seq_Last}\n")
                
                f.write(f"{self.Basename_1_Seq}\n")
                f.write(f"{self.Basename_2_Seq}\n")
                f.write(f"{self.Basename_3_Seq}\n")
                f.write(f"{self.Basename_4_Seq}\n")
                
                f.write(f"{self.Name_1_Image}\n")
                f.write(f"{self.Name_2_Image}\n")
                f.write(f"{self.Name_3_Image}\n")
                f.write(f"{self.Name_4_Image}\n")
                
                f.write(f"{self.Zmin_lay}\n")
                f.write(f"{self.Zmax_lay}\n")
                f.write(f"{self.Ymin_lay}\n")
                f.write(f"{self.Ymax_lay}\n")
                f.write(f"{self.Xmin_lay}\n")
                f.write(f"{self.Xmax_lay}\n")
                
                # Optional parameters
                f.write(f"{self.Cam_1_Reference}\n")
                f.write(f"{self.Cam_2_Reference}\n")
                f.write(f"{self.Cam_3_Reference}\n")
                f.write(f"{self.Cam_4_Reference}\n")
                f.write(f"{int(self.Inverse)}\n")
                f.write(f"{int(self.Subtr_Mask)}\n")
                f.write(f"{self.Base_Name_Mask}\n")
                
        except Exception as e:
            print(f"Error saving legacy sequence parameters: {e}")


@dataclass
class CriteriaParams(ParameterBase):
    """Correspondence criteria parameters (criteria.par/criteria.yaml)."""
    
    X_lay: float = 0.0      # X center of illuminated volume
    Zmin_lay: float = -10.0  # Min Z coordinate
    Zmax_lay: float = 10.0   # Max Z coordinate
    Ymin_lay: float = -10.0  # Min Y coordinate
    Ymax_lay: float = 10.0   # Max Y coordinate
    Xmin_lay: float = -10.0  # Min X coordinate
    Xmax_lay: float = 10.0   # Max X coordinate
    cn: float = 0.0          # Convergence limit
    cnx: float = 0.0         # Convergence limit in x
    cny: float = 0.0         # Convergence limit in y 
    csumg: float = 0.0       # Convergence limit sum of gray values
    corrmin: float = 0.0     # Minimum correlation coefficient
    eps0: float = 0.1        # Convergence criteria slope
    
    @property
    def filename(self) -> str:
        return "criteria.yaml"
    
    def load_legacy(self) -> None:
        """Load from legacy criteria.par format."""
        try:
            with open(self.legacy_filepath, "r") as f:
                lines = [line.strip() for line in f.readlines()]
                
                idx = 0
                self.X_lay = float(lines[idx])
                idx += 1
                self.Zmin_lay = float(lines[idx])
                idx += 1
                self.Zmax_lay = float(lines[idx])
                idx += 1
                self.Ymin_lay = float(lines[idx])
                idx += 1
                self.Ymax_lay = float(lines[idx])
                idx += 1
                self.Xmin_lay = float(lines[idx])
                idx += 1
                self.Xmax_lay = float(lines[idx])
                idx += 1
                self.cn = float(lines[idx])
                idx += 1
                
                if idx < len(lines):
                    self.eps0 = float(lines[idx])
                
        except Exception as e:
            print(f"Error loading legacy criteria parameters: {e}")
    
    def save_legacy(self) -> None:
        """Save to legacy criteria.par format."""
        try:
            with open(self.legacy_filepath, "w") as f:
                f.write(f"{self.X_lay}\n")
                f.write(f"{self.Zmin_lay}\n")
                f.write(f"{self.Zmax_lay}\n")
                f.write(f"{self.Ymin_lay}\n")
                f.write(f"{self.Ymax_lay}\n")
                f.write(f"{self.Xmin_lay}\n")
                f.write(f"{self.Xmax_lay}\n")
                f.write(f"{self.cn}\n")
                f.write(f"{self.eps0}\n")
                
        except Exception as e:
            print(f"Error saving legacy criteria parameters: {e}")


@dataclass
class TargetParams(ParameterBase):
    """Target recognition parameters (targ_rec.par/targ_rec.yaml)."""
    
    n_img: int = 4          # Number of cameras
    gvth_1: int = 10        # Gray value threshold for camera 1
    gvth_2: int = 10        # Gray value threshold for camera 2
    gvth_3: int = 10        # Gray value threshold for camera 3
    gvth_4: int = 10        # Gray value threshold for camera 4
    discont: int = 100      # Allowed discontinuity
    nnmin: int = 4          # Minimum number of pixels
    nnmax: int = 500        # Maximum number of pixels
    nxmin: int = 2          # Minimum size in x
    nxmax: int = 100        # Maximum size in x
    nymin: int = 2          # Minimum size in y
    nymax: int = 100        # Maximum size in y
    sumg_min: int = 150     # Minimum sum of gray values
    cr_sz: int = 2          # Cross size
    
    @property
    def filename(self) -> str:
        return "targ_rec.yaml"
    
    def load_legacy(self) -> None:
        """Load from legacy targ_rec.par format."""
        try:
            with open(self.legacy_filepath, "r") as f:
                lines = [line.strip() for line in f.readlines()]
                
                idx = 0
                self.n_img = int(lines[idx])
                idx += 1
                
                # Gray value thresholds for each camera
                for i in range(self.n_img):
                    setattr(self, f"gvth_{i+1}", int(lines[idx]))
                    idx += 1
                
                self.discont = int(lines[idx])
                idx += 1
                self.nnmin = int(lines[idx])
                idx += 1
                self.nnmax = int(lines[idx])
                idx += 1
                self.nxmin = int(lines[idx])
                idx += 1
                self.nxmax = int(lines[idx])
                idx += 1
                self.nymin = int(lines[idx])
                idx += 1
                self.nymax = int(lines[idx])
                idx += 1
                self.sumg_min = int(lines[idx])
                idx += 1
                self.cr_sz = int(lines[idx])
                
        except Exception as e:
            print(f"Error loading legacy target parameters: {e}")
    
    def save_legacy(self) -> None:
        """Save to legacy targ_rec.par format."""
        try:
            with open(self.legacy_filepath, "w") as f:
                f.write(f"{self.n_img}\n")
                
                # Gray value thresholds for each camera
                for i in range(self.n_img):
                    f.write(f"{getattr(self, f'gvth_{i+1}')}\n")
                
                f.write(f"{self.discont}\n")
                f.write(f"{self.nnmin}\n")
                f.write(f"{self.nnmax}\n")
                f.write(f"{self.nxmin}\n")
                f.write(f"{self.nxmax}\n")
                f.write(f"{self.nymin}\n")
                f.write(f"{self.nymax}\n")
                f.write(f"{self.sumg_min}\n")
                f.write(f"{self.cr_sz}\n")
                
        except Exception as e:
            print(f"Error saving legacy target parameters: {e}")


class ParameterManager:
    """Manager for all parameter types.
    
    Supports both:
    1. Individual YAML files for each parameter type (legacy)
    2. Unified YAML file with all parameters in a single file (modern)
    """
    
    def __init__(self, path: Union[str, Path] = DEFAULT_PARAMS_DIR, unified: bool = True):
        """Initialize parameter manager.
        
        Args:
            path: Path to parameter directory
            unified: Whether to use unified YAML file (True) or separate files (False)
        """
        self.path = ensure_path(path)
        self.parameters = {}
        self.unified = unified
        
        # Register parameter classes
        self._register_parameter_class(PtvParams)
        self._register_parameter_class(TrackingParams)
        self._register_parameter_class(SequenceParams)
        self._register_parameter_class(CriteriaParams)
        self._register_parameter_class(TargetParams)
    
    def _register_parameter_class(self, param_class: Type[ParameterBase]) -> None:
        """Register a parameter class.
        
        Args:
            param_class: Parameter class to register
        """
        self.parameters[param_class.__name__] = param_class
    
    def get_unified_yaml_path(self) -> Path:
        """Get the path to the unified YAML file.
        
        Returns:
            Path to unified YAML file
        """
        return self.path / UNIFIED_YAML_FILENAME
    
    def load_all(self) -> Dict[str, ParameterBase]:
        """Load all parameters.
        
        If unified is True, loads from a single YAML file.
        Otherwise, loads from individual YAML files.
        
        Returns:
            Dictionary of parameter objects
        """
        loaded_params = {}
        
        if self.unified:
            # Load from unified YAML file
            try:
                unified_path = self.get_unified_yaml_path()
                if unified_path.exists():
                    # Load unified YAML file
                    with open(unified_path, 'r') as f:
                        yaml_data = yaml.safe_load(f)
                    
                    # Create parameter objects from unified data
                    for name, param_class in self.parameters.items():
                        if name in yaml_data:
                            # Create parameter object with path
                            param = param_class(path=self.path)
                            
                            # Update parameter from YAML data
                            param_data = yaml_data[name]
                            for key, value in param_data.items():
                                if hasattr(param, key):
                                    setattr(param, key, value)
                            
                            loaded_params[name] = param
                        else:
                            # Fallback to individual file if section missing
                            loaded_params[name] = param_class.load(self.path)
                    
                    return loaded_params
            except Exception as e:
                print(f"Error loading unified YAML file: {e}")
                print("Falling back to individual files")
        
        # Fallback to individual files method
        for name, param_class in self.parameters.items():
            loaded_params[name] = param_class.load(self.path)
        
        return loaded_params
    
    def save_all(self, params: Dict[str, ParameterBase]) -> None:
        """Save all parameters.
        
        If unified is True, saves to a single YAML file.
        Otherwise, saves to individual YAML files.
        
        Args:
            params: Dictionary of parameter objects
        """
        if self.unified:
            # Save to unified YAML file
            unified_data = {}
            
            # Create data dictionary
            for name, param in params.items():
                # Convert parameter to dictionary
                param_dict = {}
                for key, value in asdict(param).items():
                    # Skip the path field
                    if key != 'path':
                        param_dict[key] = value
                
                unified_data[name] = param_dict
            
            # Ensure directory exists
            self.path.mkdir(parents=True, exist_ok=True)
            
            # Write to unified YAML file
            with open(self.get_unified_yaml_path(), 'w') as f:
                yaml.dump(unified_data, f, default_flow_style=False, sort_keys=False)
        else:
            # Save to individual files
            for param in params.values():
                param.save()
    
    def save_all_legacy(self, params: Dict[str, ParameterBase]) -> None:
        """Save all parameters in legacy format.
        
        Always saves to individual legacy (.par) files regardless of the unified setting.
        
        Args:
            params: Dictionary of parameter objects
        """
        for param in params.values():
            param.save_legacy()
    
    def load_param(self, param_class: Type[T]) -> T:
        """Load a specific parameter class.
        
        If unified is True, loads from the unified YAML file.
        Otherwise, loads from individual YAML file.
        
        Args:
            param_class: Parameter class to load
            
        Returns:
            Parameter object
        """
        if self.unified:
            # Try to load from unified YAML file
            try:
                unified_path = self.get_unified_yaml_path()
                if unified_path.exists():
                    # Load unified YAML file
                    with open(unified_path, 'r') as f:
                        yaml_data = yaml.safe_load(f)
                    
                    # Get parameter class name
                    class_name = param_class.__name__
                    
                    if class_name in yaml_data:
                        # Create parameter object with path
                        param = param_class(path=self.path)
                        
                        # Update parameter from YAML data
                        param_data = yaml_data[class_name]
                        for key, value in param_data.items():
                            if hasattr(param, key):
                                setattr(param, key, value)
                        
                        return param
            except Exception as e:
                print(f"Error loading parameter from unified YAML: {e}")
                print("Falling back to individual file")
        
        # Fallback to individual file
        return param_class.load(self.path)
    
    def update_param(self, param_class: Type[T], param: T) -> None:
        """Update a specific parameter in the unified YAML file.
        
        If unified is True, updates just that section in the unified YAML file.
        Otherwise, saves to individual YAML file.
        
        Args:
            param_class: Parameter class
            param: Parameter object with updated values
        """
        if self.unified:
            # Update in unified YAML file
            try:
                unified_path = self.get_unified_yaml_path()
                yaml_data = {}
                
                # Load existing data if file exists
                if unified_path.exists():
                    with open(unified_path, 'r') as f:
                        yaml_data = yaml.safe_load(f) or {}
                
                # Get parameter class name
                class_name = param_class.__name__
                
                # Convert parameter to dictionary
                param_dict = {}
                for key, value in asdict(param).items():
                    # Skip the path field
                    if key != 'path':
                        param_dict[key] = value
                
                # Update parameter section
                yaml_data[class_name] = param_dict
                
                # Ensure directory exists
                self.path.mkdir(parents=True, exist_ok=True)
                
                # Write back to unified YAML file
                with open(unified_path, 'w') as f:
                    yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)
                    
            except Exception as e:
                print(f"Error updating parameter in unified YAML: {e}")
                print("Falling back to individual file")
                param.save()
        else:
            # Save to individual file
            param.save()