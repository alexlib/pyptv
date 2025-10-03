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
        self.create_orientation_tab()
        self.create_manual_orientation_tab()
    
    def create_orientation_tab(self):
        """Create Orientation tab"""
        tab = self.create_tab("Orientation")
        
        ttk.Label(tab, text="Calibration orientation parameters").pack(pady=20)
        
        # Add orientation parameter widgets here
        ttk.Label(tab, text="Fixp_x:").grid(row=0, column=0, sticky='w', pady=5)
        self.add_widget(tab, "", 'entry', 'fixp_x').grid(row=0, column=1, sticky='ew', pady=5)
        
        ttk.Label(tab, text="Fixp_y:").grid(row=1, column=0, sticky='w', pady=5)
        self.add_widget(tab, "", 'entry', 'fixp_y').grid(row=1, column=1, sticky='ew', pady=5)
        
        ttk.Label(tab, text="Fixp_z:").grid(row=2, column=0, sticky='w', pady=5)
        self.add_widget(tab, "", 'entry', 'fixp_z').grid(row=2, column=1, sticky='ew', pady=5)
        
        tab.columnconfigure(1, weight=1)
    
    def create_manual_orientation_tab(self):
        """Create Manual Orientation tab"""
        tab = self.create_tab("Manual Orientation")
        
        ttk.Label(tab, text="Manual orientation parameters").pack(pady=20)
        
        # Add manual orientation widgets here
        for i in range(4):
            ttk.Label(tab, text=f"Camera {i+1} parameters:", font=('Arial', 10, 'bold')).grid(row=i*3, column=0, columnspan=2, sticky='w', pady=(10,5))
            
            ttk.Label(tab, text="X0:").grid(row=i*3+1, column=0, sticky='w', pady=2)
            self.add_widget(tab, "", 'entry', f'x0_{i}').grid(row=i*3+1, column=1, sticky='ew', pady=2)
            
            ttk.Label(tab, text="Y0:").grid(row=i*3+2, column=0, sticky='w', pady=2)
            self.add_widget(tab, "", 'entry', f'y0_{i}').grid(row=i*3+2, column=1, sticky='ew', pady=2)
        
        tab.columnconfigure(1, weight=1)
    
    def load_values(self):
        """Load calibration parameter values"""
        params = self.experiment.pm.parameters
        
        # Load cal_ori parameters
        cal_ori_params = params.get('cal_ori', {})
        self.set_widget_value('fixp_x', str(cal_ori_params.get('fixp_x', 0.0)))
        self.set_widget_value('fixp_y', str(cal_ori_params.get('fixp_y', 0.0)))
        self.set_widget_value('fixp_z', str(cal_ori_params.get('fixp_z', 0.0)))
        
        # Load manual orientation parameters
        man_ori_params = params.get('man_ori', {})
        for i in range(4):
            cam_params = man_ori_params.get(f'cam_{i}', {})
            self.set_widget_value(f'x0_{i}', str(cam_params.get('x0', 0.0)))
            self.set_widget_value(f'y0_{i}', str(cam_params.get('y0', 0.0)))
    
    def save_values(self):
        """Save calibration parameter values"""
        params = self.experiment.pm.parameters
        
        # Save cal_ori parameters
        if 'cal_ori' not in params:
            params['cal_ori'] = {}
        
        params['cal_ori'].update({
            'fixp_x': float(self.get_widget_value('fixp_x')),
            'fixp_y': float(self.get_widget_value('fixp_y')),
            'fixp_z': float(self.get_widget_value('fixp_z')),
        })
        
        # Save manual orientation parameters
        if 'man_ori' not in params:
            params['man_ori'] = {}
        
        for i in range(4):
            cam_key = f'cam_{i}'
            if cam_key not in params['man_ori']:
                params['man_ori'][cam_key] = {}
            
            params['man_ori'][cam_key].update({
                'x0': float(self.get_widget_value(f'x0_{i}')),
                'y0': float(self.get_widget_value(f'y0_{i}')),
            })


class TrackingParamsWindow(BaseParamWindow):
    """TTK version of Tracking Parameters GUI"""
    
    def __init__(self, parent, experiment):
        super().__init__(parent, experiment, "Tracking Parameters")
        self.create_tabs()
        self.load_values()
    
    def create_tabs(self):
        """Create tracking parameter tabs"""
        self.create_tracking_tab()
        self.create_examine_tab()
    
    def create_tracking_tab(self):
        """Create Tracking tab"""
        tab = self.create_tab("Tracking")
        
        ttk.Label(tab, text="Velocity range [mm/timestep]:").grid(row=0, column=0, sticky='w', pady=5)
        self.add_widget(tab, "", 'entry', 'dvxmin').grid(row=0, column=1, sticky='ew', pady=5)
        self.add_widget(tab, "", 'entry', 'dvxmax').grid(row=0, column=2, sticky='ew', pady=5)
        
        ttk.Label(tab, text="Acceleration range [mm/timestep²]:").grid(row=1, column=0, sticky='w', pady=5)
        self.add_widget(tab, "", 'entry', 'daxmin').grid(row=1, column=1, sticky='ew', pady=5)
        self.add_widget(tab, "", 'entry', 'daxmax').grid(row=1, column=2, sticky='ew', pady=5)
        
        ttk.Label(tab, text="Angle range [rad]:").grid(row=2, column=0, sticky='w', pady=5)
        self.add_widget(tab, "", 'entry', 'angle_acc').grid(row=2, column=1, sticky='ew', pady=5)
        
        for i in range(3):
            tab.columnconfigure(i, weight=1)
    
    def create_examine_tab(self):
        """Create Examine tab"""
        tab = self.create_tab("Examine")
        
        ttk.Label(tab, text="Examine parameters").pack(pady=20)
        
        ttk.Label(tab, text="Post processing flag:").grid(row=0, column=0, sticky='w', pady=5)
        self.add_widget(tab, "", 'checkbutton', 'post_flag').grid(row=0, column=1, sticky='w', pady=5)
        
        tab.columnconfigure(1, weight=1)
    
    def load_values(self):
        """Load tracking parameter values"""
        params = self.experiment.pm.parameters
        
        # Load tracking parameters
        track_params = params.get('tracking', {})
        self.set_widget_value('dvxmin', str(track_params.get('dvxmin', -10.0)))
        self.set_widget_value('dvxmax', str(track_params.get('dvxmax', 10.0)))
        self.set_widget_value('daxmin', str(track_params.get('daxmin', -1.0)))
        self.set_widget_value('daxmax', str(track_params.get('daxmax', 1.0)))
        self.set_widget_value('angle_acc', str(track_params.get('angle_acc', 0.1)))
        
        # Load examine parameters
        examine_params = params.get('examine', {})
        self.set_widget_value('post_flag', examine_params.get('post_flag', False))
    
    def save_values(self):
        """Save tracking parameter values"""
        params = self.experiment.pm.parameters
        
        # Save tracking parameters
        if 'tracking' not in params:
            params['tracking'] = {}
        
        params['tracking'].update({
            'dvxmin': float(self.get_widget_value('dvxmin')),
            'dvxmax': float(self.get_widget_value('dvxmax')),
            'daxmin': float(self.get_widget_value('daxmin')),
            'daxmax': float(self.get_widget_value('daxmax')),
            'angle_acc': float(self.get_widget_value('angle_acc')),
        })
        
        # Save examine parameters
        if 'examine' not in params:
            params['examine'] = {}
        
        params['examine'].update({
            'post_flag': self.get_widget_value('post_flag'),
        })