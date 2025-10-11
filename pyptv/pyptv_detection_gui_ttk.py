"""
Copyright (c) 2008-2013, Tel Aviv University
Copyright (c) 2013 - the OpenPTV team
The GUI software is distributed under the terms of MIT-like license
http://opensource.org/licenses/MIT
"""

import os
import sys
from pathlib import Path
from typing import Optional
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk

from optv.segmentation import target_recognition
from pyptv import ptv


class MatplotlibImageDisplay:
    """Matplotlib-based image display widget for detection"""

    def __init__(self, parent):
        self.parent = parent

        # Create matplotlib figure
        self.figure = plt.Figure(figsize=(8, 6), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_title("Detection View")
        self.ax.axis('off')

        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.figure, master=parent)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill=tk.BOTH, expand=True)

        # Store data
        self.image_data = None
        self.detection_points = []
        self.crosses = []

        # Connect click events (for future use)
        self.canvas.mpl_connect('button_press_event', self.on_click)

    def on_click(self, event):
        """Handle mouse click events"""
        if event.xdata is not None and event.ydata is not None:
            print(f"Click at ({event.xdata:.1f}, {event.ydata:.1f})")

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

    def draw_detection_points(self, x_coords: list, y_coords: list, color: str = "orange", size: int = 8):
        """Draw detected particle positions"""
        # Clear existing detection points
        for cross in self.crosses:
            cross.remove()
        self.crosses = []

        for x, y in zip(x_coords, y_coords):
            # Draw cross as two lines
            h_line = self.ax.axhline(y=y, xmin=(x-size/2)/self.image_data.shape[1] if self.image_data is not None else 0,
                                   xmax=(x+size/2)/self.image_data.shape[1] if self.image_data is not None else 1,
                                   color=color, linewidth=2)
            v_line = self.ax.axvline(x=x, ymin=(y-size/2)/self.image_data.shape[0] if self.image_data is not None else 0,
                                   ymax=(y+size/2)/self.image_data.shape[0] if self.image_data is not None else 1,
                                   color=color, linewidth=2)
            self.crosses.extend([h_line, v_line])

        self.canvas.draw()

    def clear_overlays(self):
        """Clear all overlays"""
        for cross in self.crosses:
            cross.remove()
        self.crosses = []
        self.canvas.draw()


