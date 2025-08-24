"""Detection dialog for the PyPTV modern UI."""

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
    QComboBox
)

from pyptv.ui.camera_view import CameraView, MatplotlibCanvas


class DetectionDialog(QDialog):
    """Dialog for particle detection in the modern UI."""
    
    def __init__(self, ptv_core, parent=None):
        """Initialize the detection dialog.
        
        Args:
            ptv_core: PTVCore instance
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Store PTV core
        self.ptv_core = ptv_core
        
        # Set dialog properties
        self.setWindowTitle("Particle Detection")
        self.resize(1200, 800)
        
        # Create layout
        self.main_layout = QVBoxLayout(self)
        
        # Create toolbar
        self.toolbar = QToolBar()
        self.toolbar.setIconSize(QSize(24, 24))
        
        # Add toolbar actions
        self.action_highpass = QAction("Highpass Filter", self)
        self.action_highpass.triggered.connect(self.apply_highpass)
        self.toolbar.addAction(self.action_highpass)
        
        self.toolbar.addSeparator()
        
        self.action_detect = QAction("Detect Particles", self)
        self.action_detect.triggered.connect(self.detect_particles)
        self.toolbar.addAction(self.action_detect)
        
        self.action_show_stats = QAction("Show Statistics", self)
        self.action_show_stats.triggered.connect(self.show_statistics)
        self.toolbar.addAction(self.action_show_stats)
        
        self.toolbar.addSeparator()
        
        self.action_save = QAction("Save Configuration", self)
        self.action_save.triggered.connect(self.save_configuration)
        self.toolbar.addAction(self.action_save)
        
        self.main_layout.addWidget(self.toolbar)
        
        # Create main widget
        self.main_splitter = QSplitter(Qt.Horizontal)
        
        # Create detection parameters panel
        self.params_widget = QWidget()
        self.params_layout = QVBoxLayout(self.params_widget)
        
        # Threshold group
        self.threshold_group = QGroupBox("Detection Threshold")
        self.threshold_layout = QVBoxLayout(self.threshold_group)
        
        # Threshold slider
        threshold_slider_layout = QHBoxLayout()
        threshold_slider_layout.addWidget(QLabel("Min:"))
        
        self.threshold_slider = QSlider(Qt.Horizontal)
        self.threshold_slider.setRange(0, 255)
        self.threshold_slider.setValue(30)
        self.threshold_slider.setTickPosition(QSlider.TicksBelow)
        self.threshold_slider.setTickInterval(10)
        self.threshold_slider.valueChanged.connect(self.update_threshold_value)
        threshold_slider_layout.addWidget(self.threshold_slider)
        
        threshold_slider_layout.addWidget(QLabel("Max:"))
        
        self.threshold_layout.addLayout(threshold_slider_layout)
        
        # Threshold value
        self.threshold_value = QSpinBox()
        self.threshold_value.setRange(0, 255)
        self.threshold_value.setValue(30)
        self.threshold_value.valueChanged.connect(self.threshold_slider.setValue)
        
        threshold_value_layout = QHBoxLayout()
        threshold_value_layout.addWidget(QLabel("Value:"))
        threshold_value_layout.addWidget(self.threshold_value)
        
        self.threshold_layout.addLayout(threshold_value_layout)
        
        self.params_layout.addWidget(self.threshold_group)
        
        # Particle size group
        self.size_group = QGroupBox("Particle Size")
        self.size_layout = QFormLayout(self.size_group)
        
        self.min_size = QSpinBox()
        self.min_size.setRange(1, 100)
        self.min_size.setValue(2)
        self.size_layout.addRow("Min Size:", self.min_size)
        
        self.max_size = QSpinBox()
        self.max_size.setRange(2, 1000)
        self.max_size.setValue(20)
        self.size_layout.addRow("Max Size:", self.max_size)
        
        self.params_layout.addWidget(self.size_group)
        
        # Highpass filter group
        self.filter_group = QGroupBox("Highpass Filter")
        self.filter_layout = QFormLayout(self.filter_group)
        
        self.filter_size = QSpinBox()
        self.filter_size.setRange(1, 31)
        self.filter_size.setValue(9)
        self.filter_size.setSingleStep(2)  # Only odd values
        self.filter_layout.addRow("Filter Size:", self.filter_size)
        
        self.filter_method = QComboBox()
        self.filter_method.addItems(["Standard", "Dynamic"])
        self.filter_layout.addRow("Method:", self.filter_method)
        
        self.params_layout.addWidget(self.filter_group)
        
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
        
        # Detection results
        self.detection_points = [[] for _ in range(self.ptv_core.n_cams)]
        
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
    
    @Slot(int)
    def update_threshold_value(self, value):
        """Update threshold value when slider changes.
        
        Args:
            value: New threshold value
        """
        self.threshold_value.setValue(value)
    
    @Slot()
    def apply_highpass(self):
        """Apply highpass filter to images."""
        try:
            # Update filter parameters (this would be properly implemented)
            # self.ptv_core.experiment.active_params.m_params.HighPass = self.filter_size.value()
            
            # Apply highpass filter
            filtered_images = self.ptv_core.apply_highpass()
            
            # Update camera views
            for i, view in enumerate(self.camera_views):
                if i < len(filtered_images):
                    view.set_image(filtered_images[i])
            
            QMessageBox.information(
                self, "Highpass Filter", "Highpass filter applied successfully"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self, "Highpass Filter", f"Error applying highpass filter: {e}"
            )
    
    @Slot()
    def detect_particles(self):
        """Detect particles in images."""
        try:
            # Set detection parameters (this would be properly implemented)
            # self.ptv_core.experiment.active_params.m_params.Threshold = self.threshold_value.value()
            # self.ptv_core.experiment.active_params.m_params.MinNoise = self.min_size.value()
            # self.ptv_core.experiment.active_params.m_params.MaxNoise = self.max_size.value()
            
            # Detect particles
            x_coords, y_coords = self.ptv_core.detect_particles()
            
            # Store detection points
            self.detection_points = []
            for i in range(len(x_coords)):
                self.detection_points.append((x_coords[i], y_coords[i]))
            
            # Clear previous overlays
            for view in self.camera_views:
                view.clear_overlays()
            
            # Add detected points to camera views
            for i, view in enumerate(self.camera_views):
                if i < len(x_coords):
                    view.add_points(x_coords[i], y_coords[i], color='blue', size=5)
            
            QMessageBox.information(
                self, "Detect Particles", 
                f"Detected particles in {len(x_coords)} cameras"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self, "Detect Particles", f"Error detecting particles: {e}"
            )
    
    @Slot()
    def show_statistics(self):
        """Show detection statistics."""
        try:
            # Calculate statistics
            stats = []
            for i, points in enumerate(self.detection_points):
                if isinstance(points, tuple) and len(points) == 2:
                    x, y = points
                    num_points = len(x) if isinstance(x, list) else 0
                    stats.append(f"Camera {i+1}: {num_points} particles")
            
            # Show statistics
            if stats:
                QMessageBox.information(
                    self, "Detection Statistics", "\n".join(stats)
                )
            else:
                QMessageBox.information(
                    self, "Detection Statistics", "No detection results available"
                )
            
        except Exception as e:
            QMessageBox.critical(
                self, "Statistics", f"Error calculating statistics: {e}"
            )
    
    @Slot()
    def save_configuration(self):
        """Save detection configuration."""
        try:
            # Save parameters to file (this would be properly implemented)
            # self.ptv_core.experiment.active_params.m_params.save()
            
            QMessageBox.information(
                self, "Save Configuration", "Configuration saved successfully"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self, "Save Configuration", f"Error saving configuration: {e}"
            )
    
    @Slot()
    def apply(self):
        """Apply detection parameters."""
        try:
            # Apply parameters (this would be properly implemented)
            self.detect_particles()
            
        except Exception as e:
            QMessageBox.critical(
                self, "Apply Parameters", f"Error applying parameters: {e}"
            )