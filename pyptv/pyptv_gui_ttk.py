import tkinter as tk
from tkinter import ttk, Menu, Toplevel, messagebox, filedialog
try:
    import ttkbootstrap as tb
except ModuleNotFoundError:
    tb = None
from pathlib import Path
from pyptv.parameter_gui import Main_Params, Calib_Params, Tracking_Params
from pyptv import ptv
from pyptv.experiment import Experiment

class CameraPanel(ttk.Frame):
    def __init__(self, parent, cam_name):
        super().__init__(parent, padding=5)
        self.label = ttk.Label(self, text=cam_name)
        self.label.pack(anchor='n')
        self.canvas = tk.Canvas(self, width=320, height=240, bg='black')
        self.canvas.pack(fill='both', expand=True)
        # TODO: Add image display logic

class ParameterWindow(Toplevel):
    def __init__(self, parent, param_type, experiment):
        super().__init__(parent)
        self.title(f"{param_type} Parameters")
        # TODO: Use Main_Params, Calib_Params, Tracking_Params as needed
        # For now, just show a placeholder
        ttk.Label(self, text=f"{param_type} parameters window").pack(padx=20, pady=20)

class TreeMenu(ttk.Treeview):
    def __init__(self, parent, experiment):
        super().__init__(parent)
        self.experiment = experiment
        self.heading('#0', text='Experiments')
        # Example tree structure
        exp_id = self.insert('', 'end', text='Experiment')
        params_id = self.insert(exp_id, 'end', text='Parameters')
        self.insert(params_id, 'end', text='Main')
        self.insert(params_id, 'end', text='Calibration')
        self.insert(params_id, 'end', text='Tracking')
        self.bind('<Button-3>', self.on_right_click)

    def on_right_click(self, event):
        item = self.identify_row(event.y)
        if not item:
            return
        self.selection_set(item)
        menu = Menu(self, tearoff=0)
        if self.item(item, 'text') == 'Main':
            menu.add_command(label='Edit Main Parameters', command=lambda: self.open_param_window('Main'))
        elif self.item(item, 'text') == 'Calibration':
            menu.add_command(label='Edit Calibration Parameters', command=lambda: self.open_param_window('Calibration'))
        elif self.item(item, 'text') == 'Tracking':
            menu.add_command(label='Edit Tracking Parameters', command=lambda: self.open_param_window('Tracking'))
        menu.post(event.x_root, event.y_root)

    def open_param_window(self, param_type):
        ParameterWindow(self.master, param_type, self.experiment)

# Choose a base window class depending on ttkbootstrap availability
BaseWindow = tb.Window if tb is not None else tk.Tk


