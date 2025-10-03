"""
Copyright (c) 2008-2013, Tel Aviv University
Copyright (c) 2013 - the OpenPTV team
The software is distributed under the terms of MIT-like license
http://opensource.org/licenses/MIT
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional
import numpy as np
from pathlib import Path

from pyptv.experiment import Experiment


class ParameterEditor(ttk.Frame):
    """TTK-based Parameter Editor"""

    def __init__(self, parent, experiment: Experiment, param_type: str = "main"):
        super().__init__(parent)
        self.parent = parent
        self.experiment = experiment
        self.param_type = param_type

        # Initialize parameter values
        self.param_values = {}
        self.load_parameters()

        self.setup_ui()

    def setup_ui(self):
        """Setup the user interface"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        if self.param_type == "main":
            self.setup_main_params()
        elif self.param_type == "calibration":
            self.setup_calibration_params()
        elif self.param_type == "tracking":
            self.setup_tracking_params()

        # Buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        ttk.Button(button_frame, text="Save", command=self.save_parameters).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.RIGHT)

    def setup_main_params(self):
        """Setup main parameters tabs"""
        # General tab
        general_frame = ttk.Frame(self.notebook)
        self.notebook.add(general_frame, text="General")

        self.setup_general_tab(general_frame)

        # Refractive Indices tab
        refractive_frame = ttk.Frame(self.notebook)
        self.notebook.add(refractive_frame, text="Refractive Indices")

        self.setup_refractive_tab(refractive_frame)

        # Particle Recognition tab
        recognition_frame = ttk.Frame(self.notebook)
        self.notebook.add(recognition_frame, text="Particle Recognition")

        self.setup_recognition_tab(recognition_frame)

        # Sequence tab
        sequence_frame = ttk.Frame(self.notebook)
        self.notebook.add(sequence_frame, text="Sequence")

        self.setup_sequence_tab(sequence_frame)

        # Observation Volume tab
        volume_frame = ttk.Frame(self.notebook)
        self.notebook.add(volume_frame, text="Observation Volume")

        self.setup_volume_tab(volume_frame)

        # Criteria tab
        criteria_frame = ttk.Frame(self.notebook)
        self.notebook.add(criteria_frame, text="Criteria")

        self.setup_criteria_tab(criteria_frame)

    def setup_general_tab(self, parent):
        """Setup general parameters tab"""
        # Number of cameras
        ttk.Label(parent, text="Number of cameras:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.num_cams_var = tk.IntVar(value=self.param_values.get('num_cams', 1))
        ttk.Spinbox(parent, from_=1, to=4, textvariable=self.num_cams_var).grid(row=0, column=1, pady=5)

        # Flags
        self.splitter_var = tk.BooleanVar(value=self.param_values.get('splitter', False))
        ttk.Checkbutton(parent, text="Split images into 4?", variable=self.splitter_var).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=5)

        self.allcam_var = tk.BooleanVar(value=self.param_values.get('allcam_flag', False))
        ttk.Checkbutton(parent, text="Accept only points seen from all cameras?", variable=self.allcam_var).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)

        # Image names
        ttk.Label(parent, text="Image Names:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.image_name_vars = []
        for i in range(4):
            var = tk.StringVar(value=self.param_values.get('img_name', [''])[i] if i < len(self.param_values.get('img_name', [])) else '')
            self.image_name_vars.append(var)
            ttk.Entry(parent, textvariable=var).grid(row=4+i, column=0, columnspan=2, sticky=tk.EW, padx=(20, 0))

        # Calibration images
        ttk.Label(parent, text="Calibration Images:").grid(row=8, column=0, sticky=tk.W, pady=5)
        self.cal_image_vars = []
        for i in range(4):
            var = tk.StringVar(value=self.param_values.get('img_cal', [''])[i] if i < len(self.param_values.get('img_cal', [])) else '')
            self.cal_image_vars.append(var)
            ttk.Entry(parent, textvariable=var).grid(row=9+i, column=0, columnspan=2, sticky=tk.EW, padx=(20, 0))

    def setup_refractive_tab(self, parent):
        """Setup refractive indices tab"""
        ttk.Label(parent, text="Refractive Indices:").pack(pady=10)

        frame = ttk.Frame(parent)
        frame.pack(pady=10)

        # Air
        ttk.Label(frame, text="Air:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.air_var = tk.DoubleVar(value=self.param_values.get('mmp_n1', 1.0))
        ttk.Entry(frame, textvariable=self.air_var).grid(row=0, column=1, pady=5)

        # Glass
        ttk.Label(frame, text="Glass:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.glass_var = tk.DoubleVar(value=self.param_values.get('mmp_n2', 1.5))
        ttk.Entry(frame, textvariable=self.glass_var).grid(row=1, column=1, pady=5)

        # Water
        ttk.Label(frame, text="Water:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.water_var = tk.DoubleVar(value=self.param_values.get('mmp_n3', 1.33))
        ttk.Entry(frame, textvariable=self.water_var).grid(row=2, column=1, pady=5)

        # Thickness
        ttk.Label(frame, text="Glass Thickness:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.thickness_var = tk.DoubleVar(value=self.param_values.get('mmp_d', 1.0))
        ttk.Entry(frame, textvariable=self.thickness_var).grid(row=3, column=1, pady=5)

    def setup_recognition_tab(self, parent):
        """Setup particle recognition tab"""
        # Grey thresholds
        ttk.Label(parent, text="Grey Value Thresholds:").pack(pady=5)

        thresh_frame = ttk.Frame(parent)
        thresh_frame.pack(pady=5)

        self.grey_thresh_vars = []
        for i in range(4):
            ttk.Label(thresh_frame, text=f"Camera {i+1}:").grid(row=0, column=i, padx=5)
            var = tk.IntVar(value=self.param_values.get('gvthres', [40]*4)[i] if i < len(self.param_values.get('gvthres', [])) else 40)
            self.grey_thresh_vars.append(var)
            ttk.Spinbox(thresh_frame, from_=0, to=255, textvariable=var).grid(row=1, column=i, padx=5)

        # Particle size parameters
        size_frame = ttk.Frame(parent)
        size_frame.pack(pady=10)

        # Min/Max npix
        ttk.Label(size_frame, text="Min npix:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.min_npix_var = tk.IntVar(value=self.param_values.get('nnmin', 25))
        ttk.Spinbox(size_frame, from_=1, to=1000, textvariable=self.min_npix_var).grid(row=0, column=1, pady=2)

        ttk.Label(size_frame, text="Max npix:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.max_npix_var = tk.IntVar(value=self.param_values.get('nnmax', 400))
        ttk.Spinbox(size_frame, from_=1, to=1000, textvariable=self.max_npix_var).grid(row=1, column=1, pady=2)

        # X direction
        ttk.Label(size_frame, text="Min npix X:").grid(row=0, column=2, sticky=tk.W, pady=2, padx=(10, 0))
        self.min_npix_x_var = tk.IntVar(value=self.param_values.get('nxmin', 5))
        ttk.Spinbox(size_frame, from_=1, to=100, textvariable=self.min_npix_x_var).grid(row=0, column=3, pady=2)

        ttk.Label(size_frame, text="Max npix X:").grid(row=1, column=2, sticky=tk.W, pady=2, padx=(10, 0))
        self.max_npix_x_var = tk.IntVar(value=self.param_values.get('nxmax', 50))
        ttk.Spinbox(size_frame, from_=1, to=100, textvariable=self.max_npix_x_var).grid(row=1, column=3, pady=2)

        # Y direction
        ttk.Label(size_frame, text="Min npix Y:").grid(row=0, column=4, sticky=tk.W, pady=2, padx=(10, 0))
        self.min_npix_y_var = tk.IntVar(value=self.param_values.get('nymin', 5))
        ttk.Spinbox(size_frame, from_=1, to=100, textvariable=self.min_npix_y_var).grid(row=0, column=5, pady=2)

        ttk.Label(size_frame, text="Max npix Y:").grid(row=1, column=4, sticky=tk.W, pady=2, padx=(10, 0))
        self.max_npix_y_var = tk.IntVar(value=self.param_values.get('nymax', 50))
        ttk.Spinbox(size_frame, from_=1, to=100, textvariable=self.max_npix_y_var).grid(row=1, column=5, pady=2)

        # Other parameters
        other_frame = ttk.Frame(parent)
        other_frame.pack(pady=10)

        ttk.Label(other_frame, text="Sum of grey:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.sum_grey_var = tk.IntVar(value=self.param_values.get('sumg_min', 100))
        ttk.Spinbox(other_frame, from_=1, to=1000, textvariable=self.sum_grey_var).grid(row=0, column=1, pady=2)

        ttk.Label(other_frame, text="Discontinuity:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.disco_var = tk.IntVar(value=self.param_values.get('disco', 100))
        ttk.Spinbox(other_frame, from_=0, to=255, textvariable=self.disco_var).grid(row=1, column=1, pady=2)

        ttk.Label(other_frame, text="Cross size:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.cross_size_var = tk.IntVar(value=self.param_values.get('cr_sz', 10))
        ttk.Spinbox(other_frame, from_=1, to=50, textvariable=self.cross_size_var).grid(row=2, column=1, pady=2)

        # Flags
        flags_frame = ttk.Frame(parent)
        flags_frame.pack(pady=10)

        self.hp_var = tk.BooleanVar(value=self.param_values.get('hp_flag', False))
        ttk.Checkbutton(flags_frame, text="High pass filter", variable=self.hp_var).pack(anchor=tk.W)

        self.mask_var = tk.BooleanVar(value=self.param_values.get('mask_flag', False))
        ttk.Checkbutton(flags_frame, text="Subtract mask", variable=self.mask_var).pack(anchor=tk.W)

        self.existing_var = tk.BooleanVar(value=self.param_values.get('existing_target', False))
        ttk.Checkbutton(flags_frame, text="Use existing target files", variable=self.existing_var).pack(anchor=tk.W)

    def setup_sequence_tab(self, parent):
        """Setup sequence parameters tab"""
        # Sequence range
        ttk.Label(parent, text="Sequence Range:").pack(pady=5)

        range_frame = ttk.Frame(parent)
        range_frame.pack(pady=5)

        ttk.Label(range_frame, text="First:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.seq_first_var = tk.IntVar(value=self.param_values.get('first', 1))
        ttk.Spinbox(range_frame, from_=0, to=10000, textvariable=self.seq_first_var).grid(row=0, column=1, pady=2)

        ttk.Label(range_frame, text="Last:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.seq_last_var = tk.IntVar(value=self.param_values.get('last', 100))
        ttk.Spinbox(range_frame, from_=0, to=10000, textvariable=self.seq_last_var).grid(row=1, column=1, pady=2)

        # Base names
        ttk.Label(parent, text="Base Names:").pack(pady=10)

        self.basename_vars = []
        for i in range(4):
            frame = ttk.Frame(parent)
            frame.pack(fill=tk.X, pady=2)

            ttk.Label(frame, text=f"Camera {i+1}:").pack(side=tk.LEFT)
            var = tk.StringVar(value=self.param_values.get('base_name', [''])[i] if i < len(self.param_values.get('base_name', [])) else '')
            self.basename_vars.append(var)
            ttk.Entry(frame, textvariable=var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

    def setup_volume_tab(self, parent):
        """Setup observation volume tab"""
        # X limits
        ttk.Label(parent, text="X Limits:").pack(pady=5)

        x_frame = ttk.Frame(parent)
        x_frame.pack(pady=5)

        ttk.Label(x_frame, text="Xmin:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.xmin_var = tk.IntVar(value=self.param_values.get('X_lay', [-100, 100])[0])
        ttk.Spinbox(x_frame, from_=-1000, to=1000, textvariable=self.xmin_var).grid(row=0, column=1, pady=2)

        ttk.Label(x_frame, text="Xmax:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.xmax_var = tk.IntVar(value=self.param_values.get('X_lay', [-100, 100])[1])
        ttk.Spinbox(x_frame, from_=-1000, to=1000, textvariable=self.xmax_var).grid(row=1, column=1, pady=2)

        # Z limits
        ttk.Label(parent, text="Z Limits:").pack(pady=10)

        z_frame = ttk.Frame(parent)
        z_frame.pack(pady=5)

        ttk.Label(z_frame, text="Zmin1:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.zmin1_var = tk.IntVar(value=self.param_values.get('Zmin_lay', [-50, -50])[0])
        ttk.Spinbox(z_frame, from_=-1000, to=1000, textvariable=self.zmin1_var).grid(row=0, column=1, pady=2)

        ttk.Label(z_frame, text="Zmin2:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.zmin2_var = tk.IntVar(value=self.param_values.get('Zmin_lay', [-50, -50])[1])
        ttk.Spinbox(z_frame, from_=-1000, to=1000, textvariable=self.zmin2_var).grid(row=1, column=1, pady=2)

        ttk.Label(z_frame, text="Zmax1:").grid(row=0, column=2, sticky=tk.W, pady=2, padx=(10, 0))
        self.zmax1_var = tk.IntVar(value=self.param_values.get('Zmax_lay', [50, 50])[0])
        ttk.Spinbox(z_frame, from_=-1000, to=1000, textvariable=self.zmax1_var).grid(row=0, column=3, pady=2)

        ttk.Label(z_frame, text="Zmax2:").grid(row=1, column=2, sticky=tk.W, pady=2, padx=(10, 0))
        self.zmax2_var = tk.IntVar(value=self.param_values.get('Zmax_lay', [50, 50])[1])
        ttk.Spinbox(z_frame, from_=-1000, to=1000, textvariable=self.zmax2_var).grid(row=1, column=3, pady=2)

    def setup_criteria_tab(self, parent):
        """Setup criteria tab"""
        ttk.Label(parent, text="Correspondence Criteria:").pack(pady=10)

        frame = ttk.Frame(parent)
        frame.pack(pady=10)

        # Correlation thresholds
        ttk.Label(frame, text="Min corr nx:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.corr_nx_var = tk.DoubleVar(value=self.param_values.get('cnx', 0.5))
        ttk.Entry(frame, textvariable=self.corr_nx_var).grid(row=0, column=1, pady=2)

        ttk.Label(frame, text="Min corr ny:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.corr_ny_var = tk.DoubleVar(value=self.param_values.get('cny', 0.5))
        ttk.Entry(frame, textvariable=self.corr_ny_var).grid(row=1, column=1, pady=2)

        ttk.Label(frame, text="Min corr npix:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.corr_npix_var = tk.DoubleVar(value=self.param_values.get('cn', 0.5))
        ttk.Entry(frame, textvariable=self.corr_npix_var).grid(row=2, column=1, pady=2)

        ttk.Label(frame, text="Sum of gv:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.sum_gv_var = tk.DoubleVar(value=self.param_values.get('csumg', 0.5))
        ttk.Entry(frame, textvariable=self.sum_gv_var).grid(row=3, column=1, pady=2)

        ttk.Label(frame, text="Min weight corr:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.weight_corr_var = tk.DoubleVar(value=self.param_values.get('corrmin', 0.5))
        ttk.Entry(frame, textvariable=self.weight_corr_var).grid(row=4, column=1, pady=2)

        ttk.Label(frame, text="Tolerance band:").grid(row=5, column=0, sticky=tk.W, pady=2)
        self.tol_band_var = tk.DoubleVar(value=self.param_values.get('eps0', 1.0))
        ttk.Entry(frame, textvariable=self.tol_band_var).grid(row=5, column=1, pady=2)

    def setup_calibration_params(self):
        """Setup calibration parameters tabs"""
        # Images tab
        images_frame = ttk.Frame(self.notebook)
        self.notebook.add(images_frame, text="Images")

        self.setup_calibration_images_tab(images_frame)

        # Detection tab
        detection_frame = ttk.Frame(self.notebook)
        self.notebook.add(detection_frame, text="Detection")

        self.setup_calibration_detection_tab(detection_frame)

        # Orientation tab
        orientation_frame = ttk.Frame(self.notebook)
        self.notebook.add(orientation_frame, text="Orientation")

        self.setup_calibration_orientation_tab(orientation_frame)

    def setup_calibration_images_tab(self, parent):
        """Setup calibration images tab"""
        # Calibration images
        ttk.Label(parent, text="Calibration Images:").pack(pady=5)

        self.cal_img_vars = []
        for i in range(4):
            frame = ttk.Frame(parent)
            frame.pack(fill=tk.X, pady=2)

            ttk.Label(frame, text=f"Camera {i+1}:").pack(side=tk.LEFT)
            var = tk.StringVar(value=self.param_values.get('img_cal_name', [''])[i] if i < len(self.param_values.get('img_cal_name', [])) else '')
            self.cal_img_vars.append(var)
            ttk.Entry(frame, textvariable=var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

        # Orientation images
        ttk.Label(parent, text="Orientation Images:").pack(pady=10)

        self.ori_img_vars = []
        for i in range(4):
            frame = ttk.Frame(parent)
            frame.pack(fill=tk.X, pady=2)

            ttk.Label(frame, text=f"Camera {i+1}:").pack(side=tk.LEFT)
            var = tk.StringVar(value=self.param_values.get('img_ori', [''])[i] if i < len(self.param_values.get('img_ori', [])) else '')
            self.ori_img_vars.append(var)
            ttk.Entry(frame, textvariable=var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

        # Fixp file
        ttk.Label(parent, text="Fixp file:").pack(pady=10)
        self.fixp_var = tk.StringVar(value=self.param_values.get('fixp_name', ''))
        ttk.Entry(parent, textvariable=self.fixp_var).pack(fill=tk.X, pady=2)

    def setup_calibration_detection_tab(self, parent):
        """Setup calibration detection tab"""
        # Image properties
        ttk.Label(parent, text="Image Properties:").pack(pady=5)

        props_frame = ttk.Frame(parent)
        props_frame.pack(pady=5)

        ttk.Label(props_frame, text="Horizontal size:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.h_size_var = tk.IntVar(value=self.param_values.get('imx', 1280))
        ttk.Spinbox(props_frame, from_=1, to=10000, textvariable=self.h_size_var).grid(row=0, column=1, pady=2)

        ttk.Label(props_frame, text="Vertical size:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.v_size_var = tk.IntVar(value=self.param_values.get('imy', 1024))
        ttk.Spinbox(props_frame, from_=1, to=10000, textvariable=self.v_size_var).grid(row=1, column=1, pady=2)

        ttk.Label(props_frame, text="Horizontal pixel:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.h_pix_var = tk.DoubleVar(value=self.param_values.get('pix_x', 0.01))
        ttk.Entry(props_frame, textvariable=self.h_pix_var).grid(row=2, column=1, pady=2)

        ttk.Label(props_frame, text="Vertical pixel:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.v_pix_var = tk.DoubleVar(value=self.param_values.get('pix_y', 0.01))
        ttk.Entry(props_frame, textvariable=self.v_pix_var).grid(row=3, column=1, pady=2)

        # Detection parameters would go here - simplified for brevity
        ttk.Label(parent, text="Detection parameters would be configured here").pack(pady=20)

    def setup_calibration_orientation_tab(self, parent):
        """Setup calibration orientation tab"""
        # Orientation flags
        ttk.Label(parent, text="Orientation Parameters:").pack(pady=5)

        flags_frame = ttk.Frame(parent)
        flags_frame.pack(pady=5)

        self.cc_var = tk.BooleanVar(value=self.param_values.get('cc', False))
        ttk.Checkbutton(flags_frame, text="cc", variable=self.cc_var).grid(row=0, column=0, sticky=tk.W, padx=5)

        self.xh_var = tk.BooleanVar(value=self.param_values.get('xh', False))
        ttk.Checkbutton(flags_frame, text="xh", variable=self.xh_var).grid(row=0, column=1, sticky=tk.W, padx=5)

        self.yh_var = tk.BooleanVar(value=self.param_values.get('yh', False))
        ttk.Checkbutton(flags_frame, text="yh", variable=self.yh_var).grid(row=1, column=0, sticky=tk.W, padx=5)

        self.k1_var = tk.BooleanVar(value=self.param_values.get('k1', False))
        ttk.Checkbutton(flags_frame, text="k1", variable=self.k1_var).grid(row=1, column=1, sticky=tk.W, padx=5)

        # Add more orientation parameters as needed
        ttk.Label(parent, text="Additional orientation parameters would be configured here").pack(pady=20)

    def setup_tracking_params(self):
        """Setup tracking parameters tab"""
        # Velocity limits
        ttk.Label(self.notebook, text="Velocity Limits:").pack(pady=10)

        vel_frame = ttk.Frame(self.notebook)
        vel_frame.pack(pady=10)

        # X velocity
        ttk.Label(vel_frame, text="X velocity min:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.dvxmin_var = tk.DoubleVar(value=self.param_values.get('dvxmin', -10.0))
        ttk.Entry(vel_frame, textvariable=self.dvxmin_var).grid(row=0, column=1, pady=2)

        ttk.Label(vel_frame, text="X velocity max:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.dvxmax_var = tk.DoubleVar(value=self.param_values.get('dvxmax', 10.0))
        ttk.Entry(vel_frame, textvariable=self.dvxmax_var).grid(row=1, column=1, pady=2)

        # Y velocity
        ttk.Label(vel_frame, text="Y velocity min:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.dvymin_var = tk.DoubleVar(value=self.param_values.get('dvymin', -10.0))
        ttk.Entry(vel_frame, textvariable=self.dvymin_var).grid(row=2, column=1, pady=2)

        ttk.Label(vel_frame, text="Y velocity max:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.dvymax_var = tk.DoubleVar(value=self.param_values.get('dvymax', 10.0))
        ttk.Entry(vel_frame, textvariable=self.dvymax_var).grid(row=3, column=1, pady=2)

        # Z velocity
        ttk.Label(vel_frame, text="Z velocity min:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.dvzmin_var = tk.DoubleVar(value=self.param_values.get('dvzmin', -10.0))
        ttk.Entry(vel_frame, textvariable=self.dvzmin_var).grid(row=4, column=1, pady=2)

        ttk.Label(vel_frame, text="Z velocity max:").grid(row=5, column=0, sticky=tk.W, pady=2)
        self.dvzmax_var = tk.DoubleVar(value=self.param_values.get('dvzmax', 10.0))
        ttk.Entry(vel_frame, textvariable=self.dvzmax_var).grid(row=5, column=1, pady=2)

        # Other parameters
        ttk.Label(vel_frame, text="Angle:").grid(row=6, column=0, sticky=tk.W, pady=2)
        self.angle_var = tk.DoubleVar(value=self.param_values.get('angle', 45.0))
        ttk.Entry(vel_frame, textvariable=self.angle_var).grid(row=6, column=1, pady=2)

        ttk.Label(vel_frame, text="Acceleration:").grid(row=7, column=0, sticky=tk.W, pady=2)
        self.dacc_var = tk.DoubleVar(value=self.param_values.get('dacc', 1.0))
        ttk.Entry(vel_frame, textvariable=self.dacc_var).grid(row=7, column=1, pady=2)

        # Flags
        self.new_particles_var = tk.BooleanVar(value=self.param_values.get('flagNewParticles', True))
        ttk.Checkbutton(vel_frame, text="Add new particles", variable=self.new_particles_var).grid(row=8, column=0, columnspan=2, sticky=tk.W, pady=5)

    def load_parameters(self):
        """Load parameters from experiment"""
        try:
            self.param_values = self.experiment.pm.parameters.copy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load parameters: {e}")
            self.param_values = {}

    def save_parameters(self):
        """Save parameters to experiment"""
        try:
            if self.param_type == "main":
                self.save_main_parameters()
            elif self.param_type == "calibration":
                self.save_calibration_parameters()
            elif self.param_type == "tracking":
                self.save_tracking_parameters()

            self.experiment.save_parameters()
            messagebox.showinfo("Success", "Parameters saved successfully!")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save parameters: {e}")

    def save_main_parameters(self):
        """Save main parameters"""
        # Update experiment parameters
        self.experiment.pm.parameters['num_cams'] = self.num_cams_var.get()
        self.experiment.pm.parameters['ptv']['splitter'] = self.splitter_var.get()
        self.experiment.pm.parameters['ptv']['allcam_flag'] = self.allcam_var.get()

        # Image names
        img_names = [var.get() for var in self.image_name_vars]
        self.experiment.pm.parameters['ptv']['img_name'] = img_names[:self.num_cams_var.get()]

        # Calibration images
        cal_names = [var.get() for var in self.cal_image_vars]
        self.experiment.pm.parameters['ptv']['img_cal'] = cal_names[:self.num_cams_var.get()]

        # Refractive indices
        self.experiment.pm.parameters['ptv']['mmp_n1'] = self.air_var.get()
        self.experiment.pm.parameters['ptv']['mmp_n2'] = self.glass_var.get()
        self.experiment.pm.parameters['ptv']['mmp_n3'] = self.water_var.get()
        self.experiment.pm.parameters['ptv']['mmp_d'] = self.thickness_var.get()

        # Recognition parameters
        self.experiment.pm.parameters['targ_rec']['gvthres'] = [var.get() for var in self.grey_thresh_vars]
        self.experiment.pm.parameters['targ_rec']['nnmin'] = self.min_npix_var.get()
        self.experiment.pm.parameters['targ_rec']['nnmax'] = self.max_npix_var.get()
        self.experiment.pm.parameters['targ_rec']['nxmin'] = self.min_npix_x_var.get()
        self.experiment.pm.parameters['targ_rec']['nxmax'] = self.max_npix_x_var.get()
        self.experiment.pm.parameters['targ_rec']['nymin'] = self.min_npix_y_var.get()
        self.experiment.pm.parameters['targ_rec']['nymax'] = self.max_npix_y_var.get()
        self.experiment.pm.parameters['targ_rec']['sumg_min'] = self.sum_grey_var.get()
        self.experiment.pm.parameters['targ_rec']['disco'] = self.disco_var.get()
        self.experiment.pm.parameters['targ_rec']['cr_sz'] = self.cross_size_var.get()

        # Sequence parameters
        self.experiment.pm.parameters['sequence']['first'] = self.seq_first_var.get()
        self.experiment.pm.parameters['sequence']['last'] = self.seq_last_var.get()
        base_names = [var.get() for var in self.basename_vars]
        self.experiment.pm.parameters['sequence']['base_name'] = base_names[:self.num_cams_var.get()]

        # Volume parameters
        self.experiment.pm.parameters['criteria']['X_lay'] = [self.xmin_var.get(), self.xmax_var.get()]
        self.experiment.pm.parameters['criteria']['Zmin_lay'] = [self.zmin1_var.get(), self.zmin2_var.get()]
        self.experiment.pm.parameters['criteria']['Zmax_lay'] = [self.zmax1_var.get(), self.zmax2_var.get()]

        # Criteria parameters
        self.experiment.pm.parameters['criteria']['cnx'] = self.corr_nx_var.get()
        self.experiment.pm.parameters['criteria']['cny'] = self.corr_ny_var.get()
        self.experiment.pm.parameters['criteria']['cn'] = self.corr_npix_var.get()
        self.experiment.pm.parameters['criteria']['csumg'] = self.sum_gv_var.get()
        self.experiment.pm.parameters['criteria']['corrmin'] = self.weight_corr_var.get()
        self.experiment.pm.parameters['criteria']['eps0'] = self.tol_band_var.get()

        # Flags
        self.experiment.pm.parameters['ptv']['hp_flag'] = self.hp_var.get()
        self.experiment.pm.parameters['masking']['mask_flag'] = self.mask_var.get()
        self.experiment.pm.parameters['pft_version']['Existing_Target'] = self.existing_var.get()

    def save_calibration_parameters(self):
        """Save calibration parameters"""
        # Image names
        cal_names = [var.get() for var in self.cal_img_vars]
        self.experiment.pm.parameters['cal_ori']['img_cal_name'] = cal_names[:self.experiment.get_n_cam()]

        ori_names = [var.get() for var in self.ori_img_vars]
        self.experiment.pm.parameters['cal_ori']['img_ori'] = ori_names[:self.experiment.get_n_cam()]

        # Fixp file
        self.experiment.pm.parameters['cal_ori']['fixp_name'] = self.fixp_var.get()

        # Image properties
        self.experiment.pm.parameters['ptv']['imx'] = self.h_size_var.get()
        self.experiment.pm.parameters['ptv']['imy'] = self.v_size_var.get()
        self.experiment.pm.parameters['ptv']['pix_x'] = self.h_pix_var.get()
        self.experiment.pm.parameters['ptv']['pix_y'] = self.v_pix_var.get()

        # Orientation flags
        self.experiment.pm.parameters['orient']['cc'] = self.cc_var.get()
        self.experiment.pm.parameters['orient']['xh'] = self.xh_var.get()
        self.experiment.pm.parameters['orient']['yh'] = self.yh_var.get()
        self.experiment.pm.parameters['orient']['k1'] = self.k1_var.get()

    def save_tracking_parameters(self):
        """Save tracking parameters"""
        self.experiment.pm.parameters['track']['dvxmin'] = self.dvxmin_var.get()
        self.experiment.pm.parameters['track']['dvxmax'] = self.dvxmax_var.get()
        self.experiment.pm.parameters['track']['dvymin'] = self.dvymin_var.get()
        self.experiment.pm.parameters['track']['dvymax'] = self.dvymax_var.get()
        self.experiment.pm.parameters['track']['dvzmin'] = self.dvzmin_var.get()
        self.experiment.pm.parameters['track']['dvzmax'] = self.dvzmax_var.get()
        self.experiment.pm.parameters['track']['angle'] = self.angle_var.get()
        self.experiment.pm.parameters['track']['dacc'] = self.dacc_var.get()
        self.experiment.pm.parameters['track']['flagNewParticles'] = self.new_particles_var.get()

    def cancel(self):
        """Cancel editing"""
        self.parent.destroy()


def create_parameter_editor(experiment: Experiment, param_type: str = "main") -> tk.Toplevel:
    """Create and return a parameter editor window"""
    window = tk.Toplevel()
    window.title(f"PyPTV {param_type.title()} Parameters")
    window.geometry("800x600")

    editor = ParameterEditor(window, experiment, param_type)
    editor.pack(fill=tk.BOTH, expand=True)

    return window


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python pyptv_parameter_gui_ttk.py <yaml_file> <param_type>")
        print("param_type: main, calibration, or tracking")
        sys.exit(1)

    yaml_path = Path(sys.argv[1])
    param_type = sys.argv[2]

    if not yaml_path.exists():
        print(f"Error: YAML file '{yaml_path}' does not exist.")
        sys.exit(1)

    # Create experiment
    from pyptv.parameter_manager import ParameterManager
    pm = ParameterManager()
    pm.from_yaml(yaml_path)
    experiment = Experiment(pm=pm)

    root = tk.Tk()
    root.title(f"PyPTV {param_type.title()} Parameters")

    editor = ParameterEditor(root, experiment, param_type)
    editor.pack(fill=tk.BOTH, expand=True)

    root.mainloop()
