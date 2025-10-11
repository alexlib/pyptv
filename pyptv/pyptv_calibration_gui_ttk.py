"""
Copyright (c) 2008-2013, Tel Aviv University
Copyright (c) 2013 - the OpenPTV team
The software is distributed under the terms of MIT-like license
http://opensource.org/licenses/MIT
"""

import os
import shutil
import re
from pathlib import Path
from typing import Union, List, Optional
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Circle
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import threading

from pyptv import ptv
from pyptv.experiment import Experiment
from pyptv.parameter_manager import ParameterManager

# recognized names for the flags:
NAMES = ["cc", "xh", "yh", "k1", "k2", "k3", "p1", "p2", "scale", "shear"]
SCALE = 5000


class MatplotlibImageDisplay:
    """Matplotlib-based image display widget for calibration"""

    def __init__(self, parent, camera_name: str):
        self.parent = parent
        self.camera_name = camera_name
        self.cameraN = 0

        # Create matplotlib figure
        self.figure = plt.Figure(figsize=(6, 4), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_title(f"Camera {camera_name}")
        self.ax.axis('off')

        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.figure, master=parent)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill=tk.BOTH, expand=True)

        # Store data
        self.image_data = None
        self._x = []
        self._y = []
        self.man_ori = [1, 2, 3, 4]
        self.crosses = []
        self.text_overlays = []

        # Connect click events
        self.canvas.mpl_connect('button_press_event', self.on_click)

    def on_click(self, event):
        """Handle mouse click events"""
        if event.xdata is not None and event.ydata is not None:
            if len(self._x) < 4:
                self._x.append(event.xdata)
                self._y.append(event.ydata)
                self.draw_crosses()
                self.draw_text_overlays()
                print(f"Camera {self.camera_name}: Click {len(self._x)} at ({event.xdata:.1f}, {event.ydata:.1f})")

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

    def draw_crosses(self, x_coords: Optional[List] = None, y_coords: Optional[List] = None,
                    color: str = "red", size: int = 5):
        """Draw crosses at specified coordinates"""
        if x_coords is None:
            x_coords = self._x
        if y_coords is None:
            y_coords = self._y

        # Clear existing crosses
        for cross in self.crosses:
            cross.remove()
        self.crosses = []

        for x, y in zip(x_coords, y_coords):
            # Draw cross as two lines
            h_line = self.ax.axhline(y=y, xmin=(x-size/2)/self.image_data.shape[1] if self.image_data is not None else 0,
                                   xmax=(x+size/2)/self.image_data.shape[1] if self.image_data is not None else 1,
                                   color=color, linewidth=1)
            v_line = self.ax.axvline(x=x, ymin=(y-size/2)/self.image_data.shape[0] if self.image_data is not None else 0,
                                   ymax=(y+size/2)/self.image_data.shape[0] if self.image_data is not None else 1,
                                   color=color, linewidth=1)
            self.crosses.extend([h_line, v_line])

        self.canvas.draw()

    def draw_text_overlays(self, x_coords: Optional[List] = None, y_coords: Optional[List] = None,
                          texts: Optional[List] = None, text_color: str = "white", border_color: str = "red"):
        """Draw text overlays at specified coordinates"""
        if x_coords is None:
            x_coords = self._x
        if y_coords is None:
            y_coords = self._y
        if texts is None:
            texts = self.man_ori

        # Clear existing text overlays
        for text in self.text_overlays:
            text.remove()
        self.text_overlays = []

        for x, y, text in zip(x_coords, y_coords, texts):
            text_obj = self.ax.text(x, y, str(text), color=text_color,
                                  bbox=dict(boxstyle="round,pad=0.3", facecolor=border_color, alpha=0.7),
                                  ha='center', va='center', fontsize=8)
            self.text_overlays.append(text_obj)

        self.canvas.draw()

    def clear_overlays(self):
        """Clear all overlays"""
        for cross in self.crosses:
            cross.remove()
        for text in self.text_overlays:
            text.remove()
        self.crosses = []
        self.text_overlays = []
        self._x = []
        self._y = []
        self.canvas.draw()


