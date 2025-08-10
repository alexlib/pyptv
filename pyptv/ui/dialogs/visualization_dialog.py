"""3D visualization dialog for viewing particle trajectories and positions."""

import os
import sys
import numpy as np
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QSpinBox,
    QCheckBox,
    QGroupBox,
    QWidget,
    QSlider,
    QColorDialog,
    QFileDialog
)

from flowtracks.io import trajectories_ptvis


class TrajectoryCanvas(FigureCanvas):
    """Canvas for displaying 3D trajectories."""
    
    def __init__(self, parent=None, width=8, height=6, dpi=100):
        """Initialize the canvas."""
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111, projection='3d')
        super().__init__(self.fig)
        
        # Initialize plot elements
        self.trajectory_plots = []
        self.position_plots = []
        self.axes.set_xlabel('X [mm]')
        self.axes.set_ylabel('Y [mm]')
        self.axes.set_zlabel('Z [mm]')
        self.axes.set_title('3D Trajectories')
        
        # Set default view
        self.axes.view_init(elev=30, azim=45)
        
        # Set equal aspect ratio for all axes
        self.axes.set_box_aspect([1, 1, 1])
        
    def clear_plot(self):
        """Clear all trajectories from the plot."""
        # Clear the current plots
        for plot in self.trajectory_plots:
            plot.remove()
        for plot in self.position_plots:
            plot.remove()
            
        self.trajectory_plots = []
        self.position_plots = []
        self.draw()
        
    def plot_trajectories(self, trajectories, color_by='trajectory_id', 
                         show_heads=True, head_size=30, line_width=1):
        """Plot trajectories in 3D.
        
        Args:
            trajectories: List of trajectory objects
            color_by: Method to color trajectories ('trajectory_id', 'velocity', 'frame')
            show_heads: Whether to show the start points of trajectories
            head_size: Size of the trajectory start points
            line_width: Width of trajectory lines
        """
        # Clear existing plots
        self.clear_plot()
        
        if not trajectories:
            return
        
        # Create colormap
        cmap = matplotlib.cm.get_cmap('viridis')
        
        # Track min/max for axis limits
        all_points = []
        
        # Plot each trajectory
        for i, traj in enumerate(trajectories):
            # Extract positions
            positions = traj.pos()
            
            if len(positions) < 2:
                continue
                
            # Accumulate points for axis scaling
            all_points.append(positions)
            
            # Determine color
            if color_by == 'trajectory_id':
                # Color by trajectory ID (unique for each trajectory)
                color = cmap(float(i) / max(1, len(trajectories) - 1))
            elif color_by == 'velocity':
                # Color by velocity magnitude (normalized across trajectory)
                velocities = np.linalg.norm(traj.velocity(), axis=1)
                vel_max = np.max(velocities) if len(velocities) > 0 else 1
                vel_min = np.min(velocities) if len(velocities) > 0 else 0
                vel_range = vel_max - vel_min
                if vel_range == 0:
                    colors = [cmap(0.5)] * len(positions)
                else:
                    colors = [cmap((v - vel_min) / vel_range) for v in velocities]
            elif color_by == 'frame':
                # Color by frame number (time progression)
                frames = traj.time()
                frame_max = np.max(frames) if len(frames) > 0 else 1
                frame_min = np.min(frames) if len(frames) > 0 else 0
                frame_range = frame_max - frame_min
                if frame_range == 0:
                    colors = [cmap(0.5)] * len(positions)
                else:
                    colors = [cmap((f - frame_min) / frame_range) for f in frames]
            else:
                # Default - single color
                color = 'blue'
            
            # Plot the trajectory
            if color_by in ['velocity', 'frame']:
                # For segment coloring (velocity or frame)
                for i in range(len(positions) - 1):
                    line, = self.axes.plot(
                        positions[i:i+2, 0], 
                        positions[i:i+2, 1], 
                        positions[i:i+2, 2],
                        color=colors[i],
                        linewidth=line_width
                    )
                    self.trajectory_plots.append(line)
            else:
                # For trajectory coloring
                line, = self.axes.plot(
                    positions[:, 0], 
                    positions[:, 1], 
                    positions[:, 2],
                    color=color,
                    linewidth=line_width
                )
                self.trajectory_plots.append(line)
            
            # Plot the trajectory head (start point)
            if show_heads:
                scatter = self.axes.scatter(
                    positions[0, 0],
                    positions[0, 1],
                    positions[0, 2],
                    s=head_size,
                    color=colors[0] if color_by in ['velocity', 'frame'] else color,
                    marker='o',
                    edgecolors='black'
                )
                self.position_plots.append(scatter)
        
        # Set axis limits to contain all trajectories
        if all_points:
            all_points = np.vstack(all_points)
            x_min, y_min, z_min = np.min(all_points, axis=0)
            x_max, y_max, z_max = np.max(all_points, axis=0)
            
            # Add some padding
            pad = max(
                0.1 * (x_max - x_min),
                0.1 * (y_max - y_min),
                0.1 * (z_max - z_min),
                0.1  # Minimum padding
            )
            
            self.axes.set_xlim(x_min - pad, x_max + pad)
            self.axes.set_ylim(y_min - pad, y_max + pad)
            self.axes.set_zlim(z_min - pad, z_max + pad)
        
        # Update canvas
        self.draw()
    
    def set_title(self, title):
        """Set the plot title."""
        self.axes.set_title(title)
        self.draw()
        
    def set_view_angle(self, elev, azim):
        """Set the viewing angle of the 3D plot."""
        self.axes.view_init(elev=elev, azim=azim)
        self.draw()
        
    def add_target_points(self, points, color='red', marker='o', size=30):
        """Add calibration target points to the visualization."""
        if points is not None and len(points) > 0:
            scatter = self.axes.scatter(
                points[:, 0],
                points[:, 1],
                points[:, 2],
                s=size,
                color=color,
                marker=marker,
                edgecolors='black'
            )
            self.position_plots.append(scatter)
            self.draw()


