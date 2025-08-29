"""
Copyright (c) 2008-2013, Tel Aviv University
Copyright (c) 2013 - the OpenPTV team
The software is distributed under the terms of MIT-like license
http://opensource.org/licenses/MIT
"""

import os
from pathlib import Path
from typing import List, Optional
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Polygon
import tkinter as tk
from tkinter import ttk, messagebox

from pyptv import ptv
from pyptv.experiment import Experiment


class MatplotlibImageDisplay:
    """Matplotlib-based image display widget for mask drawing"""

    def __init__(self, parent, camera_name: str):
        self.parent = parent
        self.camera_name = camera_name
        self.cameraN = 0

        # Create matplotlib figure
        self.figure = plt.Figure(figsize=(8, 6), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_title(f"Camera {camera_name}")
        self.ax.axis('off')

        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.figure, master=parent)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill=tk.BOTH, expand=True)

        # Store data
        self.image_data = None
        self.mask_points = []  # List of (x, y) tuples
        self.polygon_patch = None
        self.point_markers = []

        # Connect click events
        self.canvas.mpl_connect('button_press_event', self.on_click)

    def on_click(self, event):
        """Handle mouse click events"""
        if event.xdata is not None and event.ydata is not None:
            if event.button == 1:  # Left click - add point
                self.mask_points.append((event.xdata, event.ydata))
                self.draw_mask_points()
                self.draw_polygon()
                print(f"Camera {self.camera_name}: Added point at ({event.xdata:.1f}, {event.ydata:.1f})")
            elif event.button == 3:  # Right click - remove last point
                if self.mask_points:
                    removed_point = self.mask_points.pop()
                    self.draw_mask_points()
                    self.draw_polygon()
                    print(f"Camera {self.camera_name}: Removed point {removed_point}")

    def update_image(self, image: np.ndarray, is_float: bool = False):
        """Update the displayed image"""
        self.image_data = image
        self.ax.clear()
        self.ax.axis('off')

        if is_float:
            self.ax.imshow(image, cmap='gray')
        else:
            self.ax.imshow(image, cmap='gray')

        self.canvas.draw()

    def draw_mask_points(self):
        """Draw the mask points as crosses"""
        # Clear existing markers
        for marker in self.point_markers:
            marker.remove()
        self.point_markers = []

        for i, (x, y) in enumerate(self.mask_points):
            # Draw cross
            h_line = self.ax.axhline(y=y, xmin=(x-5)/self.image_data.shape[1] if self.image_data is not None else 0,
                                   xmax=(x+5)/self.image_data.shape[1] if self.image_data is not None else 1,
                                   color='red', linewidth=2)
            v_line = self.ax.axvline(x=x, ymin=(y-5)/self.image_data.shape[0] if self.image_data is not None else 0,
                                   ymax=(y+5)/self.image_data.shape[0] if self.image_data is not None else 1,
                                   color='red', linewidth=2)
            self.point_markers.extend([h_line, v_line])

            # Draw point number
            text = self.ax.text(x+10, y-10, str(i+1), color='white',
                              bbox=dict(boxstyle="round,pad=0.3", facecolor='red', alpha=0.7),
                              ha='center', va='center', fontsize=8)
            self.point_markers.append(text)

        self.canvas.draw()

    def draw_polygon(self):
        """Draw the polygon connecting the mask points"""
        # Remove existing polygon
        if self.polygon_patch is not None:
            self.polygon_patch.remove()
            self.polygon_patch = None

        if len(self.mask_points) >= 3:
            # Create polygon patch
            polygon = Polygon(self.mask_points, facecolor='cyan', edgecolor='blue',
                            alpha=0.5, linewidth=2)
            self.ax.add_patch(polygon)
            self.polygon_patch = polygon

        self.canvas.draw()

    def clear_mask(self):
        """Clear all mask points and polygon"""
        self.mask_points = []

        # Clear markers
        for marker in self.point_markers:
            marker.remove()
        self.point_markers = []

        # Clear polygon
        if self.polygon_patch is not None:
            self.polygon_patch.remove()
            self.polygon_patch = None

        self.canvas.draw()

    def get_mask_points(self) -> List[tuple]:
        """Get the current mask points"""
        return self.mask_points.copy()


