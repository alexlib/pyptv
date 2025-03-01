"""Core PTV functionality integration for the modern UI.

This module serves as a bridge between the modern UI and the existing PTV code.
It reuses the existing functionality while adapting it to the new interface.
"""

import os
import sys
import time
import importlib
from pathlib import Path
import numpy as np
from skimage.io import imread
from skimage.util import img_as_ubyte
from skimage.color import rgb2gray

# NumPy is configured once at import time
np.set_printoptions(precision=4, suppress=True)

# Import existing PTV code
from pyptv import ptv
import optv.orientation
import optv.epipolar

# Import YAML parameter system
from pyptv.yaml_parameters import (
    ParameterManager,
    PtvParams,
    TrackingParams,
    SequenceParams,
    CriteriaParams
)


class PTVCore:
    """Core class to handle PTV functionality in the modern UI.
    
    This class acts as a facade to the existing PTV code, adapting it to
    the new interface and adding functionality where needed.
    """
    
    def __init__(self, exp_path=None, software_path=None):
        """Initialize the PTV core.
        
        Args:
            exp_path: Path to the experiment directory
            software_path: Path to the software directory
        """
        # Set paths
        self.exp_path = Path(exp_path) if exp_path else Path.cwd()
        self.software_path = Path(software_path) if software_path else Path.cwd()
        
        print(f"Using direct PTVCore implementation with experiment path: {self.exp_path}")
        # Initialize parameter manager
        params_dir = self.exp_path / "parameters"
        self.param_manager = ParameterManager(params_dir)
        self.yaml_params = None
        
        # Initialize plugin system
        self.plugins = {}
        self._load_plugins()
        
        # Initialize parameters and images
        self.initialized = False
        self.n_cams = 0
        self.orig_images = []
        self.cpar = None
        self.vpar = None
        self.spar = None
        self.epar = None
        self.track_par = None
        self.tpar = None
        self.cals = None
        
        # Initialize detection and correspondence results
        self.detections = None
        self.corrected = None
        self.sorted_pos = None
        self.sorted_corresp = None
        self.num_targs = None
    
    def _load_plugins(self):
        """Load the available plugins."""
        # Load sequence plugins
        sequence_plugins = Path(os.path.abspath(os.curdir)) / "sequence_plugins.txt"
        if sequence_plugins.exists():
            with open(sequence_plugins, "r", encoding="utf8") as f:
                plugins = f.read().strip().split("\n")
                self.plugins["sequence"] = ["default"] + plugins
        else:
            self.plugins["sequence"] = ["default"]
        
        # Load tracking plugins
        tracking_plugins = Path(os.path.abspath(os.curdir)) / "tracking_plugins.txt"
        if tracking_plugins.exists():
            with open(tracking_plugins, "r", encoding="utf8") as f:
                plugins = f.read().strip().split("\n")
                self.plugins["tracking"] = ["default"] + plugins
        else:
            self.plugins["tracking"] = ["default"]
    
    def initialize(self):
        """Initialize the PTV system using YAML parameters.
        """
        # Change to experiment directory
        if self.exp_path.exists():
            os.chdir(self.exp_path)
        
        print(f"PTVCore: initializing from {os.getcwd()}")
        
        # Load parameters from YAML
        try:
            self.load_yaml_parameters()
            print("Using YAML parameters")
            
            # Get number of cameras from YAML params
            self.n_cams = self.yaml_params.get("PtvParams").n_img
            
            # Get image dimensions
            imx = self.yaml_params.get("PtvParams").imx
            imy = self.yaml_params.get("PtvParams").imy
            
            # Get reference images from sequence params
            seq_params = self.yaml_params.get("SequenceParams")
            ref_images = []
            
            # Safely get image paths for each camera
            for i in range(1, self.n_cams + 1):
                image_attr = f"Name_{i}_Image"
                if hasattr(seq_params, image_attr):
                    img_path = getattr(seq_params, image_attr)
                    ref_images.append(img_path)
                else:
                    # Log the missing attribute
                    print(f"Missing {image_attr} in sequence parameters")
                    ref_images.append(None)
            
            # Initialize images array
            self.orig_images = [None] * self.n_cams
            
            # Load initial images
            for i in range(self.n_cams):
                try:
                    if i < len(ref_images) and ref_images[i]:
                        img_path = ref_images[i]
                        if not os.path.exists(img_path):
                            raise FileNotFoundError(f"Image file {img_path} not found")
                            
                        img = imread(img_path)
                        if img.ndim > 2:
                            img = rgb2gray(img)
                        self.orig_images[i] = img_as_ubyte(img)
                    else:
                        print(f"Warning: Reference image for camera {i+1} not found, using blank image")
                        self.orig_images[i] = np.zeros((imy, imx), dtype=np.uint8)
                except Exception as e:
                    print(f"Error loading image {i+1}: {e}")
                    self.orig_images[i] = np.zeros((imy, imx), dtype=np.uint8)
            
            # Initialize PTV parameters through the existing code, now using YAML
            try:
                print(f"Creating parameters from YAML parameters for {self.n_cams} cameras")
                (
                    self.cpar,
                    self.spar,
                    self.vpar,
                    self.track_par,
                    self.tpar,
                    self.cals,
                    self.epar,
                ) = ptv.py_start_proc_c(self.n_cams, exp_path=self.exp_path)
                print("Successfully created parameter objects from YAML parameters")
            except Exception as init_error:
                print(f"Error initializing core PTV: {init_error}")
                # Check if experiment attribute exists before creating
                if not hasattr(self, 'experiment'):
                    from pyptv import Experiment
                    self.experiment = Experiment(self.n_cams)
                    self.experiment.initialize(self.exp_path, self.software_path)
                raise init_error
            
            # Mark as initialized
            self.initialized = True
            
            return self.orig_images
            
        except Exception as e:
            print(f"Failed to initialize: {e}")
            self.initialized = False
            return []
        
    def load_yaml_parameters(self):
        """Load parameters from unified YAML file."""
        # Create parameter manager with unified YAML enabled
        params_dir = self.exp_path / "parameters"
        self.param_manager = ParameterManager(params_dir, unified=True)
        
        # Load all parameter types
        self.yaml_params = self.param_manager.load_all()
        
        # Validate required parameters
        required_param_types = ["PtvParams", "TrackingParams", "SequenceParams", "CriteriaParams", "TargetParams"]
        for param_type in required_param_types:
            if param_type not in self.yaml_params:
                print(f"Warning: Required parameter type {param_type} not found in unified file")
                print(f"Attempting to load from individual file...")
                
                # Try to find the parameter class
                for cls_name, cls in self.param_manager.parameters.items():
                    if cls_name == param_type:
                        # Load the parameter and add it to yaml_params
                        self.yaml_params[param_type] = cls.load(params_dir)
                        break
                
                # Check if we found the parameter
                if param_type not in self.yaml_params:
                    raise ValueError(f"Required parameter type {param_type} not found")
        
        # Save all parameters to the unified YAML file
        # This ensures any parameters loaded from individual files are merged into the unified file
        self.param_manager.save_all(self.yaml_params)
        
        return self.yaml_params
        
    def update_yaml_parameter(self, param_type, updated_param):
        """
        Update a specific parameter in the unified YAML file.
        
        Args:
            param_type: Parameter type name (e.g., "PtvParams")
            updated_param: Updated parameter object
        """
        if self.param_manager and hasattr(self.param_manager, 'update_param'):
            # Get the parameter class
            for cls_name, cls in self.param_manager.parameters.items():
                if cls_name == param_type:
                    # Update the parameter in the unified YAML file
                    self.param_manager.update_param(cls, updated_param)
                    
                    # Update in memory as well
                    self.yaml_params[param_type] = updated_param
                    break
    
    def apply_highpass(self):
        """Apply highpass filter to the images."""
        if not self.initialized:
            raise ValueError("PTV system not initialized")
        
        # Check if we're using YAML parameters
        if self.yaml_params:
            seq_params = self.yaml_params.get("SequenceParams")
            inverse = seq_params.Inverse
            subtr_mask = seq_params.Subtr_Mask
            base_name_mask = seq_params.Base_Name_Mask
        else:
            # Use legacy parameters
            inverse = self.experiment.active_params.m_params.Inverse
            subtr_mask = self.experiment.active_params.m_params.Subtr_Mask
            base_name_mask = self.experiment.active_params.m_params.Base_Name_Mask
        
        # Apply inverse if needed
        if inverse:
            for i, im in enumerate(self.orig_images):
                self.orig_images[i] = 255 - im
        
        # Apply mask subtraction if needed
        if subtr_mask:
            try:
                for i, im in enumerate(self.orig_images):
                    background_name = base_name_mask.replace("#", str(i))
                    background = imread(background_name)
                    self.orig_images[i] = np.clip(
                        self.orig_images[i] - background, 0, 255
                    ).astype(np.uint8)
            except Exception as e:
                raise ValueError(f"Failed subtracting mask: {e}")
        
        # Apply highpass filter - check if highpass is enabled
        if self.yaml_params and self.yaml_params.get("PtvParams").hp_flag:
            self.orig_images = ptv.py_pre_processing_c(
                self.orig_images, self.cpar
            )
        elif not self.yaml_params and self.experiment.active_params.m_params.Hp_flag:
            self.orig_images = ptv.py_pre_processing_c(
                self.orig_images, self.cpar
            )
        
        return self.orig_images
    
    def detect_particles(self):
        """Detect particles in the images."""
        if not self.initialized:
            raise ValueError("PTV system not initialized")
        
        # Run detection
        (
            self.detections,
            self.corrected,
        ) = ptv.py_detection_proc_c(
            self.orig_images,
            self.cpar,
            self.tpar,
            self.cals,
        )
        
        # Extract detection coordinates
        x = [[i.pos()[0] for i in row] for row in self.detections]
        y = [[i.pos()[1] for i in row] for row in self.detections]
        
        return x, y
    
    def find_correspondences(self):
        """Find correspondences between particles in different cameras."""
        if not self.initialized:
            raise ValueError("PTV system not initialized")
        
        # Run correspondence
        (
            self.sorted_pos,
            self.sorted_corresp,
            self.num_targs,
        ) = ptv.py_correspondences_proc_c(self)
        
        # Process results based on number of cameras
        results = []
        
        if len(self.sorted_pos) > 0:
            # Organize by correspondence type (pair, triplet, quad)
            names = ["pair", "tripl", "quad"]
            colors = ["yellow", "green", "red"]
            
            for i, subset in enumerate(reversed(self.sorted_pos)):
                # Clean up the correspondences (remove invalid points)
                x_coords = []
                y_coords = []
                
                for cam_points in subset:
                    # Get valid points for this camera
                    valid_points = cam_points[(cam_points != -999).any(axis=1)]
                    x_coords.append(valid_points[:, 0] if len(valid_points) > 0 else [])
                    y_coords.append(valid_points[:, 1] if len(valid_points) > 0 else [])
                
                results.append({
                    "type": names[i],
                    "color": colors[i],
                    "x": x_coords,
                    "y": y_coords
                })
        
        return results
    
    def determine_3d_positions(self):
        """Determine 3D positions from correspondences."""
        if not self.initialized or self.sorted_pos is None:
            raise ValueError("Correspondences not found")
        
        # Run determination
        ptv.py_determination_proc_c(
            self.n_cams,
            self.sorted_pos,
            self.sorted_corresp,
            self.corrected,
        )
        
        return True
    
    def run_sequence(self, start_frame=None, end_frame=None):
        """Run sequence processing on a range of frames.
        
        Args:
            start_frame: First frame to process (or None for default)
            end_frame: Last frame to process (or None for default)
            
        Returns:
            Boolean indicating success
        """
        if not self.initialized:
            raise ValueError("PTV system not initialized")
        
        # Get frame range from YAML if available
        if self.yaml_params:
            seq_params = self.yaml_params.get("SequenceParams")
            if start_frame is None:
                start_frame = seq_params.Seq_First
            if end_frame is None:
                end_frame = seq_params.Seq_Last
                
            # Update sequence parameters in memory
            self.spar.first = seq_params.Seq_First
            self.spar.last = seq_params.Seq_Last
            
            # Update the processing volume parameters
            criteria_params = self.yaml_params.get("CriteriaParams")
            self.vpar.X_lay[0] = criteria_params.X_lay
            self.vpar.Zmin_lay[0] = criteria_params.Zmin_lay
            self.vpar.Zmax_lay[0] = criteria_params.Zmax_lay
            self.vpar.Ymin_lay[0] = criteria_params.Ymin_lay
            self.vpar.Ymax_lay[0] = criteria_params.Ymax_lay
            self.vpar.Xmin_lay[0] = criteria_params.Xmin_lay
            self.vpar.Xmax_lay[0] = criteria_params.Xmax_lay
            
        else:
            # Use legacy parameters
            if start_frame is None:
                start_frame = self.experiment.active_params.m_params.Seq_First
            if end_frame is None:
                end_frame = self.experiment.active_params.m_params.Seq_Last
        
        # Check if a plugin is selected
        sequence_alg = self.plugins.get("sequence_alg", "default")
        
        if sequence_alg != "default":
            # Run external plugin
            ptv.run_plugin(self)
        else:
            # Run default sequence
            ptv.py_sequence_loop(self)
        
        return True
    
    def track_particles(self, backward=False):
        """Track particles across frames.
        
        Args:
            backward: Whether to track backward in time
            
        Returns:
            Boolean indicating success
        """
        if not self.initialized:
            raise ValueError("PTV system not initialized")
        
        # Set up tracking parameters from YAML if available
        if self.yaml_params:
            track_params = self.yaml_params.get("TrackingParams")
            
            if track_params:
                # Update tracking parameters in memory
                try:
                    self.track_par.dvxmin = track_params.dvxmin
                    self.track_par.dvxmax = track_params.dvxmax
                    self.track_par.dvymin = track_params.dvymin
                    self.track_par.dvymax = track_params.dvymax
                    self.track_par.dvzmin = track_params.dvzmin
                    self.track_par.dvzmax = track_params.dvzmax
                    self.track_par.angle = track_params.angle
                    self.track_par.dacc = track_params.dacc
                    self.track_par.add_particle = 1 if track_params.flagNewParticles else 0
                except Exception as e:
                    print(f"Error updating tracking parameters: {e}")
        
        # Check if a plugin is selected
        track_alg = self.plugins.get("track_alg", "default")
        
        try:
            if track_alg != "default":
                # Run external plugin
                try:
                    # Handle both legacy and modern code paths
                    if hasattr(self, 'experiment') and hasattr(self.experiment, 'software_path'):
                        os.chdir(self.experiment.software_path)
                    else:
                        os.chdir(self.software_path)
                        
                    track = importlib.import_module(track_alg)
                except Exception as e:
                    print(f"Error loading {track_alg}: {e}. Falling back to default tracker")
                    track_alg = "default"
                
                # Change back to working path
                if hasattr(self, 'experiment') and hasattr(self.experiment, 'exp_path'):
                    os.chdir(self.experiment.exp_path)
                else:
                    os.chdir(self.exp_path)
            
            if track_alg == "default":
                # Run default tracker
                if not hasattr(self, "tracker"):
                    self.tracker = ptv.py_trackcorr_init(self)
                
                if backward:
                    self.tracker.full_backward()
                else:
                    self.tracker.full_forward()
            else:
                # Run plugin tracker
                if hasattr(self, 'experiment'):
                    tracker = track.Tracking(ptv=ptv, exp1=self.experiment)
                else:
                    # Modern version passes self instead of experiment
                    tracker = track.Tracking(ptv=ptv, exp1=self)
                    
                if backward:
                    tracker.do_back_tracking()
                else:
                    tracker.do_tracking()
            
            return True
            
        except Exception as e:
            print(f"Error in tracking: {e}")
            return False
    
    def get_trajectories(self, start_frame=None, end_frame=None):
        """Get trajectories for visualization.
        
        Args:
            start_frame: First frame to include (or None for default)
            end_frame: Last frame to include (or None for default)
            
        Returns:
            List of camera projections of trajectories
        """
        if not self.initialized:
            raise ValueError("PTV system not initialized")
        
        # Get frame range from YAML if available
        if self.yaml_params:
            seq_params = self.yaml_params.get("SequenceParams")
            if start_frame is None:
                start_frame = seq_params.Seq_First
            if end_frame is None:
                end_frame = seq_params.Seq_Last
        else:
            # Use legacy parameters
            if start_frame is None:
                start_frame = self.experiment.active_params.m_params.Seq_First
            if end_frame is None:
                end_frame = self.experiment.active_params.m_params.Seq_Last
        
        # Use flowtracks to load trajectories
        try:
            from flowtracks.io import trajectories_ptvis
            
            dataset = trajectories_ptvis(
                "res/ptv_is.%d", 
                first=start_frame, 
                last=end_frame, 
                xuap=False,
                traj_min_len=3
            )
            
            # Project 3D trajectories to each camera view
            cam_projections = []
            
            for i_cam in range(self.n_cams):
                heads_x, heads_y = [], []
                tails_x, tails_y = [], []
                ends_x, ends_y = [], []
                
                for traj in dataset:
                    # Project 3D positions to camera coordinates
                    projected = optv.imgcoord.image_coordinates(
                        np.atleast_2d(traj.pos() * 1000),  # Convert to mm
                        self.cals[i_cam],
                        self.cpar.get_multimedia_params(),
                    )
                    
                    # Convert to pixel coordinates
                    pos = optv.transforms.convert_arr_metric_to_pixel(
                        projected, self.cpar
                    )
                    
                    if len(pos) > 0:
                        # Store trajectory points
                        heads_x.append(pos[0, 0])  # First point
                        heads_y.append(pos[0, 1])
                        
                        if len(pos) > 2:
                            # Middle points
                            tails_x.extend(list(pos[1:-1, 0]))
                            tails_y.extend(list(pos[1:-1, 1]))
                        
                        if len(pos) > 1:
                            # Last point
                            ends_x.append(pos[-1, 0])
                            ends_y.append(pos[-1, 1])
                
                cam_projections.append({
                    "heads": {"x": heads_x, "y": heads_y, "color": "red"},
                    "tails": {"x": tails_x, "y": tails_y, "color": "green"},
                    "ends": {"x": ends_x, "y": ends_y, "color": "orange"}
                })
            
            return cam_projections
            
        except Exception as e:
            print(f"Error loading trajectories: {e}")
            return None
    
    def export_to_paraview(self, start_frame=None, end_frame=None):
        """Export trajectories to Paraview format."""
        if not self.initialized:
            raise ValueError("PTV system not initialized")
        
        # Get frame range
        if start_frame is None:
            start_frame = self.experiment.active_params.m_params.Seq_First
        if end_frame is None:
            end_frame = self.experiment.active_params.m_params.Seq_Last
        
        try:
            import pandas as pd
            from flowtracks.io import trajectories_ptvis
            
            # Load trajectories
            dataset = trajectories_ptvis("res/ptv_is.%d", xuap=False)
            
            # Convert to dataframes
            dataframes = []
            for traj in dataset:
                dataframes.append(
                    pd.DataFrame.from_records(
                        traj, 
                        columns=["x", "y", "z", "dx", "dy", "dz", "frame", "particle"]
                    )
                )
            
            if not dataframes:
                return False
                
            # Combine dataframes
            df = pd.concat(dataframes, ignore_index=True)
            df["particle"] = df["particle"].astype(np.int32)
            df["frame"] = df["frame"].astype(np.int32)
            
            # Export by frame
            df_grouped = df.reset_index().groupby("frame")
            for index, group in df_grouped:
                output_path = Path("./res") / f"ptv_{int(index):05d}.txt"
                group.to_csv(
                    output_path,
                    mode="w",
                    columns=["particle", "x", "y", "z", "dx", "dy", "dz"],
                    index=False,
                )
            
            return True
            
        except Exception as e:
            print(f"Error exporting to Paraview: {e}")
            return False
    
    def calculate_epipolar_line(self, camera_id, x, y):
        """Calculate epipolar lines corresponding to a point in a camera.
        
        Args:
            camera_id: ID of the camera where the point is selected
            x: X coordinate of the point
            y: Y coordinate of the point
        
        Returns:
            Dictionary mapping camera IDs to epipolar curve coordinates
        """
        if not self.initialized:
            raise ValueError("PTV system not initialized")
        
        epipolar_lines = {}
        num_points = 100  # Number of points to generate for each epipolar curve
        
        point = np.array([x, y], dtype="float64")
        
        # Generate epipolar lines for each other camera
        for cam_id in range(self.n_cams):
            if cam_id == camera_id:
                continue
                
            try:
                # Calculate epipolar curve
                pts = optv.epipolar.epipolar_curve(
                    point,
                    self.cals[camera_id],
                    self.cals[cam_id],
                    num_points,
                    self.cpar,
                    self.vpar,
                )
                
                if len(pts) > 1:
                    epipolar_lines[cam_id] = pts
            except Exception as e:
                print(f"Error calculating epipolar line for camera {cam_id}: {e}")
        
        return epipolar_lines
    
    def load_sequence_image(self, frame_num, camera_id=None):
        """Load an image from a sequence.
        
        Args:
            frame_num: Frame number to load
            camera_id: Optional camera ID to load for (if None, loads all cameras)
            
        Returns:
            List of loaded images or a single image if camera_id is specified
        """
        if not self.initialized:
            raise ValueError("PTV system not initialized")
        
        # Get base names for sequence images
        if self.yaml_params:
            # Use YAML parameters
            seq_params = self.yaml_params.get("SequenceParams")
            base_names = []
            for i in range(self.n_cams):
                basename_attr = f"Name_{i+1}_Seq"
                if hasattr(seq_params, basename_attr):
                    base_names.append(getattr(seq_params, basename_attr))
                else:
                    base_names.append(None)
        else:
            # Use legacy parameters
            base_names = [
                getattr(self.experiment.active_params.m_params, f"Basename_{i+1}_Seq")
                for i in range(self.n_cams)
            ]
        
        if camera_id is not None:
            # Load image for a specific camera
            if 0 <= camera_id < self.n_cams:
                try:
                    if base_names[camera_id]:
                        img_path = base_names[camera_id] % frame_num
                        img = imread(img_path)
                        if img.ndim > 2:
                            img = rgb2gray(img)
                        return img_as_ubyte(img)
                    else:
                        raise ValueError(f"Base name for camera {camera_id} is not set")
                except Exception as e:
                    print(f"Error loading image {camera_id} for frame {frame_num}: {e}")
                    # Return empty image with the correct dimensions
                    if self.yaml_params:
                        h_img = self.yaml_params.get("PtvParams").imx
                        v_img = self.yaml_params.get("PtvParams").imy
                    else:
                        h_img = self.experiment.active_params.m_params.imx
                        v_img = self.experiment.active_params.m_params.imy
                    return np.zeros((v_img, h_img), dtype=np.uint8)
            else:
                raise ValueError(f"Invalid camera ID: {camera_id}")
        else:
            # Load images for all cameras
            images = []
            for i, base_name in enumerate(base_names):
                try:
                    if base_name:
                        img_path = base_name % frame_num
                        img = imread(img_path)
                        if img.ndim > 2:
                            img = rgb2gray(img)
                        images.append(img_as_ubyte(img))
                    else:
                        raise ValueError(f"Base name for camera {i} is not set")
                except Exception as e:
                    print(f"Error loading image {i} for frame {frame_num}: {e}")
                    # Add empty image with the correct dimensions
                    if self.yaml_params:
                        h_img = self.yaml_params.get("PtvParams").imx
                        v_img = self.yaml_params.get("PtvParams").imy
                    else:
                        h_img = self.experiment.active_params.m_params.imx
                        v_img = self.experiment.active_params.m_params.imy
                    images.append(np.zeros((v_img, h_img), dtype=np.uint8))
            
            return images