class DetectionGUI(ttk.Frame):
    """TTK-based Detection GUI"""

    def __init__(self, parent, working_directory: Path = Path("tests/test_cavity")):
        super().__init__(parent)
        self.parent = parent
        self.working_directory = working_directory

        # Initialize state variables
        self.parameters_loaded = False
        self.image_loaded = False
        self.raw_image = None
        self.processed_image = None

        # Parameter structures
        self.cpar = None
        self.tpar = None

        # Detection parameters (hardcoded defaults)
        self.thresholds = [40, 0, 0, 0]
        self.pixel_count_bounds = [25, 400]
        self.xsize_bounds = [5, 50]
        self.ysize_bounds = [5, 50]
        self.sum_grey = 100
        self.disco = 100

        # Current parameter values
        self.grey_thresh_val = tk.IntVar(value=40)
        self.min_npix_val = tk.IntVar(value=25)
        self.max_npix_val = tk.IntVar(value=400)
        self.min_npix_x_val = tk.IntVar(value=5)
        self.max_npix_x_val = tk.IntVar(value=50)
        self.min_npix_y_val = tk.IntVar(value=5)
        self.max_npix_y_val = tk.IntVar(value=50)
        self.disco_val = tk.IntVar(value=100)
        self.sum_grey_val = tk.IntVar(value=100)

        # Flags
        self.hp_flag_val = tk.BooleanVar(value=False)
        self.inverse_flag_val = tk.BooleanVar(value=False)

        self.setup_ui()
        self.image_display = MatplotlibImageDisplay(self.image_frame)

    def setup_ui(self):
        """Setup the user interface"""
        # Main layout
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left panel - Controls
        left_panel = ttk.Frame(main_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        # File controls
        file_frame = ttk.LabelFrame(left_panel, text="File Controls", padding=10)
        file_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(file_frame, text="Image file:").pack(anchor=tk.W)
        self.image_name_var = tk.StringVar(value="cal/cam1.tif")
        image_entry = ttk.Entry(file_frame, textvariable=self.image_name_var)
        image_entry.pack(fill=tk.X, pady=(0, 5))

        ttk.Button(file_frame, text="Load Image",
                  command=self.load_image).pack(fill=tk.X, pady=(0, 5))

        # Preprocessing controls
        preproc_frame = ttk.LabelFrame(left_panel, text="Preprocessing", padding=10)
        preproc_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Checkbutton(preproc_frame, text="Highpass filter",
                       variable=self.hp_flag_val,
                       command=self.on_preprocessing_change).pack(anchor=tk.W)
        ttk.Checkbutton(preproc_frame, text="Inverse image",
                       variable=self.inverse_flag_val,
                       command=self.on_preprocessing_change).pack(anchor=tk.W)

        # Detection button
        ttk.Button(left_panel, text="Run Detection",
                  command=self.run_detection).pack(fill=tk.X, pady=(0, 10))

        # Parameter controls
        param_frame = ttk.LabelFrame(left_panel, text="Detection Parameters", padding=10)
        param_frame.pack(fill=tk.X, pady=(0, 10))

        self.slider_configs = {}

        def add_slider(parent, text, var, from_, to, label_widget):
            ttk.Label(parent, text=text).pack(anchor=tk.W)
            frame = ttk.Frame(parent)
            frame.pack(fill=tk.X, pady=(0, 2))
            
            slider = ttk.Scale(frame, from_=from_, to=to, variable=var, command=self.on_param_change)
            slider.pack(side=tk.LEFT, fill=tk.X, expand=True)
            label_widget.pack(side=tk.RIGHT, padx=(5,0))
            
            range_frame = ttk.Frame(parent)
            range_frame.pack(fill=tk.X, pady=(0, 10))
            min_var = tk.StringVar(value=str(from_))
            max_var = tk.StringVar(value=str(to))
            ttk.Label(range_frame, text="Range:").pack(side=tk.LEFT, padx=(10, 5))
            ttk.Entry(range_frame, textvariable=min_var, width=5).pack(side=tk.LEFT)
            ttk.Label(range_frame, text="-").pack(side=tk.LEFT, padx=2)
            ttk.Entry(range_frame, textvariable=max_var, width=5).pack(side=tk.LEFT)

            self.slider_configs[text] = {
                'slider': slider, 'var': var, 'min_var': min_var, 'max_var': max_var
            }

        self.grey_thresh_label = ttk.Label(param_frame, text="40", width=4)
        add_slider(param_frame, "Grey threshold:", self.grey_thresh_val, 1, 255, self.grey_thresh_label)

        self.min_npix_label = ttk.Label(param_frame, text="25", width=4)
        add_slider(param_frame, "Min pixels:", self.min_npix_val, 1, 100, self.min_npix_label)

        self.max_npix_label = ttk.Label(param_frame, text="400", width=4)
        add_slider(param_frame, "Max pixels:", self.max_npix_val, 1, 500, self.max_npix_label)

        self.min_npix_x_label = ttk.Label(param_frame, text="5", width=4)
        add_slider(param_frame, "Min pixels X:", self.min_npix_x_val, 1, 20, self.min_npix_x_label)

        self.max_npix_x_label = ttk.Label(param_frame, text="50", width=4)
        add_slider(param_frame, "Max pixels X:", self.max_npix_x_val, 1, 100, self.max_npix_x_label)

        self.min_npix_y_label = ttk.Label(param_frame, text="5", width=4)
        add_slider(param_frame, "Min pixels Y:", self.min_npix_y_val, 1, 20, self.min_npix_y_label)

        self.max_npix_y_label = ttk.Label(param_frame, text="50", width=4)
        add_slider(param_frame, "Max pixels Y:", self.max_npix_y_val, 1, 100, self.max_npix_y_label)

        self.disco_label = ttk.Label(param_frame, text="100", width=4)
        add_slider(param_frame, "Discontinuity:", self.disco_val, 0, 255, self.disco_label)

        self.sum_grey_label = ttk.Label(param_frame, text="100", width=4)
        add_slider(param_frame, "Sum of grey:", self.sum_grey_val, 50, 200, self.sum_grey_label)

        ttk.Button(param_frame, text="Update Slider Ranges", command=self.update_slider_ranges).pack(fill=tk.X, pady=10)


        # Right panel - Image display
        self.image_frame = ttk.Frame(main_frame)
        self.image_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready - Load parameters and image to start")
        status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Initially disable parameter controls
        self.set_parameter_controls_state(tk.DISABLED)

    def update_slider_ranges(self):
        """Update slider ranges based on user input in the Entry widgets."""
        try:
            for config in self.slider_configs.values():
                slider = config['slider']
                min_val = int(config['min_var'].get())
                max_val = int(config['max_var'].get())
                var = config['var']

                if min_val >= max_val:
                    messagebox.showwarning("Invalid Range", f"Minimum value ({min_val}) must be less than maximum value ({max_val}).")
                    continue

                slider.config(from_=min_val, to=max_val)

                # Ensure current value is within the new range
                current_val = var.get()
                if current_val < min_val:
                    var.set(min_val)
                elif current_val > max_val:
                    var.set(max_val)
            
            self.on_param_change() # Trigger a detection run with the potentially adjusted values
            self.status_var.set("Slider ranges updated.")

        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid integers for slider ranges.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update slider ranges: {e}")

    def set_parameter_controls_state(self, state):
        """Enable/disable parameter controls"""
        for config in self.slider_configs.values():
            config['slider'].config(state=state)

    def load_image(self):
        """Load image and initialize parameters"""
        try:
            image_path = self.working_directory / self.image_name_var.get()
            if not image_path.exists():
                messagebox.showerror("Error", f"Image file not found: {image_path}")
                return

            # Change to working directory
            os.chdir(self.working_directory)

            # Load image
            from skimage.io import imread
            from skimage.util import img_as_ubyte
            from skimage.color import rgb2gray

            self.raw_image = imread(str(image_path))
            if self.raw_image.ndim > 2:
                self.raw_image = rgb2gray(self.raw_image)
            self.raw_image = img_as_ubyte(self.raw_image)

            # Initialize control parameters
            self.cpar = ptv.ControlParams(1)
            self.cpar.set_image_size((self.raw_image.shape[1], self.raw_image.shape[0]))
            self.cpar.set_pixel_size((0.01, 0.01))
            self.cpar.set_hp_flag(self.hp_flag_val.get())

            # Initialize target parameters
            self.tpar = ptv.TargetParams()
            self.tpar.set_grey_thresholds([10, 0, 0, 0])
            self.tpar.set_pixel_count_bounds([1, 50])
            self.tpar.set_xsize_bounds([1, 15])
            self.tpar.set_ysize_bounds([1, 15])
            self.tpar.set_min_sum_grey(100)
            self.tpar.set_max_discontinuity(100)

            self.parameters_loaded = True
            self.image_loaded = True

            # Update parameter controls
            self.update_parameter_controls()
            self.set_parameter_controls_state(True)

            # Process and display image
            self.update_processed_image()
            self.image_display.update_image(self.processed_image)

            # Run initial detection
            self.run_detection()

            self.status_var.set(f"Image loaded: {self.image_name_var.get()}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {e}")
            self.status_var.set(f"Error loading image: {e}")

    def update_processed_image(self):
        """Update processed image based on current settings"""
        if self.raw_image is None:
            return

        # Start with raw image
        im = self.raw_image.copy()

        # Apply inverse flag
        if self.inverse_flag_val.get():
            im = 255 - im

        # Apply highpass filter if enabled
        if self.hp_flag_val.get():
            im = ptv.preprocess_image(im, 0, self.cpar, 25)

        self.processed_image = im

    def update_parameter_controls(self):
        """Update parameter control values and ranges"""
        # Update slider ranges and values
        self.grey_thresh_slider.config(from_=1, to=255)
        self.grey_thresh_val.set(self.thresholds[0])
        self.grey_thresh_label.config(text=str(self.thresholds[0]))

        self.min_npix_slider.config(from_=1, to=100)
        self.min_npix_val.set(self.pixel_count_bounds[0])
        self.min_npix_label.config(text=str(self.pixel_count_bounds[0]))

        self.max_npix_slider.config(from_=1, to=500)
        self.max_npix_val.set(self.pixel_count_bounds[1])
        self.max_npix_label.config(text=str(self.pixel_count_bounds[1]))

        self.min_npix_x_slider.config(from_=1, to=20)
        self.min_npix_x_val.set(self.xsize_bounds[0])
        self.min_npix_x_label.config(text=str(self.xsize_bounds[0]))

        self.max_npix_x_slider.config(from_=1, to=100)
        self.max_npix_x_val.set(self.xsize_bounds[1])
        self.max_npix_x_label.config(text=str(self.xsize_bounds[1]))

        self.min_npix_y_slider.config(from_=1, to=20)
        self.min_npix_y_val.set(self.ysize_bounds[0])
        self.min_npix_y_label.config(text=str(self.ysize_bounds[0]))

        self.max_npix_y_slider.config(from_=1, to=100)
        self.max_npix_y_val.set(self.ysize_bounds[1])
        self.max_npix_y_label.config(text=str(self.ysize_bounds[1]))

        self.disco_slider.config(from_=0, to=255)
        self.disco_val.set(self.disco)
        self.disco_label.config(text=str(self.disco))

        self.sum_grey_slider.config(from_=50, to=200)
        self.sum_grey_val.set(self.sum_grey)
        self.sum_grey_label.config(text=str(self.sum_grey))

    def on_preprocessing_change(self):
        """Handle preprocessing flag changes"""
        if self.image_loaded:
            self.cpar.set_hp_flag(self.hp_flag_val.get())
            self.update_processed_image()
            self.image_display.update_image(self.processed_image)
            self.run_detection()

    def on_param_change(self, event=None):
        """Handle parameter slider changes"""
        if not self.parameters_loaded:
            return

        # Update parameter values
        self.thresholds[0] = self.grey_thresh_val.get()
        self.pixel_count_bounds[0] = self.min_npix_val.get()
        self.pixel_count_bounds[1] = self.max_npix_val.get()
        self.xsize_bounds[0] = self.min_npix_x_val.get()
        self.xsize_bounds[1] = self.max_npix_x_val.get()
        self.ysize_bounds[0] = self.min_npix_y_val.get()
        self.ysize_bounds[1] = self.max_npix_y_val.get()
        self.disco = self.disco_val.get()
        self.sum_grey = self.sum_grey_val.get()

        # Update target parameters
        self.tpar.set_grey_thresholds(self.thresholds)
        self.tpar.set_pixel_count_bounds(self.pixel_count_bounds)
        self.tpar.set_xsize_bounds(self.xsize_bounds)
        self.tpar.set_ysize_bounds(self.ysize_bounds)
        self.tpar.set_min_sum_grey(self.sum_grey)
        self.tpar.set_max_discontinuity(self.disco)

        # Update labels
        self.grey_thresh_label.config(text=str(self.thresholds[0]))
        self.min_npix_label.config(text=str(self.pixel_count_bounds[0]))
        self.max_npix_label.config(text=str(self.pixel_count_bounds[1]))
        self.min_npix_x_label.config(text=str(self.xsize_bounds[0]))
        self.max_npix_x_label.config(text=str(self.xsize_bounds[1]))
        self.min_npix_y_label.config(text=str(self.ysize_bounds[0]))
        self.max_npix_y_label.config(text=str(self.ysize_bounds[1]))
        self.disco_label.config(text=str(self.disco))
        self.sum_grey_label.config(text=str(self.sum_grey))

        # Run detection with new parameters
        self.run_detection()

    def run_detection(self):
        """Run particle detection"""
        if not self.image_loaded or not self.parameters_loaded:
            self.status_var.set("Please load image and parameters first")
            return

        if self.processed_image is None:
            self.status_var.set("No processed image available")
            return

        self.status_var.set("Running detection...")

        try:
            # Run detection
            targs = target_recognition(self.processed_image, self.tpar, 0, self.cpar)
            targs.sort_y()

            # Extract particle positions
            x_coords = [i.pos()[0] for i in targs]
            y_coords = [i.pos()[1] for i in targs]

            # Update display
            self.image_display.clear_overlays()
            self.image_display.draw_detection_points(x_coords, y_coords, "orange", 8)

            # Update status
            self.status_var.set(f"Detected {len(x_coords)} particles")

        except Exception as e:
            self.status_var.set(f"Detection error: {e}")
            messagebox.showerror("Detection Error", f"Detection failed: {e}")


def create_detection_gui(working_directory: Path = Path("tests/test_cavity")) -> tk.Toplevel:
    """Create and return a detection GUI window"""
    window = tk.Toplevel()
    window.title("PyPTV Detection")
    window.geometry("1400x900")

    gui = DetectionGUI(window, working_directory)
    gui.pack(fill=tk.BOTH, expand=True)

    return window


if __name__ == "__main__":
    if len(sys.argv) == 1:
        working_dir = Path("tests/test_cavity")
    else:
        working_dir = Path(sys.argv[1])

    print(f"Loading PyPTV Detection GUI with working directory: {working_dir}")

    root = tk.Tk()
    root.title("PyPTV Detection")

    gui = DetectionGUI(root, working_dir)
    gui.pack(fill=tk.BOTH, expand=True)

    root.mainloop()
