"""Calibration dialog for the PyPTV modern UI."""

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
    QToolBar
)

from pyptv.ui.camera_view import CameraView, MatplotlibCanvas


class CalibrationDialog(QDialog):
    """Dialog for camera calibration in the modern UI."""
    
    def __init__(self, ptv_core, parent=None):
        """Initialize the calibration dialog.
        
        Args:
            ptv_core: PTVCore instance
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Store PTV core
        self.ptv_core = ptv_core
        
        # Set dialog properties
        self.setWindowTitle("Camera Calibration")
        self.resize(1200, 800)
        
        # Create layout
        self.main_layout = QVBoxLayout(self)
        
        # Create toolbar
        self.toolbar = QToolBar()
        self.toolbar.setIconSize(QSize(24, 24))
        
        # Add toolbar actions
        self.action_load_target = QAction("Load Target", self)
        self.action_load_target.triggered.connect(self.load_target)
        self.toolbar.addAction(self.action_load_target)
        
        self.toolbar.addSeparator()
        
        self.action_detect_target = QAction("Detect Target", self)
        self.action_detect_target.triggered.connect(self.detect_target)
        self.toolbar.addAction(self.action_detect_target)
        
        self.action_sort_target = QAction("Sort Grid", self)
        self.action_sort_target.triggered.connect(self.sort_target_grid)
        self.toolbar.addAction(self.action_sort_target)
        
        self.toolbar.addSeparator()
        
        self.action_calibrate = QAction("Calibrate", self)
        self.action_calibrate.triggered.connect(self.calibrate)
        self.toolbar.addAction(self.action_calibrate)
        
        self.action_orient = QAction("Orient", self)
        self.action_orient.triggered.connect(self.orient)
        self.toolbar.addAction(self.action_orient)
        
        self.toolbar.addSeparator()
        
        self.action_show_results = QAction("Show Results", self)
        self.action_show_results.triggered.connect(self.show_results)
        self.toolbar.addAction(self.action_show_results)
        
        self.main_layout.addWidget(self.toolbar)
        
        # Create main widget
        self.main_splitter = QSplitter(Qt.Horizontal)
        
        # Create calibration parameters panel
        self.params_widget = QWidget()
        self.params_layout = QVBoxLayout(self.params_widget)
        
        # Parameters group
        self.cal_params_group = QGroupBox("Calibration Parameters")
        self.cal_params_layout = QFormLayout(self.cal_params_group)
        
        # Add parameter fields
        self.img_base_name = QLineEdit()
        self.cal_params_layout.addRow("Image Base Name:", self.img_base_name)
        
        self.cal_file = QLineEdit()
        self.cal_params_layout.addRow("Calibration File:", self.cal_file)
        
        self.params_layout.addWidget(self.cal_params_group)
        
        # Target parameters group
        self.target_params_group = QGroupBox("Target Parameters")
        self.target_params_layout = QFormLayout(self.target_params_group)
        
        self.target_file = QLineEdit()
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self.browse_target_file)
        
        target_file_layout = QHBoxLayout()
        target_file_layout.addWidget(self.target_file)
        target_file_layout.addWidget(browse_button)
        
        self.target_params_layout.addRow("Target File:", target_file_layout)
        
        self.target_num_points = QSpinBox()
        self.target_num_points.setRange(0, 1000)
        self.target_num_points.setValue(0)
        self.target_params_layout.addRow("Target Points:", self.target_num_points)
        
        self.params_layout.addWidget(self.target_params_group)
        
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
        
        # Connect signals
        self.connect_signals()
        
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
    
    def connect_signals(self):
        """Connect signals to slots."""
        # Connect camera view signals
        for i, view in enumerate(self.camera_views):
            view.point_clicked.connect(lambda name, x, y, button, cam_id=i: 
                                       self.handle_point_clicked(cam_id, x, y, button))
    
    @Slot(int, float, float, int)
    def handle_point_clicked(self, cam_id, x, y, button):
        """Handle point click events from camera views.
        
        Args:
            cam_id: Camera ID
            x: X coordinate
            y: Y coordinate
            button: Mouse button (1=left, 3=right)
        """
        # Left click: Add calibration point
        if button == 1:
            self.add_calibration_point(cam_id, x, y)
        
        # Right click: Show epipolar lines
        elif button == 3:
            self.show_epipolar_lines(cam_id, x, y)
    
    def add_calibration_point(self, cam_id, x, y):
        """Add a calibration point for the specified camera.
        
        Args:
            cam_id: Camera ID
            x: X coordinate
            y: Y coordinate
        """
        # Mark the point on the camera view
        self.camera_views[cam_id].add_points(x, y, color='red', size=10, marker='x')
        
        # TODO: Add to calibration points list
        print(f"Added calibration point at ({x:.1f}, {y:.1f}) for Camera {cam_id+1}")
    
    def show_epipolar_lines(self, cam_id, x, y):
        """Show epipolar lines for a point in one camera view.
        
        Args:
            cam_id: Camera ID
            x: X coordinate
            y: Y coordinate
        """
        try:
            # Calculate epipolar lines
            epipolar_lines = self.ptv_core.calculate_epipolar_line(cam_id, x, y)
            
            # Mark the clicked point
            self.camera_views[cam_id].add_points(x, y, color='cyan', size=10, marker='o')
            
            # Add epipolar lines to other camera views
            for other_cam_id, points in epipolar_lines.items():
                self.camera_views[other_cam_id].add_epipolar_line(
                    points, color=self.get_camera_color(cam_id)
                )
                
            print(f"Showing epipolar lines for point ({x:.1f}, {y:.1f}) in Camera {cam_id+1}")
            
        except Exception as e:
            QMessageBox.warning(
                self, "Epipolar Lines", f"Error calculating epipolar lines: {e}"
            )
    
    def get_camera_color(self, cam_id):
        """Get color for a camera.
        
        Args:
            cam_id: Camera ID
            
        Returns:
            Color string
        """
        colors = ['red', 'green', 'blue', 'yellow']
        return colors[cam_id % len(colors)]
    
    @Slot()
    def load_target(self):
        """Load calibration target."""
        try:
            # Get target file
            target_file = self.target_file.text()
            if not target_file:
                QMessageBox.warning(
                    self, "Load Target", "Please specify a target file"
                )
                return
            
            # TODO: Implement target loading
            QMessageBox.information(
                self, "Load Target", f"Loading target from {target_file}"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self, "Load Target", f"Error loading target: {e}"
            )
    
    @Slot()
    def detect_target(self):
        """Detect calibration target in images."""
        try:
            # TODO: Implement target detection
            QMessageBox.information(
                self, "Detect Target", "Target detection will be implemented here"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self, "Detect Target", f"Error detecting target: {e}"
            )
    
    @Slot()
    def sort_target_grid(self):
        """Sort detected target grid points."""
        try:
            # TODO: Implement grid sorting
            QMessageBox.information(
                self, "Sort Grid", "Grid sorting will be implemented here"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self, "Sort Grid", f"Error sorting grid: {e}"
            )
    
    @Slot()
    def calibrate(self):
        """Perform calibration."""
        try:
            # TODO: Implement calibration
            QMessageBox.information(
                self, "Calibrate", "Calibration will be implemented here"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self, "Calibrate", f"Error during calibration: {e}"
            )
    
    @Slot()
    def orient(self):
        """Perform orientation."""
        try:
            # TODO: Implement orientation
            QMessageBox.information(
                self, "Orient", "Orientation will be implemented here"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self, "Orient", f"Error during orientation: {e}"
            )
    
    @Slot()
    def show_results(self):
        """Show calibration results."""
        try:
            # TODO: Implement results display
            QMessageBox.information(
                self, "Results", "Calibration results will be shown here"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self, "Results", f"Error showing results: {e}"
            )
    
    @Slot()
    def browse_target_file(self):
        """Browse for target file."""
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter("Text files (*.txt)")
        
        if file_dialog.exec_():
            file_paths = file_dialog.selectedFiles()
            if file_paths:
                self.target_file.setText(file_paths[0])
    
    @Slot()
    def apply(self):
        """Apply calibration parameters."""
        try:
            # TODO: Save calibration parameters
            QMessageBox.information(
                self, "Apply Parameters", "Parameters applied successfully"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self, "Apply Parameters", f"Error applying parameters: {e}"
            )