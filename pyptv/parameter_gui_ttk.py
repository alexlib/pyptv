"""
TTK-based Parameter GUI classes for PyPTV

This module provides TTK implementations of the parameter editing GUIs
that were originally built with TraitsUI. These classes provide the same
functionality but using modern TTK widgets.

Classes:
    MainParamsWindow: Main PTV parameters editor
    CalibParamsWindow: Calibration parameters editor  
    TrackingParamsWindow: Tracking parameters editor
"""

import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as tb
from pathlib import Path
from typing import Optional, Dict, Any


class BaseParamWindow(tb.Window):
    """Base class for parameter editing windows"""
    
    def __init__(self, parent, experiment, title: str):
        super().__init__(themename='superhero')
        self.parent = parent
        self.experiment = experiment
        self.title(title)
        self.geometry('900x700')
        self.resizable(True, True)
        
        # Create main frame
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill='both', expand=True)
        
        # Create button frame
        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.pack(fill='x', pady=(10, 0))
        
        # Create buttons
        self.ok_button = ttk.Button(self.button_frame, text="OK", command=self.on_ok)
        self.ok_button.pack(side='right', padx=(5, 0))
        
        self.cancel_button = ttk.Button(self.button_frame, text="Cancel", command=self.on_cancel)
        self.cancel_button.pack(side='right')
        
        # Initialize data structures
        self.widgets = {}
        self.original_values = {}
        
        # Load current values
        self.load_values()
        
    def create_tab(self, name: str) -> ttk.Frame:
        """Create a new tab and return the frame"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text=name)
        return frame
    
    def add_widget(self, tab_frame: ttk.Frame, label_text: str, widget_type: str, 
                   var_name: str, **kwargs) -> tk.Widget:
        """Add a widget to a tab frame"""
        # Create label
        label = ttk.Label(tab_frame, text=label_text)
        
        # Create variable
        if widget_type == 'entry':
            var = tk.StringVar()
            widget = ttk.Entry(tab_frame, textvariable=var, **kwargs)
        elif widget_type == 'spinbox':
            var = tk.StringVar()
            widget = ttk.Spinbox(tab_frame, textvariable=var, **kwargs)
        elif widget_type == 'checkbutton':
            var = tk.BooleanVar()
            widget = ttk.Checkbutton(tab_frame, variable=var, **kwargs)
        elif widget_type == 'combobox':
            var = tk.StringVar()
            widget = ttk.Combobox(tab_frame, textvariable=var, **kwargs)
        
        # Store references
        self.widgets[var_name] = {'widget': widget, 'var': var, 'label': label}
        
        return widget
    
    def load_values(self):
        """Load current parameter values - to be implemented by subclasses"""
        pass
    
    def save_values(self):
        """Save parameter values - to be implemented by subclasses"""
        pass
    
    def get_widget_value(self, var_name: str):
        """Get value from widget by variable name"""
        if var_name in self.widgets:
            var = self.widgets[var_name]['var']
            return var.get()
        return None
    
    def set_widget_value(self, var_name: str, value):
        """Set value to widget by variable name"""
        if var_name in self.widgets:
            var = self.widgets[var_name]['var']
            var.set(value)
    
    def on_ok(self):
        """Handle OK button click"""
        try:
            self.save_values()
            self.experiment.save_parameters()
            messagebox.showinfo("Success", "Parameters saved successfully!")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save parameters: {e}")
    
    def on_cancel(self):
        """Handle Cancel button click"""
        self.destroy()


class MainParamsWindow(BaseParamWindow):
    """TTK version of Main_Params GUI"""
    
    def __init__(self, parent, experiment):
        super().__init__(parent, experiment, "Main Parameters")
        self.create_tabs()
        self.load_values()
    
    def create_tabs(self):
        """Create all parameter tabs"""
        self.create_general_tab()
        self.create_refractive_tab()
        self.create_particle_recognition_tab()
        self.create_sequence_tab()
        self.create_observation_volume_tab()
        self.create_criteria_tab()
    
    def create_general_tab(self):
        """Create General tab"""
        tab = self.create_tab("General")
        
        # Number of cameras
        ttk.Label(tab, text="Number of cameras:").grid(row=0, column=0, sticky='w', pady=5)
        self.add_widget(tab, "", 'spinbox', 'num_cams', from_=1, to=4).grid(row=0, column=1, sticky='ew', pady=5)
        
        # Splitter checkbox
        self.add_widget(tab, "Split images into 4?", 'checkbutton', 'splitter').grid(row=1, column=0, columnspan=2, sticky='w', pady=5)
        
        # Accept only all cameras checkbox
        self.add_widget(tab, "Accept only points seen from all cameras?", 'checkbutton', 'allcam_flag').grid(row=2, column=0, columnspan=2, sticky='w', pady=5)
        
        # Image names section
        ttk.Label(tab, text="Image Names:", font=('Arial', 10, 'bold')).grid(row=3, column=0, columnspan=2, sticky='w', pady=(20,5))
        
        for i in range(4):
            ttk.Label(tab, text=f"Name of {i+1}. image").grid(row=4+i, column=0, sticky='w', pady=2)
            self.add_widget(tab, "", 'entry', f'img_name_{i}').grid(row=4+i, column=1, sticky='ew', pady=2)
        
        # Calibration images section
        ttk.Label(tab, text="Calibration Data:", font=('Arial', 10, 'bold')).grid(row=8, column=0, columnspan=2, sticky='w', pady=(20,5))
        
        for i in range(4):
            ttk.Label(tab, text=f"Calibration data for {i+1}. image").grid(row=9+i, column=0, sticky='w', pady=2)
            self.add_widget(tab, "", 'entry', f'img_cal_{i}').grid(row=9+i, column=1, sticky='ew', pady=2)
        
        # Configure grid
        tab.columnconfigure(1, weight=1)
    
    def create_refractive_tab(self):
        """Create Refractive Indices tab"""
        tab = self.create_tab("Refractive Indices")
        
        ttk.Label(tab, text="Air:").grid(row=0, column=0, sticky='w', pady=5)
        self.add_widget(tab, "", 'entry', 'mmp_n1').grid(row=0, column=1, sticky='ew', pady=5)
        
        ttk.Label(tab, text="Glass:").grid(row=1, column=0, sticky='w', pady=5)
        self.add_widget(tab, "", 'entry', 'mmp_n2').grid(row=1, column=1, sticky='ew', pady=5)
        
        ttk.Label(tab, text="Water:").grid(row=2, column=0, sticky='w', pady=5)
        self.add_widget(tab, "", 'entry', 'mmp_n3').grid(row=2, column=1, sticky='ew', pady=5)
        
        ttk.Label(tab, text="Thickness of glass:").grid(row=3, column=0, sticky='w', pady=5)
        self.add_widget(tab, "", 'entry', 'mmp_d').grid(row=3, column=1, sticky='ew', pady=5)
        
        tab.columnconfigure(1, weight=1)
    
    def create_particle_recognition_tab(self):
        """Create Particle Recognition tab"""
        tab = self.create_tab("Particle Recognition")
        
        # Gray value thresholds
        ttk.Label(tab, text="Gray value threshold:", font=('Arial', 10, 'bold')).grid(row=0, column=0, columnspan=4, sticky='w', pady=5)
        
        for i in range(4):
            ttk.Label(tab, text=f"{i+1}st image").grid(row=1, column=i, sticky='w', padx=5)
            self.add_widget(tab, "", 'entry', f'gvthres_{i}').grid(row=2, column=i, sticky='ew', padx=5)
        
        # Particle size parameters
        ttk.Label(tab, text="Particle Size Parameters:", font=('Arial', 10, 'bold')).grid(row=3, column=0, columnspan=4, sticky='w', pady=(20,5))
        
        ttk.Label(tab, text="min npix").grid(row=4, column=0, sticky='w', pady=2)
        self.add_widget(tab, "", 'entry', 'nnmin').grid(row=4, column=1, sticky='ew', pady=2)
        
        ttk.Label(tab, text="max npix").grid(row=5, column=0, sticky='w', pady=2)
        self.add_widget(tab, "", 'entry', 'nnmax').grid(row=5, column=1, sticky='ew', pady=2)
        
        ttk.Label(tab, text="Sum of grey value").grid(row=6, column=0, sticky='w', pady=2)
        self.add_widget(tab, "", 'entry', 'sumg_min').grid(row=6, column=1, sticky='ew', pady=2)
        
        ttk.Label(tab, text="Tolerable discontinuity").grid(row=4, column=2, sticky='w', pady=2)
        self.add_widget(tab, "", 'entry', 'disco').grid(row=4, column=3, sticky='ew', pady=2)
        
        ttk.Label(tab, text="Size of crosses").grid(row=5, column=2, sticky='w', pady=2)
        self.add_widget(tab, "", 'entry', 'cr_sz').grid(row=5, column=3, sticky='ew', pady=2)
        
        # Additional options
        self.add_widget(tab, "High pass filter", 'checkbutton', 'hp_flag').grid(row=7, column=0, columnspan=2, sticky='w', pady=(20,2))
        self.add_widget(tab, "Subtract mask", 'checkbutton', 'mask_flag').grid(row=8, column=0, columnspan=2, sticky='w', pady=2)
        self.add_widget(tab, "Use existing_target files?", 'checkbutton', 'existing_target').grid(row=9, column=0, columnspan=2, sticky='w', pady=2)
        
        ttk.Label(tab, text="Base name for the mask").grid(row=10, column=0, sticky='w', pady=2)
        self.add_widget(tab, "", 'entry', 'mask_base_name').grid(row=10, column=1, columnspan=3, sticky='ew', pady=2)
        
        # Configure grid
        for i in range(4):
            tab.columnconfigure(i, weight=1)
    
    def create_sequence_tab(self):
        """Create Sequence tab"""
        tab = self.create_tab("Sequence")
        
        ttk.Label(tab, text="First sequence image:").grid(row=0, column=0, sticky='w', pady=5)
        self.add_widget(tab, "", 'entry', 'seq_first').grid(row=0, column=1, sticky='ew', pady=5)
        
        ttk.Label(tab, text="Last sequence image:").grid(row=1, column=0, sticky='w', pady=5)
        self.add_widget(tab, "", 'entry', 'seq_last').grid(row=1, column=1, sticky='ew', pady=5)
        
        ttk.Label(tab, text="Basenames for sequences:", font=('Arial', 10, 'bold')).grid(row=2, column=0, columnspan=2, sticky='w', pady=(20,5))
        
        for i in range(4):
            ttk.Label(tab, text=f"Basename for {i+1}. sequence").grid(row=3+i, column=0, sticky='w', pady=2)
            self.add_widget(tab, "", 'entry', f'base_name_{i}').grid(row=3+i, column=1, sticky='ew', pady=2)
        
        tab.columnconfigure(1, weight=1)
    
    def create_observation_volume_tab(self):
        """Create Observation Volume tab"""
        tab = self.create_tab("Observation Volume")
        
        ttk.Label(tab, text="Xmin").grid(row=0, column=0, sticky='w', pady=5)
        self.add_widget(tab, "", 'entry', 'xmin').grid(row=0, column=1, sticky='ew', pady=5)
        
        ttk.Label(tab, text="Xmax").grid(row=1, column=0, sticky='w', pady=5)
        self.add_widget(tab, "", 'entry', 'xmax').grid(row=1, column=1, sticky='ew', pady=5)
        
        ttk.Label(tab, text="Zmin").grid(row=0, column=2, sticky='w', pady=5)
        self.add_widget(tab, "", 'entry', 'zmin1').grid(row=0, column=3, sticky='ew', pady=5)
        self.add_widget(tab, "", 'entry', 'zmin2').grid(row=1, column=3, sticky='ew', pady=5)
        
        for i in range(4):
            tab.columnconfigure(i, weight=1)
    
    def create_criteria_tab(self):
        """Create Criteria tab"""
        tab = self.create_tab("Criteria")
        
        ttk.Label(tab, text="min corr for ratio nx").grid(row=0, column=0, sticky='w', pady=5)
        self.add_widget(tab, "", 'entry', 'cnx').grid(row=0, column=1, sticky='ew', pady=5)
        
        ttk.Label(tab, text="min corr for ratio ny").grid(row=1, column=0, sticky='w', pady=5)
        self.add_widget(tab, "", 'entry', 'cny').grid(row=1, column=1, sticky='ew', pady=5)
        
        ttk.Label(tab, text="min corr for ratio npix").grid(row=2, column=0, sticky='w', pady=5)
        self.add_widget(tab, "", 'entry', 'cn').grid(row=2, column=1, sticky='ew', pady=5)
        
        ttk.Label(tab, text="sum of gv").grid(row=0, column=2, sticky='w', pady=5)
        self.add_widget(tab, "", 'entry', 'csumg').grid(row=0, column=3, sticky='ew', pady=5)
        
        ttk.Label(tab, text="min for weighted correlation").grid(row=1, column=2, sticky='w', pady=5)
        self.add_widget(tab, "", 'entry', 'corrmin').grid(row=1, column=3, sticky='ew', pady=5)
        
        ttk.Label(tab, text="Tolerance of epipolar band [mm]").grid(row=2, column=2, sticky='w', pady=5)
        self.add_widget(tab, "", 'entry', 'eps0').grid(row=2, column=3, sticky='ew', pady=5)
        
        # Configure grid
        for i in range(4):
            tab.columnconfigure(i, weight=1)
    
    def load_values(self):
        """Load current parameter values from experiment"""
        params = self.experiment.pm.parameters
        num_cams = self.experiment.get_n_cam()
        
        # PTV parameters
        ptv_params = params.get('ptv', {})
        self.set_widget_value('num_cams', str(num_cams))
        self.set_widget_value('splitter', bool(ptv_params.get('splitter', False)))
        self.set_widget_value('allcam_flag', bool(ptv_params.get('allcam_flag', False)))
        self.set_widget_value('hp_flag', bool(ptv_params.get('hp_flag', False)))
        self.set_widget_value('mmp_n1', str(ptv_params.get('mmp_n1', 1.0)))
        self.set_widget_value('mmp_n2', str(ptv_params.get('mmp_n2', 1.5)))
        self.set_widget_value('mmp_n3', str(ptv_params.get('mmp_n3', 1.33)))
        self.set_widget_value('mmp_d', str(ptv_params.get('mmp_d', 0.0)))
        
        # Image names
        img_names = ptv_params.get('img_name', [])
        for i in range(4):
            var_name = f'img_name_{i}'
            if i < len(img_names):
                self.set_widget_value(var_name, str(img_names[i]))
            else:
                self.set_widget_value(var_name, '')
        
        # Calibration images
        img_cals = ptv_params.get('img_cal', [])
        for i in range(4):
            var_name = f'img_cal_{i}'
            if i < len(img_cals):
                self.set_widget_value(var_name, str(img_cals[i]))
            else:
                self.set_widget_value(var_name, '')
        
        # Target recognition parameters
        targ_rec_params = params.get('targ_rec', {})
        gvthres = targ_rec_params.get('gvthres', [])
        for i in range(4):
            var_name = f'gvthres_{i}'
            if i < len(gvthres):
                self.set_widget_value(var_name, str(gvthres[i]))
            else:
                self.set_widget_value(var_name, '0')
        
        self.set_widget_value('nnmin', str(targ_rec_params.get('nnmin', 1)))
        self.set_widget_value('nnmax', str(targ_rec_params.get('nnmax', 100)))
        self.set_widget_value('sumg_min', str(targ_rec_params.get('sumg_min', 0)))
        self.set_widget_value('disco', str(targ_rec_params.get('disco', 0)))
        self.set_widget_value('cr_sz', str(targ_rec_params.get('cr_sz', 3)))
        
        # PFT version parameters
        pft_params = params.get('pft_version', {})
        self.set_widget_value('mask_flag', bool(pft_params.get('mask_flag', False)))
        self.set_widget_value('existing_target', bool(pft_params.get('existing_target', False)))
        self.set_widget_value('mask_base_name', str(pft_params.get('mask_base_name', '')))
        
        # Sequence parameters
        seq_params = params.get('sequence', {})
        self.set_widget_value('seq_first', str(seq_params.get('first', 0)))
        self.set_widget_value('seq_last', str(seq_params.get('last', 0)))
        
        base_names = seq_params.get('base_name', [])
        for i in range(4):
            var_name = f'base_name_{i}'
            if i < len(base_names):
                self.set_widget_value(var_name, str(base_names[i]))
            else:
                self.set_widget_value(var_name, '')
        
        # Observation volume parameters
        vol_params = params.get('volume', {})
        self.set_widget_value('xmin', str(vol_params.get('xmin', -100)))
        self.set_widget_value('xmax', str(vol_params.get('xmax', 100)))
        self.set_widget_value('zmin1', str(vol_params.get('zmin1', -100)))
        self.set_widget_value('zmin2', str(vol_params.get('zmin2', -100)))
        
        # Criteria parameters
        crit_params = params.get('criteria', {})
        self.set_widget_value('cnx', str(crit_params.get('cnx', 0.5)))
        self.set_widget_value('cny', str(crit_params.get('cny', 0.5)))
        self.set_widget_value('cn', str(crit_params.get('cn', 0.5)))
        self.set_widget_value('csumg', str(crit_params.get('csumg', 0)))
        self.set_widget_value('corrmin', str(crit_params.get('corrmin', 0.5)))
        self.set_widget_value('eps0', str(crit_params.get('eps0', 0.1)))
    
    def save_values(self):
        """Save parameter values to experiment"""
        params = self.experiment.pm.parameters
        
        # Update number of cameras
        num_cams = int(self.get_widget_value('num_cams'))
        self.experiment.set_n_cam(num_cams)
        
        # Update PTV parameters
        if 'ptv' not in params:
            params['ptv'] = {}
        
        params['ptv'].update({
            'splitter': self.get_widget_value('splitter'),
            'allcam_flag': self.get_widget_value('allcam_flag'),
            'hp_flag': self.get_widget_value('hp_flag'),
            'mmp_n1': float(self.get_widget_value('mmp_n1')),
            'mmp_n2': float(self.get_widget_value('mmp_n2')),
            'mmp_n3': float(self.get_widget_value('mmp_n3')),
            'mmp_d': float(self.get_widget_value('mmp_d')),
        })
        
        # Update image names
        img_names = []
        for i in range(num_cams):
            name = self.get_widget_value(f'img_name_{i}')
            if name:
                img_names.append(name)
        params['ptv']['img_name'] = img_names
        
        # Update calibration images
        img_cals = []
        for i in range(num_cams):
            cal = self.get_widget_value(f'img_cal_{i}')
            if cal:
                img_cals.append(cal)
        params['ptv']['img_cal'] = img_cals
        
        # Update target recognition parameters
        if 'targ_rec' not in params:
            params['targ_rec'] = {}
        
        gvthres = []
        for i in range(num_cams):
            val = self.get_widget_value(f'gvthres_{i}')
            if val:
                gvthres.append(int(val))
        
        params['targ_rec'].update({
            'gvthres': gvthres,
            'nnmin': int(self.get_widget_value('nnmin')),
            'nnmax': int(self.get_widget_value('nnmax')),
            'sumg_min': int(self.get_widget_value('sumg_min')),
            'disco': int(self.get_widget_value('disco')),
            'cr_sz': int(self.get_widget_value('cr_sz')),
        })
        
        # Update PFT version parameters
        if 'pft_version' not in params:
            params['pft_version'] = {}
        
        params['pft_version'].update({
            'mask_flag': self.get_widget_value('mask_flag'),
            'existing_target': self.get_widget_value('existing_target'),
            'mask_base_name': self.get_widget_value('mask_base_name'),
        })
        
        # Update sequence parameters
        if 'sequence' not in params:
            params['sequence'] = {}
        
        base_names = []
        for i in range(num_cams):
            name = self.get_widget_value(f'base_name_{i}')
            if name:
                base_names.append(name)
        
        params['sequence'].update({
            'first': int(self.get_widget_value('seq_first')),
            'last': int(self.get_widget_value('seq_last')),
            'base_name': base_names,
        })
        
        # Update observation volume parameters
        if 'volume' not in params:
            params['volume'] = {}
        
        params['volume'].update({
            'xmin': float(self.get_widget_value('xmin')),
            'xmax': float(self.get_widget_value('xmax')),
            'zmin1': float(self.get_widget_value('zmin1')),
            'zmin2': float(self.get_widget_value('zmin2')),
        })
        
        # Update criteria parameters
        if 'criteria' not in params:
            params['criteria'] = {}
        
        params['criteria'].update({
            'cnx': float(self.get_widget_value('cnx')),
            'cny': float(self.get_widget_value('cny')),
            'cn': float(self.get_widget_value('cn')),
            'csumg': int(self.get_widget_value('csumg')),
            'corrmin': float(self.get_widget_value('corrmin')),
            'eps0': float(self.get_widget_value('eps0')),
        })


class CalibParamsWindow(BaseParamWindow):
    """TTK version of Calibration Parameters GUI"""

    def __init__(self, parent, experiment):
        super().__init__(parent, experiment, "Calibration Parameters")
        self.create_tabs()
        self.load_values()

    def create_tabs(self):
        """Create calibration parameter tabs"""
        self.create_images_data_tab()
        self.create_detection_tab()
        self.create_manual_orientation_tab()
        self.create_orientation_params_tab()
        self.create_shaking_tab()
        self.create_dumbbell_tab()

    def create_images_data_tab(self):
        tab = self.create_tab("Images Data")
        self.add_widget(tab, "Split calib images?", 'checkbutton', 'cal_splitter').grid(row=0, column=0, columnspan=2, sticky='w', pady=5)

        # Calibration images
        cal_frame = ttk.LabelFrame(tab, text="Calibration Images")
        cal_frame.grid(row=1, column=0, columnspan=2, sticky='ew', padx=5, pady=5)
        for i in range(4):
            ttk.Label(cal_frame, text=f"Calib. pic cam {i+1}").grid(row=i, column=0, sticky='w', padx=5, pady=2)
            self.add_widget(cal_frame, "", 'entry', f'cam_{i+1}').grid(row=i, column=1, sticky='ew', padx=5, pady=2)
        cal_frame.columnconfigure(1, weight=1)

        # Orientation data
        ori_frame = ttk.LabelFrame(tab, text="Orientation Data")
        ori_frame.grid(row=1, column=2, columnspan=2, sticky='ew', padx=5, pady=5)
        for i in range(4):
            ttk.Label(ori_frame, text=f"Orientation data cam {i+1}").grid(row=i, column=0, sticky='w', padx=5, pady=2)
            self.add_widget(ori_frame, "", 'entry', f'ori_cam_{i+1}').grid(row=i, column=1, sticky='ew', padx=5, pady=2)
        ori_frame.columnconfigure(1, weight=1)

        # Coordinates file
        ttk.Label(tab, text="File of Coordinates on plate").grid(row=2, column=0, sticky='w', pady=5)
        self.add_widget(tab, "", 'entry', 'fixp_name').grid(row=2, column=1, columnspan=3, sticky='ew', pady=5)

        tab.columnconfigure(1, weight=1)
        tab.columnconfigure(3, weight=1)

    def create_detection_tab(self):
        tab = self.create_tab("Detection")
        
        # Image properties
        props_frame = ttk.LabelFrame(tab, text="Image Properties")
        props_frame.pack(fill='x', expand=True, padx=5, pady=5)
        
        ttk.Label(props_frame, text="Image size horizontal").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        self.add_widget(props_frame, "", 'entry', 'h_image_size').grid(row=0, column=1, sticky='ew', padx=5, pady=2)
        ttk.Label(props_frame, text="Image size vertical").grid(row=1, column=0, sticky='w', padx=5, pady=2)
        self.add_widget(props_frame, "", 'entry', 'v_image_size').grid(row=1, column=1, sticky='ew', padx=5, pady=2)
        ttk.Label(props_frame, text="Pixel size horizontal").grid(row=0, column=2, sticky='w', padx=5, pady=2)
        self.add_widget(props_frame, "", 'entry', 'h_pixel_size').grid(row=0, column=3, sticky='ew', padx=5, pady=2)
        ttk.Label(props_frame, text="Pixel size vertical").grid(row=1, column=2, sticky='w', padx=5, pady=2)
        self.add_widget(props_frame, "", 'entry', 'v_pixel_size').grid(row=1, column=3, sticky='ew', padx=5, pady=2)
        props_frame.columnconfigure(1, weight=1)
        props_frame.columnconfigure(3, weight=1)

        # Thresholds
        thresh_frame = ttk.LabelFrame(tab, text="Grayvalue Threshold")
        thresh_frame.pack(fill='x', expand=True, padx=5, pady=5)
        for i in range(4):
            ttk.Label(thresh_frame, text=f"Image {i+1}").grid(row=0, column=i, sticky='w', padx=5)
            self.add_widget(thresh_frame, "", 'entry', f'gvth_{i+1}').grid(row=1, column=i, sticky='ew', padx=5)
            thresh_frame.columnconfigure(i, weight=1)

        # Particle size params
        parts_frame = ttk.LabelFrame(tab, text="Particle Size")
        parts_frame.pack(fill='x', expand=True, padx=5, pady=5)
        
        ttk.Label(parts_frame, text="min npix").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        self.add_widget(parts_frame, "", 'entry', 'min_npix').grid(row=0, column=1)
        ttk.Label(parts_frame, text="max npix").grid(row=1, column=0, sticky='w', padx=5, pady=2)
        self.add_widget(parts_frame, "", 'entry', 'max_npix').grid(row=1, column=1)
        
        ttk.Label(parts_frame, text="min npix in x").grid(row=0, column=2, sticky='w', padx=5, pady=2)
        self.add_widget(parts_frame, "", 'entry', 'min_npix_x').grid(row=0, column=3)
        ttk.Label(parts_frame, text="max npix in x").grid(row=1, column=2, sticky='w', padx=5, pady=2)
        self.add_widget(parts_frame, "", 'entry', 'max_npix_x').grid(row=1, column=3)

        ttk.Label(parts_frame, text="min npix in y").grid(row=0, column=4, sticky='w', padx=5, pady=2)
        self.add_widget(parts_frame, "", 'entry', 'min_npix_y').grid(row=0, column=5)
        ttk.Label(parts_frame, text="max npix in y").grid(row=1, column=4, sticky='w', padx=5, pady=2)
        self.add_widget(parts_frame, "", 'entry', 'max_npix_y').grid(row=1, column=5)

        ttk.Label(parts_frame, text="Sum of greyvalue").grid(row=2, column=0, sticky='w', padx=5, pady=2)
        self.add_widget(parts_frame, "", 'entry', 'sum_of_grey').grid(row=2, column=1)
        ttk.Label(parts_frame, text="Tolerable discontinuity").grid(row=2, column=2, sticky='w', padx=5, pady=2)
        self.add_widget(parts_frame, "", 'entry', 'tolerable_discontinuity').grid(row=2, column=3)
        ttk.Label(parts_frame, text="Size of crosses").grid(row=2, column=4, sticky='w', padx=5, pady=2)
        self.add_widget(parts_frame, "", 'entry', 'size_of_crosses').grid(row=2, column=5)

    def create_manual_orientation_tab(self):
        tab = self.create_tab("Manual Orientation")
        for i in range(4):
            frame = ttk.LabelFrame(tab, text=f"Image {i+1}")
            frame.pack(fill='x', expand=True, padx=5, pady=5)
            for j in range(4):
                ttk.Label(frame, text=f"P{j+1}").grid(row=0, column=j*2, sticky='w', padx=5)
                self.add_widget(frame, "", 'entry', f'img_{i+1}_p{j+1}').grid(row=0, column=j*2+1, padx=5)

    def create_orientation_params_tab(self):
        tab = self.create_tab("Orientation Params")
        
        frame1 = ttk.LabelFrame(tab, text="Flags")
        frame1.pack(fill='x', expand=True, padx=5, pady=5)
        self.add_widget(frame1, "Calibrate with different Z", 'checkbutton', 'Examine_Flag').pack(side='left', padx=5)
        self.add_widget(frame1, "Combine preprocessed planes", 'checkbutton', 'Combine_Flag').pack(side='left', padx=5)

        frame2 = ttk.LabelFrame(tab, text="Orientation Parameters")
        frame2.pack(fill='x', expand=True, padx=5, pady=5)
        ttk.Label(frame2, text="Point number of orientation").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        self.add_widget(frame2, "", 'entry', 'point_number_of_orientation').grid(row=0, column=1, padx=5, pady=2)
        
        self.add_widget(frame2, "cc", 'checkbutton', 'cc').grid(row=1, column=0, sticky='w')
        self.add_widget(frame2, "xh", 'checkbutton', 'xh').grid(row=1, column=1, sticky='w')
        self.add_widget(frame2, "yh", 'checkbutton', 'yh').grid(row=1, column=2, sticky='w')

        frame3 = ttk.LabelFrame(tab, text="Lens distortion (Brown)")
        frame3.pack(fill='x', expand=True, padx=5, pady=5)
        self.add_widget(frame3, "k1", 'checkbutton', 'k1').grid(row=0, column=0, sticky='w')
        self.add_widget(frame3, "k2", 'checkbutton', 'k2').grid(row=0, column=1, sticky='w')
        self.add_widget(frame3, "k3", 'checkbutton', 'k3').grid(row=0, column=2, sticky='w')
        self.add_widget(frame3, "p1", 'checkbutton', 'p1').grid(row=0, column=3, sticky='w')
        self.add_widget(frame3, "p2", 'checkbutton', 'p2').grid(row=0, column=4, sticky='w')

        frame4 = ttk.LabelFrame(tab, text="Affin transformation")
        frame4.pack(fill='x', expand=True, padx=5, pady=5)
        self.add_widget(frame4, "scale", 'checkbutton', 'scale').grid(row=0, column=0, sticky='w')
        self.add_widget(frame4, "shear", 'checkbutton', 'shear').grid(row=0, column=1, sticky='w')
        
        self.add_widget(tab, "interfaces check box are available", 'checkbutton', 'interf').pack(pady=5)

    def create_shaking_tab(self):
        tab = self.create_tab("Shaking")
        frame = ttk.LabelFrame(tab, text="Shaking calibration parameters")
        frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        ttk.Label(frame, text="shaking first frame").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        self.add_widget(frame, "", 'entry', 'shaking_first_frame').grid(row=0, column=1, sticky='ew', padx=5, pady=2)
        ttk.Label(frame, text="shaking last frame").grid(row=1, column=0, sticky='w', padx=5, pady=2)
        self.add_widget(frame, "", 'entry', 'shaking_last_frame').grid(row=1, column=1, sticky='ew', padx=5, pady=2)
        ttk.Label(frame, text="shaking max num points").grid(row=2, column=0, sticky='w', padx=5, pady=2)
        self.add_widget(frame, "", 'entry', 'shaking_max_num_points').grid(row=2, column=1, sticky='ew', padx=5, pady=2)
        ttk.Label(frame, text="shaking max num frames").grid(row=3, column=0, sticky='w', padx=5, pady=2)
        self.add_widget(frame, "", 'entry', 'shaking_max_num_frames').grid(row=3, column=1, sticky='ew', padx=5, pady=2)
        frame.columnconfigure(1, weight=1)

    def create_dumbbell_tab(self):
        tab = self.create_tab("Dumbbell")
        frame = ttk.LabelFrame(tab, text="Dumbbell calibration parameters")
        frame.pack(fill='both', expand=True, padx=5, pady=5)

        ttk.Label(frame, text="dumbbell epsilon").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        self.add_widget(frame, "", 'entry', 'dumbbell_eps').grid(row=0, column=1, sticky='ew', padx=5, pady=2)
        ttk.Label(frame, text="dumbbell scale").grid(row=1, column=0, sticky='w', padx=5, pady=2)
        self.add_widget(frame, "", 'entry', 'dumbbell_scale').grid(row=1, column=1, sticky='ew', padx=5, pady=2)
        ttk.Label(frame, text="dumbbell gradient descent factor").grid(row=2, column=0, sticky='w', padx=5, pady=2)
        self.add_widget(frame, "", 'entry', 'dumbbell_gradient_descent').grid(row=2, column=1, sticky='ew', padx=5, pady=2)
        ttk.Label(frame, text="weight for dumbbell penalty").grid(row=3, column=0, sticky='w', padx=5, pady=2)
        self.add_widget(frame, "", 'entry', 'dumbbell_penalty_weight').grid(row=3, column=1, sticky='ew', padx=5, pady=2)
        ttk.Label(frame, text="step size through sequence").grid(row=4, column=0, sticky='w', padx=5, pady=2)
        self.add_widget(frame, "", 'entry', 'dumbbell_step').grid(row=4, column=1, sticky='ew', padx=5, pady=2)
        ttk.Label(frame, text="number of iterations per click").grid(row=5, column=0, sticky='w', padx=5, pady=2)
        self.add_widget(frame, "", 'entry', 'dumbbell_niter').grid(row=5, column=1, sticky='ew', padx=5, pady=2)
        frame.columnconfigure(1, weight=1)

    def load_values(self):
        """Load calibration parameter values"""
        params = self.experiment.pm.parameters
        num_cams = self.experiment.get_n_cam()

        # PTV params
        ptv_params = params.get('ptv', {})
        self.set_widget_value('h_image_size', ptv_params.get('imx', 1024))
        self.set_widget_value('v_image_size', ptv_params.get('imy', 1024))
        self.set_widget_value('h_pixel_size', ptv_params.get('pix_x', 0.01))
        self.set_widget_value('v_pixel_size', ptv_params.get('pix_y', 0.01))

        # Cal_ori params
        cal_ori_params = params.get('cal_ori', {})
        self.set_widget_value('cal_splitter', cal_ori_params.get('cal_splitter', False))
        self.set_widget_value('fixp_name', cal_ori_params.get('fixp_name', ''))
        cal_names = cal_ori_params.get('img_cal_name', [])
        ori_names = cal_ori_params.get('img_ori', [])
        for i in range(4):
            self.set_widget_value(f'cam_{i+1}', cal_names[i] if i < len(cal_names) else '')
            self.set_widget_value(f'ori_cam_{i+1}', ori_names[i] if i < len(ori_names) else '')

        # Detect_plate params
        detect_plate_params = params.get('detect_plate', {})
        for i in range(4):
            self.set_widget_value(f'gvth_{i+1}', detect_plate_params.get(f'gvth_{i+1}', 0))
        self.set_widget_value('tolerable_discontinuity', detect_plate_params.get('tol_dis', 0))
        self.set_widget_value('min_npix', detect_plate_params.get('min_npix', 1))
        self.set_widget_value('max_npix', detect_plate_params.get('max_npix', 100))
        self.set_widget_value('min_npix_x', detect_plate_params.get('min_npix_x', 1))
        self.set_widget_value('max_npix_x', detect_plate_params.get('max_npix_x', 100))
        self.set_widget_value('min_npix_y', detect_plate_params.get('min_npix_y', 1))
        self.set_widget_value('max_npix_y', detect_plate_params.get('max_npix_y', 100))
        self.set_widget_value('sum_of_grey', detect_plate_params.get('sum_grey', 0))
        self.set_widget_value('size_of_crosses', detect_plate_params.get('size_cross', 3))

        # Man_ori params
        man_ori_params = params.get('man_ori', {})
        nr = man_ori_params.get('nr', [0]*16)
        for i in range(4):
            for j in range(4):
                self.set_widget_value(f'img_{i+1}_p{j+1}', nr[i*4+j] if (i*4+j) < len(nr) else 0)

        # Examine params
        examine_params = params.get('examine', {})
        self.set_widget_value('Examine_Flag', examine_params.get('Examine_Flag', False))
        self.set_widget_value('Combine_Flag', examine_params.get('Combine_Flag', False))

        # Orient params
        orient_params = params.get('orient', {})
        self.set_widget_value('point_number_of_orientation', orient_params.get('pnfo', 0))
        self.set_widget_value('cc', orient_params.get('cc', False))
        self.set_widget_value('xh', orient_params.get('xh', False))
        self.set_widget_value('yh', orient_params.get('yh', False))
        self.set_widget_value('k1', orient_params.get('k1', False))
        self.set_widget_value('k2', orient_params.get('k2', False))
        self.set_widget_value('k3', orient_params.get('k3', False))
        self.set_widget_value('p1', orient_params.get('p1', False))
        self.set_widget_value('p2', orient_params.get('p2', False))
        self.set_widget_value('scale', orient_params.get('scale', False))
        self.set_widget_value('shear', orient_params.get('shear', False))
        self.set_widget_value('interf', orient_params.get('interf', False))

        # Shaking params
        shaking_params = params.get('shaking', {})
        self.set_widget_value('shaking_first_frame', shaking_params.get('shaking_first_frame', 0))
        self.set_widget_value('shaking_last_frame', shaking_params.get('shaking_last_frame', 0))
        self.set_widget_value('shaking_max_num_points', shaking_params.get('shaking_max_num_points', 0))
        self.set_widget_value('shaking_max_num_frames', shaking_params.get('shaking_max_num_frames', 0))

        # Dumbbell params
        dumbbell_params = params.get('dumbbell', {})
        self.set_widget_value('dumbbell_eps', dumbbell_params.get('dumbbell_eps', 0.0))
        self.set_widget_value('dumbbell_scale', dumbbell_params.get('dumbbell_scale', 0.0))
        self.set_widget_value('dumbbell_gradient_descent', dumbbell_params.get('dumbbell_gradient_descent', 0.0))
        self.set_widget_value('dumbbell_penalty_weight', dumbbell_params.get('dumbbell_penalty_weight', 0.0))
        self.set_widget_value('dumbbell_step', dumbbell_params.get('dumbbell_step', 0))
        self.set_widget_value('dumbbell_niter', dumbbell_params.get('dumbbell_niter', 0))

    def save_values(self):
        """Save calibration parameter values"""
        params = self.experiment.pm.parameters
        num_cams = self.experiment.get_n_cam()

        # Ensure sections exist
        for key in ['ptv', 'cal_ori', 'detect_plate', 'man_ori', 'examine', 'orient', 'shaking', 'dumbbell']:
            if key not in params:
                params[key] = {}

        # PTV params
        params['ptv']['imx'] = int(self.get_widget_value('h_image_size'))
        params['ptv']['imy'] = int(self.get_widget_value('v_image_size'))
        params['ptv']['pix_x'] = float(self.get_widget_value('h_pixel_size'))
        params['ptv']['pix_y'] = float(self.get_widget_value('v_pixel_size'))

        # Cal_ori params
        params['cal_ori']['cal_splitter'] = self.get_widget_value('cal_splitter')
        params['cal_ori']['fixp_name'] = self.get_widget_value('fixp_name')
        params['cal_ori']['img_cal_name'] = [self.get_widget_value(f'cam_{i+1}') for i in range(num_cams)]
        params['cal_ori']['img_ori'] = [self.get_widget_value(f'ori_cam_{i+1}') for i in range(num_cams)]

        # Detect_plate params
        for i in range(4):
            params['detect_plate'][f'gvth_{i+1}'] = int(self.get_widget_value(f'gvth_{i+1}'))
        params['detect_plate']['tol_dis'] = int(self.get_widget_value('tolerable_discontinuity'))
        params['detect_plate']['min_npix'] = int(self.get_widget_value('min_npix'))
        params['detect_plate']['max_npix'] = int(self.get_widget_value('max_npix'))
        params['detect_plate']['min_npix_x'] = int(self.get_widget_value('min_npix_x'))
        params['detect_plate']['max_npix_x'] = int(self.get_widget_value('max_npix_x'))
        params['detect_plate']['min_npix_y'] = int(self.get_widget_value('min_npix_y'))
        params['detect_plate']['max_npix_y'] = int(self.get_widget_value('max_npix_y'))
        params['detect_plate']['sum_grey'] = int(self.get_widget_value('sum_of_grey'))
        params['detect_plate']['size_cross'] = int(self.get_widget_value('size_of_crosses'))

        # Man_ori params
        nr = []
        for i in range(4):
            for j in range(4):
                nr.append(int(self.get_widget_value(f'img_{i+1}_p{j+1}')))
        params['man_ori']['nr'] = nr

        # Examine params
        params['examine']['Examine_Flag'] = self.get_widget_value('Examine_Flag')
        params['examine']['Combine_Flag'] = self.get_widget_value('Combine_Flag')

        # Orient params
        params['orient']['pnfo'] = int(self.get_widget_value('point_number_of_orientation'))
        params['orient']['cc'] = self.get_widget_value('cc')
        params['orient']['xh'] = self.get_widget_value('xh')
        params['orient']['yh'] = self.get_widget_value('yh')
        params['orient']['k1'] = self.get_widget_value('k1')
        params['orient']['k2'] = self.get_widget_value('k2')
        params['orient']['k3'] = self.get_widget_value('k3')
        params['orient']['p1'] = self.get_widget_value('p1')
        params['orient']['p2'] = self.get_widget_value('p2')
        params['orient']['scale'] = self.get_widget_value('scale')
        params['orient']['shear'] = self.get_widget_value('shear')
        params['orient']['interf'] = self.get_widget_value('interf')

        # Shaking params
        params['shaking']['shaking_first_frame'] = int(self.get_widget_value('shaking_first_frame'))
        params['shaking']['shaking_last_frame'] = int(self.get_widget_value('shaking_last_frame'))
        params['shaking']['shaking_max_num_points'] = int(self.get_widget_value('shaking_max_num_points'))
        params['shaking']['shaking_max_num_frames'] = int(self.get_widget_value('shaking_max_num_frames'))

        # Dumbbell params
        params['dumbbell']['dumbbell_eps'] = float(self.get_widget_value('dumbbell_eps'))
        params['dumbbell']['dumbbell_scale'] = float(self.get_widget_value('dumbbell_scale'))
        params['dumbbell']['dumbbell_gradient_descent'] = float(self.get_widget_value('dumbbell_gradient_descent'))
        params['dumbbell']['dumbbell_penalty_weight'] = float(self.get_widget_value('dumbbell_penalty_weight'))
        params['dumbbell']['dumbbell_step'] = int(self.get_widget_value('dumbbell_step'))
        params['dumbbell']['dumbbell_niter'] = int(self.get_widget_value('dumbbell_niter'))


class TrackingParamsWindow(BaseParamWindow):
    """TTK version of Tracking Parameters GUI"""

    def __init__(self, parent, experiment):
        super().__init__(parent, experiment, "Tracking Parameters")
        self.geometry('500x400')
        self.create_widgets()
        self.load_values()

    def create_widgets(self):
        """Create all tracking parameter widgets in a single tab"""
        tab = self.create_tab("Tracking Parameters")
        
        frame = ttk.Frame(tab)
        frame.pack(fill='both', expand=True, padx=10, pady=10)

        ttk.Label(frame, text="dvxmin:").grid(row=0, column=0, sticky='w', pady=2)
        self.add_widget(frame, "", 'entry', 'dvxmin').grid(row=0, column=1, sticky='ew', pady=2)
        ttk.Label(frame, text="dvxmax:").grid(row=0, column=2, sticky='w', padx=5, pady=2)
        self.add_widget(frame, "", 'entry', 'dvxmax').grid(row=0, column=3, sticky='ew', pady=2)

        ttk.Label(frame, text="dvymin:").grid(row=1, column=0, sticky='w', pady=2)
        self.add_widget(frame, "", 'entry', 'dvymin').grid(row=1, column=1, sticky='ew', pady=2)
        ttk.Label(frame, text="dvymax:").grid(row=1, column=2, sticky='w', padx=5, pady=2)
        self.add_widget(frame, "", 'entry', 'dvymax').grid(row=1, column=3, sticky='ew', pady=2)

        ttk.Label(frame, text="dvzmin:").grid(row=2, column=0, sticky='w', pady=2)
        self.add_widget(frame, "", 'entry', 'dvzmin').grid(row=2, column=1, sticky='ew', pady=2)
        ttk.Label(frame, text="dvzmax:").grid(row=2, column=2, sticky='w', padx=5, pady=2)
        self.add_widget(frame, "", 'entry', 'dvzmax').grid(row=2, column=3, sticky='ew', pady=2)

        ttk.Label(frame, text="angle [gon]:").grid(row=3, column=0, sticky='w', pady=5)
        self.add_widget(frame, "", 'entry', 'angle').grid(row=3, column=1, columnspan=3, sticky='ew', pady=5)

        ttk.Label(frame, text="dacc:").grid(row=4, column=0, sticky='w', pady=5)
        self.add_widget(frame, "", 'entry', 'dacc').grid(row=4, column=1, columnspan=3, sticky='ew', pady=5)

        self.add_widget(frame, "Add new particles?", 'checkbutton', 'flagNewParticles').grid(row=5, column=0, columnspan=4, sticky='w', pady=10)

        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(3, weight=1)

    def load_values(self):
        """Load tracking parameter values"""
        params = self.experiment.pm.parameters.get('track', {})
        self.set_widget_value('dvxmin', params.get('dvxmin', 0.0))
        self.set_widget_value('dvxmax', params.get('dvxmax', 0.0))
        self.set_widget_value('dvymin', params.get('dvymin', 0.0))
        self.set_widget_value('dvymax', params.get('dvymax', 0.0))
        self.set_widget_value('dvzmin', params.get('dvzmin', 0.0))
        self.set_widget_value('dvzmax', params.get('dvzmax', 0.0))
        self.set_widget_value('angle', params.get('angle', 0.0))
        self.set_widget_value('dacc', params.get('dacc', 0.0))
        self.set_widget_value('flagNewParticles', params.get('flagNewParticles', True))

    def save_values(self):
        """Save tracking parameter values"""
        if 'track' not in self.experiment.pm.parameters:
            self.experiment.pm.parameters['track'] = {}
            
        self.experiment.pm.parameters['track'].update({
            'dvxmin': float(self.get_widget_value('dvxmin')),
            'dvxmax': float(self.get_widget_value('dvxmax')),
            'dvymin': float(self.get_widget_value('dvymin')),
            'dvymax': float(self.get_widget_value('dvymax')),
            'dvzmin': float(self.get_widget_value('dvzmin')),
            'dvzmax': float(self.get_widget_value('dvzmax')),
            'angle': float(self.get_widget_value('angle')),
            'dacc': float(self.get_widget_value('dacc')),
            'flagNewParticles': self.get_widget_value('flagNewParticles')
        })