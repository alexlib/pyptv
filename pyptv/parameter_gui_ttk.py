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
from pyptv.experiment import Experiment


class BaseParamWindow(tb.Window):
    """Base class for parameter editing windows"""
    
    def __init__(self, parent, experiment: Experiment, title: str):
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
    
    def __init__(self, parent, experiment: Experiment):
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
        
        ttk.Label(tab, text="Zmax").grid(row=0, column=4, sticky='w', pady=5)
        self.add_widget(tab, "", 'entry', 'zmax1').grid(row=0, column=5, sticky='ew', pady=5)
        self.add_widget(tab, "", 'entry', 'zmax2').grid(row=1, column=5, sticky='ew', pady=5)
        
        # Configure grid
        for i in range(6):
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
        self.widgets['num_cams']['var'].set(str(num_cams))
        self.widgets['splitter']['var'].set(bool(ptv_params.get('splitter', False)))
        self.widgets['allcam_flag']['var'].set(bool(ptv_params.get('allcam_flag', False)))
        self.widgets['hp_flag']['var'].set(bool(ptv_params.get('hp_flag', False)))
        self.widgets['mmp_n1']['var'].set(str(ptv_params.get('mmp_n1', 1.0)))
        self.widgets['mmp_n2']['var'].set(str(ptv_params.get('mmp_n2', 1.5)))
        self.widgets['mmp_n3']['var'].set(str(ptv_params.get('mmp_n3', 1.33)))
        self.widgets['mmp_d']['var'].set(str(ptv_params.get('mmp_d', 0.0)))
        
        # Image names
        img_names = ptv_params.get('img_name', [])
        for i in range(4):
            var_name = f'img_name_{i}'
            if i < len(img_names):
                self.widgets[var_name]['var'].set(str(img_names[i]))
            else:
                self.widgets[var_name]['var'].set('')
        
        # Calibration images
        img_cals = ptv_params.get('img_cal', [])
        for i in range(4):
            var_name = f'img_cal_{i}'
            if i < len(img_cals):
                self.widgets[var_name]['var'].set(str(img_cals[i]))
            else:
                self.widgets[var_name]['var'].set('')
        
        # Target recognition parameters
        targ_rec_params = params.get('targ_rec', {})
        gvthres = targ_rec_params.get('gvthres', [])
        for i in range(4):
            var_name = f'gvthres_{i}'
            if i < len(gvthres):
                self.widgets[var_name]['var'].set(str(gvthres[i]))
            else:
                self.widgets[var_name]['var'].set('0')
        
        self.widgets['nnmin']['var'].set(str(targ_rec_params.get('nnmin', 1)))
        self.widgets['nnmax']['var'].set(str(targ_rec_params.get('nnmax', 100)))
        self.widgets['sumg_min']['var'].set(str(targ_rec_params.get('sumg_min', 0)))
        self.widgets['disco']['var'].set(str(targ_rec_params.get('disco', 0)))
        self.widgets['cr_sz']['var'].set(str(targ_rec_params.get('cr_sz', 3)))
        
        # PFT version parameters
        pft_params = params.get('pft_version', {})
        self.widgets['existing_target']['var'].set(bool(pft_params.get('Existing_Target', False)))
        
        # Sequence parameters
        seq_params = params.get('sequence', {})
        self.widgets['seq_first']['var'].set(str(seq_params.get('first', 0)))
        self.widgets['seq_last']['var'].set(str(seq_params.get('last', 100)))
        
        base_names = seq_params.get('base_name', [])
        for i in range(4):
            var_name = f'base_name_{i}'
            if i < len(base_names):
                self.widgets[var_name]['var'].set(str(base_names[i]))
            else:
                self.widgets[var_name]['var'].set('')
        
        # Criteria parameters
        criteria_params = params.get('criteria', {})
        self.widgets['cnx']['var'].set(str(criteria_params.get('cnx', 0.0)))
        self.widgets['cny']['var'].set(str(criteria_params.get('cny', 0.0)))
        self.widgets['cn']['var'].set(str(criteria_params.get('cn', 0.0)))
        self.widgets['csumg']['var'].set(str(criteria_params.get('csumg', 0.0)))
        self.widgets['corrmin']['var'].set(str(criteria_params.get('corrmin', 0.0)))
        self.widgets['eps0']['var'].set(str(criteria_params.get('eps0', 0.0)))
        
        # Masking parameters
        masking_params = params.get('masking', {})
        self.widgets['mask_flag']['var'].set(bool(masking_params.get('mask_flag', False)))
        self.widgets['mask_base_name']['var'].set(str(masking_params.get('mask_base_name', '')))
        
        # Observation volume parameters
        X_lay = criteria_params.get('X_lay', [0, 100])
        Zmin_lay = criteria_params.get('Zmin_lay', [0, 0])
        Zmax_lay = criteria_params.get('Zmax_lay', [100, 100])
        
        self.widgets['xmin']['var'].set(str(X_lay[0] if len(X_lay) > 0 else 0))
        self.widgets['xmax']['var'].set(str(X_lay[1] if len(X_lay) > 1 else 100))
        self.widgets['zmin1']['var'].set(str(Zmin_lay[0] if len(Zmin_lay) > 0 else 0))
        self.widgets['zmin2']['var'].set(str(Zmin_lay[1] if len(Zmin_lay) > 1 else 0))
        self.widgets['zmax1']['var'].set(str(Zmax_lay[0] if len(Zmax_lay) > 0 else 100))
        self.widgets['zmax2']['var'].set(str(Zmax_lay[1] if len(Zmax_lay) > 1 else 100))
    
    def save_values(self):
        """Save parameter values back to experiment"""
        params = self.experiment.pm.parameters
        
        # Get number of cameras
        num_cams = int(self.widgets['num_cams']['var'].get())
        
        # Update PTV parameters
        if 'ptv' not in params:
            params['ptv'] = {}
        
        params['num_cams'] = num_cams
        params['ptv'].update({
            'splitter': self.widgets['splitter']['var'].get(),
            'allcam_flag': self.widgets['allcam_flag']['var'].get(),
            'hp_flag': self.widgets['hp_flag']['var'].get(),
            'mmp_n1': float(self.widgets['mmp_n1']['var'].get()),
            'mmp_n2': float(self.widgets['mmp_n2']['var'].get()),
            'mmp_n3': float(self.widgets['mmp_n3']['var'].get()),
            'mmp_d': float(self.widgets['mmp_d']['var'].get()),
        })
        
        # Update image names
        img_names = []
        for i in range(num_cams):
            var_name = f'img_name_{i}'
            img_names.append(self.widgets[var_name]['var'].get())
        params['ptv']['img_name'] = img_names
        
        # Update calibration images
        img_cals = []
        for i in range(num_cams):
            var_name = f'img_cal_{i}'
            img_cals.append(self.widgets[var_name]['var'].get())
        params['ptv']['img_cal'] = img_cals
        
        # Update target recognition parameters
        if 'targ_rec' not in params:
            params['targ_rec'] = {}
        
        gvthres = []
        for i in range(num_cams):
            var_name = f'gvthres_{i}'
            gvthres.append(int(self.widgets[var_name]['var'].get()))
        params['targ_rec']['gvthres'] = gvthres
        
        params['targ_rec'].update({
            'nnmin': int(self.widgets['nnmin']['var'].get()),
            'nnmax': int(self.widgets['nnmax']['var'].get()),
            'sumg_min': int(self.widgets['sumg_min']['var'].get()),
            'disco': int(self.widgets['disco']['var'].get()),
            'cr_sz': int(self.widgets['cr_sz']['var'].get()),
        })
        
        # Update PFT version parameters
        if 'pft_version' not in params:
            params['pft_version'] = {}
        params['pft_version']['Existing_Target'] = self.widgets['existing_target']['var'].get()
        
        # Update sequence parameters
        if 'sequence' not in params:
            params['sequence'] = {}
        
        base_names = []
        for i in range(num_cams):
            var_name = f'base_name_{i}'
            base_names.append(self.widgets[var_name]['var'].get())
        params['sequence'].update({
            'first': int(self.widgets['seq_first']['var'].get()),
            'last': int(self.widgets['seq_last']['var'].get()),
            'base_name': base_names,
        })
        
        # Update criteria parameters
        if 'criteria' not in params:
            params['criteria'] = {}
        
        params['criteria'].update({
            'cnx': float(self.widgets['cnx']['var'].get()),
            'cny': float(self.widgets['cny']['var'].get()),
            'cn': float(self.widgets['cn']['var'].get()),
            'csumg': float(self.widgets['csumg']['var'].get()),
            'corrmin': float(self.widgets['corrmin']['var'].get()),
            'eps0': float(self.widgets['eps0']['var'].get()),
            'X_lay': [int(self.widgets['xmin']['var'].get()), int(self.widgets['xmax']['var'].get())],
            'Zmin_lay': [int(self.widgets['zmin1']['var'].get()), int(self.widgets['zmin2']['var'].get())],
            'Zmax_lay': [int(self.widgets['zmax1']['var'].get()), int(self.widgets['zmax2']['var'].get())],
        })
        
        # Update masking parameters
        if 'masking' not in params:
            params['masking'] = {}
        params['masking'].update({
            'mask_flag': self.widgets['mask_flag']['var'].get(),
            'mask_base_name': self.widgets['mask_base_name']['var'].get(),
        })


