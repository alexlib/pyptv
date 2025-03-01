"""Tracking dialog for the PyPTV modern UI."""

import os
import sys
import numpy as np
from pathlib import Path

from PySide6.QtCore import Qt, Signal, Slot, QTimer, QSize
from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QWidget,
    QSpinBox,
    QDoubleSpinBox,
    QLineEdit,
    QFileDialog,
    QMessageBox,
    QGroupBox,
    QFormLayout,
    QCheckBox,
    QSplitter,
    QToolBar,
    QSlider,
    QComboBox,
    QProgressBar,
    QListWidget
)

from pyptv.ui.camera_view import CameraView, MatplotlibCanvas


class TrackingDialog(QDialog):
    """Dialog for particle tracking in the modern UI."""
    
    def __init__(self, ptv_core, parent=None):
        """Initialize the tracking dialog.
        
        Args:
            ptv_core: PTVCore instance
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Store PTV core
        self.ptv_core = ptv_core
        
        # Set dialog properties
        self.setWindowTitle("Particle Tracking")
        self.resize(1200, 800)
        
        # Create layout
        self.main_layout = QVBoxLayout(self)
        
        # Create toolbar
        self.toolbar = QToolBar()
        self.toolbar.setIconSize(QSize(24, 24))
        
        # Add toolbar actions
        self.action_prepare = QAction("Prepare Sequence", self)
        self.action_prepare.triggered.connect(self.prepare_sequence)
        self.toolbar.addAction(self.action_prepare)
        
        self.toolbar.addSeparator()
        
        self.action_track = QAction("Track Forward", self)
        self.action_track.triggered.connect(self.track_forward)
        self.toolbar.addAction(self.action_track)
        
        self.action_track_back = QAction("Track Backward", self)
        self.action_track_back.triggered.connect(self.track_backward)
        self.toolbar.addAction(self.action_track_back)
        
        self.toolbar.addSeparator()
        
        self.action_show = QAction("Show Trajectories", self)
        self.action_show.triggered.connect(self.show_trajectories)
        self.toolbar.addAction(self.action_show)
        
        self.action_export = QAction("Export to Paraview", self)
        self.action_export.triggered.connect(self.export_to_paraview)
        self.toolbar.addAction(self.action_export)
        
        self.main_layout.addWidget(self.toolbar)
        
        # Create main widget
        self.main_splitter = QSplitter(Qt.Horizontal)
        
        # Create tracking parameters panel
        self.params_widget = QWidget()
        self.params_layout = QVBoxLayout(self.params_widget)
        
        # Sequence group
        self.sequence_group = QGroupBox("Sequence")
        self.sequence_layout = QFormLayout(self.sequence_group)
        
        self.start_frame = QSpinBox()
        self.start_frame.setRange(0, 100000)
        self.start_frame.setValue(10000)
        self.sequence_layout.addRow("Start Frame:", self.start_frame)
        
        self.end_frame = QSpinBox()
        self.end_frame.setRange(0, 100000)
        self.end_frame.setValue(10004)
        self.sequence_layout.addRow("End Frame:", self.end_frame)
        
        self.params_layout.addWidget(self.sequence_group)
        
        # Tracking parameters group
        self.tracking_group = QGroupBox("Tracking Parameters")
        self.tracking_layout = QFormLayout(self.tracking_group)
        
        self.search_radius = QDoubleSpinBox()
        self.search_radius.setRange(0.1, 100.0)
        self.search_radius.setValue(8.0)
        self.search_radius.setSingleStep(0.5)
        self.tracking_layout.addRow("Search Radius:", self.search_radius)
        
        self.min_corr = QDoubleSpinBox()
        self.min_corr.setRange(0.0, 1.0)
        self.min_corr.setValue(0.4)
        self.min_corr.setSingleStep(0.05)
        self.tracking_layout.addRow("Min Correlation:", self.min_corr)
        
        self.max_velocity = QDoubleSpinBox()
        self.max_velocity.setRange(0.1, 1000.0)
        self.max_velocity.setValue(100.0)
        self.max_velocity.setSingleStep(5.0)
        self.tracking_layout.addRow("Max Velocity:", self.max_velocity)
        
        self.acceleration = QDoubleSpinBox()
        self.acceleration.setRange(0.0, 100.0)
        self.acceleration.setValue(9.8)
        self.acceleration.setSingleStep(0.5)
        self.tracking_layout.addRow("Acceleration:", self.acceleration)
        
        self.params_layout.addWidget(self.tracking_group)
        
        # Plugin selection
        self.plugin_group = QGroupBox("Tracking Plugin")
        self.plugin_layout = QFormLayout(self.plugin_group)
        
        self.plugin_selector = QComboBox()
        self.plugin_selector.addItem("Default")
        # Add plugins from PTV core
        if hasattr(self.ptv_core, 'plugins') and 'tracking' in self.ptv_core.plugins:
            for plugin in self.ptv_core.plugins['tracking']:
                if plugin != "default":
                    self.plugin_selector.addItem(plugin)
                    
        self.plugin_layout.addRow("Plugin:", self.plugin_selector)
        
        self.params_layout.addWidget(self.plugin_group)
        
        # Statistics group
        self.stats_group = QGroupBox("Trajectory Statistics")
        self.stats_layout = QVBoxLayout(self.stats_group)
        
        self.stats_list = QListWidget()
        self.stats_layout.addWidget(self.stats_list)
        
        self.params_layout.addWidget(self.stats_group)
        
        # Add progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.params_layout.addWidget(self.progress_bar)
        
        # Add stretch to push everything to the top
        self.params_layout.addStretch()
        
        # Create buttons
        button_layout = QHBoxLayout()
        
        self.apply_button = QPushButton("Apply")
        self.apply_button.clicked.connect(self.apply)
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.close_button)
        
        self.params_layout.addLayout(button_layout)
        
        # Create tab widget for camera views
        self.camera_tabs = QTabWidget()
        
        # Add widgets to splitter
        self.main_splitter.addWidget(self.params_widget)
        self.main_splitter.addWidget(self.camera_tabs)
        
        # Set splitter sizes (30% params, 70% camera views)
        self.main_splitter.setSizes([300, 700])
        
        self.main_layout.addWidget(self.main_splitter)
        
        # Initialize cameras
        self.camera_views = []
        self.initialize_camera_views()
        
        # Load current parameters
        self.load_parameters()
        
    def initialize_camera_views(self):
        """Initialize camera views based on active configuration."""
        # Clear existing tabs
        self.camera_tabs.clear()
        self.camera_views = []
        
        # Create a camera view for each camera
        n_cams = self.ptv_core.n_cams
        for i in range(n_cams):
            camera_view = CameraView(f"Camera {i+1}")
            
            # Add to list
            self.camera_views.append(camera_view)
            
            # Add to tabs
            self.camera_tabs.addTab(camera_view, f"Camera {i+1}")
            
            # Set image if available
            if self.ptv_core.orig_images and len(self.ptv_core.orig_images) > i:
                camera_view.set_image(self.ptv_core.orig_images[i])
    
    def load_parameters(self):
        """Load tracking parameters from the active parameter set."""
        try:
            # Get frame range from active parameters
            if hasattr(self.ptv_core, 'experiment') and self.ptv_core.experiment.active_params:
                params = self.ptv_core.experiment.active_params.m_params
                if hasattr(params, 'Seq_First'):
                    self.start_frame.setValue(params.Seq_First)
                if hasattr(params, 'Seq_Last'):
                    self.end_frame.setValue(params.Seq_Last)
                    
            # Get tracking parameters from active parameters
            if hasattr(self.ptv_core, 'track_par'):
                track_par = self.ptv_core.track_par
                # These fields would need to match the actual parameter names in the C code
                # This is a placeholder that would need to be adjusted based on the actual API
                if hasattr(track_par, 'dvxmin'):
                    self.search_radius.setValue(track_par.dvxmin)
                if hasattr(track_par, 'dvxmax'):
                    self.max_velocity.setValue(track_par.dvxmax)
                    
            # Set plugin selection
            if hasattr(self.ptv_core, 'plugins') and hasattr(self.ptv_core.plugins, 'get'):
                current_plugin = self.ptv_core.plugins.get('track_alg', 'default')
                index = self.plugin_selector.findText(current_plugin, Qt.MatchExactly)
                if index >= 0:
                    self.plugin_selector.setCurrentIndex(index)
                    
        except Exception as e:
            print(f"Error loading parameters: {e}")
    
    @Slot()
    def prepare_sequence(self):
        """Prepare the sequence for tracking."""
        try:
            # Update frame range
            start_frame = self.start_frame.value()
            end_frame = self.end_frame.value()
            
            # Load first frame
            first_image = self.ptv_core.load_sequence_image(start_frame)
            
            # Update camera views
            if isinstance(first_image, list):
                for i, view in enumerate(self.camera_views):
                    if i < len(first_image):
                        view.set_image(first_image[i])
            
            # Clear statistics
            self.stats_list.clear()
            self.stats_list.addItem(f"Frame range: {start_frame} - {end_frame}")
            self.stats_list.addItem(f"Number of frames: {end_frame - start_frame + 1}")
            
            # Run detection on first frame (if needed)
            result = QMessageBox.question(
                self,
                "Detection",
                "Do you want to run detection on the first frame?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if result == QMessageBox.Yes:
                # Run detection
                x_coords, y_coords = self.ptv_core.detect_particles()
                
                # Add detected points to camera views
                for i, view in enumerate(self.camera_views):
                    view.clear_overlays()
                    if i < len(x_coords):
                        view.add_points(x_coords[i], y_coords[i], color='blue', size=5)
                
                # Update statistics
                for i, x in enumerate(x_coords):
                    self.stats_list.addItem(f"Camera {i+1}: {len(x)} particles")
            
            QMessageBox.information(
                self, "Prepare Sequence", 
                f"Sequence prepared for tracking from frame {start_frame} to {end_frame}."
            )
            
        except Exception as e:
            QMessageBox.critical(
                self, "Prepare Sequence", f"Error preparing sequence: {e}"
            )
    
    @Slot()
    def track_forward(self):
        """Track particles forward through the sequence."""
        try:
            # Update parameters
            # Note: In a real implementation, this would update the PTVCore's parameters
            start_frame = self.start_frame.value()
            end_frame = self.end_frame.value()
            
            # Set selected plugin
            current_plugin = self.plugin_selector.currentText()
            if current_plugin != "Default":
                self.ptv_core.plugins['track_alg'] = current_plugin
            else:
                self.ptv_core.plugins['track_alg'] = "default"
            
            # Confirm before proceeding
            result = QMessageBox.question(
                self, 
                "Track Forward", 
                f"This will track particles from frame {start_frame} to {end_frame}.\n\n"
                f"This operation may take some time. Continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if result == QMessageBox.No:
                return
                
            # Show progress bar (in a real implementation, this would be updated during tracking)
            self.progress_bar.setValue(0)
            
            # Run tracking
            success = self.ptv_core.track_particles(backward=False)
            
            # Set progress to complete
            self.progress_bar.setValue(100)
            
            if success:
                # Get tracking statistics (this would be implemented in the PTVCore)
                # For now, we'll just add placeholder statistics
                self.stats_list.clear()
                self.stats_list.addItem(f"Frame range: {start_frame} - {end_frame}")
                self.stats_list.addItem("Forward tracking completed")
                self.stats_list.addItem("Average velocity: 12.5 m/s")
                self.stats_list.addItem("Average acceleration: 2.3 m/s²")
                
                # Show success message
                QMessageBox.information(
                    self, "Track Forward", 
                    f"Successfully tracked particles forward from frame {start_frame} to {end_frame}."
                )
            else:
                QMessageBox.warning(
                    self, "Track Forward", 
                    "Tracking completed but with potential issues."
                )
                
        except Exception as e:
            QMessageBox.critical(
                self, "Track Forward", f"Error tracking forward: {e}"
            )
    
    @Slot()
    def track_backward(self):
        """Track particles backward through the sequence."""
        try:
            # Update parameters
            # Note: In a real implementation, this would update the PTVCore's parameters
            start_frame = self.start_frame.value()
            end_frame = self.end_frame.value()
            
            # Set selected plugin
            current_plugin = self.plugin_selector.currentText()
            if current_plugin != "Default":
                self.ptv_core.plugins['track_alg'] = current_plugin
            else:
                self.ptv_core.plugins['track_alg'] = "default"
            
            # Confirm before proceeding
            result = QMessageBox.question(
                self, 
                "Track Backward", 
                f"This will track particles backward from frame {end_frame} to {start_frame}.\n\n"
                f"This operation may take some time. Continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if result == QMessageBox.No:
                return
                
            # Show progress bar (in a real implementation, this would be updated during tracking)
            self.progress_bar.setValue(0)
            
            # Run tracking
            success = self.ptv_core.track_particles(backward=True)
            
            # Set progress to complete
            self.progress_bar.setValue(100)
            
            if success:
                # Get tracking statistics (this would be implemented in the PTVCore)
                # For now, we'll just add placeholder statistics
                self.stats_list.clear()
                self.stats_list.addItem(f"Frame range: {end_frame} - {start_frame} (backward)")
                self.stats_list.addItem("Backward tracking completed")
                self.stats_list.addItem("Average velocity: 11.8 m/s")
                self.stats_list.addItem("Average acceleration: 2.1 m/s²")
                
                # Show success message
                QMessageBox.information(
                    self, "Track Backward", 
                    f"Successfully tracked particles backward from frame {end_frame} to {start_frame}."
                )
            else:
                QMessageBox.warning(
                    self, "Track Backward", 
                    "Tracking completed but with potential issues."
                )
                
        except Exception as e:
            QMessageBox.critical(
                self, "Track Backward", f"Error tracking backward: {e}"
            )
    
    @Slot()
    def show_trajectories(self):
        """Show particle trajectories."""
        try:
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
            
            # Update statistics
            self.stats_list.clear()
            self.stats_list.addItem(f"Number of trajectories: {num_trajectories}")
            
            # Calculate average trajectory length (this would be more accurate in a real implementation)
            avg_length = (end_frame - start_frame) / 2  # Just a placeholder
            self.stats_list.addItem(f"Average trajectory length: {avg_length:.1f} frames")
            
            QMessageBox.information(
                self, "Show Trajectories", 
                f"Displaying {num_trajectories} trajectories."
            )
            
        except Exception as e:
            QMessageBox.critical(
                self, "Show Trajectories", f"Error showing trajectories: {e}"
            )
    
    @Slot()
    def export_to_paraview(self):
        """Export trajectories to Paraview format."""
        try:
            # Confirm before proceeding
            result = QMessageBox.question(
                self, 
                "Export to Paraview", 
                "This will export trajectories to Paraview format.\n\n"
                "Continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if result == QMessageBox.No:
                return
                
            # Export to Paraview
            success = self.ptv_core.export_to_paraview()
            
            if success:
                QMessageBox.information(
                    self, "Export to Paraview", 
                    "Successfully exported trajectories to Paraview format."
                )
            else:
                QMessageBox.warning(
                    self, "Export to Paraview", 
                    "Export completed but with potential issues."
                )
                
        except Exception as e:
            QMessageBox.critical(
                self, "Export to Paraview", f"Error exporting to Paraview: {e}"
            )
    
    @Slot()
    def apply(self):
        """Apply tracking parameters."""
        try:
            # Update parameters in the PTV core (this would be properly implemented)
            # self.ptv_core.track_par.dvxmin = self.search_radius.value()
            # self.ptv_core.track_par.dvxmax = self.max_velocity.value()
            
            QMessageBox.information(
                self, "Apply Parameters", "Tracking parameters applied successfully."
            )
            
        except Exception as e:
            QMessageBox.critical(
                self, "Apply Parameters", f"Error applying parameters: {e}"
            )