class MaskGUI(ttk.Frame):
    """TTK-based Mask Drawing GUI"""

    def __init__(self, parent, experiment: Experiment):
        super().__init__(parent)
        self.parent = parent
        self.experiment = experiment
        self.active_path = Path(experiment.active_params.yaml_path).parent
        self.working_folder = self.active_path.parent

        # Initialize state
        self.num_cams = 0
        self.camera_displays = []
        self.images = []
        self.mask_files = []
        self.pass_init = False

        self.setup_ui()
        self.initialize_cameras()

    def setup_ui(self):
        """Setup the user interface"""
        # Main layout
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left panel - Controls
        left_panel = ttk.Frame(main_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        # Control buttons
        control_frame = ttk.LabelFrame(left_panel, text="Mask Controls", padding=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(control_frame, text="Load Images",
                  command=self.load_images).pack(fill=tk.X, pady=2)

        self.btn_draw_mask = ttk.Button(control_frame, text="Draw and Store Mask",
                                       command=self.draw_and_store_mask, state=tk.DISABLED)
        self.btn_draw_mask.pack(fill=tk.X, pady=2)

        ttk.Button(control_frame, text="Clear Mask",
                  command=self.clear_mask).pack(fill=tk.X, pady=2)

        # Instructions
        instr_frame = ttk.LabelFrame(left_panel, text="Instructions", padding=10)
        instr_frame.pack(fill=tk.X, pady=(10, 0))

        instructions = """
• Load images first
• Left click to add mask points
• Right click to remove last point
• Draw polygon around areas to mask
• Save mask when complete
• Avoid crossing lines
        """.strip()

        instr_label = ttk.Label(instr_frame, text=instructions, justify=tk.LEFT)
        instr_label.pack(anchor=tk.W)

        # Right panel - Camera displays
        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Tabbed interface for cameras
        self.camera_notebook = ttk.Notebook(right_panel)
        self.camera_notebook.pack(fill=tk.BOTH, expand=True)

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready - Load images to start")
        status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def initialize_cameras(self):
        """Initialize camera displays based on experiment"""
        try:
            ptv_params = self.experiment.get_parameter('ptv')
            if ptv_params is None:
                raise ValueError("Failed to load PTV parameters")

            self.num_cams = self.experiment.get_n_cam()

            # Create camera display tabs
            for i in range(self.num_cams):
                frame = ttk.Frame(self.camera_notebook)
                self.camera_notebook.add(frame, text=f"Camera {i+1}")

                display = MatplotlibImageDisplay(frame, f"Camera {i+1}")
                display.cameraN = i
                self.camera_displays.append(display)

            self.status_var.set(f"Initialized {self.num_cams} cameras")

        except Exception as e:
            messagebox.showerror("Initialization Error", f"Failed to initialize cameras: {e}")
            self.status_var.set("Initialization failed")

    def load_images(self):
        """Load images for all cameras"""
        try:
            self.status_var.set("Loading images...")

            # Change to working directory
            os.chdir(self.working_folder)

            # Load parameters
            (self.cpar, self.spar, self.vpar, self.track_par,
             self.tpar, self.cals, self.epar) = ptv.py_start_proc_c(self.experiment.pm)

            # Load images
            self.images = []
            ptv_params = self.experiment.get_parameter('ptv')

            for i in range(self.num_cams):
                imname = ptv_params['img_name'][i]
                if Path(imname).exists():
                    from skimage.io import imread
                    from skimage.util import img_as_ubyte
                    from skimage.color import rgb2gray

                    im = imread(imname)
                    if im.ndim > 2:
                        im = rgb2gray(im[:, :, :3])
                    im = img_as_ubyte(im)
                    self.images.append(im)
                else:
                    # Create blank image if file doesn't exist
                    h_img = ptv_params['imy']
                    w_img = ptv_params['imx']
                    im = np.zeros((h_img, w_img), dtype=np.uint8)
                    self.images.append(im)

            # Update displays
            for i, display in enumerate(self.camera_displays):
                display.update_image(self.images[i])

            self.pass_init = True
            self.btn_draw_mask.config(state=tk.NORMAL)
            self.status_var.set("Images loaded successfully")

        except Exception as e:
            messagebox.showerror("Loading Error", f"Failed to load images: {e}")
            self.status_var.set("Loading failed")

    def draw_and_store_mask(self):
        """Draw and store mask polygons"""
        try:
            # Check if all cameras have enough points
            points_set = True
            total_points = 0

            for i, display in enumerate(self.camera_displays):
                points = display.get_mask_points()
                total_points += len(points)
                if len(points) < 3:
                    print(f"Camera {i+1}: Only {len(points)} points (need at least 3)")
                    points_set = False
                else:
                    print(f"Camera {i+1}: {len(points)} points")

            if not points_set:
                self.status_var.set("Each camera needs at least 3 points to create a mask polygon")
                return

            # Create mask files
            self.mask_files = [f"mask_{cam}.txt" for cam in range(self.num_cams)]

            # Save mask points for each camera
            for cam in range(self.num_cams):
                points = self.camera_displays[cam].get_mask_points()
                with open(self.mask_files[cam], "w", encoding="utf-8") as f:
                    for x, y in points:
                        f.write(".6f")

                print(f"Saved mask for camera {cam+1} to {self.mask_files[cam]}")

            self.status_var.set(f"Saved {len(self.mask_files)} mask files with {total_points} total points")

        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save mask: {e}")
            self.status_var.set("Mask save failed")

    def clear_mask(self):
        """Clear all mask points and polygons"""
        for display in self.camera_displays:
            display.clear_mask()

        self.status_var.set("Mask cleared")


def create_mask_gui(experiment: Experiment) -> tk.Toplevel:
    """Create and return a mask GUI window"""
    window = tk.Toplevel()
    window.title("PyPTV Mask Drawing")
    window.geometry("1400x900")

    gui = MaskGUI(window, experiment)
    gui.pack(fill=tk.BOTH, expand=True)

    return window


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python pyptv_mask_gui_ttk.py <yaml_file>")
        sys.exit(1)

    yaml_path = Path(sys.argv[1])
    if not yaml_path.exists():
        print(f"Error: YAML file '{yaml_path}' does not exist.")
        sys.exit(1)

    # Create experiment
    from pyptv.parameter_manager import ParameterManager
    pm = ParameterManager()
    pm.from_yaml(yaml_path)
    experiment = Experiment(pm=pm)

    root = tk.Tk()
    root.title("PyPTV Mask Drawing")

    gui = MaskGUI(root, experiment)
    gui.pack(fill=tk.BOTH, expand=True)

    root.mainloop()