class CalibrationGUI(ttk.Frame):
    """TTK-based Calibration GUI"""

    def __init__(self, parent, yaml_path: Union[Path, str]):
        super().__init__(parent)
        self.parent = parent
        self.yaml_path = Path(yaml_path).resolve()
        self.working_folder = self.yaml_path.parent

        # Initialize experiment
        self.experiment = None
        self.num_cams = 0
        self.camera_displays = []
        self.cal_images = []
        self.detections = None
        self.cals = []
        self.sorted_targs = []

        # Status tracking
        self.pass_init = False
        self.pass_sortgrid = False
        self.pass_raw_orient = False

        # Multiplane parameters
        self.MultiParams = None

        self.setup_ui()
        self.initialize_experiment()

    def setup_ui(self):
        """Setup the user interface"""
        # Main layout
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left panel - Controls
        left_panel = ttk.Frame(main_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        # Control buttons
        control_frame = ttk.LabelFrame(left_panel, text="Calibration Controls", padding=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))

        # Basic operations
        ttk.Button(control_frame, text="Load Images/Parameters",
                  command=self.load_images_parameters).pack(fill=tk.X, pady=2)
        self.btn_detection = ttk.Button(control_frame, text="Detection",
                                      command=self.run_detection, state=tk.DISABLED)
        self.btn_detection.pack(fill=tk.X, pady=2)

        # Orientation methods
        ttk.Button(control_frame, text="Manual Orientation",
                  command=self.manual_orientation, state=tk.DISABLED).pack(fill=tk.X, pady=2)
        ttk.Button(control_frame, text="Orientation with File",
                  command=self.orientation_with_file, state=tk.DISABLED).pack(fill=tk.X, pady=2)
        ttk.Button(control_frame, text="Show Initial Guess",
                  command=self.show_initial_guess, state=tk.DISABLED).pack(fill=tk.X, pady=2)

        # Advanced operations
        self.btn_sort_grid = ttk.Button(control_frame, text="Sort Grid",
                                       command=self.sort_grid, state=tk.DISABLED)
        self.btn_sort_grid.pack(fill=tk.X, pady=2)
        self.btn_raw_orient = ttk.Button(control_frame, text="Raw Orientation",
                                        command=self.raw_orientation, state=tk.DISABLED)
        self.btn_raw_orient.pack(fill=tk.X, pady=2)
        self.btn_fine_orient = ttk.Button(control_frame, text="Fine Tuning",
                                         command=self.fine_tuning, state=tk.DISABLED)
        self.btn_fine_orient.pack(fill=tk.X, pady=2)

        # Special methods
        ttk.Button(control_frame, text="Orientation from Dumbbell",
                  command=self.orientation_dumbbell, state=tk.DISABLED).pack(fill=tk.X, pady=2)
        ttk.Button(control_frame, text="Orientation with Particles",
                  command=self.orientation_particles, state=tk.DISABLED).pack(fill=tk.X, pady=2)
        ttk.Button(control_frame, text="Restore ORI Files",
                  command=self.restore_ori_files, state=tk.DISABLED).pack(fill=tk.X, pady=2)

        # Parameter editing
        param_frame = ttk.LabelFrame(left_panel, text="Parameter Editing", padding=10)
        param_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(param_frame, text="Edit Calibration Parameters",
                  command=self.edit_cal_parameters).pack(fill=tk.X, pady=2)
        ttk.Button(param_frame, text="Edit ORI Files",
                  command=self.edit_ori_files).pack(fill=tk.X, pady=2)
        ttk.Button(param_frame, text="Edit Addpar Files",
                  command=self.edit_addpar_files).pack(fill=tk.X, pady=2)

        # Options
        options_frame = ttk.LabelFrame(left_panel, text="Options", padding=10)
        options_frame.pack(fill=tk.X, pady=(10, 0))

        self.splitter_var = tk.BooleanVar()
        ttk.Checkbutton(options_frame, text="Split into 4?", variable=self.splitter_var).pack(anchor=tk.W)

        # Right panel - Camera displays
        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Tabbed interface for cameras
        self.camera_notebook = ttk.Notebook(right_panel)
        self.camera_notebook.pack(fill=tk.BOTH, expand=True)

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def initialize_experiment(self):
        """Initialize the experiment from YAML file"""
        try:
            pm = ParameterManager()
            pm.from_yaml(self.yaml_path)
            self.experiment = Experiment(pm=pm)
            self.experiment.populate_runs(self.working_folder)

            ptv_params = self.experiment.get_parameter('ptv')
            if ptv_params is None:
                raise ValueError("PTV parameters not found")

            self.num_cams = self.experiment.get_n_cam()

            # Create camera display tabs
            for i in range(self.num_cams):
                frame = ttk.Frame(self.camera_notebook)
                self.camera_notebook.add(frame, text=f"Camera {i+1}")

                display = MatplotlibImageDisplay(frame, f"Camera {i+1}")
                display.cameraN = i
                self.camera_displays.append(display)

            self.status_var.set("Experiment initialized successfully")

        except Exception as e:
            messagebox.showerror("Initialization Error", f"Failed to initialize experiment: {e}")
            self.status_var.set("Initialization failed")

    def get_parameter(self, key: str):
        """Get parameter from experiment"""
        params = self.experiment.get_parameter(key)
        if params is None:
            raise KeyError(f"Parameter '{key}' not found")
        return params

    def load_images_parameters(self):
        """Load images and parameters"""
        try:
            self.status_var.set("Loading images and parameters...")

            # Load parameters
            (self.cpar, self.spar, self.vpar, self.track_par,
             self.tpar, self.cals, self.epar) = ptv.py_start_proc_c(self.experiment.pm)

            # Check for multiplane
            if self.epar.get('Combine_Flag', False):
                self.MultiParams = self.get_parameter('multi_planes')
                for i in range(self.MultiParams['n_planes']):
                    print(self.MultiParams['plane_name'][i])
                self.pass_raw_orient = True
                self.status_var.set("Multiplane calibration loaded")

            ptv_params = self.experiment.pm.get_parameter('ptv')

            # Load calibration images
            if self.get_parameter('cal_ori').get('cal_splitter') or self.splitter_var.get():
                print("Using splitter in Calibration")
                imname = self.get_parameter('cal_ori')['img_cal_name'][0]
                if Path(imname).exists():
                    print(f"Splitting calibration image: {imname}")
                    temp_img = np.array(Image.open(imname))
                    if temp_img.ndim > 2:
                        temp_img = np.mean(temp_img, axis=2).astype(np.uint8)
                    # Simple splitter simulation - in real implementation use ptv.image_split
                    h, w = temp_img.shape
                    split_images = [
                        temp_img[:h//2, :w//2],
                        temp_img[:h//2, w//2:],
                        temp_img[h//2:, :w//2],
                        temp_img[h//2:, w//2:]
                    ]
                    self.cal_images = split_images[:self.num_cams]
                else:
                    print(f"Calibration image not found: {imname}")
                    for i in range(self.num_cams):
                        self.cal_images.append(np.zeros((ptv_params['imy'], ptv_params['imx']), dtype=np.uint8))
            else:
                for i in range(self.num_cams):
                    imname = self.get_parameter('cal_ori')['img_cal_name'][i]
                    if Path(imname).exists():
                        img = np.array(Image.open(imname))
                        if img.ndim > 2:
                            img = np.mean(img, axis=2).astype(np.uint8)
                        self.cal_images.append(img)
                    else:
                        print(f"Calibration image not found: {imname}")
                        self.cal_images.append(np.zeros((ptv_params['imy'], ptv_params['imx']), dtype=np.uint8))

            # Update displays
            for i, display in enumerate(self.camera_displays):
                display.update_image(self.cal_images[i])

            # Load manual orientation numbers
            man_ori_params = self.get_parameter('man_ori')
            for i in range(self.num_cams):
                for j in range(4):
                    self.camera_displays[i].man_ori[j] = man_ori_params['nr'][i*4+j]

            self.pass_init = True
            self.enable_buttons()
            self.status_var.set("Images and parameters loaded successfully")

        except Exception as e:
            messagebox.showerror("Loading Error", f"Failed to load images/parameters: {e}")
            self.status_var.set("Loading failed")

    def enable_buttons(self):
        """Enable buttons after initialization"""
        self.btn_detection.config(state=tk.NORMAL)

        # Enable orientation buttons
        for child in self.winfo_children():
            if isinstance(child, ttk.Frame):
                for frame_child in child.winfo_children():
                    if isinstance(frame_child, ttk.LabelFrame):
                        for button in frame_child.winfo_children():
                            if isinstance(button, ttk.Button) and "Load Images" not in button.cget('text'):
                                button.config(state=tk.NORMAL)

    def run_detection(self):
        """Run detection on calibration images"""
        if not self.pass_init:
            messagebox.showwarning("Warning", "Please load images and parameters first")
            return

        try:
            self.status_var.set("Running detection...")

            # Preprocessing if needed
            if self.cpar.get_hp_flag():
                for i, im in enumerate(self.cal_images):
                    self.cal_images[i] = ptv.preprocess_image(im.copy(), 1, self.cpar, 25)

            # Update displays
            for i, display in enumerate(self.camera_displays):
                display.update_image(self.cal_images[i])

            # Get parameters for detection
            ptv_params = self.get_parameter('ptv')
            target_params_dict = {'detect_plate': self.get_parameter('detect_plate')}

            # Run detection
            self.detections, corrected = ptv.py_detection_proc_c(
                self.num_cams, self.cal_images, ptv_params, target_params_dict
            )

            # Draw detected points
            x_coords = [[i.pos()[0] for i in row] for row in self.detections]
            y_coords = [[i.pos()[1] for i in row] for row in self.detections]

            for i, display in enumerate(self.camera_displays):
                display.draw_crosses(x_coords[i], y_coords[i], "blue", 4)

            self.status_var.set("Detection completed")

        except Exception as e:
            messagebox.showerror("Detection Error", f"Detection failed: {e}")
            self.status_var.set("Detection failed")

    def manual_orientation(self):
        """Handle manual orientation"""
        points_set = True
        for i, display in enumerate(self.camera_displays):
            if len(display._x) < 4:
                print(f"Camera {i+1}: Not enough points ({len(display._x)}/4)")
                points_set = False
            else:
                print(f"Camera {i+1}: {len(display._x)} points set")

        if points_set:
            # Save coordinates to YAML
            man_ori_coords = {}
            for i, display in enumerate(self.camera_displays):
                cam_key = f'camera_{i}'
                man_ori_coords[cam_key] = {}
                for j in range(4):
                    point_key = f'point_{j + 1}'
                    man_ori_coords[cam_key][point_key] = {
                        'x': float(display._x[j]),
                        'y': float(display._y[j])
                    }

            self.experiment.pm.parameters['man_ori_coordinates'] = man_ori_coords
            self.experiment.save_parameters()
            self.status_var.set("Manual orientation coordinates saved")
        else:
            self.status_var.set("Click on 4 points in each camera for manual orientation")

    def orientation_with_file(self):
        """Load orientation from file/YAML"""
        try:
            man_ori_coords = self.experiment.pm.parameters.get('man_ori_coordinates', {})

            if not man_ori_coords:
                self.status_var.set("No manual orientation coordinates found")
                return

            for i, display in enumerate(self.camera_displays):
                cam_key = f'camera_{i}'
                display._x = []
                display._y = []

                if cam_key in man_ori_coords:
                    for j in range(4):
                        point_key = f'point_{j + 1}'
                        if point_key in man_ori_coords[cam_key]:
                            point_data = man_ori_coords[cam_key][point_key]
                            display._x.append(float(point_data['x']))
                            display._y.append(float(point_data['y']))
                        else:
                            display._x.append(0.0)
                            display._y.append(0.0)
                else:
                    for j in range(4):
                        display._x.append(0.0)
                        display._y.append(0.0)

                display.draw_crosses()
                display.draw_text_overlays()

            self.status_var.set("Manual orientation coordinates loaded")

        except Exception as e:
            messagebox.showerror("Loading Error", f"Failed to load orientation: {e}")

    def show_initial_guess(self):
        """Show initial guess for calibration"""
        try:
            self.status_var.set("Showing initial guess...")

            cal_points = self._read_cal_points()

            self.cals = []
            for i_cam in range(self.num_cams):
                from optv.calibration import Calibration
                cal = Calibration()
                tmp = self.get_parameter('cal_ori')['img_ori'][i_cam]
                cal.from_file(tmp, tmp.replace(".ori", ".addpar"))
                self.cals.append(cal)

            for i_cam in range(self.num_cams):
                self._project_cal_points(i_cam, "orange")

            self.status_var.set("Initial guess displayed")

        except Exception as e:
            messagebox.showerror("Initial Guess Error", f"Failed to show initial guess: {e}")

    def _read_cal_points(self):
        """Read calibration points from file"""
        from optv.imgcoord import image_coordinates
        from optv.transforms import convert_arr_metric_to_pixel

        fixp_name = self.get_parameter('cal_ori')['fixp_name']
        return np.atleast_1d(
            np.loadtxt(
                str(fixp_name),
                dtype=[("id", "i4"), ("pos", "3f8")],
                skiprows=0,
            )
        )

    def _project_cal_points(self, i_cam: int, color: str = "orange"):
        """Project calibration points to camera view"""
        from optv.imgcoord import image_coordinates
        from optv.transforms import convert_arr_metric_to_pixel

        x, y, pnr = [], [], []
        for row in self.cal_points:
            projected = image_coordinates(
                np.atleast_2d(row["pos"]),
                self.cals[i_cam],
                self.cpar.get_multimedia_params(),
            )
            pos = convert_arr_metric_to_pixel(projected, self.cpar)

            x.append(pos[0][0])
            y.append(pos[0][1])
            pnr.append(row["id"])

        self.camera_displays[i_cam].draw_crosses(x, y, color, 3)
        self.camera_displays[i_cam].draw_text_overlays(x, y, pnr)

    def sort_grid(self):
        """Sort calibration grid"""
        if self.detections is None:
            messagebox.showwarning("Warning", "Please run detection first")
            return

        try:
            self.status_var.set("Sorting calibration grid...")

            from optv.orientation import match_detection_to_ref

            self.cal_points = self._read_cal_points()
            self.sorted_targs = []

            for i_cam in range(self.num_cams):
                targs = match_detection_to_ref(
                    self.cals[i_cam],
                    self.cal_points["pos"],
                    self.detections[i_cam],
                    self.cpar,
                )
                x, y, pnr = [], [], []
                for t in targs:
                    if t.pnr() != -999:
                        pnr.append(self.cal_points["id"][t.pnr()])
                        x.append(t.pos()[0])
                        y.append(t.pos()[1])

                self.sorted_targs.append(targs)
                self.camera_displays[i_cam].clear_overlays()
                self.camera_displays[i_cam].draw_text_overlays(x, y, pnr)

            self.pass_sortgrid = True
            self.btn_raw_orient.config(state=tk.NORMAL)
            self.status_var.set("Grid sorting completed")

        except Exception as e:
            messagebox.showerror("Sort Grid Error", f"Failed to sort grid: {e}")

    def raw_orientation(self):
        """Perform raw orientation"""
        try:
            self.status_var.set("Performing raw orientation...")

            from optv.orientation import external_calibration

            self._backup_ori_files()

            for i_cam in range(self.num_cams):
                selected_points = np.zeros((4, 3))
                for i, cp_id in enumerate(self.cal_points["id"]):
                    for j in range(4):
                        if cp_id == self.camera_displays[i_cam].man_ori[j]:
                            selected_points[j, :] = self.cal_points["pos"][i, :]
                            continue

                manual_detection_points = np.array(
                    (self.camera_displays[i_cam]._x, self.camera_displays[i_cam]._y)
                ).T

                success = external_calibration(
                    self.cals[i_cam],
                    selected_points,
                    manual_detection_points,
                    self.cpar,
                )

                if success is False:
                    print(f"Initial guess failed for camera {i_cam}")
                else:
                    self.camera_displays[i_cam].clear_overlays()
                    self._project_cal_points(i_cam, color="red")
                    self._write_ori(i_cam)

            self.pass_raw_orient = True
            self.btn_fine_orient.config(state=tk.NORMAL)
            self.status_var.set("Raw orientation completed")

        except Exception as e:
            messagebox.showerror("Raw Orientation Error", f"Raw orientation failed: {e}")

    def fine_tuning(self):
        """Perform fine tuning of calibration"""
        try:
            self.status_var.set("Performing fine tuning...")

            from optv.orientation import full_calibration

            orient_params = self.get_parameter('orient')
            flags = [name for name in NAMES if orient_params.get(name) == 1]

            self._backup_ori_files()

            for i_cam in range(self.num_cams):
                if self.epar.get('Combine_Flag', False):
                    # Multiplane handling - simplified for now
                    targs = self.sorted_targs[i_cam]
                else:
                    targs = self.sorted_targs[i_cam]

                try:
                    print(f"Calibrating camera {i_cam} with flags: {flags}")
                    residuals, targ_ix, err_est = full_calibration(
                        self.cals[i_cam],
                        self.cal_points["pos"],
                        targs,
                        self.cpar,
                        flags,
                    )
                except Exception:
                    print(f"OPTV calibration failed for camera {i_cam}, trying scipy")
                    residuals = ptv.full_scipy_calibration(
                        self.cals[i_cam],
                        self.cal_points["pos"],
                        targs,
                        self.cpar,
                        flags=flags,
                    )
                    targ_ix = [t.pnr() for t in targs if t.pnr() != -999]

                self._write_ori(i_cam, addpar_flag=True)

                x, y = [], []
                for t in targ_ix:
                    if t != -999:
                        pos = targs[t].pos()
                        x.append(pos[0])
                        y.append(pos[1])

                self.camera_displays[i_cam].clear_overlays()
                self.camera_displays[i_cam].draw_crosses(x, y, "orange", 5)

            self.status_var.set("Fine tuning completed")

        except Exception as e:
            messagebox.showerror("Fine Tuning Error", f"Fine tuning failed: {e}")

    def orientation_dumbbell(self):
        """Orientation using dumbbell method"""
        try:
            self.status_var.set("Performing dumbbell orientation...")
            self._backup_ori_files()
            ptv.py_calibration(12, self)
            self.status_var.set("Dumbbell orientation completed")
        except Exception as e:
            messagebox.showerror("Dumbbell Orientation Error", f"Dumbbell orientation failed: {e}")

    def orientation_particles(self):
        """Orientation using particle tracking"""
        try:
            self.status_var.set("Performing particle orientation...")
            self._backup_ori_files()
            targs_all, targ_ix_all, residuals_all = ptv.py_calibration(10, self)
            self.status_var.set("Particle orientation completed")
        except Exception as e:
            messagebox.showerror("Particle Orientation Error", f"Particle orientation failed: {e}")

    def restore_ori_files(self):
        """Restore original orientation files"""
        try:
            self.status_var.set("Restoring ORI files...")
            for f in self.get_parameter('cal_ori')['img_ori'][:self.num_cams]:
                print(f"Restoring {f}")
                shutil.copyfile(f + ".bck", f)
                g = f.replace("ori", "addpar")
                shutil.copyfile(g + ".bck", g)
            self.status_var.set("ORI files restored")
        except Exception as e:
            messagebox.showerror("Restore Error", f"Failed to restore ORI files: {e}")

    def edit_cal_parameters(self):
        """Edit calibration parameters"""
        try:
            from pyptv.parameter_gui_ttk import CalibParamsWindow
            # This now opens the new TTK-based window
            CalibParamsWindow(self, self.experiment)
        except Exception as e:
            messagebox.showerror("Parameter Edit Error", f"Failed to open parameter editor: {e}")

    def edit_ori_files(self):
        """Edit orientation files"""
        try:
            from pyptv.code_editor import open_ori_editors
            open_ori_editors(self.experiment, self)
        except Exception as e:
            messagebox.showerror("ORI Editor Error", f"Failed to open ORI editor: {e}")

    def edit_addpar_files(self):
        """Edit additional parameter files"""
        try:
            from pyptv.code_editor import open_addpar_editors
            open_addpar_editors(self.experiment, self)
        except Exception as e:
            messagebox.showerror("Addpar Editor Error", f"Failed to open addpar editor: {e}")

    def _backup_ori_files(self):
        """Backup orientation files"""
        for f in self.get_parameter('cal_ori')['img_ori'][:self.num_cams]:
            print(f"Backing up {f}")
            shutil.copyfile(f, f + ".bck")
            g = f.replace("ori", "addpar")
            shutil.copyfile(g, g + ".bck")

    def _write_ori(self, i_cam: int, addpar_flag: bool = False):
        """Write orientation file"""
        tmp = np.array([
            self.cals[i_cam].get_pos(),
            self.cals[i_cam].get_angles(),
            self.cals[i_cam].get_affine(),
            self.cals[i_cam].get_decentering(),
            self.cals[i_cam].get_radial_distortion(),
        ], dtype=object)

        if np.any(np.isnan(np.hstack(tmp))):
            raise ValueError(f"Calibration parameters for camera {i_cam} contain NaNs")

        ori = self.get_parameter('cal_ori')['img_ori'][i_cam]
        if addpar_flag:
            addpar = ori.replace("ori", "addpar")
        else:
            addpar = "tmp.addpar"

        print(f"Saving: {ori}, {addpar}")
        self.cals[i_cam].write(ori.encode(), addpar.encode())


def create_calibration_gui(yaml_path: Union[Path, str]) -> tk.Toplevel:
    """Create and return a calibration GUI window"""
    window = tk.Toplevel()
    window.title("PyPTV Calibration")
    window.geometry("1200x800")

    gui = CalibrationGUI(window, yaml_path)
    gui.pack(fill=tk.BOTH, expand=True)

    return window


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python pyptv_calibration_gui_ttk.py <parameters_yaml_file>")
        sys.exit(1)

    yaml_path = Path(sys.argv[1]).resolve()
    if not yaml_path.exists():
        print(f"Error: Parameter file '{yaml_path}' does not exist.")
        sys.exit(1)

    root = tk.Tk()
    root.title("PyPTV Calibration")

    gui = CalibrationGUI(root, yaml_path)
    gui.pack(fill=tk.BOTH, expand=True)

    root.mainloop()