class MainApp(BaseWindow):
    def __init__(self, experiment=None):
        if tb is not None:
            super().__init__(themename='superhero') # or flatly 
        else:
            super().__init__()
        self.title('pyPTV Modern GUI')
        self.geometry('1200x700')
        self.experiment = experiment
        self.layout_mode = 'tabs'  # 'tabs' or 'grid'
        self.create_menu()
        self.create_layout()

    def create_menu(self):
        menubar = Menu(self)

        # File menu
        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_command(label='New', command=self.not_implemented)
        filemenu.add_command(label='Open', command=self.open_yaml_action)
        filemenu.add_command(label='Save As', command=self.not_implemented)
        filemenu.add_separator()
        filemenu.add_command(label='Exit', command=self.quit)
        menubar.add_cascade(label='File', menu=filemenu)

        # Start menu
        startmenu = Menu(menubar, tearoff=0)
        startmenu.add_command(label='Init / Reload', command=self.not_implemented)
        menubar.add_cascade(label='Start', menu=startmenu)

        # Preprocess menu
        preprocessmenu = Menu(menubar, tearoff=0)
        preprocessmenu.add_command(label='High pass filter', command=self.not_implemented)
        preprocessmenu.add_command(label='Image coord', command=self.not_implemented)
        preprocessmenu.add_command(label='Correspondences', command=self.not_implemented)
        menubar.add_cascade(label='Preprocess', menu=preprocessmenu)

        # 3D Positions menu
        pos3dmenu = Menu(menubar, tearoff=0)
        pos3dmenu.add_command(label='3D positions', command=self.not_implemented)
        menubar.add_cascade(label='3D Positions', menu=pos3dmenu)

        # Calibration menu
        calibmenu = Menu(menubar, tearoff=0)
        calibmenu.add_command(label='Create calibration', command=self.not_implemented)
        menubar.add_cascade(label='Calibration', menu=calibmenu)

        # Sequence menu
        seqmenu = Menu(menubar, tearoff=0)
        seqmenu.add_command(label='Sequence without display', command=self.not_implemented)
        menubar.add_cascade(label='Sequence', menu=seqmenu)

        # Tracking menu
        trackingmenu = Menu(menubar, tearoff=0)
        trackingmenu.add_command(label='Detected Particles', command=self.not_implemented)
        trackingmenu.add_command(label='Tracking without display', command=self.not_implemented)
        trackingmenu.add_command(label='Tracking backwards', command=self.not_implemented)
        trackingmenu.add_command(label='Show trajectories', command=self.not_implemented)
        trackingmenu.add_command(label='Save Paraview files', command=self.not_implemented)
        menubar.add_cascade(label='Tracking', menu=trackingmenu)

        # Plugins menu
        pluginsmenu = Menu(menubar, tearoff=0)
        pluginsmenu.add_command(label='Select plugin', command=self.not_implemented)
        menubar.add_cascade(label='Plugins', menu=pluginsmenu)

        # Detection demo menu
        detectionmenu = Menu(menubar, tearoff=0)
        detectionmenu.add_command(label='Detection GUI demo', command=self.not_implemented)
        menubar.add_cascade(label='Detection demo', menu=detectionmenu)

        # Drawing mask menu
        maskmenu = Menu(menubar, tearoff=0)
        maskmenu.add_command(label='Draw mask', command=self.not_implemented)
        menubar.add_cascade(label='Drawing mask', menu=maskmenu)

        # View menu
        viewmenu = Menu(menubar, tearoff=0)
        viewmenu.add_command(label='Tabs', command=self.set_layout_tabs)
        viewmenu.add_command(label='Panels (2x2 grid)', command=self.set_layout_grid)
        menubar.add_cascade(label='View', menu=viewmenu)

        self.config(menu=menubar)

    def refresh_tree(self):
        # Rebuild the left tree when experiment changes
        for child in self.left_panel.winfo_children():
            child.destroy()
        self.tree = TreeMenu(self.left_panel, self.experiment)
        self.tree.pack(fill='both', expand=True)

    def open_yaml_action(self):
        # Ask user for a YAML file and open as Experiment using core helpers
        filetypes = [("YAML files", "*.yaml *.yml"), ("All files", "*.*")]
        path = filedialog.askopenfilename(title="Open parameters YAML", filetypes=filetypes)
        if not path:
            return
        try:
            exp = ptv.open_experiment_from_yaml(Path(path))
        except Exception as e:
            messagebox.showerror("Open failed", f"Could not open experiment:\n{e}")
            return
        self.experiment = exp
        self.refresh_tree()
        messagebox.showinfo("Experiment loaded", f"Loaded: {Path(path).name}\nParamsets: {len(exp.paramsets)}")

    def not_implemented(self):
        messagebox.showinfo('Not implemented', 'This feature is not yet implemented.')

    def create_layout(self):
        # Paned window for resizable left tree and right content
        self.main_paned = ttk.Panedwindow(self, orient='horizontal')
        self.main_paned.pack(fill='both', expand=True)

        # Left: Tree panel
        self.left_panel = ttk.Frame(self.main_paned, padding=(5, 5))
        self.tree = TreeMenu(self.left_panel, self.experiment)
        self.tree.pack(fill='both', expand=True)
        self.main_paned.add(self.left_panel, weight=1)

        # Right: Container for camera views (tabs or grid)
        self.right_container = ttk.Frame(self.main_paned, padding=(5, 5))
        self.main_paned.add(self.right_container, weight=4)

        # Build initial layout
        if self.layout_mode == 'tabs':
            self.build_tabs()
        else:
            self.build_grid()

    def clear_right_container(self):
        for w in self.right_container.winfo_children():
            w.destroy()
        self.cameras = []

    def build_tabs(self):
        self.clear_right_container()
        nb = ttk.Notebook(self.right_container)
        nb.pack(fill='both', expand=True)
        self.cameras = []
        for i in range(4):
            frame = ttk.Frame(nb)
            cam_panel = CameraPanel(frame, f'Camera {i+1}')
            cam_panel.pack(fill='both', expand=True)
            nb.add(frame, text=f'Camera {i+1}')
            self.cameras.append(cam_panel)

    def build_grid(self):
        self.clear_right_container()
        grid = ttk.Frame(self.right_container)
        grid.pack(fill='both', expand=True)
        self.cameras = []
        for i in range(2):
            for j in range(2):
                cam_panel = CameraPanel(grid, f'Camera {i*2+j+1}')
                cam_panel.grid(row=i, column=j, padx=10, pady=10, sticky='nsew')
                self.cameras.append(cam_panel)
        for i in range(2):
            grid.rowconfigure(i, weight=1)
            grid.columnconfigure(i, weight=1)

    def set_layout_tabs(self):
        self.layout_mode = 'tabs'
        self.build_tabs()

    def set_layout_grid(self):
        self.layout_mode = 'grid'
        self.build_grid()

if __name__ == '__main__':
    # TODO: Load experiment object as needed
    app = MainApp(experiment=None)
    app.mainloop()
