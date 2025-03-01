"""
Bridge module that connects the new PySide6 UI to the existing core functionality.
This allows gradual migration to PySide6/Matplotlib.
"""

import os
import sys
import importlib
from pathlib import Path
import numpy as np

# NumPy is configured once at import time
np.set_printoptions(precision=4, suppress=True)

# Import modules
import optv
from pyptv.yaml_parameters import ParameterManager

class PTVCoreBridge:
    """
    A bridge class that interfaces between the new UI and the existing PTVCore functionality.
    This serves as a transition layer to integrate modern UI with existing functionality.
    """
    
    def __init__(self, exp_path, software_path=None):
        """
        Initialize the bridge to core functionality.
        
        Args:
            exp_path: Path to experiment directory
            software_path: Path to software directory (optional)
        """
        self.exp_path = Path(exp_path)
        self.software_path = Path(software_path) if software_path else None
        
        # YAML parameters with unified YAML enabled
        self.param_manager = ParameterManager(self.exp_path / "parameters", unified=True)
        self.yaml_params = None
        
        # Number of cameras and initialization state
        self.n_cams = 0
        self.initialized = False
        
        # Plugins
        self.plugins = {}
        self.active_plugins = {}
        self._load_plugins()
        
    def _load_plugins(self):
        """Load available sequence and tracking plugins."""
        # Sequence plugins
        try:
            sequence_plugins_file = self.exp_path / "sequence_plugins.txt"
            if sequence_plugins_file.exists():
                with open(sequence_plugins_file, "r") as f:
                    sequence_plugins = [line.strip() for line in f if line.strip()]
                    
                for plugin_name in sequence_plugins:
                    try:
                        module_path = f"pyptv.plugins.{plugin_name}"
                        module = importlib.import_module(module_path)
                        self.plugins[plugin_name] = module
                    except ImportError:
                        print(f"Could not import sequence plugin: {plugin_name}")
        except Exception as e:
            print(f"Error loading sequence plugins: {e}")
            
        # Tracking plugins
        try:
            tracking_plugins_file = self.exp_path / "tracking_plugins.txt"
            if tracking_plugins_file.exists():
                with open(tracking_plugins_file, "r") as f:
                    tracking_plugins = [line.strip() for line in f if line.strip()]
                    
                for plugin_name in tracking_plugins:
                    try:
                        module_path = f"pyptv.plugins.{plugin_name}"
                        module = importlib.import_module(module_path)
                        self.plugins[plugin_name] = module
                    except ImportError:
                        print(f"Could not import tracking plugin: {plugin_name}")
        except Exception as e:
            print(f"Error loading tracking plugins: {e}")
            
    def initialize(self):
        """
        Initialize the PTV system using YAML parameters.
        
        Returns:
            List of initial images (numpy arrays)
        """
        # Load parameters using YAML system
        try:
            self.yaml_params = self.param_manager.load_all()
            print("Loaded YAML parameters")
            
            # Get number of cameras from YAML params
            ptv_params = self.yaml_params.get("PtvParams")
            if ptv_params:
                self.n_cams = ptv_params.n_img
            else:
                raise ValueError("Could not find PTV parameters in YAML.")
            
            # Create parameter objects using the parameter builder
            try:
                import optv
                from pyptv import ptv
                print(f"Creating parameter objects from YAML for {self.n_cams} cameras")
                (
                    self.cpar,
                    self.spar,
                    self.vpar,
                    self.track_par,
                    self.tpar,
                    self.cals,
                    self.epar,
                ) = ptv.py_start_proc_c(self.n_cams, exp_path=self.exp_path)
                print("Successfully created parameter objects")
            except Exception as param_error:
                print(f"Warning: Could not create parameter objects: {param_error}")
                print("Continuing with basic bridge functionality")
                
            # Initialize the PTV system
            print(f"Initializing with {self.n_cams} cameras")
            self.initialized = True
            
            # Load initial images
            images = self._load_images()
            return images
            
        except Exception as e:
            print(f"Error initializing: {e}")
            self.initialized = False
            return []
        
    def _load_images(self):
        """
        Load initial images from cal/cam*.tif
        
        Returns:
            List of numpy arrays containing calibration images
        """
        images = []
        for i in range(1, self.n_cams + 1):
            image_path = self.exp_path / "cal" / f"cam{i}.tif"
            
            if not image_path.exists():
                # Try alternative path
                image_path = self.exp_path / "cal" / f"camera{i}.tif"
                
            if image_path.exists():
                try:
                    from skimage import io
                    img = io.imread(str(image_path))
                    if len(img.shape) > 2:  # Color image
                        img = img.mean(axis=2).astype(np.uint8)  # Convert to grayscale
                    images.append(img)
                except Exception as e:
                    print(f"Error loading image {image_path}: {e}")
                    # Add a dummy image
                    images.append(np.ones((480, 640), dtype=np.uint8) * 128)
            else:
                # Add a dummy image
                images.append(np.ones((480, 640), dtype=np.uint8) * 128)
                
        return images
        
    def apply_highpass(self):
        """
        Apply highpass filter to images.
        
        Returns:
            List of filtered images
        """
        if not self.initialized:
            raise RuntimeError("PTV system not initialized.")
            
        # Get images
        images = self._load_images()
        
        # Apply filter
        filtered_images = []
        for img in images:
            # Simple highpass filter using Gaussian blur difference
            from scipy.ndimage import gaussian_filter
            blurred = gaussian_filter(img, sigma=5)
            filtered = img - blurred
            filtered = np.clip(filtered + 128, 0, 255).astype(np.uint8)
            filtered_images.append(filtered)
            
        return filtered_images
        
    def detect_particles(self):
        """
        Detect particles in images.
        
        Returns:
            Tuple of (x_coords, y_coords) where each is a list of arrays of coordinates
        """
        if not self.initialized:
            raise RuntimeError("PTV system not initialized.")
            
        # Get parameters
        if self.yaml_params:
            detection_params = self.yaml_params.get("DetectionParams")
            threshold = detection_params.threshold if detection_params else 0.5
        else:
            if hasattr(self.experiment.active_params, 'detection_params'):
                threshold = self.experiment.active_params.detection_params.threshold
            else:
                threshold = 0.5
        
        # Get images
        images = self._load_images()
        
        # Simple particle detection (thresholding + connected components)
        from skimage import measure
        
        x_coords = []
        y_coords = []
        
        for img in images:
            # Normalize image
            img_norm = img.astype(float) / 255.0
            
            # Apply threshold
            binary = img_norm > threshold
            
            # Find connected components
            labels = measure.label(binary)
            regions = measure.regionprops(labels)
            
            # Extract centroids
            x = []
            y = []
            
            for region in regions:
                y_coord, x_coord = region.centroid
                x.append(x_coord)
                y.append(y_coord)
                
            x_coords.append(np.array(x))
            y_coords.append(np.array(y))
            
        return x_coords, y_coords
        
    def find_correspondences(self):
        """
        Find correspondences between camera views.
        
        Returns:
            List of correspondence results
        """
        if not self.initialized:
            raise RuntimeError("PTV system not initialized.")
            
        # Get particle coordinates
        x_coords, y_coords = self.detect_particles()
        
        # For demonstration, just return some random correspondences
        import random
        
        # Generate some random correspondences
        # In a real implementation, this would use epipolar geometry
        
        # Create quads (points visible in all cameras)
        num_quads = min(len(coord) for coord in x_coords) // 3
        quad_result = {
            "x": [],
            "y": [],
            "color": "red"
        }
        
        for i in range(self.n_cams):
            indices = random.sample(range(len(x_coords[i])), num_quads)
            quad_result["x"].append(x_coords[i][indices])
            quad_result["y"].append(y_coords[i][indices])
            
        # Create triplets (points visible in 3 cameras)
        num_triplets = min(len(coord) for coord in x_coords) // 4
        triplet_result = {
            "x": [],
            "y": [],
            "color": "green"
        }
        
        for i in range(self.n_cams):
            indices = random.sample(range(len(x_coords[i])), num_triplets)
            triplet_result["x"].append(x_coords[i][indices])
            triplet_result["y"].append(y_coords[i][indices])
            
        # Create pairs (points visible in 2 cameras)
        num_pairs = min(len(coord) for coord in x_coords) // 5
        pair_result = {
            "x": [],
            "y": [],
            "color": "blue"
        }
        
        for i in range(self.n_cams):
            indices = random.sample(range(len(x_coords[i])), num_pairs)
            pair_result["x"].append(x_coords[i][indices])
            pair_result["y"].append(y_coords[i][indices])
            
        return [quad_result, triplet_result, pair_result]
        
    def track_particles(self):
        """
        Track particles through a sequence.
        
        Returns:
            True if tracking was successful
        """
        if not self.initialized:
            raise RuntimeError("PTV system not initialized.")
            
        # In a real implementation, this would call the tracking algorithm
        # For now, just simulate the tracking process
        
        print("Tracking particles...")
        time.sleep(1)  # Simulate tracking time
        
        return True
        
    def get_trajectories(self):
        """
        Get trajectory data for display in camera views.
        
        Returns:
            List of trajectory data for each camera
        """
        if not self.initialized:
            raise RuntimeError("PTV system not initialized.")
            
        # For demonstration, generate some random trajectories
        import random
        
        trajectory_data = []
        
        for i in range(self.n_cams):
            # Generate random trajectory data
            num_trajectories = 20
            
            # Heads (start points)
            heads_x = [random.uniform(100, 500) for _ in range(num_trajectories)]
            heads_y = [random.uniform(100, 400) for _ in range(num_trajectories)]
            
            # Tails (middle points)
            tails_x = []
            tails_y = []
            
            for j in range(num_trajectories):
                # Add some points along a path
                num_points = random.randint(3, 10)
                for k in range(num_points):
                    tails_x.append(heads_x[j] + random.uniform(-20, 20) * k/num_points)
                    tails_y.append(heads_y[j] + random.uniform(-15, 15) * k/num_points)
            
            # Ends (final points)
            ends_x = [heads_x[j] + random.uniform(-40, 40) for j in range(num_trajectories)]
            ends_y = [heads_y[j] + random.uniform(-30, 30) for j in range(num_trajectories)]
            
            camera_data = {
                "heads": {
                    "x": heads_x,
                    "y": heads_y,
                    "color": "green"
                },
                "tails": {
                    "x": tails_x,
                    "y": tails_y,
                    "color": "blue"
                },
                "ends": {
                    "x": ends_x,
                    "y": ends_y,
                    "color": "red"
                }
            }
            
            trajectory_data.append(camera_data)
            
        return trajectory_data
        
    def get_3d_trajectories(self):
        """
        Get 3D trajectory data.
        
        Returns:
            List of 3D trajectories, where each trajectory is a list of points (x, y, z, frame)
        """
        if not self.initialized:
            raise RuntimeError("PTV system not initialized.")
            
        # For demonstration, generate some random 3D trajectories
        import random
        
        trajectories = []
        
        # Generate some random trajectories
        num_trajectories = 30
        
        for i in range(num_trajectories):
            # Random starting position
            start_x = random.uniform(-50, 50)
            start_y = random.uniform(-50, 50)
            start_z = random.uniform(-50, 50)
            
            # Random velocity
            vel_x = random.uniform(-5, 5)
            vel_y = random.uniform(-5, 5)
            vel_z = random.uniform(-5, 5)
            
            # Random acceleration
            acc_x = random.uniform(-0.2, 0.2)
            acc_y = random.uniform(-0.2, 0.2)
            acc_z = random.uniform(-0.2, 0.2)
            
            # Create trajectory
            traj_length = random.randint(5, 30)
            trajectory = []
            
            for frame in range(traj_length):
                # Position with acceleration
                x = start_x + vel_x * frame + 0.5 * acc_x * frame * frame
                y = start_y + vel_y * frame + 0.5 * acc_y * frame * frame
                z = start_z + vel_z * frame + 0.5 * acc_z * frame * frame
                
                trajectory.append((x, y, z, frame))
                
            trajectories.append(trajectory)
            
        return trajectories
        
    def get_camera_positions(self):
        """
        Get camera positions for 3D visualization.
        
        Returns:
            List of camera positions (x, y, z)
        """
        if not self.initialized:
            raise RuntimeError("PTV system not initialized.")
            
        # In a real implementation, this would read from calibration data
        # For now, return some reasonable camera positions
        
        camera_positions = []
        
        # Place cameras at corners of a cube
        radius = 150
        
        if self.n_cams >= 1:
            camera_positions.append((radius, radius, radius))
        if self.n_cams >= 2:
            camera_positions.append((-radius, radius, radius))
        if self.n_cams >= 3:
            camera_positions.append((radius, -radius, radius))
        if self.n_cams >= 4:
            camera_positions.append((-radius, -radius, radius))
            
        return camera_positions