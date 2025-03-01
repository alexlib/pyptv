"""Main window implementation for the modernized PyPTV UI."""

import os
import sys
from pathlib import Path

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from pyptv import __version__
from pyptv.ui.camera_view import CameraView
from pyptv.ui.parameter_sidebar import ParameterSidebar


class MainWindow(QMainWindow):
    """Main window for the PyPTV application using PySide6."""

    def __init__(self, exp_path=None, software_path=None):
        """Initialize the main window.

        Args:
            exp_path (Path, optional): Path to experiment data. Defaults to None.
            software_path (Path, optional): Path to software directory. Defaults to None.
        """
        super().__init__()
        
        # Store paths
        self.exp_path = Path(exp_path) if exp_path else Path.cwd()
        self.software_path = Path(software_path) if software_path else Path(__file__).parent.parent.parent
        
        print(f"Experiment path: {self.exp_path}")
        print(f"Software path: {self.software_path}")
        
        # Set window properties
        self.setWindowTitle(f"PyPTV {__version__}")
        self.resize(1200, 800)
        
        # Create the central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create the main splitter for sidebar and camera views
        self.main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self.main_splitter)
        
        # Add parameter sidebar
        self.parameter_sidebar = ParameterSidebar()
        self.main_splitter.addWidget(self.parameter_sidebar)
        
        # Add camera views container
        self.camera_container = QWidget()
        self.camera_layout = QVBoxLayout(self.camera_container)
        self.main_splitter.addWidget(self.camera_container)
        
        # Set initial splitter sizes (30% sidebar, 70% cameras)
        self.main_splitter.setSizes([300, 700])
        
        # Create menus and toolbar
        self.create_menus()
        self.create_toolbar()
        
        # Initialize camera views (placeholder)
        self.camera_views = []
        
        # Show a welcome message if no experiment path is provided
        if not exp_path:
            QMessageBox.information(
                self, 
                "Welcome to PyPTV", 
                "Please open an experiment directory to begin."
            )

    def create_menus(self):
        """Create the application menus."""
        # File menu
        file_menu = self.menuBar().addMenu("&File")
        
        open_action = QAction("&Open Experiment...", self)
        open_action.triggered.connect(self.open_experiment)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Workflow menu
        workflow_menu = self.menuBar().addMenu("&Workflow")
        
        init_action = QAction("&Initialize", self)
        init_action.triggered.connect(self.initialize_experiment)
        workflow_menu.addAction(init_action)
        
        workflow_menu.addSeparator()
        
        calib_action = QAction("&Calibration...", self)
        calib_action.triggered.connect(self.open_calibration)
        workflow_menu.addAction(calib_action)
        
        detection_action = QAction("&Detection...", self)
        detection_action.triggered.connect(self.open_detection)
        workflow_menu.addAction(detection_action)
        
        tracking_action = QAction("&Tracking...", self)
        tracking_action.triggered.connect(self.open_tracking)
        workflow_menu.addAction(tracking_action)
        
        # Parameters menu
        params_menu = self.menuBar().addMenu("&Parameters")
        
        edit_params_action = QAction("&Edit Parameters...", self)
        edit_params_action.triggered.connect(self.edit_parameters)
        params_menu.addAction(edit_params_action)
        
        # Plugins menu
        plugins_menu = self.menuBar().addMenu("&Plugins")
        
        config_plugins_action = QAction("&Configure Plugins...", self)
        config_plugins_action.triggered.connect(self.configure_plugins)
        plugins_menu.addAction(config_plugins_action)
        
        # Visualization menu
        visualization_menu = self.menuBar().addMenu("&Visualization")
        
        trajectories_action = QAction("&3D Trajectories...", self)
        trajectories_action.triggered.connect(self.open_3d_visualization)
        visualization_menu.addAction(trajectories_action)
        
        # Help menu
        help_menu = self.menuBar().addMenu("&Help")
        
        about_action = QAction("&About PyPTV", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_toolbar(self):
        """Create the main toolbar."""
        self.toolbar = QToolBar("Main Toolbar")
        self.addToolBar(self.toolbar)
        
        # Initialize action
        init_action = QAction("Initialize", self)
        init_action.triggered.connect(self.initialize_experiment)
        self.toolbar.addAction(init_action)
        
        self.toolbar.addSeparator()
        
        # Processing actions
        highpass_action = QAction("Highpass Filter", self)
        highpass_action.triggered.connect(self.apply_highpass)
        self.toolbar.addAction(highpass_action)
        
        detection_action = QAction("Detect Particles", self)
        detection_action.triggered.connect(self.detect_particles)
        self.toolbar.addAction(detection_action)
        
        correspondence_action = QAction("Find Correspondences", self)
        correspondence_action.triggered.connect(self.find_correspondences)
        self.toolbar.addAction(correspondence_action)
        
        self.toolbar.addSeparator()
        
        # Tracking actions
        tracking_action = QAction("Track Sequence", self)
        tracking_action.triggered.connect(self.track_sequence)
        self.toolbar.addAction(tracking_action)
        
        show_trajectories_action = QAction("Show Trajectories", self)
        show_trajectories_action.triggered.connect(self.show_trajectories)
        self.toolbar.addAction(show_trajectories_action)
        
        # 3D visualization action
        visualization_action = QAction("3D Visualization", self)
        visualization_action.triggered.connect(self.open_3d_visualization)
        self.toolbar.addAction(visualization_action)

    def initialize_camera_views(self, num_cameras):
        """Initialize camera views based on current experiment.
        
        Args:
            num_cameras (int): Number of cameras to display
        """
        # Clear existing camera views
        for i in reversed(range(self.camera_layout.count())): 
            self.camera_layout.itemAt(i).widget().setParent(None)
        
        self.camera_views = []
        
        # Create camera grid based on number of cameras
        if num_cameras <= 2:
            # Vertical layout for 1-2 cameras
            for i in range(num_cameras):
                camera_view = CameraView(f"Camera {i+1}")
                self.camera_layout.addWidget(camera_view)
                self.camera_views.append(camera_view)
        else:
            # Grid layout for 3-4 cameras
            import math
            cols = math.ceil(math.sqrt(num_cameras))
            rows = math.ceil(num_cameras / cols)
            
            for r in range(rows):
                row_widget = QWidget()
                row_layout = QHBoxLayout(row_widget)
                row_layout.setContentsMargins(0, 0, 0, 0)
                self.camera_layout.addWidget(row_widget)
                
                for c in range(cols):
                    idx = r * cols + c
                    if idx < num_cameras:
                        camera_view = CameraView(f"Camera {idx+1}")
                        row_layout.addWidget(camera_view)
                        self.camera_views.append(camera_view)

    # Slot implementations
    @Slot()
    def open_experiment(self):
        """Open an experiment directory."""
        directory = QFileDialog.getExistingDirectory(
            self, "Open Experiment Directory", str(self.exp_path)
        )
        
        if directory:
            self.exp_path = Path(directory)
            
            # Check for parameters directory
            params_dir = self.exp_path / "parameters"
            if not params_dir.is_dir():
                result = QMessageBox.question(
                    self,
                    "Parameters Missing",
                    f"No parameters directory found at {params_dir}.\nDo you want to initialize the experiment anyway?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if result == QMessageBox.No:
                    return
            
            # Initialize experiment if user confirms
            QMessageBox.information(
                self, "Experiment Loaded", f"Loaded experiment from: {self.exp_path}\nPress 'Initialize' to load parameters and images."
            )

    @Slot()
    def initialize_experiment(self):
        """Initialize the experiment."""
        try:
            from pyptv.ui.ptv_core import PTVCore
            
            # Create PTV core if not already created
            if not hasattr(self, 'ptv_core'):
                self.ptv_core = PTVCore(self.exp_path, self.software_path)
            
            # Initialize progress message
            progress_msg = QMessageBox(self)
            progress_msg.setIcon(QMessageBox.Information)
            progress_msg.setWindowTitle("Initialization")
            progress_msg.setText("Initializing experiment...\nThis may take a moment.")
            progress_msg.setStandardButtons(QMessageBox.NoButton)
            progress_msg.show()
            
            # Process events to make sure the message is displayed
            QApplication.processEvents()
            
            # Initialize PTV system using YAML parameters
            try:
                images = self.ptv_core.initialize()
            except Exception as init_error:
                progress_msg.close()
                raise init_error
            
            # Close progress message
            progress_msg.close()
            
            # Create camera views based on number of cameras
            self.initialize_camera_views(self.ptv_core.n_cams)
            
            # Display initial images
            for i, camera_view in enumerate(self.camera_views):
                if i < len(images):
                    camera_view.set_image(images[i])
                else:
                    # Create blank image if we don't have enough images
                    camera_view.set_image(None)
            
            QMessageBox.information(
                self, "Initialization", 
                f"Experiment initialized with {self.ptv_core.n_cams} cameras"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self, "Initialization Error", f"Error initializing experiment: {e}"
            )

    @Slot()
    def open_calibration(self):
        """Open the calibration dialog."""
        try:
            from pyptv.ui.dialogs.calibration_dialog import CalibrationDialog
            from pyptv.ui.ptv_core import PTVCore
            
            # Create PTV core if not already created
            if not hasattr(self, 'ptv_core'):
                self.ptv_core = PTVCore(self.exp_path, self.software_path)
                
                # Make sure it's initialized with YAML parameters
                if not self.ptv_core.initialized:
                    self.ptv_core.initialize()
            
            # Create and show the calibration dialog
            dialog = CalibrationDialog(self.ptv_core, self)
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(
                self, "Calibration Error", f"Error opening calibration dialog: {e}"
            )

    @Slot()
    def open_detection(self):
        """Open the detection dialog."""
        try:
            from pyptv.ui.dialogs.detection_dialog import DetectionDialog
            from pyptv.ui.ptv_core import PTVCore
            
            # Create PTV core if not already created
            if not hasattr(self, 'ptv_core'):
                self.ptv_core = PTVCore(self.exp_path, self.software_path)
                
                # Make sure it's initialized with YAML parameters
                if not self.ptv_core.initialized:
                    self.ptv_core.initialize()
            
            # Create and show the detection dialog
            dialog = DetectionDialog(self.ptv_core, self)
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(
                self, "Detection Error", f"Error opening detection dialog: {e}"
            )

    @Slot()
    def open_tracking(self):
        """Open the tracking dialog."""
        try:
            from pyptv.ui.dialogs.tracking_dialog import TrackingDialog
            from pyptv.ui.ptv_core import PTVCore
            
            # Create PTV core if not already created
            if not hasattr(self, 'ptv_core'):
                self.ptv_core = PTVCore(self.exp_path, self.software_path)
                
                # Make sure it's initialized with YAML parameters
                if not self.ptv_core.initialized:
                    self.ptv_core.initialize()
            
            # Create and show the tracking dialog
            dialog = TrackingDialog(self.ptv_core, self)
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(
                self, "Tracking Error", f"Error opening tracking dialog: {e}"
            )
            
    @Slot()
    def edit_parameters(self):
        """Open the parameter editor dialog."""
        try:
            from pyptv.ui.parameter_dialog import show_parameter_dialog
            
            # Get the parameters directory
            params_dir = self.exp_path / "parameters"
            
            # Show the parameter dialog
            show_parameter_dialog(params_dir, self)
            
            # Refresh PTV core if it exists
            if hasattr(self, 'ptv_core') and self.ptv_core.initialized:
                QMessageBox.information(
                    self,
                    "Parameters Updated",
                    "Parameters have been updated. You may need to reinitialize the experiment for changes to take effect."
                )
            
        except Exception as e:
            QMessageBox.critical(
                self, "Parameter Editor Error", f"Error opening parameter editor: {e}"
            )
    
    @Slot()
    def open_3d_visualization(self):
        """Open the 3D visualization dialog."""
        try:
            from pyptv.ui.dialogs.visualization_dialog import VisualizationDialog
            from pyptv.ui.ptv_core import PTVCore
            
            # Create PTV core if not already created
            if not hasattr(self, 'ptv_core'):
                self.ptv_core = PTVCore(self.exp_path, self.software_path)
                
                # Make sure it's initialized with YAML parameters
                if not self.ptv_core.initialized:
                    self.ptv_core.initialize()
            
            # Create and show the visualization dialog
            dialog = VisualizationDialog(self.ptv_core, self)
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(
                self, "Visualization Error", f"Error opening visualization dialog: {e}"
            )

    @Slot()
    def configure_plugins(self):
        """Configure plugins."""
        try:
            from pyptv.ui.dialogs.plugin_dialog import PluginManagerDialog
            from pyptv.ui.ptv_core import PTVCore
            
            # Create PTV core if not already created
            if not hasattr(self, 'ptv_core'):
                self.ptv_core = PTVCore(self.exp_path, self.software_path)
                
                # Make sure it's initialized with YAML parameters
                if not self.ptv_core.initialized:
                    self.ptv_core.initialize()
            
            # Create and show the plugin manager dialog
            dialog = PluginManagerDialog(self.ptv_core, self)
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(
                self, "Plugin Manager Error", f"Error opening plugin manager: {e}"
            )

    @Slot()
    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About PyPTV",
            f"<h3>PyPTV {__version__}</h3>"
            "<p>Python GUI for the OpenPTV library</p>"
            "<p>Copyright © 2008-2025 Turbulence Structure Laboratory, "
            "Tel Aviv University</p>"
            "<p><a href='http://www.openptv.net'>www.openptv.net</a></p>"
        )

    @Slot()
    def apply_highpass(self):
        """Apply highpass filter to images."""
        try:
            # Check if PTV core exists and is initialized
            if not hasattr(self, 'ptv_core') or not self.ptv_core.initialized:
                QMessageBox.warning(
                    self, "Highpass Filter", 
                    "Please initialize the experiment first."
                )
                return
                
            # Apply highpass filter
            filtered_images = self.ptv_core.apply_highpass()
            
            # Update camera views
            for i, camera_view in enumerate(self.camera_views):
                if i < len(filtered_images):
                    camera_view.set_image(filtered_images[i])
            
            QMessageBox.information(
                self, "Highpass Filter", "Highpass filter applied successfully."
            )
            
        except Exception as e:
            QMessageBox.critical(
                self, "Highpass Filter", f"Error applying highpass filter: {e}"
            )

    @Slot()
    def detect_particles(self):
        """Detect particles in images."""
        try:
            # Check if PTV core exists and is initialized
            if not hasattr(self, 'ptv_core') or not self.ptv_core.initialized:
                QMessageBox.warning(
                    self, "Detect Particles", 
                    "Please initialize the experiment first."
                )
                return
                
            # Detect particles
            x_coords, y_coords = self.ptv_core.detect_particles()
            
            # Clear existing overlays in camera views
            for view in self.camera_views:
                view.clear_overlays()
            
            # Add detected points to camera views
            for i, view in enumerate(self.camera_views):
                if i < len(x_coords):
                    view.add_points(x_coords[i], y_coords[i], color='blue', size=5)
            
            QMessageBox.information(
                self, "Detect Particles", 
                f"Detected particles in {len(x_coords)} cameras."
            )
            
        except Exception as e:
            QMessageBox.critical(
                self, "Detect Particles", f"Error detecting particles: {e}"
            )

    @Slot()
    def find_correspondences(self):
        """Find correspondences between camera views."""
        try:
            # Check if PTV core exists and is initialized
            if not hasattr(self, 'ptv_core') or not self.ptv_core.initialized:
                QMessageBox.warning(
                    self, "Find Correspondences", 
                    "Please initialize the experiment first."
                )
                return
                
            # Find correspondences
            correspondence_results = self.ptv_core.find_correspondences()
            
            if not correspondence_results:
                QMessageBox.information(
                    self, "Find Correspondences", 
                    "No correspondences found."
                )
                return
                
            # Clear existing overlays in camera views
            for view in self.camera_views:
                view.clear_overlays()
            
            # Add correspondence points to camera views
            for result in correspondence_results:
                for i, view in enumerate(self.camera_views):
                    if i < len(result["x"]):
                        view.add_points(
                            result["x"][i], 
                            result["y"][i], 
                            color=result["color"], 
                            size=5
                        )
            
            num_quads = sum(len(x) for x in correspondence_results[0]["x"]) if len(correspondence_results) > 0 else 0
            num_triplets = sum(len(x) for x in correspondence_results[1]["x"]) if len(correspondence_results) > 1 else 0
            num_pairs = sum(len(x) for x in correspondence_results[2]["x"]) if len(correspondence_results) > 2 else 0
            
            QMessageBox.information(
                self, "Find Correspondences", 
                f"Found correspondences:\n"
                f"Quadruplets: {num_quads}\n"
                f"Triplets: {num_triplets}\n"
                f"Pairs: {num_pairs}"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self, "Find Correspondences", f"Error finding correspondences: {e}"
            )

    @Slot()
    def track_sequence(self):
        """Track particles through a sequence."""
        try:
            # Check if PTV core exists and is initialized
            if not hasattr(self, 'ptv_core') or not self.ptv_core.initialized:
                QMessageBox.warning(
                    self, "Track Sequence", 
                    "Please initialize the experiment first."
                )
                return
            
            # Get frame range from YAML parameters if available, otherwise from legacy parameters
            if hasattr(self.ptv_core, 'yaml_params') and self.ptv_core.yaml_params:
                seq_params = self.ptv_core.yaml_params.get("SequenceParams")
                start_frame = seq_params.Seq_First
                end_frame = seq_params.Seq_Last
            else:
                start_frame = self.ptv_core.experiment.active_params.m_params.Seq_First
                end_frame = self.ptv_core.experiment.active_params.m_params.Seq_Last
            
            # Confirm before proceeding
            result = QMessageBox.question(
                self, 
                "Track Sequence", 
                f"This will track particles from frame {start_frame} to {end_frame}.\n\n"
                f"This operation may take some time. Continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if result == QMessageBox.No:
                return
                
            # Run tracking
            success = self.ptv_core.track_particles()
            
            if success:
                QMessageBox.information(
                    self, "Track Sequence", 
                    f"Successfully tracked particles from frame {start_frame} to {end_frame}."
                )
            else:
                QMessageBox.warning(
                    self, "Track Sequence", 
                    "Tracking completed but with potential issues."
                )
                
        except Exception as e:
            QMessageBox.critical(
                self, "Track Sequence", f"Error tracking sequence: {e}"
            )

    @Slot()
    def show_trajectories(self):
        """Show particle trajectories."""
        try:
            # Check if PTV core exists and is initialized
            if not hasattr(self, 'ptv_core') or not self.ptv_core.initialized:
                QMessageBox.warning(
                    self, "Show Trajectories", 
                    "Please initialize the experiment first."
                )
                return
                
            # Get trajectories
            trajectory_data = self.ptv_core.get_trajectories()
            
            if not trajectory_data:
                QMessageBox.information(
                    self, "Show Trajectories", 
                    "No trajectories found. Please run tracking first."
                )
                return
                
            # Clear existing overlays in camera views
            for view in self.camera_views:
                view.clear_overlays()
            
            # Add trajectory points to camera views
            for i, view in enumerate(self.camera_views):
                if i < len(trajectory_data):
                    # Add heads (start points)
                    view.add_points(
                        trajectory_data[i]["heads"]["x"], 
                        trajectory_data[i]["heads"]["y"], 
                        color=trajectory_data[i]["heads"]["color"], 
                        size=7,
                        marker='o'
                    )
                    
                    # Add tails (middle points)
                    view.add_points(
                        trajectory_data[i]["tails"]["x"], 
                        trajectory_data[i]["tails"]["y"], 
                        color=trajectory_data[i]["tails"]["color"], 
                        size=3
                    )
                    
                    # Add ends (final points)
                    view.add_points(
                        trajectory_data[i]["ends"]["x"], 
                        trajectory_data[i]["ends"]["y"], 
                        color=trajectory_data[i]["ends"]["color"], 
                        size=7,
                        marker='o'
                    )
            
            # Count trajectories
            num_trajectories = len(trajectory_data[0]["heads"]["x"]) if trajectory_data and len(trajectory_data) > 0 else 0
            
            QMessageBox.information(
                self, "Show Trajectories", 
                f"Displaying {num_trajectories} trajectories."
            )
            
        except Exception as e:
            QMessageBox.critical(
                self, "Show Trajectories", f"Error showing trajectories: {e}"
            )


def main():
    """Main function to start the application."""
    app = QApplication(sys.argv)
    
    # Set application metadata
    app.setApplicationName("PyPTV")
    app.setApplicationVersion(__version__)
    
    # Parse command line for experiment path
    exp_path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    
    # Create and show the main window
    window = MainWindow(exp_path=exp_path)
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()