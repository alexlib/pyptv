"""Modern parameter handling for PyPTV using YAML.

This module provides a new parameter handling system based on YAML files
rather than the legacy ASCII parameter files. It maintains compatibility
with the old system while providing a more flexible and maintainable approach.
"""

import os
from pathlib import Path
import yaml
from typing import Dict, List, Any, Optional, Union, TypeVar, Generic, Type
import json
from dataclasses import dataclass, field, asdict, is_dataclass

# Default locations
DEFAULT_PARAMS_DIR = "parameters"

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
    
    Seq_First: int = 10000  # First frame in sequence
    Seq_Last: int = 10004   # Last frame in sequence
    Basename_1_Seq: str = "img/cam1."  # Base name for cam 1
    Basename_2_Seq: str = "img/cam2."  # Base name for cam 2
    Basename_3_Seq: str = "img/cam3."  # Base name for cam 3
    Basename_4_Seq: str = "img/cam4."  # Base name for cam 4
    Name_1_Image: str = "img/cam1.10002"  # Reference image for cam 1
    Name_2_Image: str = "img/cam2.10002"  # Reference image for cam 2
    Name_3_Image: str = "img/cam3.10002"  # Reference image for cam 3
    Name_4_Image: str = "img/cam4.10002"  # Reference image for cam 4
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


class ParameterManager:
    """Manager for all parameter types."""
    
    def __init__(self, path: Union[str, Path] = DEFAULT_PARAMS_DIR):
        """Initialize parameter manager.
        
        Args:
            path: Path to parameter directory
        """
        self.path = ensure_path(path)
        self.parameters = {}
        
        # Register parameter classes
        self._register_parameter_class(PtvParams)
        self._register_parameter_class(TrackingParams)
        self._register_parameter_class(SequenceParams)
        self._register_parameter_class(CriteriaParams)
    
    def _register_parameter_class(self, param_class: Type[ParameterBase]) -> None:
        """Register a parameter class.
        
        Args:
            param_class: Parameter class to register
        """
        self.parameters[param_class.__name__] = param_class
    
    def load_all(self) -> Dict[str, ParameterBase]:
        """Load all parameters.
        
        Returns:
            Dictionary of parameter objects
        """
        loaded_params = {}
        
        for name, param_class in self.parameters.items():
            loaded_params[name] = param_class.load(self.path)
        
        return loaded_params
    
    def save_all(self, params: Dict[str, ParameterBase]) -> None:
        """Save all parameters.
        
        Args:
            params: Dictionary of parameter objects
        """
        for param in params.values():
            param.save()
    
    def save_all_legacy(self, params: Dict[str, ParameterBase]) -> None:
        """Save all parameters in legacy format.
        
        Args:
            params: Dictionary of parameter objects
        """
        for param in params.values():
            param.save_legacy()
    
    def load_param(self, param_class: Type[T]) -> T:
        """Load a specific parameter class.
        
        Args:
            param_class: Parameter class to load
            
        Returns:
            Parameter object
        """
        return param_class.load(self.path)