class VisualizationDialog(QDialog):
    """Dialog for 3D visualization of trajectories and positions."""
    
    def __init__(self, ptv_core, parent=None):
        """Initialize the visualization dialog.
        
        Args:
            ptv_core: PTVCore instance
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Store reference to the PTV core
        self.ptv_core = ptv_core
        
        # Set up the dialog
        self.setWindowTitle("3D Visualization")
        self.resize(1000, 800)
        
        # Create the main layout
        main_layout = QVBoxLayout(self)
        
        # Create the visualization canvas
        self.canvas = TrajectoryCanvas(self, width=8, height=6, dpi=100)
        
        # Create the toolbar
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        # Add toolbar and canvas to layout
        main_layout.addWidget(self.toolbar)
        main_layout.addWidget(self.canvas)
        
        # Create control panel layout
        control_layout = QHBoxLayout()
        
        # Create data controls group
        data_group = QGroupBox("Data Controls")
        data_layout = QVBoxLayout(data_group)
        
        # Frame range selection
        frame_layout = QHBoxLayout()
        frame_layout.addWidget(QLabel("Frame Range:"))
        
        self.start_frame = QSpinBox()
        self.start_frame.setMinimum(0)
        self.start_frame.setMaximum(10000)
        self.start_frame.setValue(self.ptv_core.experiment.active_params.m_params.Seq_First)
        frame_layout.addWidget(self.start_frame)
        
        frame_layout.addWidget(QLabel("to"))
        
        self.end_frame = QSpinBox()
        self.end_frame.setMinimum(0)
        self.end_frame.setMaximum(10000)
        self.end_frame.setValue(self.ptv_core.experiment.active_params.m_params.Seq_Last)
        frame_layout.addWidget(self.end_frame)
        
        data_layout.addLayout(frame_layout)
        
        # Min trajectory length
        length_layout = QHBoxLayout()
        length_layout.addWidget(QLabel("Min Trajectory Length:"))
        
        self.min_length = QSpinBox()
        self.min_length.setMinimum(2)
        self.min_length.setMaximum(1000)
        self.min_length.setValue(3)
        length_layout.addWidget(self.min_length)
        
        data_layout.addLayout(length_layout)
        
        # Load trajectories button
        self.load_button = QPushButton("Load Trajectories")
        self.load_button.clicked.connect(self.load_trajectories)
        data_layout.addWidget(self.load_button)
        
        # Load calibration target button
        self.load_target_button = QPushButton("Load Calibration Target")
        self.load_target_button.clicked.connect(self.load_calibration_target)
        data_layout.addWidget(self.load_target_button)
        
        # Add data group to control layout
        control_layout.addWidget(data_group)
        
        # Create display controls group
        display_group = QGroupBox("Display Controls")
        display_layout = QVBoxLayout(display_group)
        
        # Color by option
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Color By:"))
        
        self.color_by = QComboBox()
        self.color_by.addItems(["Trajectory ID", "Velocity", "Frame"])
        self.color_by.currentIndexChanged.connect(self.update_visualization)
        color_layout.addWidget(self.color_by)
        
        display_layout.addLayout(color_layout)
        
        # Show heads checkbox
        self.show_heads = QCheckBox("Show Trajectory Start Points")
        self.show_heads.setChecked(True)
        self.show_heads.stateChanged.connect(self.update_visualization)
        display_layout.addWidget(self.show_heads)
        
        # Point size slider
        point_size_layout = QHBoxLayout()
        point_size_layout.addWidget(QLabel("Point Size:"))
        
        self.point_size = QSlider(Qt.Horizontal)
        self.point_size.setMinimum(1)
        self.point_size.setMaximum(50)
        self.point_size.setValue(30)
        self.point_size.setTickPosition(QSlider.TicksBelow)
        self.point_size.setTickInterval(5)
        self.point_size.valueChanged.connect(self.update_visualization)
        point_size_layout.addWidget(self.point_size)
        
        display_layout.addLayout(point_size_layout)
        
        # Line width slider
        line_width_layout = QHBoxLayout()
        line_width_layout.addWidget(QLabel("Line Width:"))
        
        self.line_width = QSlider(Qt.Horizontal)
        self.line_width.setMinimum(1)
        self.line_width.setMaximum(10)
        self.line_width.setValue(1)
        self.line_width.setTickPosition(QSlider.TicksBelow)
        self.line_width.setTickInterval(1)
        self.line_width.valueChanged.connect(self.update_visualization)
        line_width_layout.addWidget(self.line_width)
        
        display_layout.addLayout(line_width_layout)
        
        # Export controls
        export_layout = QHBoxLayout()
        
        self.export_button = QPushButton("Export Image")
        self.export_button.clicked.connect(self.export_image)
        export_layout.addWidget(self.export_button)
        
        self.export_paraview_button = QPushButton("Export for ParaView")
        self.export_paraview_button.clicked.connect(self.export_to_paraview)
        export_layout.addWidget(self.export_paraview_button)
        
        display_layout.addLayout(export_layout)
        
        # Add display group to control layout
        control_layout.addWidget(display_group)
        
        # Create view controls group
        view_group = QGroupBox("View Controls")
        view_layout = QVBoxLayout(view_group)
        
        # Elevation slider
        elev_layout = QHBoxLayout()
        elev_layout.addWidget(QLabel("Elevation:"))
        
        self.elev_slider = QSlider(Qt.Horizontal)
        self.elev_slider.setMinimum(0)
        self.elev_slider.setMaximum(180)
        self.elev_slider.setValue(30)
        self.elev_slider.setTickPosition(QSlider.TicksBelow)
        self.elev_slider.setTickInterval(10)
        self.elev_slider.valueChanged.connect(self.update_view)
        elev_layout.addWidget(self.elev_slider)
        
        view_layout.addLayout(elev_layout)
        
        # Azimuth slider
        azim_layout = QHBoxLayout()
        azim_layout.addWidget(QLabel("Azimuth:"))
        
        self.azim_slider = QSlider(Qt.Horizontal)
        self.azim_slider.setMinimum(0)
        self.azim_slider.setMaximum(360)
        self.azim_slider.setValue(45)
        self.azim_slider.setTickPosition(QSlider.TicksBelow)
        self.azim_slider.setTickInterval(30)
        self.azim_slider.valueChanged.connect(self.update_view)
        azim_layout.addWidget(self.azim_slider)
        
        view_layout.addLayout(azim_layout)
        
        # Preset views
        preset_layout = QHBoxLayout()
        
        self.preset_xy = QPushButton("XY View")
        self.preset_xy.clicked.connect(lambda: self.set_preset_view(90, 0))
        preset_layout.addWidget(self.preset_xy)
        
        self.preset_xz = QPushButton("XZ View")
        self.preset_xz.clicked.connect(lambda: self.set_preset_view(0, 0))
        preset_layout.addWidget(self.preset_xz)
        
        self.preset_yz = QPushButton("YZ View")
        self.preset_yz.clicked.connect(lambda: self.set_preset_view(0, 90))
        preset_layout.addWidget(self.preset_yz)
        
        view_layout.addLayout(preset_layout)
        
        # Add view group to control layout
        control_layout.addWidget(view_group)
        
        # Add control layout to main layout
        main_layout.addLayout(control_layout)
        
        # Initialize data
        self.trajectories = None
        self.target_points = None
        
    @Slot()
    def load_trajectories(self):
        """Load trajectories from PTV results."""
        try:
            # Get frame range from controls
            start_frame = self.start_frame.value()
            end_frame = self.end_frame.value()
            min_length = self.min_length.value()
            
            # Load trajectories using flowtracks
            data_path = str(self.ptv_core.exp_path / "res/ptv_is.%d")
            self.trajectories = trajectories_ptvis(
                data_path, 
                first=start_frame, 
                last=end_frame, 
                traj_min_len=min_length,
                xuap=False
            )
            
            # Update the visualization
            self.update_visualization()
            
            # Update title with trajectory count
            self.canvas.set_title(f"3D Trajectories (Count: {len(self.trajectories)})")
            
        except Exception as e:
            self.canvas.set_title(f"Error: {e}")
            print(f"Error loading trajectories: {e}")
    
    @Slot()
    def load_calibration_target(self):
        """Load calibration target for visualization."""
        try:
            # Open file dialog to select target file
            file_path, _ = QFileDialog.getOpenFileName(
                self, 
                "Select Calibration Target File",
                str(self.ptv_core.exp_path / "cal"),
                "Target Files (*.txt)"
            )
            
            if file_path:
                # Load target data
                target_data = np.loadtxt(file_path)
                
                # Extract coordinates (expected format: id, x, y, z)
                if target_data.shape[1] >= 4:  # Has at least 4 columns
                    self.target_points = target_data[:, 1:4]  # Extract x, y, z
                    
                    # Add target points to visualization
                    self.canvas.add_target_points(self.target_points)
                    
                    # Update title with target information
                    current_title = self.canvas.axes.get_title()
                    self.canvas.set_title(f"{current_title} + Target ({len(self.target_points)} points)")
                    
        except Exception as e:
            self.canvas.set_title(f"Error loading target: {e}")
            print(f"Error loading calibration target: {e}")
    
    @Slot()
    def update_visualization(self):
        """Update the trajectory visualization based on current settings."""
        if not self.trajectories:
            return
            
        # Get display parameters
        color_map = {
            0: "trajectory_id",
            1: "velocity",
            2: "frame"
        }
        color_by = color_map.get(self.color_by.currentIndex(), "trajectory_id")
        show_heads = self.show_heads.isChecked()
        head_size = self.point_size.value()
        line_width = self.line_width.value() / 2.0  # Scale down for better appearance
        
        # Update the plot
        self.canvas.plot_trajectories(
            self.trajectories,
            color_by=color_by,
            show_heads=show_heads,
            head_size=head_size,
            line_width=line_width
        )
        
        # Re-add target points if they exist
        if self.target_points is not None:
            self.canvas.add_target_points(self.target_points)
    
    @Slot()
    def update_view(self):
        """Update the 3D view based on slider values."""
        elev = self.elev_slider.value()
        azim = self.azim_slider.value()
        self.canvas.set_view_angle(elev, azim)
    
    def set_preset_view(self, elev, azim):
        """Set a preset view angle."""
        self.elev_slider.setValue(elev)
        self.azim_slider.setValue(azim)
        self.canvas.set_view_angle(elev, azim)
    
    @Slot()
    def export_image(self):
        """Export the current visualization as an image."""
        try:
            # Open file dialog to select save location
            file_path, _ = QFileDialog.getSaveFileName(
                self, 
                "Save Visualization",
                str(self.ptv_core.exp_path / "res/visualization.png"),
                "PNG Images (*.png);;JPEG Images (*.jpg);;PDF Files (*.pdf)"
            )
            
            if file_path:
                # Save the figure
                self.canvas.fig.savefig(file_path, dpi=300, bbox_inches='tight')
                print(f"Visualization saved to {file_path}")
        
        except Exception as e:
            print(f"Error exporting image: {e}")
    
    @Slot()
    def export_to_paraview(self):
        """Export trajectories to ParaView format."""
        try:
            # Get frame range from controls
            start_frame = self.start_frame.value()
            end_frame = self.end_frame.value()
            
            # Use PTV core to export
            if self.ptv_core.export_to_paraview(start_frame, end_frame):
                print("Successfully exported trajectories for ParaView")
            else:
                print("Error exporting trajectories")
        
        except Exception as e:
            print(f"Error exporting to ParaView: {e}")