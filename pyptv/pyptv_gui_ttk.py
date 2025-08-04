import tkinter as tk
from tkinter import ttk, Menu, Toplevel, messagebox
import ttkbootstrap as tb
from pathlib import Path
from pyptv.parameter_gui import Main_Params, Calib_Params, Tracking_Params

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

class MainApp(tb.Window):
    def __init__(self, experiment=None):
        super().__init__(themename='flatly')
        self.title('pyPTV Modern GUI')
        self.geometry('1200x700')
        self.experiment = experiment
        self.create_menu()
        self.create_layout()

    def create_menu(self):
        menubar = Menu(self)
        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_command(label='Open')
        filemenu.add_command(label='Save As')
        filemenu.add_separator()
        filemenu.add_command(label='Exit', command=self.quit)
        menubar.add_cascade(label='File', menu=filemenu)
        self.config(menu=menubar)

    def create_layout(self):
        main_frame = ttk.Frame(self)
        main_frame.pack(fill='both', expand=True)
        # Left: Tree
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(side='left', fill='y', padx=5, pady=5)
        self.tree = TreeMenu(tree_frame, self.experiment)
        self.tree.pack(fill='y', expand=True)
        # Right: Camera panels
        cam_frame = ttk.Frame(main_frame)
        cam_frame.pack(side='right', fill='both', expand=True, padx=5, pady=5)
        cam_grid = ttk.Frame(cam_frame)
        cam_grid.pack(fill='both', expand=True)
        self.cameras = []
        for i in range(2):
            for j in range(2):
                cam_panel = CameraPanel(cam_grid, f'Camera {i*2+j+1}')
                cam_panel.grid(row=i, column=j, padx=10, pady=10, sticky='nsew')
                self.cameras.append(cam_panel)
        for i in range(2):
            cam_grid.rowconfigure(i, weight=1)
            cam_grid.columnconfigure(i, weight=1)

if __name__ == '__main__':
    # TODO: Load experiment object as needed
    app = MainApp(experiment=None)
    app.mainloop()