class CalibParamsWindow(BaseParamWindow):
    """TTK version of Calib_Params GUI"""
    
    def __init__(self, parent, experiment: Experiment):
        super().__init__(parent, experiment, "Calibration Parameters")
        self.create_tabs()
        self.load_values()
    
    def create_tabs(self):
        """Create all calibration parameter tabs"""
        self.create_images_tab()
        self.create_detection_tab()
        self.create_orientation_tab()
        self.create_dumbbell_tab()
        self.create_shaking_tab()
    
    def create_images_tab(self):
        """Create Images Data tab"""
        tab = self.create_tab("Images Data")
        
        # Calibration images section
        ttk.Label(tab, text="Calibration images:", font=('Arial', 10, 'bold')).grid(row=0, column=0, columnspan=2, sticky='w', pady=5)
        
        for i in range(4):
            ttk.Label(tab, text=f"Calibration picture camera {i+1}").grid(row=1+i, column=0, sticky='w', pady=2)
            self.add_widget(tab, "", 'entry', f'cal_img_{i}').grid(row=1+i, column=1, sticky='ew', pady=2)
        
        # Orientation data section
        ttk.Label(tab, text="Orientation data:", font=('Arial', 10, 'bold')).grid(row=5, column=0, columnspan=2, sticky='w', pady=(20,5))
        
        for i in range(4):
            ttk.Label(tab, text=f"Orientation data picture camera {i+1}").grid(row=6+i, column=0, sticky='w', pady=2)
            self.add_widget(tab, "", 'entry', f'ori_img_{i}').grid(row=6+i, column=1, sticky='ew', pady=2)
        
        # Fixp name
        ttk.Label(tab, text="File of Coordinates on plate").grid(row=10, column=0, sticky='w', pady=(20,2))
        self.add_widget(tab, "", 'entry', 'fixp_name').grid(row=10, column=1, sticky='ew', pady=2)
        
        # Splitter checkbox
        self.add_widget(tab, "Split calibration image into 4?", 'checkbutton', 'cal_splitter').grid(row=11, column=0, columnspan=2, sticky='w', pady=(10,2))
        
        tab.columnconfigure(1, weight=1)
    
    def create_detection_tab(self):
        """Create Calibration Data Detection tab"""
        tab = self.create_tab("Calibration Data Detection")
        
        # Image properties section
        ttk.Label(tab, text="Image properties:", font=('Arial', 10, 'bold')).grid(row=0, column=0, columnspan=4, sticky='w', pady=5)
        
        ttk.Label(tab, text="Image size horizontal").grid(row=1, column=0, sticky='w', pady=2)
        self.add_widget(tab, "", 'entry', 'imx').grid(row=1, column=1, sticky='ew', pady=2)
        
        ttk.Label(tab, text="Image size vertical").grid(row=2, column=0, sticky='w', pady=2)
        self.add_widget(tab, "", 'entry', 'imy').grid(row=2, column=1, sticky='ew', pady=2)
        
        ttk.Label(tab, text="Pixel size horizontal").grid(row=1, column=2, sticky='w', pady=2)
        self.add_widget(tab, "", 'entry', 'pix_x').grid(row=1, column=3, sticky='ew', pady=2)
        
        ttk.Label(tab, text="Pixel size vertical").grid(row=2, column=2, sticky='w', pady=2)
        self.add_widget(tab, "", 'entry', 'pix_y').grid(row=2, column=3, sticky='ew', pady=2)
        
        # Gray value thresholds
        ttk.Label(tab, text="Grayvalue threshold:", font=('Arial', 10, 'bold')).grid(row=3, column=0, columnspan=4, sticky='w', pady=(20,5))
        
        for i in range(4):
            ttk.Label(tab, text=f"Camera {i+1}").grid(row=4, column=i, sticky='w', padx=5)
            self.add_widget(tab, "", 'entry', f'detect_gvth_{i}').grid(row=5, column=i, sticky='ew', padx=5)
        
        # Detection parameters
        ttk.Label(tab, text="Detection parameters:", font=('Arial', 10, 'bold')).grid(row=6, column=0, columnspan=4, sticky='w', pady=(20,5))
        
        ttk.Label(tab, text="min npix").grid(row=7, column=0, sticky='w', pady=2)
        self.add_widget(tab, "", 'entry', 'detect_min_npix').grid(row=7, column=1, sticky='ew', pady=2)
        
        ttk.Label(tab, text="max npix").grid(row=8, column=0, sticky='w', pady=2)
        self.add_widget(tab, "", 'entry', 'detect_max_npix').grid(row=8, column=1, sticky='ew', pady=2)
        
        ttk.Label(tab, text="Sum of greyvalue").grid(row=7, column=2, sticky='w', pady=2)
        self.add_widget(tab, "", 'entry', 'detect_sum_grey').grid(row=7, column=3, sticky='ew', pady=2)
        
        ttk.Label(tab, text="Size of crosses").grid(row=8, column=2, sticky='w', pady=2)
        self.add_widget(tab, "", 'entry', 'detect_size_cross').grid(row=8, column=3, sticky='ew', pady=2)
        
        # Additional parameters
        ttk.Label(tab, text="Tolerable discontinuity").grid(row=9, column=0, sticky='w', pady=(10,2))
        self.add_widget(tab, "", 'entry', 'detect_tol_dis').grid(row=9, column=1, sticky='ew', pady=2)
        
        # Configure grid
        for i in range(4):
            tab.columnconfigure(i, weight=1)
    
    def create_orientation_tab(self):
        """Create Manual Pre-orientation tab"""
        tab = self.create_tab("Manual Pre-orientation")
        
        # Manual orientation points for each camera
        for cam in range(4):
            ttk.Label(tab, text=f"Camera {cam+1} orientation points:", font=('Arial', 10, 'bold')).grid(
                row=cam*5, column=0, columnspan=8, sticky='w', pady=(10 if cam > 0 else 5, 5))
            
            for point in range(4):
                ttk.Label(tab, text=f"P{point+1}").grid(row=cam*5 + 1, column=point*2, sticky='w', padx=5)
                self.add_widget(tab, "", 'entry', f'cam{cam+1}_p{point+1}').grid(
                    row=cam*5 + 2, column=point*2, columnspan=2, sticky='ew', padx=5)
        
        # Orientation parameters section
        ttk.Label(tab, text="Orientation Parameters:", font=('Arial', 10, 'bold')).grid(
            row=20, column=0, columnspan=8, sticky='w', pady=(20,5))
        
        ttk.Label(tab, text="Point number of orientation").grid(row=21, column=0, sticky='w', pady=2)
        self.add_widget(tab, "", 'entry', 'pnfo').grid(row=21, column=1, columnspan=2, sticky='ew', pady=2)
        
        # Lens distortion checkboxes
        ttk.Label(tab, text="Lens distortion (Brown):", font=('Arial', 9, 'bold')).grid(row=22, column=0, columnspan=4, sticky='w', pady=(10,2))
        
        distortion_checks = ['cc', 'xh', 'yh', 'k1', 'k2', 'k3', 'p1', 'p2']
        for i, check in enumerate(distortion_checks):
            self.add_widget(tab, check.upper(), 'checkbutton', f'orient_{check}').grid(
                row=23 + i//4, column=i%4, sticky='w', pady=1)
        
        # Affine transformation
        ttk.Label(tab, text="Affine transformation:", font=('Arial', 9, 'bold')).grid(row=25, column=4, columnspan=2, sticky='w', pady=(10,2))
        
        self.add_widget(tab, "scale", 'checkbutton', 'orient_scale').grid(row=26, column=4, sticky='w', pady=1)
        self.add_widget(tab, "shear", 'checkbutton', 'orient_shear').grid(row=27, column=4, sticky='w', pady=1)
        
        # Additional flags
        self.add_widget(tab, "Calibrate with different Z", 'checkbutton', 'examine_flag').grid(row=28, column=0, columnspan=3, sticky='w', pady=(10,2))
        self.add_widget(tab, "Combine preprocessed planes", 'checkbutton', 'combine_flag').grid(row=29, column=0, columnspan=3, sticky='w', pady=2)
        self.add_widget(tab, "Interfaces check box", 'checkbutton', 'interf_flag').grid(row=28, column=4, columnspan=2, sticky='w', pady=2)
        
        # Configure grid
        for i in range(8):
            tab.columnconfigure(i, weight=1)
    
    def create_dumbbell_tab(self):
        """Create Dumbbell calibration tab"""
        tab = self.create_tab("Dumbbell Calibration")
        
        ttk.Label(tab, text="Dumbbell epsilon").grid(row=0, column=0, sticky='w', pady=5)
        self.add_widget(tab, "", 'entry', 'dumbbell_eps').grid(row=0, column=1, sticky='ew', pady=5)
        
        ttk.Label(tab, text="Dumbbell scale").grid(row=1, column=0, sticky='w', pady=5)
        self.add_widget(tab, "", 'entry', 'dumbbell_scale').grid(row=1, column=1, sticky='ew', pady=5)
        
        ttk.Label(tab, text="Dumbbell gradient descent factor").grid(row=2, column=0, sticky='w', pady=5)
        self.add_widget(tab, "", 'entry', 'dumbbell_gradient_descent').grid(row=2, column=1, sticky='ew', pady=5)
        
        ttk.Label(tab, text="Weight for dumbbell penalty").grid(row=3, column=0, sticky='w', pady=5)
        self.add_widget(tab, "", 'entry', 'dumbbell_penalty_weight').grid(row=3, column=1, sticky='ew', pady=5)
        
        ttk.Label(tab, text="Step size through sequence").grid(row=4, column=0, sticky='w', pady=5)
        self.add_widget(tab, "", 'entry', 'dumbbell_step').grid(row=4, column=1, sticky='ew', pady=5)
        
        ttk.Label(tab, text="Number of iterations per click").grid(row=5, column=0, sticky='w', pady=5)
        self.add_widget(tab, "", 'entry', 'dumbbell_niter').grid(row=5, column=1, sticky='ew', pady=5)
        
        tab.columnconfigure(1, weight=1)
    
    def create_shaking_tab(self):
        """Create Shaking calibration tab"""
        tab = self.create_tab("Shaking Calibration")
        
        ttk.Label(tab, text="Shaking first frame").grid(row=0, column=0, sticky='w', pady=5)
        self.add_widget(tab, "", 'entry', 'shaking_first_frame').grid(row=0, column=1, sticky='ew', pady=5)
        
        ttk.Label(tab, text="Shaking last frame").grid(row=1, column=0, sticky='w', pady=5)
        self.add_widget(tab, "", 'entry', 'shaking_last_frame').grid(row=1, column=1, sticky='ew', pady=5)
        
        ttk.Label(tab, text="Shaking max num points").grid(row=2, column=0, sticky='w', pady=5)
        self.add_widget(tab, "", 'entry', 'shaking_max_num_points').grid(row=2, column=1, sticky='ew', pady=5)
        
        ttk.Label(tab, text="Shaking max num frames").grid(row=3, column=0, sticky='w', pady=5)
        self.add_widget(tab, "", 'entry', 'shaking_max_num_frames').grid(row=3, column=1, sticky='ew', pady=5)
        
        tab.columnconfigure(1, weight=1)
    
    def load_values(self):
        """Load current calibration parameter values from experiment"""
        params = self.experiment.pm.parameters
        num_cams = self.experiment.get_n_cam()
        
        # PTV parameters (for image properties)
        ptv_params = params.get('ptv', {})
        self.widgets['imx']['var'].set(str(ptv_params.get('imx', 1024)))
        self.widgets['imy']['var'].set(str(ptv_params.get('imy', 1024)))
        self.widgets['pix_x']['var'].set(str(ptv_params.get('pix_x', 1.0)))
        self.widgets['pix_y']['var'].set(str(ptv_params.get('pix_y', 1.0)))
        
        # Cal_ori parameters
        cal_ori_params = params.get('cal_ori', {})
        
        # Calibration images
        cal_names = cal_ori_params.get('img_cal_name', [])
        for i in range(num_cams):
            var_name = f'cal_img_{i}'
            if i < len(cal_names):
                self.widgets[var_name]['var'].set(str(cal_names[i]))
            else:
                self.widgets[var_name]['var'].set('')
        
        # Orientation images
        ori_names = cal_ori_params.get('img_ori', [])
        for i in range(num_cams):
            var_name = f'ori_img_{i}'
            if i < len(ori_names):
                self.widgets[var_name]['var'].set(str(ori_names[i]))
            else:
                self.widgets[var_name]['var'].set('')
        
        self.widgets['fixp_name']['var'].set(str(cal_ori_params.get('fixp_name', '')))
        self.widgets['cal_splitter']['var'].set(bool(cal_ori_params.get('cal_splitter', False)))
        
        # Detect_plate parameters
        detect_params = params.get('detect_plate', {})
        gvthres = detect_params.get('gvthres', [0, 0, 0, 0])
        for i in range(num_cams):
            var_name = f'detect_gvth_{i}'
            if i < len(gvthres):
                self.widgets[var_name]['var'].set(str(gvthres[i]))
            else:
                self.widgets[var_name]['var'].set('0')
        
        self.widgets['detect_min_npix']['var'].set(str(detect_params.get('min_npix', 1)))
        self.widgets['detect_max_npix']['var'].set(str(detect_params.get('max_npix', 100)))
        self.widgets['detect_sum_grey']['var'].set(str(detect_params.get('sum_grey', 0)))
        self.widgets['detect_size_cross']['var'].set(str(detect_params.get('size_cross', 3)))
        self.widgets['detect_tol_dis']['var'].set(str(detect_params.get('tol_dis', 0)))
        
        # Man_ori parameters
        man_ori_params = params.get('man_ori', {})
        nr = man_ori_params.get('nr', [])
        for cam in range(num_cams):
            for point in range(4):
                var_name = f'cam{cam+1}_p{point+1}'
                idx = cam * 4 + point
                if idx < len(nr):
                    self.widgets[var_name]['var'].set(str(nr[idx]))
                else:
                    self.widgets[var_name]['var'].set('0')
        
        # Orient parameters
        orient_params = params.get('orient', {})
        self.widgets['pnfo']['var'].set(str(orient_params.get('pnfo', 0)))
        self.widgets['orient_cc']['var'].set(bool(orient_params.get('cc', False)))
        self.widgets['orient_xh']['var'].set(bool(orient_params.get('xh', False)))
        self.widgets['orient_yh']['var'].set(bool(orient_params.get('yh', False)))
        self.widgets['orient_k1']['var'].set(bool(orient_params.get('k1', False)))
        self.widgets['orient_k2']['var'].set(bool(orient_params.get('k2', False)))
        self.widgets['orient_k3']['var'].set(bool(orient_params.get('k3', False)))
        self.widgets['orient_p1']['var'].set(bool(orient_params.get('p1', False)))
        self.widgets['orient_p2']['var'].set(bool(orient_params.get('p2', False)))
        self.widgets['orient_scale']['var'].set(bool(orient_params.get('scale', False)))
        self.widgets['orient_shear']['var'].set(bool(orient_params.get('shear', False)))
        self.widgets['interf_flag']['var'].set(bool(orient_params.get('interf', False)))
        
        # Examine parameters
        examine_params = params.get('examine', {})
        self.widgets['examine_flag']['var'].set(bool(examine_params.get('Examine_Flag', False)))
        self.widgets['combine_flag']['var'].set(bool(examine_params.get('Combine_Flag', False)))
        
        # Dumbbell parameters
        dumbbell_params = params.get('dumbbell', {})
        self.widgets['dumbbell_eps']['var'].set(str(dumbbell_params.get('dumbbell_eps', 0.0)))
        self.widgets['dumbbell_scale']['var'].set(str(dumbbell_params.get('dumbbell_scale', 1.0)))
        self.widgets['dumbbell_gradient_descent']['var'].set(str(dumbbell_params.get('dumbbell_gradient_descent', 1.0)))
        self.widgets['dumbbell_penalty_weight']['var'].set(str(dumbbell_params.get('dumbbell_penalty_weight', 1.0)))
        self.widgets['dumbbell_step']['var'].set(str(dumbbell_params.get('dumbbell_step', 1)))
        self.widgets['dumbbell_niter']['var'].set(str(dumbbell_params.get('dumbbell_niter', 10)))
        
        # Shaking parameters
        shaking_params = params.get('shaking', {})
        self.widgets['shaking_first_frame']['var'].set(str(shaking_params.get('shaking_first_frame', 0)))
        self.widgets['shaking_last_frame']['var'].set(str(shaking_params.get('shaking_last_frame', 100)))
        self.widgets['shaking_max_num_points']['var'].set(str(shaking_params.get('shaking_max_num_points', 100)))
        self.widgets['shaking_max_num_frames']['var'].set(str(shaking_params.get('shaking_max_num_frames', 10)))
    
    def save_values(self):
        """Save calibration parameter values back to experiment"""
        params = self.experiment.pm.parameters
        num_cams = int(self.widgets['num_cams']['var'].get()) if 'num_cams' in self.widgets else self.experiment.get_n_cam()
        
        # Update PTV parameters (image properties)
        if 'ptv' not in params:
            params['ptv'] = {}
        params['ptv'].update({
            'imx': int(self.widgets['imx']['var'].get()),
            'imy': int(self.widgets['imy']['var'].get()),
            'pix_x': float(self.widgets['pix_x']['var'].get()),
            'pix_y': float(self.widgets['pix_y']['var'].get()),
        })
        
        # Update cal_ori parameters
        if 'cal_ori' not in params:
            params['cal_ori'] = {}
        
        # Calibration images
        cal_names = []
        for i in range(num_cams):
            var_name = f'cal_img_{i}'
            cal_names.append(self.widgets[var_name]['var'].get())
        params['cal_ori']['img_cal_name'] = cal_names
        
        # Orientation images
        ori_names = []
        for i in range(num_cams):
            var_name = f'ori_img_{i}'
            ori_names.append(self.widgets[var_name]['var'].get())
        params['cal_ori']['img_ori'] = ori_names
        
        params['cal_ori'].update({
            'fixp_name': self.widgets['fixp_name']['var'].get(),
            'cal_splitter': self.widgets['cal_splitter']['var'].get(),
        })
        
        # Update detect_plate parameters
        if 'detect_plate' not in params:
            params['detect_plate'] = {}
        
        gvthres = []
        for i in range(num_cams):
            var_name = f'detect_gvth_{i}'
            gvthres.append(int(self.widgets[var_name]['var'].get()))
        params['detect_plate']['gvthres'] = gvthres
        
        params['detect_plate'].update({
            'min_npix': int(self.widgets['detect_min_npix']['var'].get()),
            'max_npix': int(self.widgets['detect_max_npix']['var'].get()),
            'sum_grey': int(self.widgets['detect_sum_grey']['var'].get()),
            'size_cross': int(self.widgets['detect_size_cross']['var'].get()),
            'tol_dis': int(self.widgets['detect_tol_dis']['var'].get()),
        })
        
        # Update man_ori parameters
        if 'man_ori' not in params:
            params['man_ori'] = {}
        
        nr = []
        for cam in range(num_cams):
            for point in range(4):
                var_name = f'cam{cam+1}_p{point+1}'
                nr.append(int(self.widgets[var_name]['var'].get()))
        params['man_ori']['nr'] = nr
        
        # Update orient parameters
        if 'orient' not in params:
            params['orient'] = {}
        
        params['orient'].update({
            'pnfo': int(self.widgets['pnfo']['var'].get()),
            'cc': self.widgets['orient_cc']['var'].get(),
            'xh': self.widgets['orient_xh']['var'].get(),
            'yh': self.widgets['orient_yh']['var'].get(),
            'k1': self.widgets['orient_k1']['var'].get(),
            'k2': self.widgets['orient_k2']['var'].get(),
            'k3': self.widgets['orient_k3']['var'].get(),
            'p1': self.widgets['orient_p1']['var'].get(),
            'p2': self.widgets['orient_p2']['var'].get(),
            'scale': self.widgets['orient_scale']['var'].get(),
            'shear': self.widgets['orient_shear']['var'].get(),
            'interf': self.widgets['interf_flag']['var'].get(),
        })
        
        # Update examine parameters
        if 'examine' not in params:
            params['examine'] = {}
        params['examine'].update({
            'Examine_Flag': self.widgets['examine_flag']['var'].get(),
            'Combine_Flag': self.widgets['combine_flag']['var'].get(),
        })
        
        # Update dumbbell parameters
        if 'dumbbell' not in params:
            params['dumbbell'] = {}
        params['dumbbell'].update({
            'dumbbell_eps': float(self.widgets['dumbbell_eps']['var'].get()),
            'dumbbell_scale': float(self.widgets['dumbbell_scale']['var'].get()),
            'dumbbell_gradient_descent': float(self.widgets['dumbbell_gradient_descent']['var'].get()),
            'dumbbell_penalty_weight': float(self.widgets['dumbbell_penalty_weight']['var'].get()),
            'dumbbell_step': int(self.widgets['dumbbell_step']['var'].get()),
            'dumbbell_niter': int(self.widgets['dumbbell_niter']['var'].get()),
        })
        
        # Update shaking parameters
        if 'shaking' not in params:
            params['shaking'] = {}
        params['shaking'].update({
            'shaking_first_frame': int(self.widgets['shaking_first_frame']['var'].get()),
            'shaking_last_frame': int(self.widgets['shaking_last_frame']['var'].get()),
            'shaking_max_num_points': int(self.widgets['shaking_max_num_points']['var'].get()),
            'shaking_max_num_frames': int(self.widgets['shaking_max_num_frames']['var'].get()),
        })


class TrackingParamsWindow(BaseParamWindow):
    """TTK version of Tracking_Params GUI"""
    
    def __init__(self, parent, experiment: Experiment):
        super().__init__(parent, experiment, "Tracking Parameters")
        self.create_tracking_tab()
        self.load_values()
    
    def create_tracking_tab(self):
        """Create tracking parameters tab"""
        tab = self.create_tab("Tracking Parameters")
        
        # Velocity limits
        ttk.Label(tab, text="Velocity Limits (X):", font=('Arial', 10, 'bold')).grid(row=0, column=0, columnspan=2, sticky='w', pady=5)
        
        ttk.Label(tab, text="dvxmin:").grid(row=1, column=0, sticky='w', pady=2)
        self.add_widget(tab, "", 'entry', 'dvxmin').grid(row=1, column=1, sticky='ew', pady=2)
        
        ttk.Label(tab, text="dvxmax:").grid(row=2, column=0, sticky='w', pady=2)
        self.add_widget(tab, "", 'entry', 'dvxmax').grid(row=2, column=1, sticky='ew', pady=2)
        
        ttk.Label(tab, text="Velocity Limits (Y):", font=('Arial', 10, 'bold')).grid(row=3, column=0, columnspan=2, sticky='w', pady=(15,5))
        
        ttk.Label(tab, text="dvymin:").grid(row=4, column=0, sticky='w', pady=2)
        self.add_widget(tab, "", 'entry', 'dvymin').grid(row=4, column=1, sticky='ew', pady=2)
        
        ttk.Label(tab, text="dvymax:").grid(row=5, column=0, sticky='w', pady=2)
        self.add_widget(tab, "", 'entry', 'dvymax').grid(row=5, column=1, sticky='ew', pady=2)
        
        ttk.Label(tab, text="Velocity Limits (Z):", font=('Arial', 10, 'bold')).grid(row=6, column=0, columnspan=2, sticky='w', pady=(15,5))
        
        ttk.Label(tab, text="dvzmin:").grid(row=7, column=0, sticky='w', pady=2)
        self.add_widget(tab, "", 'entry', 'dvzmin').grid(row=7, column=1, sticky='ew', pady=2)
        
        ttk.Label(tab, text="dvzmax:").grid(row=8, column=0, sticky='w', pady=2)
        self.add_widget(tab, "", 'entry', 'dvzmax').grid(row=8, column=1, sticky='ew', pady=2)
        
        # Other parameters
        ttk.Label(tab, text="Other Parameters:", font=('Arial', 10, 'bold')).grid(row=9, column=0, columnspan=2, sticky='w', pady=(15,5))
        
        ttk.Label(tab, text="angle [gon]:").grid(row=10, column=0, sticky='w', pady=2)
        self.add_widget(tab, "", 'entry', 'angle').grid(row=10, column=1, sticky='ew', pady=2)
        
        ttk.Label(tab, text="dacc:").grid(row=11, column=0, sticky='w', pady=2)
        self.add_widget(tab, "", 'entry', 'dacc').grid(row=11, column=1, sticky='ew', pady=2)
        
        # Checkbox
        self.add_widget(tab, "Add new particles?", 'checkbutton', 'flagNewParticles').grid(row=12, column=0, columnspan=2, sticky='w', pady=(10,2))
        
        tab.columnconfigure(1, weight=1)
    
    def load_values(self):
        """Load current tracking parameter values from experiment"""
        params = self.experiment.pm.parameters
        
        # Track parameters
        track_params = params.get('track', {})
        self.widgets['dvxmin']['var'].set(str(track_params.get('dvxmin', -10.0)))
        self.widgets['dvxmax']['var'].set(str(track_params.get('dvxmax', 10.0)))
        self.widgets['dvymin']['var'].set(str(track_params.get('dvymin', -10.0)))
        self.widgets['dvymax']['var'].set(str(track_params.get('dvymax', 10.0)))
        self.widgets['dvzmin']['var'].set(str(track_params.get('dvzmin', -10.0)))
        self.widgets['dvzmax']['var'].set(str(track_params.get('dvzmax', 10.0)))
        self.widgets['angle']['var'].set(str(track_params.get('angle', 45.0)))
        self.widgets['dacc']['var'].set(str(track_params.get('dacc', 1.0)))
        self.widgets['flagNewParticles']['var'].set(bool(track_params.get('flagNewParticles', True)))
    
    def save_values(self):
        """Save tracking parameter values back to experiment"""
        params = self.experiment.pm.parameters
        
        # Update track parameters
        if 'track' not in params:
            params['track'] = {}
        
        params['track'].update({
            'dvxmin': float(self.widgets['dvxmin']['var'].get()),
            'dvxmax': float(self.widgets['dvxmax']['var'].get()),
            'dvymin': float(self.widgets['dvymin']['var'].get()),
            'dvymax': float(self.widgets['dvymax']['var'].get()),
            'dvzmin': float(self.widgets['dvzmin']['var'].get()),
            'dvzmax': float(self.widgets['dvzmax']['var'].get()),
            'angle': float(self.widgets['angle']['var'].get()),
            'dacc': float(self.widgets['dacc']['var'].get()),
            'flagNewParticles': self.widgets['flagNewParticles']['var'].get(),
        })


# Convenience functions for opening parameter windows
def open_main_params_window(parent, experiment: Experiment):
    """Open main parameters window"""
    window = MainParamsWindow(parent, experiment)
    return window


def open_calib_params_window(parent, experiment: Experiment):
    """Open calibration parameters window"""
    window = CalibParamsWindow(parent, experiment)
    return window


def open_tracking_params_window(parent, experiment: Experiment):
    """Open tracking parameters window"""
    window = TrackingParamsWindow(parent, experiment)
    return window


class MainParamsTTK(tk.Toplevel):
    """TTK-based Main Parameters GUI"""

    def __init__(self, parent, experiment: Experiment):
        super().__init__(parent)
        self.title("Main Parameters")
        self.geometry("800x600")
        self.experiment = experiment

        # Initialize variables
        self._init_variables()

        # Load parameters from experiment
        self._load_parameters()

        # Create GUI
        self._create_gui()

        # Center window
        self.transient(parent)
        self.grab_set()

    def _init_variables(self):
        """Initialize all parameter variables"""
        # General parameters
        self.num_cams = tk.IntVar(value=4)
        self.accept_only_all = tk.BooleanVar(value=False)
        self.pair_flag = tk.BooleanVar(value=True)
        self.splitter = tk.BooleanVar(value=False)

        # Image names
        self.name_1 = tk.StringVar()
        self.name_2 = tk.StringVar()
        self.name_3 = tk.StringVar()
        self.name_4 = tk.StringVar()
        self.cali_1 = tk.StringVar()
        self.cali_2 = tk.StringVar()
        self.cali_3 = tk.StringVar()
        self.cali_4 = tk.StringVar()

        # Refractive indices
        self.refr_air = tk.DoubleVar(value=1.0)
        self.refr_glass = tk.DoubleVar(value=1.5)
        self.refr_water = tk.DoubleVar(value=1.33)
        self.thick_glass = tk.DoubleVar(value=0.0)

        # Particle recognition
        self.highpass = tk.BooleanVar(value=False)
        self.gray_thresh_1 = tk.IntVar(value=50)
        self.gray_thresh_2 = tk.IntVar(value=50)
        self.gray_thresh_3 = tk.IntVar(value=50)
        self.gray_thresh_4 = tk.IntVar(value=50)
        self.min_npix = tk.IntVar(value=1)
        self.max_npix = tk.IntVar(value=100)
        self.min_npix_x = tk.IntVar(value=1)
        self.max_npix_x = tk.IntVar(value=100)
        self.min_npix_y = tk.IntVar(value=1)
        self.max_npix_y = tk.IntVar(value=100)
        self.sum_grey = tk.IntVar(value=0)
        self.tol_disc = tk.IntVar(value=5)
        self.size_cross = tk.IntVar(value=3)
        self.subtr_mask = tk.BooleanVar(value=False)
        self.base_name_mask = tk.StringVar()
        self.existing_target = tk.BooleanVar(value=False)
        self.inverse = tk.BooleanVar(value=False)

        # Sequence
        self.seq_first = tk.IntVar(value=0)
        self.seq_last = tk.IntVar(value=100)
        self.basename_1 = tk.StringVar()
        self.basename_2 = tk.StringVar()
        self.basename_3 = tk.StringVar()
        self.basename_4 = tk.StringVar()

        # Observation volume
        self.xmin = tk.IntVar(value=0)
        self.xmax = tk.IntVar(value=100)
        self.zmin1 = tk.IntVar(value=0)
        self.zmin2 = tk.IntVar(value=0)
        self.zmax1 = tk.IntVar(value=100)
        self.zmax2 = tk.IntVar(value=100)

        # Criteria
        self.min_corr_nx = tk.DoubleVar(value=0.5)
        self.min_corr_ny = tk.DoubleVar(value=0.5)
        self.min_corr_npix = tk.DoubleVar(value=0.5)
        self.sum_gv = tk.DoubleVar(value=0.0)
        self.min_weight_corr = tk.DoubleVar(value=0.5)
        self.tol_band = tk.DoubleVar(value=1.0)

    def _load_parameters(self):
        """Load parameters from experiment"""
        params = self.experiment.pm.parameters
        num_cams = self.experiment.get_n_cam()

        # PTV parameters
        ptv_params = params.get('ptv', {})
        self.num_cams.set(num_cams)
        self.accept_only_all.set(ptv_params.get('allcam_flag', False))
        self.splitter.set(ptv_params.get('splitter', False))

        # Image names
        img_names = ptv_params.get('img_name', [])
        img_cals = ptv_params.get('img_cal', [])
        for i in range(min(4, len(img_names))):
            getattr(self, f'name_{i+1}').set(img_names[i] if i < len(img_names) else '')
            getattr(self, f'cali_{i+1}').set(img_cals[i] if i < len(img_cals) else '')

        # Refractive indices
        self.refr_air.set(ptv_params.get('mmp_n1', 1.0))
        self.refr_glass.set(ptv_params.get('mmp_n2', 1.5))
        self.refr_water.set(ptv_params.get('mmp_n3', 1.33))
        self.thick_glass.set(ptv_params.get('mmp_d', 0.0))

        # Particle recognition
        self.highpass.set(ptv_params.get('hp_flag', False))

        targ_rec = params.get('targ_rec', {})
        gvthres = targ_rec.get('gvthres', [50, 50, 50, 50])
        for i in range(min(4, len(gvthres))):
            getattr(self, f'gray_thresh_{i+1}').set(gvthres[i])

        self.min_npix.set(targ_rec.get('nnmin', 1))
        self.max_npix.set(targ_rec.get('nnmax', 100))
        self.min_npix_x.set(targ_rec.get('nxmin', 1))
        self.max_npix_x.set(targ_rec.get('nxmax', 100))
        self.min_npix_y.set(targ_rec.get('nymin', 1))
        self.max_npix_y.set(targ_rec.get('nymax', 100))
        self.sum_grey.set(targ_rec.get('sumg_min', 0))
        self.tol_disc.set(targ_rec.get('disco', 5))
        self.size_cross.set(targ_rec.get('cr_sz', 3))

        # Masking
        masking = params.get('masking', {})
        self.subtr_mask.set(masking.get('mask_flag', False))
        self.base_name_mask.set(masking.get('mask_base_name', ''))

        # PFT version
        pft_version = params.get('pft_version', {})
        self.existing_target.set(pft_version.get('Existing_Target', False))

        # Sequence
        sequence = params.get('sequence', {})
        self.seq_first.set(sequence.get('first', 0))
        self.seq_last.set(sequence.get('last', 100))

        base_names = sequence.get('base_name', [])
        for i in range(min(4, len(base_names))):
            getattr(self, f'basename_{i+1}').set(base_names[i] if i < len(base_names) else '')

        # Criteria
        criteria = params.get('criteria', {})
        x_lay = criteria.get('X_lay', [0, 100])
        zmin_lay = criteria.get('Zmin_lay', [0, 0])
        zmax_lay = criteria.get('Zmax_lay', [100, 100])

        self.xmin.set(x_lay[0] if len(x_lay) > 0 else 0)
        self.xmax.set(x_lay[1] if len(x_lay) > 1 else 100)
        self.zmin1.set(zmin_lay[0] if len(zmin_lay) > 0 else 0)
        self.zmin2.set(zmin_lay[1] if len(zmin_lay) > 1 else 0)
        self.zmax1.set(zmax_lay[0] if len(zmax_lay) > 0 else 100)
        self.zmax2.set(zmax_lay[1] if len(zmax_lay) > 1 else 100)

        self.min_corr_nx.set(criteria.get('cnx', 0.5))
        self.min_corr_ny.set(criteria.get('cny', 0.5))
        self.min_corr_npix.set(criteria.get('cn', 0.5))
        self.sum_gv.set(criteria.get('csumg', 0.0))
        self.min_weight_corr.set(criteria.get('corrmin', 0.5))
        self.tol_band.set(criteria.get('eps0', 1.0))

    def _create_gui(self):
        """Create the GUI with notebook tabs"""
        # Create notebook
        notebook = ttk.Notebook(self)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Create tabs
        self._create_general_tab(notebook)
        self._create_refractive_tab(notebook)
        self._create_particle_tab(notebook)
        self._create_sequence_tab(notebook)
        self._create_volume_tab(notebook)
        self._create_criteria_tab(notebook)

        # Buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(fill='x', padx=10, pady=(0, 10))

        ttk.Button(button_frame, text="OK", command=self._on_ok).pack(side='right', padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", command=self._on_cancel).pack(side='right')

    def _create_general_tab(self, notebook):
        """Create General tab"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="General")

        # Number of cameras and flags
        ttk.Label(frame, text="Number of cameras:").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        ttk.Spinbox(frame, from_=1, to=4, textvariable=self.num_cams, width=5).grid(row=0, column=1, padx=5, pady=2)

        ttk.Checkbutton(frame, text="Accept only points seen from all cameras", variable=self.accept_only_all).grid(row=1, column=0, columnspan=2, sticky='w', padx=5, pady=2)
        ttk.Checkbutton(frame, text="Include pairs", variable=self.pair_flag).grid(row=2, column=0, columnspan=2, sticky='w', padx=5, pady=2)
        ttk.Checkbutton(frame, text="Split images into 4", variable=self.splitter).grid(row=3, column=0, columnspan=2, sticky='w', padx=5, pady=2)

        # Image names
        ttk.Label(frame, text="Image Names", font=('Arial', 10, 'bold')).grid(row=4, column=0, columnspan=2, pady=(10, 5))

        ttk.Label(frame, text="Camera 1:").grid(row=5, column=0, sticky='w', padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.name_1).grid(row=5, column=1, sticky='ew', padx=5, pady=2)

        ttk.Label(frame, text="Camera 2:").grid(row=6, column=0, sticky='w', padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.name_2).grid(row=6, column=1, sticky='ew', padx=5, pady=2)

        ttk.Label(frame, text="Camera 3:").grid(row=7, column=0, sticky='w', padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.name_3).grid(row=7, column=1, sticky='ew', padx=5, pady=2)

        ttk.Label(frame, text="Camera 4:").grid(row=8, column=0, sticky='w', padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.name_4).grid(row=8, column=1, sticky='ew', padx=5, pady=2)

        # Calibration images
        ttk.Label(frame, text="Calibration Images", font=('Arial', 10, 'bold')).grid(row=9, column=0, columnspan=2, pady=(10, 5))

        ttk.Label(frame, text="Cal Cam 1:").grid(row=10, column=0, sticky='w', padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.cali_1).grid(row=10, column=1, sticky='ew', padx=5, pady=2)

        ttk.Label(frame, text="Cal Cam 2:").grid(row=11, column=0, sticky='w', padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.cali_2).grid(row=11, column=1, sticky='ew', padx=5, pady=2)

        ttk.Label(frame, text="Cal Cam 3:").grid(row=12, column=0, sticky='w', padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.cali_3).grid(row=12, column=1, sticky='ew', padx=5, pady=2)

        ttk.Label(frame, text="Cal Cam 4:").grid(row=13, column=0, sticky='w', padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.cali_4).grid(row=13, column=1, sticky='ew', padx=5, pady=2)

        frame.columnconfigure(1, weight=1)

    def _create_refractive_tab(self, notebook):
        """Create Refractive Indices tab"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Refractive Indices")

        ttk.Label(frame, text="Air:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.refr_air).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Glass:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.refr_glass).grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Water:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.refr_water).grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Glass Thickness:").grid(row=3, column=0, sticky='w', padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.thick_glass).grid(row=3, column=1, padx=5, pady=5)

    def _create_particle_tab(self, notebook):
        """Create Particle Recognition tab"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Particle Recognition")

        # Gray value thresholds
        ttk.Label(frame, text="Gray Value Thresholds", font=('Arial', 10, 'bold')).grid(row=0, column=0, columnspan=4, pady=(5, 10))

        ttk.Label(frame, text="Cam 1:").grid(row=1, column=0, padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.gray_thresh_1, width=8).grid(row=1, column=1, padx=5, pady=2)

        ttk.Label(frame, text="Cam 2:").grid(row=1, column=2, padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.gray_thresh_2, width=8).grid(row=1, column=3, padx=5, pady=2)

        ttk.Label(frame, text="Cam 3:").grid(row=2, column=0, padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.gray_thresh_3, width=8).grid(row=2, column=1, padx=5, pady=2)

        ttk.Label(frame, text="Cam 4:").grid(row=2, column=2, padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.gray_thresh_4, width=8).grid(row=2, column=3, padx=5, pady=2)

        # Particle size limits
        ttk.Label(frame, text="Particle Size Limits", font=('Arial', 10, 'bold')).grid(row=3, column=0, columnspan=4, pady=(15, 10))

        ttk.Label(frame, text="Min Npix:").grid(row=4, column=0, sticky='w', padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.min_npix).grid(row=4, column=1, padx=5, pady=2)

        ttk.Label(frame, text="Max Npix:").grid(row=4, column=2, sticky='w', padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.max_npix).grid(row=4, column=3, padx=5, pady=2)

        ttk.Label(frame, text="Min Npix X:").grid(row=5, column=0, sticky='w', padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.min_npix_x).grid(row=5, column=1, padx=5, pady=2)

        ttk.Label(frame, text="Max Npix X:").grid(row=5, column=2, sticky='w', padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.max_npix_x).grid(row=5, column=3, padx=5, pady=2)

        ttk.Label(frame, text="Min Npix Y:").grid(row=6, column=0, sticky='w', padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.min_npix_y).grid(row=6, column=1, padx=5, pady=2)

        ttk.Label(frame, text="Max Npix Y:").grid(row=6, column=2, sticky='w', padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.max_npix_y).grid(row=6, column=3, padx=5, pady=2)

        # Other parameters
        ttk.Label(frame, text="Sum of Grey:").grid(row=7, column=0, sticky='w', padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.sum_grey).grid(row=7, column=1, padx=5, pady=2)

        ttk.Label(frame, text="Tolerance:").grid(row=7, column=2, sticky='w', padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.tol_disc).grid(row=7, column=3, padx=5, pady=2)

        ttk.Label(frame, text="Cross Size:").grid(row=8, column=0, sticky='w', padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.size_cross).grid(row=8, column=1, padx=5, pady=2)

        # Checkboxes
        ttk.Checkbutton(frame, text="High pass filter", variable=self.highpass).grid(row=9, column=0, columnspan=2, sticky='w', padx=5, pady=5)
        ttk.Checkbutton(frame, text="Subtract mask", variable=self.subtr_mask).grid(row=9, column=2, columnspan=2, sticky='w', padx=5, pady=5)

        ttk.Label(frame, text="Mask Base Name:").grid(row=10, column=0, sticky='w', padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.base_name_mask).grid(row=10, column=1, columnspan=3, sticky='ew', padx=5, pady=2)

        ttk.Checkbutton(frame, text="Use existing target files", variable=self.existing_target).grid(row=11, column=0, columnspan=2, sticky='w', padx=5, pady=5)
        ttk.Checkbutton(frame, text="Negative images", variable=self.inverse).grid(row=11, column=2, columnspan=2, sticky='w', padx=5, pady=5)

        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(3, weight=1)

    def _create_sequence_tab(self, notebook):
        """Create Sequence tab"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Sequence")

        ttk.Label(frame, text="First Image:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.seq_first).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Last Image:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.seq_last).grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Base Names", font=('Arial', 10, 'bold')).grid(row=2, column=0, columnspan=2, pady=(15, 5))

        ttk.Label(frame, text="Camera 1:").grid(row=3, column=0, sticky='w', padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.basename_1).grid(row=3, column=1, sticky='ew', padx=5, pady=2)

        ttk.Label(frame, text="Camera 2:").grid(row=4, column=0, sticky='w', padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.basename_2).grid(row=4, column=1, sticky='ew', padx=5, pady=2)

        ttk.Label(frame, text="Camera 3:").grid(row=5, column=0, sticky='w', padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.basename_3).grid(row=5, column=1, sticky='ew', padx=5, pady=2)

        ttk.Label(frame, text="Camera 4:").grid(row=6, column=0, sticky='w', padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.basename_4).grid(row=6, column=1, sticky='ew', padx=5, pady=2)

        frame.columnconfigure(1, weight=1)

    def _create_volume_tab(self, notebook):
        """Create Observation Volume tab"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Observation Volume")

        ttk.Label(frame, text="X Limits", font=('Arial', 10, 'bold')).grid(row=0, column=0, columnspan=2, pady=(5, 10))

        ttk.Label(frame, text="X Min:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.xmin).grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(frame, text="X Max:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.xmax).grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Z Limits", font=('Arial', 10, 'bold')).grid(row=3, column=0, columnspan=2, pady=(15, 10))

        ttk.Label(frame, text="Z Min 1:").grid(row=4, column=0, sticky='w', padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.zmin1).grid(row=4, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Z Min 2:").grid(row=5, column=0, sticky='w', padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.zmin2).grid(row=5, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Z Max 1:").grid(row=6, column=0, sticky='w', padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.zmax1).grid(row=6, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Z Max 2:").grid(row=7, column=0, sticky='w', padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.zmax2).grid(row=7, column=1, padx=5, pady=5)

    def _create_criteria_tab(self, notebook):
        """Create Criteria tab"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Criteria")

        ttk.Label(frame, text="Correspondence Criteria", font=('Arial', 10, 'bold')).grid(row=0, column=0, columnspan=2, pady=(5, 10))

        ttk.Label(frame, text="Min Corr NX:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.min_corr_nx).grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Min Corr NY:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.min_corr_ny).grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Min Corr Npix:").grid(row=3, column=0, sticky='w', padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.min_corr_npix).grid(row=3, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Sum GV:").grid(row=4, column=0, sticky='w', padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.sum_gv).grid(row=4, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Min Weight Corr:").grid(row=5, column=0, sticky='w', padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.min_weight_corr).grid(row=5, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Tolerance Band:").grid(row=6, column=0, sticky='w', padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.tol_band).grid(row=6, column=1, padx=5, pady=5)

    def _on_ok(self):
        """Handle OK button - save parameters"""
        try:
            self._save_parameters()
            messagebox.showinfo("Success", "Parameters saved successfully!")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save parameters: {e}")

    def _on_cancel(self):
        """Handle Cancel button"""
        self.destroy()

    def _save_parameters(self):
        """Save parameters back to experiment"""
        params = self.experiment.pm.parameters

        # Update num_cams
        params['num_cams'] = self.num_cams.get()

        # Update PTV parameters
        ptv_params = params.get('ptv', {})
        ptv_params.update({
            'img_name': [
                self.name_1.get(), self.name_2.get(),
                self.name_3.get(), self.name_4.get()
            ],
            'img_cal': [
                self.cali_1.get(), self.cali_2.get(),
                self.cali_3.get(), self.cali_4.get()
            ],
            'allcam_flag': self.accept_only_all.get(),
            'hp_flag': self.highpass.get(),
            'mmp_n1': self.refr_air.get(),
            'mmp_n2': self.refr_glass.get(),
            'mmp_n3': self.refr_water.get(),
            'mmp_d': self.thick_glass.get(),
            'splitter': self.splitter.get()
        })
        params['ptv'] = ptv_params

        # Update target recognition parameters
        targ_rec = params.get('targ_rec', {})
        targ_rec.update({
            'gvthres': [
                self.gray_thresh_1.get(), self.gray_thresh_2.get(),
                self.gray_thresh_3.get(), self.gray_thresh_4.get()
            ],
            'nnmin': self.min_npix.get(),
            'nnmax': self.max_npix.get(),
            'nxmin': self.min_npix_x.get(),
            'nxmax': self.max_npix_x.get(),
            'nymin': self.min_npix_y.get(),
            'nymax': self.max_npix_y.get(),
            'sumg_min': self.sum_grey.get(),
            'disco': self.tol_disc.get(),
            'cr_sz': self.size_cross.get()
        })
        params['targ_rec'] = targ_rec

        # Update sequence parameters
        sequence = params.get('sequence', {})
        sequence.update({
            'first': self.seq_first.get(),
            'last': self.seq_last.get(),
            'base_name': [
                self.basename_1.get(), self.basename_2.get(),
                self.basename_3.get(), self.basename_4.get()
            ]
        })
        params['sequence'] = sequence

        # Update criteria parameters
        criteria = params.get('criteria', {})
        criteria.update({
            'X_lay': [self.xmin.get(), self.xmax.get()],
            'Zmin_lay': [self.zmin1.get(), self.zmin2.get()],
            'Zmax_lay': [self.zmax1.get(), self.zmax2.get()],
            'cnx': self.min_corr_nx.get(),
            'cny': self.min_corr_ny.get(),
            'cn': self.min_corr_npix.get(),
            'csumg': self.sum_gv.get(),
            'corrmin': self.min_weight_corr.get(),
            'eps0': self.tol_band.get()
        })
        params['criteria'] = criteria

        # Update masking parameters
        masking = params.get('masking', {})
        masking.update({
            'mask_flag': self.subtr_mask.get(),
            'mask_base_name': self.base_name_mask.get()
        })
        params['masking'] = masking

        # Update PFT version parameters
        pft_version = params.get('pft_version', {})
        pft_version['Existing_Target'] = self.existing_target.get()
        params['pft_version'] = pft_version

        # Save to YAML file
        self.experiment.save_parameters()
        print("Main parameters saved successfully!")


class CalibParamsTTK(tk.Toplevel):
    """TTK-based Calibration Parameters GUI"""

    def __init__(self, parent, experiment: Experiment):
        super().__init__(parent)
        self.title("Calibration Parameters")
        self.geometry("900x700")
        self.experiment = experiment

        # Initialize variables
        self._init_variables()

        # Load parameters from experiment
        self._load_parameters()

        # Create GUI
        self._create_gui()

        # Center window
        self.transient(parent)
        self.grab_set()

    def _init_variables(self):
        """Initialize all calibration parameter variables"""
        # Image data
        self.cam_1 = tk.StringVar()
        self.cam_2 = tk.StringVar()
        self.cam_3 = tk.StringVar()
        self.cam_4 = tk.StringVar()
        self.ori_cam_1 = tk.StringVar()
        self.ori_cam_2 = tk.StringVar()
        self.ori_cam_3 = tk.StringVar()
        self.ori_cam_4 = tk.StringVar()
        self.fixp_name = tk.StringVar()
        self.cal_splitter = tk.BooleanVar(value=False)

        # Image properties
        self.h_image_size = tk.IntVar(value=1024)
        self.v_image_size = tk.IntVar(value=1024)
        self.h_pixel_size = tk.DoubleVar(value=1.0)
        self.v_pixel_size = tk.DoubleVar(value=1.0)

        # Detection parameters
        self.grey_thresh_1 = tk.IntVar(value=50)
        self.grey_thresh_2 = tk.IntVar(value=50)
        self.grey_thresh_3 = tk.IntVar(value=50)
        self.grey_thresh_4 = tk.IntVar(value=50)
        self.tol_discontinuity = tk.IntVar(value=5)
        self.min_npix = tk.IntVar(value=1)
        self.max_npix = tk.IntVar(value=100)
        self.min_npix_x = tk.IntVar(value=1)
        self.max_npix_x = tk.IntVar(value=100)
        self.min_npix_y = tk.IntVar(value=1)
        self.max_npix_y = tk.IntVar(value=100)
        self.sum_grey = tk.IntVar(value=0)
        self.size_crosses = tk.IntVar(value=3)

        # Manual orientation points
        self.img_1_p1 = tk.IntVar(value=0)
        self.img_1_p2 = tk.IntVar(value=0)
        self.img_1_p3 = tk.IntVar(value=0)
        self.img_1_p4 = tk.IntVar(value=0)
        self.img_2_p1 = tk.IntVar(value=0)
        self.img_2_p2 = tk.IntVar(value=0)
        self.img_2_p3 = tk.IntVar(value=0)
        self.img_2_p4 = tk.IntVar(value=0)
        self.img_3_p1 = tk.IntVar(value=0)
        self.img_3_p2 = tk.IntVar(value=0)
        self.img_3_p3 = tk.IntVar(value=0)
        self.img_3_p4 = tk.IntVar(value=0)
        self.img_4_p1 = tk.IntVar(value=0)
        self.img_4_p2 = tk.IntVar(value=0)
        self.img_4_p3 = tk.IntVar(value=0)
        self.img_4_p4 = tk.IntVar(value=0)

        # Orientation parameters
        self.examine_flag = tk.BooleanVar(value=False)
        self.combine_flag = tk.BooleanVar(value=False)
        self.point_num_ori = tk.IntVar(value=8)
        self.cc = tk.BooleanVar(value=False)
        self.xh = tk.BooleanVar(value=False)
        self.yh = tk.BooleanVar(value=False)
        self.k1 = tk.BooleanVar(value=False)
        self.k2 = tk.BooleanVar(value=False)
        self.k3 = tk.BooleanVar(value=False)
        self.p1 = tk.BooleanVar(value=False)
        self.p2 = tk.BooleanVar(value=False)
        self.scale = tk.BooleanVar(value=False)
        self.shear = tk.BooleanVar(value=False)
        self.interf = tk.BooleanVar(value=False)

        # Dumbbell parameters
        self.dumbbell_eps = tk.DoubleVar(value=0.1)
        self.dumbbell_scale = tk.DoubleVar(value=1.0)
        self.dumbbell_grad = tk.DoubleVar(value=0.1)
        self.dumbbell_penalty = tk.DoubleVar(value=1.0)
        self.dumbbell_step = tk.IntVar(value=1)
        self.dumbbell_niter = tk.IntVar(value=10)

        # Shaking parameters
        self.shaking_first = tk.IntVar(value=0)
        self.shaking_last = tk.IntVar(value=100)
        self.shaking_max_points = tk.IntVar(value=100)
        self.shaking_max_frames = tk.IntVar(value=10)

    def _load_parameters(self):
        """Load calibration parameters from experiment"""
        params = self.experiment.pm.parameters
        num_cams = self.experiment.get_n_cam()

        # Image data
        cal_ori = params.get('cal_ori', {})
        img_cal_names = cal_ori.get('img_cal_name', [])
        img_ori_names = cal_ori.get('img_ori', [])

        for i in range(min(4, num_cams)):
            if i < len(img_cal_names):
                getattr(self, f'cam_{i+1}').set(img_cal_names[i])
            if i < len(img_ori_names):
                getattr(self, f'ori_cam_{i+1}').set(img_ori_names[i])

        self.fixp_name.set(cal_ori.get('fixp_name', ''))
        self.cal_splitter.set(cal_ori.get('cal_splitter', False))

        # Image properties
        ptv_params = params.get('ptv', {})
        self.h_image_size.set(ptv_params.get('imx', 1024))
        self.v_image_size.set(ptv_params.get('imy', 1024))
        self.h_pixel_size.set(ptv_params.get('pix_x', 1.0))
        self.v_pixel_size.set(ptv_params.get('pix_y', 1.0))

        # Detection parameters
        detect_plate = params.get('detect_plate', {})
        gvthres = detect_plate.get('gvthres', [50, 50, 50, 50])
        for i in range(min(4, len(gvthres))):
            getattr(self, f'grey_thresh_{i+1}').set(gvthres[i])

        self.tol_discontinuity.set(detect_plate.get('tol_dis', 5))
        self.min_npix.set(detect_plate.get('min_npix', 1))
        self.max_npix.set(detect_plate.get('max_npix', 100))
        self.min_npix_x.set(detect_plate.get('min_npix_x', 1))
        self.max_npix_x.set(detect_plate.get('max_npix_x', 100))
        self.min_npix_y.set(detect_plate.get('min_npix_y', 1))
        self.max_npix_y.set(detect_plate.get('max_npix_y', 100))
        self.sum_grey.set(detect_plate.get('sum_grey', 0))
        self.size_crosses.set(detect_plate.get('size_cross', 3))

        # Manual orientation
        man_ori = params.get('man_ori', {})
        nr = man_ori.get('nr', [0] * 16)  # 4 cameras * 4 points each

        for cam in range(min(4, num_cams)):
            for point in range(4):
                idx = cam * 4 + point
                if idx < len(nr):
                    getattr(self, f'img_{cam+1}_p{point+1}').set(nr[idx])

        # Orientation parameters
        examine = params.get('examine', {})
        self.examine_flag.set(examine.get('Examine_Flag', False))
        self.combine_flag.set(examine.get('Combine_Flag', False))

        orient = params.get('orient', {})
        self.point_num_ori.set(orient.get('pnfo', 8))
        self.cc.set(orient.get('cc', False))
        self.xh.set(orient.get('xh', False))
        self.yh.set(orient.get('yh', False))
        self.k1.set(orient.get('k1', False))
        self.k2.set(orient.get('k2', False))
        self.k3.set(orient.get('k3', False))
        self.p1.set(orient.get('p1', False))
        self.p2.set(orient.get('p2', False))
        self.scale.set(orient.get('scale', False))
        self.shear.set(orient.get('shear', False))
        self.interf.set(orient.get('interf', False))

        # Dumbbell parameters
        dumbbell = params.get('dumbbell', {})
        self.dumbbell_eps.set(dumbbell.get('dumbbell_eps', 0.1))
        self.dumbbell_scale.set(dumbbell.get('dumbbell_scale', 1.0))
        self.dumbbell_grad.set(dumbbell.get('dumbbell_gradient_descent', 0.1))
        self.dumbbell_penalty.set(dumbbell.get('dumbbell_penalty_weight', 1.0))
        self.dumbbell_step.set(dumbbell.get('dumbbell_step', 1))
        self.dumbbell_niter.set(dumbbell.get('dumbbell_niter', 10))

        # Shaking parameters
        shaking = params.get('shaking', {})
        self.shaking_first.set(shaking.get('shaking_first_frame', 0))
        self.shaking_last.set(shaking.get('shaking_last_frame', 100))
        self.shaking_max_points.set(shaking.get('shaking_max_num_points', 100))
        self.shaking_max_frames.set(shaking.get('shaking_max_num_frames', 10))

    def _create_gui(self):
        """Create the GUI with notebook tabs"""
        # Create notebook
        notebook = ttk.Notebook(self)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Create tabs
        self._create_images_tab(notebook)
        self._create_detection_tab(notebook)
        self._create_orientation_tab(notebook)
        self._create_dumbbell_tab(notebook)
        self._create_shaking_tab(notebook)

        # Buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(fill='x', padx=10, pady=(0, 10))

        ttk.Button(button_frame, text="OK", command=self._on_ok).pack(side='right', padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", command=self._on_cancel).pack(side='right')

    def _create_images_tab(self, notebook):
        """Create Images Data tab"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Images Data")

        # Calibration images
        ttk.Label(frame, text="Calibration Images", font=('Arial', 10, 'bold')).grid(row=0, column=0, columnspan=2, pady=(5, 10))

        ttk.Label(frame, text="Camera 1:").grid(row=1, column=0, sticky='w', padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.cam_1).grid(row=1, column=1, sticky='ew', padx=5, pady=2)

        ttk.Label(frame, text="Camera 2:").grid(row=2, column=0, sticky='w', padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.cam_2).grid(row=2, column=1, sticky='ew', padx=5, pady=2)

        ttk.Label(frame, text="Camera 3:").grid(row=3, column=0, sticky='w', padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.cam_3).grid(row=3, column=1, sticky='ew', padx=5, pady=2)

        ttk.Label(frame, text="Camera 4:").grid(row=4, column=0, sticky='w', padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.cam_4).grid(row=4, column=1, sticky='ew', padx=5, pady=2)

        # Orientation images
        ttk.Label(frame, text="Orientation Images", font=('Arial', 10, 'bold')).grid(row=5, column=0, columnspan=2, pady=(15, 10))

        ttk.Label(frame, text="Ori Cam 1:").grid(row=6, column=0, sticky='w', padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.ori_cam_1).grid(row=6, column=1, sticky='ew', padx=5, pady=2)

        ttk.Label(frame, text="Ori Cam 2:").grid(row=7, column=0, sticky='w', padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.ori_cam_2).grid(row=7, column=1, sticky='ew', padx=5, pady=2)

        ttk.Label(frame, text="Ori Cam 3:").grid(row=8, column=0, sticky='w', padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.ori_cam_3).grid(row=8, column=1, sticky='ew', padx=5, pady=2)

        ttk.Label(frame, text="Ori Cam 4:").grid(row=9, column=0, sticky='w', padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.ori_cam_4).grid(row=9, column=1, sticky='ew', padx=5, pady=2)

        # Fixed point name
        ttk.Label(frame, text="Fixed Point File:").grid(row=10, column=0, sticky='w', padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.fixp_name).grid(row=10, column=1, sticky='ew', padx=5, pady=5)

        ttk.Checkbutton(frame, text="Split calibration image into 4", variable=self.cal_splitter).grid(row=11, column=0, columnspan=2, sticky='w', padx=5, pady=5)

        frame.columnconfigure(1, weight=1)

    def _create_detection_tab(self, notebook):
        """Create Calibration Data Detection tab"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Detection")

        # Image properties
        ttk.Label(frame, text="Image Properties", font=('Arial', 10, 'bold')).grid(row=0, column=0, columnspan=4, pady=(5, 10))

        ttk.Label(frame, text="Width:").grid(row=1, column=0, sticky='w', padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.h_image_size, width=8).grid(row=1, column=1, padx=5, pady=2)

        ttk.Label(frame, text="Height:").grid(row=1, column=2, sticky='w', padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.v_image_size, width=8).grid(row=1, column=3, padx=5, pady=2)

        ttk.Label(frame, text="Pixel X:").grid(row=2, column=0, sticky='w', padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.h_pixel_size, width=8).grid(row=2, column=1, padx=5, pady=2)

        ttk.Label(frame, text="Pixel Y:").grid(row=2, column=2, sticky='w', padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.v_pixel_size, width=8).grid(row=2, column=3, padx=5, pady=2)

        # Gray thresholds
        ttk.Label(frame, text="Gray Value Thresholds", font=('Arial', 10, 'bold')).grid(row=3, column=0, columnspan=4, pady=(15, 10))

        ttk.Label(frame, text="Cam 1:").grid(row=4, column=0, padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.grey_thresh_1, width=8).grid(row=4, column=1, padx=5, pady=2)

        ttk.Label(frame, text="Cam 2:").grid(row=4, column=2, padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.grey_thresh_2, width=8).grid(row=4, column=3, padx=5, pady=2)

        ttk.Label(frame, text="Cam 3:").grid(row=5, column=0, padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.grey_thresh_3, width=8).grid(row=5, column=1, padx=5, pady=2)

        ttk.Label(frame, text="Cam 4:").grid(row=5, column=2, padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.grey_thresh_4, width=8).grid(row=5, column=3, padx=5, pady=2)

        # Particle detection parameters
        ttk.Label(frame, text="Particle Detection", font=('Arial', 10, 'bold')).grid(row=6, column=0, columnspan=4, pady=(15, 10))

        ttk.Label(frame, text="Min Npix:").grid(row=7, column=0, sticky='w', padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.min_npix, width=8).grid(row=7, column=1, padx=5, pady=2)

        ttk.Label(frame, text="Max Npix:").grid(row=7, column=2, sticky='w', padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.max_npix, width=8).grid(row=7, column=3, padx=5, pady=2)

        ttk.Label(frame, text="Min X:").grid(row=8, column=0, sticky='w', padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.min_npix_x, width=8).grid(row=8, column=1, padx=5, pady=2)

        ttk.Label(frame, text="Max X:").grid(row=8, column=2, sticky='w', padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.max_npix_x, width=8).grid(row=8, column=3, padx=5, pady=2)

        ttk.Label(frame, text="Min Y:").grid(row=9, column=0, sticky='w', padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.min_npix_y, width=8).grid(row=9, column=1, padx=5, pady=2)

        ttk.Label(frame, text="Max Y:").grid(row=9, column=2, sticky='w', padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.max_npix_y, width=8).grid(row=9, column=3, padx=5, pady=2)

        ttk.Label(frame, text="Sum Grey:").grid(row=10, column=0, sticky='w', padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.sum_grey, width=8).grid(row=10, column=1, padx=5, pady=2)

        ttk.Label(frame, text="Tolerance:").grid(row=10, column=2, sticky='w', padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.tol_discontinuity, width=8).grid(row=10, column=3, padx=5, pady=2)

        ttk.Label(frame, text="Cross Size:").grid(row=11, column=0, sticky='w', padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.size_crosses, width=8).grid(row=11, column=1, padx=5, pady=2)

    def _create_orientation_tab(self, notebook):
        """Create Orientation Parameters tab"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Orientation")

        # Manual pre-orientation points
        ttk.Label(frame, text="Manual Pre-orientation Points", font=('Arial', 10, 'bold')).grid(row=0, column=0, columnspan=5, pady=(5, 10))

        # Camera 1 points
        ttk.Label(frame, text="Camera 1", font=('Arial', 9, 'bold')).grid(row=1, column=1, columnspan=4, pady=(0, 5))
        ttk.Label(frame, text="P1:").grid(row=2, column=1, padx=2, pady=2)
        ttk.Entry(frame, textvariable=self.img_1_p1, width=6).grid(row=2, column=2, padx=2, pady=2)
        ttk.Label(frame, text="P2:").grid(row=2, column=3, padx=2, pady=2)
        ttk.Entry(frame, textvariable=self.img_1_p2, width=6).grid(row=2, column=4, padx=2, pady=2)
        ttk.Label(frame, text="P3:").grid(row=3, column=1, padx=2, pady=2)
        ttk.Entry(frame, textvariable=self.img_1_p3, width=6).grid(row=3, column=2, padx=2, pady=2)
        ttk.Label(frame, text="P4:").grid(row=3, column=3, padx=2, pady=2)
        ttk.Entry(frame, textvariable=self.img_1_p4, width=6).grid(row=3, column=4, padx=2, pady=2)

        # Camera 2 points
        ttk.Label(frame, text="Camera 2", font=('Arial', 9, 'bold')).grid(row=4, column=1, columnspan=4, pady=(10, 5))
        ttk.Label(frame, text="P1:").grid(row=5, column=1, padx=2, pady=2)
        ttk.Entry(frame, textvariable=self.img_2_p1, width=6).grid(row=5, column=2, padx=2, pady=2)
        ttk.Label(frame, text="P2:").grid(row=5, column=3, padx=2, pady=2)
        ttk.Entry(frame, textvariable=self.img_2_p2, width=6).grid(row=5, column=4, padx=2, pady=2)
        ttk.Label(frame, text="P3:").grid(row=6, column=1, padx=2, pady=2)
        ttk.Entry(frame, textvariable=self.img_2_p3, width=6).grid(row=6, column=2, padx=2, pady=2)
        ttk.Label(frame, text="P4:").grid(row=6, column=3, padx=2, pady=2)
        ttk.Entry(frame, textvariable=self.img_2_p4, width=6).grid(row=6, column=4, padx=2, pady=2)

        # Camera 3 points
        ttk.Label(frame, text="Camera 3", font=('Arial', 9, 'bold')).grid(row=7, column=1, columnspan=4, pady=(10, 5))
        ttk.Label(frame, text="P1:").grid(row=8, column=1, padx=2, pady=2)
        ttk.Entry(frame, textvariable=self.img_3_p1, width=6).grid(row=8, column=2, padx=2, pady=2)
        ttk.Label(frame, text="P2:").grid(row=8, column=3, padx=2, pady=2)
        ttk.Entry(frame, textvariable=self.img_3_p2, width=6).grid(row=8, column=4, padx=2, pady=2)
        ttk.Label(frame, text="P3:").grid(row=9, column=1, padx=2, pady=2)
        ttk.Entry(frame, textvariable=self.img_3_p3, width=6).grid(row=9, column=2, padx=2, pady=2)
        ttk.Label(frame, text="P4:").grid(row=9, column=3, padx=2, pady=2)
        ttk.Entry(frame, textvariable=self.img_3_p4, width=6).grid(row=9, column=4, padx=2, pady=2)

        # Camera 4 points
        ttk.Label(frame, text="Camera 4", font=('Arial', 9, 'bold')).grid(row=10, column=1, columnspan=4, pady=(10, 5))
        ttk.Label(frame, text="P1:").grid(row=11, column=1, padx=2, pady=2)
        ttk.Entry(frame, textvariable=self.img_4_p1, width=6).grid(row=11, column=2, padx=2, pady=2)
        ttk.Label(frame, text="P2:").grid(row=11, column=3, padx=2, pady=2)
        ttk.Entry(frame, textvariable=self.img_4_p2, width=6).grid(row=11, column=4, padx=2, pady=2)
        ttk.Label(frame, text="P3:").grid(row=12, column=1, padx=2, pady=2)
        ttk.Entry(frame, textvariable=self.img_4_p3, width=6).grid(row=12, column=2, padx=2, pady=2)
        ttk.Label(frame, text="P4:").grid(row=12, column=3, padx=2, pady=2)
        ttk.Entry(frame, textvariable=self.img_4_p4, width=6).grid(row=12, column=4, padx=2, pady=2)

        # Orientation flags
        ttk.Label(frame, text="Orientation Parameters", font=('Arial', 10, 'bold')).grid(row=13, column=0, columnspan=5, pady=(20, 10))

        ttk.Checkbutton(frame, text="Examine Flag", variable=self.examine_flag).grid(row=14, column=0, columnspan=2, sticky='w', padx=5, pady=2)
        ttk.Checkbutton(frame, text="Combine Flag", variable=self.combine_flag).grid(row=14, column=2, columnspan=2, sticky='w', padx=5, pady=2)

        ttk.Label(frame, text="Point Num:").grid(row=15, column=0, sticky='w', padx=5, pady=2)
        ttk.Entry(frame, textvariable=self.point_num_ori, width=8).grid(row=15, column=1, padx=5, pady=2)

        # Lens distortion checkboxes
        ttk.Label(frame, text="Lens Distortion (Brown)", font=('Arial', 9, 'bold')).grid(row=16, column=0, columnspan=5, pady=(10, 5))

        ttk.Checkbutton(frame, text="cc", variable=self.cc).grid(row=17, column=0, padx=5, pady=2)
        ttk.Checkbutton(frame, text="xh", variable=self.xh).grid(row=17, column=1, padx=5, pady=2)
        ttk.Checkbutton(frame, text="yh", variable=self.yh).grid(row=17, column=2, padx=5, pady=2)
        ttk.Checkbutton(frame, text="k1", variable=self.k1).grid(row=17, column=3, padx=5, pady=2)
        ttk.Checkbutton(frame, text="k2", variable=self.k2).grid(row=17, column=4, padx=5, pady=2)

        ttk.Checkbutton(frame, text="k3", variable=self.k3).grid(row=18, column=0, padx=5, pady=2)
        ttk.Checkbutton(frame, text="p1", variable=self.p1).grid(row=18, column=1, padx=5, pady=2)
        ttk.Checkbutton(frame, text="p2", variable=self.p2).grid(row=18, column=2, padx=5, pady=2)
        ttk.Checkbutton(frame, text="scale", variable=self.scale).grid(row=18, column=3, padx=5, pady=2)
        ttk.Checkbutton(frame, text="shear", variable=self.shear).grid(row=18, column=4, padx=5, pady=2)

        ttk.Checkbutton(frame, text="interfaces", variable=self.interf).grid(row=19, column=0, columnspan=2, sticky='w', padx=5, pady=5)

    def _create_dumbbell_tab(self, notebook):
        """Create Dumbbell Calibration tab"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Dumbbell")

        ttk.Label(frame, text="Dumbbell Calibration Parameters", font=('Arial', 10, 'bold')).grid(row=0, column=0, columnspan=2, pady=(5, 15))

        ttk.Label(frame, text="Epsilon:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.dumbbell_eps).grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Scale:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.dumbbell_scale).grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Gradient Descent:").grid(row=3, column=0, sticky='w', padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.dumbbell_grad).grid(row=3, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Penalty Weight:").grid(row=4, column=0, sticky='w', padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.dumbbell_penalty).grid(row=4, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Step Size:").grid(row=5, column=0, sticky='w', padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.dumbbell_step).grid(row=5, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Iterations:").grid(row=6, column=0, sticky='w', padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.dumbbell_niter).grid(row=6, column=1, padx=5, pady=5)

    def _create_shaking_tab(self, notebook):
        """Create Shaking Calibration tab"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Shaking")

        ttk.Label(frame, text="Shaking Calibration Parameters", font=('Arial', 10, 'bold')).grid(row=0, column=0, columnspan=2, pady=(5, 15))

        ttk.Label(frame, text="First Frame:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.shaking_first).grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Last Frame:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.shaking_last).grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Max Points:").grid(row=3, column=0, sticky='w', padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.shaking_max_points).grid(row=3, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Max Frames:").grid(row=4, column=0, sticky='w', padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.shaking_max_frames).grid(row=4, column=1, padx=5, pady=5)

    def _on_ok(self):
        """Handle OK button - save parameters"""
        try:
            self._save_parameters()
            messagebox.showinfo("Success", "Calibration parameters saved successfully!")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save parameters: {e}")

    def _on_cancel(self):
        """Handle Cancel button"""
        self.destroy()

    def _save_parameters(self):
        """Save calibration parameters back to experiment"""
        params = self.experiment.pm.parameters
        num_cams = self.experiment.get_n_cam()

        # Update PTV parameters (image size, pixel size)
        ptv_params = params.get('ptv', {})
        ptv_params.update({
            'imx': self.h_image_size.get(),
            'imy': self.v_image_size.get(),
            'pix_x': self.h_pixel_size.get(),
            'pix_y': self.v_pixel_size.get()
        })
        params['ptv'] = ptv_params

        # Update cal_ori parameters
        cal_ori = params.get('cal_ori', {})
        cal_ori.update({
            'img_cal_name': [
                self.cam_1.get(), self.cam_2.get(),
                self.cam_3.get(), self.cam_4.get()
            ],
            'img_ori': [
                self.ori_cam_1.get(), self.ori_cam_2.get(),
                self.ori_cam_3.get(), self.ori_cam_4.get()
            ],
            'fixp_name': self.fixp_name.get(),
            'cal_splitter': self.cal_splitter.get()
        })
        params['cal_ori'] = cal_ori

        # Update detect_plate parameters
        detect_plate = params.get('detect_plate', {})
        detect_plate.update({
            'gvth_1': self.grey_thresh_1.get(),
            'gvth_2': self.grey_thresh_2.get(),
            'gvth_3': self.grey_thresh_3.get(),
            'gvth_4': self.grey_thresh_4.get(),
            'tol_dis': self.tol_discontinuity.get(),
            'min_npix': self.min_npix.get(),
            'max_npix': self.max_npix.get(),
            'min_npix_x': self.min_npix_x.get(),
            'max_npix_x': self.max_npix_x.get(),
            'min_npix_y': self.min_npix_y.get(),
            'max_npix_y': self.max_npix_y.get(),
            'sum_grey': self.sum_grey.get(),
            'size_cross': self.size_crosses.get()
        })
        params['detect_plate'] = detect_plate

        # Update man_ori parameters
        nr = []
        for cam in range(num_cams):
            for point in range(4):
                nr.append(getattr(self, f'img_{cam+1}_p{point+1}').get())

        man_ori = params.get('man_ori', {})
        man_ori['nr'] = nr
        params['man_ori'] = man_ori

        # Update examine parameters
        examine = params.get('examine', {})
        examine.update({
            'Examine_Flag': self.examine_flag.get(),
            'Combine_Flag': self.combine_flag.get()
        })
        params['examine'] = examine

        # Update orient parameters
        orient = params.get('orient', {})
        orient.update({
            'pnfo': self.point_num_ori.get(),
            'cc': self.cc.get(),
            'xh': self.xh.get(),
            'yh': self.yh.get(),
            'k1': self.k1.get(),
            'k2': self.k2.get(),
            'k3': self.k3.get(),
            'p1': self.p1.get(),
            'p2': self.p2.get(),
            'scale': self.scale.get(),
            'shear': self.shear.get(),
            'interf': self.interf.get()
        })
        params['orient'] = orient

        # Update dumbbell parameters
        dumbbell = params.get('dumbbell', {})
        dumbbell.update({
            'dumbbell_eps': self.dumbbell_eps.get(),
            'dumbbell_scale': self.dumbbell_scale.get(),
            'dumbbell_gradient_descent': self.dumbbell_grad.get(),
            'dumbbell_penalty_weight': self.dumbbell_penalty.get(),
            'dumbbell_step': self.dumbbell_step.get(),
            'dumbbell_niter': self.dumbbell_niter.get()
        })
        params['dumbbell'] = dumbbell

        # Update shaking parameters
        shaking = params.get('shaking', {})
        shaking.update({
            'shaking_first_frame': self.shaking_first.get(),
            'shaking_last_frame': self.shaking_last.get(),
            'shaking_max_num_points': self.shaking_max_points.get(),
            'shaking_max_num_frames': self.shaking_max_frames.get()
        })
        params['shaking'] = shaking

        # Save to YAML file
        self.experiment.save_parameters()
        print("Calibration parameters saved successfully!")


class TrackingParamsTTK(tk.Toplevel):
    """TTK-based Tracking Parameters GUI"""

    def __init__(self, parent, experiment: Experiment):
        super().__init__(parent)
        self.title("Tracking Parameters")
        self.geometry("400x300")
        self.experiment = experiment

        # Initialize variables
        self._init_variables()

        # Load parameters from experiment
        self._load_parameters()

        # Create GUI
        self._create_gui()

        # Center window
        self.transient(parent)
        self.grab_set()

    def _init_variables(self):
        """Initialize tracking parameter variables"""
        self.dvxmin = tk.DoubleVar(value=-10.0)
        self.dvxmax = tk.DoubleVar(value=10.0)
        self.dvymin = tk.DoubleVar(value=-10.0)
        self.dvymax = tk.DoubleVar(value=10.0)
        self.dvzmin = tk.DoubleVar(value=-10.0)
        self.dvzmax = tk.DoubleVar(value=10.0)
        self.angle = tk.DoubleVar(value=45.0)
        self.dacc = tk.DoubleVar(value=1.0)
        self.add_new_particles = tk.BooleanVar(value=True)

    def _load_parameters(self):
        """Load tracking parameters from experiment"""
        params = self.experiment.pm.parameters
        track_params = params.get('track', {})

        self.dvxmin.set(track_params.get('dvxmin', -10.0))
        self.dvxmax.set(track_params.get('dvxmax', 10.0))
        self.dvymin.set(track_params.get('dvymin', -10.0))
        self.dvymax.set(track_params.get('dvymax', 10.0))
        self.dvzmin.set(track_params.get('dvzmin', -10.0))
        self.dvzmax.set(track_params.get('dvzmax', 10.0))
        self.angle.set(track_params.get('angle', 45.0))
        self.dacc.set(track_params.get('dacc', 1.0))
        self.add_new_particles.set(track_params.get('flagNewParticles', True))

    def _create_gui(self):
        """Create the tracking parameters GUI"""
        # Main frame
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill='both', expand=True)

        # Title
        ttk.Label(main_frame, text="Tracking Parameters", font=('Arial', 12, 'bold')).pack(pady=(0, 20))

        # Velocity limits
        ttk.Label(main_frame, text="Velocity Limits (mm/frame)", font=('Arial', 10, 'bold')).pack(anchor='w', pady=(0, 10))

        # X velocity
        x_frame = ttk.Frame(main_frame)
        x_frame.pack(fill='x', pady=2)
        ttk.Label(x_frame, text="X Velocity:").pack(side='left')
        ttk.Entry(x_frame, textvariable=self.dvxmin, width=8).pack(side='left', padx=(5, 2))
        ttk.Label(x_frame, text="to").pack(side='left', padx=2)
        ttk.Entry(x_frame, textvariable=self.dvxmax, width=8).pack(side='left', padx=(2, 5))

        # Y velocity
        y_frame = ttk.Frame(main_frame)
        y_frame.pack(fill='x', pady=2)
        ttk.Label(y_frame, text="Y Velocity:").pack(side='left')
        ttk.Entry(y_frame, textvariable=self.dvymin, width=8).pack(side='left', padx=(5, 2))
        ttk.Label(y_frame, text="to").pack(side='left', padx=2)
        ttk.Entry(y_frame, textvariable=self.dvymax, width=8).pack(side='left', padx=(2, 5))

        # Z velocity
        z_frame = ttk.Frame(main_frame)
        z_frame.pack(fill='x', pady=2)
        ttk.Label(z_frame, text="Z Velocity:").pack(side='left')
        ttk.Entry(z_frame, textvariable=self.dvzmin, width=8).pack(side='left', padx=(5, 2))
        ttk.Label(z_frame, text="to").pack(side='left', padx=2)
        ttk.Entry(z_frame, textvariable=self.dvzmax, width=8).pack(side='left', padx=(2, 5))

        # Other parameters
        ttk.Label(main_frame, text="Other Parameters", font=('Arial', 10, 'bold')).pack(anchor='w', pady=(20, 10))

        angle_frame = ttk.Frame(main_frame)
        angle_frame.pack(fill='x', pady=2)
        ttk.Label(angle_frame, text="Angle (gon):").pack(side='left')
        ttk.Entry(angle_frame, textvariable=self.angle, width=10).pack(side='left', padx=(5, 0))

        dacc_frame = ttk.Frame(main_frame)
        dacc_frame.pack(fill='x', pady=2)
        ttk.Label(dacc_frame, text="Dacc:").pack(side='left')
        ttk.Entry(dacc_frame, textvariable=self.dacc, width=10).pack(side='left', padx=(5, 0))

        # Checkbox
        ttk.Checkbutton(main_frame, text="Add new particles during tracking", variable=self.add_new_particles).pack(anchor='w', pady=(10, 0))

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(30, 0))

        ttk.Button(button_frame, text="OK", command=self._on_ok).pack(side='right', padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", command=self._on_cancel).pack(side='right')

    def _on_ok(self):
        """Handle OK button - save parameters"""
        try:
            self._save_parameters()
            messagebox.showinfo("Success", "Tracking parameters saved successfully!")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save parameters: {e}")

    def _on_cancel(self):
        """Handle Cancel button"""
        self.destroy()

    def _save_parameters(self):
        """Save tracking parameters back to experiment"""
        params = self.experiment.pm.parameters

        # Ensure track section exists
        if 'track' not in params:
            params['track'] = {}

        # Update tracking parameters
        params['track'].update({
            'dvxmin': self.dvxmin.get(),
            'dvxmax': self.dvxmax.get(),
            'dvymin': self.dvymin.get(),
            'dvymax': self.dvymax.get(),
            'dvzmin': self.dvzmin.get(),
            'dvzmax': self.dvzmax.get(),
            'angle': self.angle.get(),
            'dacc': self.dacc.get(),
            'flagNewParticles': self.add_new_particles.get()
        })

        # Save to YAML file
        self.experiment.save_parameters()
        print("Tracking parameters saved successfully!")
