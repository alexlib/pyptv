"""
Tkinter-based editor for editing camera orientation and parameter files.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from pyptv.experiment import Experiment

class CodeEditorFrame(ttk.Frame):
    """A frame containing a text editor and a save button for a single file."""
    def __init__(self, parent, file_path: Path):
        super().__init__(parent)
        self.file_path = file_path

        # Create widgets
        self.text_widget = tk.Text(self, wrap='word', undo=True)
        self.scrollbar = ttk.Scrollbar(self, orient='vertical', command=self.text_widget.yview)
        self.text_widget.config(yscrollcommand=self.scrollbar.set)

        self.save_button = ttk.Button(self, text=f"Save {self.file_path.name}", command=self.save_file)

        # Layout
        self.text_widget.pack(side='left', fill='both', expand=True)
        self.scrollbar.pack(side='right', fill='y')
        self.save_button.pack(fill='x', pady=5)

        # Load content
        self.load_file()

    def load_file(self):
        """Load file content into the text widget."""
        try:
            content = self.file_path.read_text(encoding='utf-8')
            self.text_widget.delete('1.0', 'end')
            self.text_widget.insert('1.0', content)
        except Exception as e:
            self.text_widget.delete('1.0', 'end')
            self.text_widget.insert('1.0', f"Error loading file: {e}")

    def save_file(self):
        """Save content from the text widget back to the file."""
        try:
            content = self.text_widget.get('1.0', 'end-1c') # -1c to exclude trailing newline
            self.file_path.write_text(content, encoding='utf-8')
            messagebox.showinfo("Success", f"Saved {self.file_path.name}", parent=self)
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save file: {e}", parent=self)

class TabbedCodeEditor(tk.Toplevel):
    """A Toplevel window with a tabbed interface for editing multiple files."""
    def __init__(self, parent, file_paths: list, title: str):
        super().__init__(parent)
        self.title(title)
        self.geometry("800x600")

        notebook = ttk.Notebook(self)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)

        for file_path in file_paths:
            if not file_path.exists():
                print(f"Warning: File not found, skipping: {file_path}")
                continue
            
            editor_frame = ttk.Frame(notebook)
            notebook.add(editor_frame, text=file_path.name)
            
            # Embed the code editor frame
            CodeEditorFrame(editor_frame, file_path).pack(fill='both', expand=True)

def open_ori_editors(experiment: Experiment, parent):
    """Opens a tabbed editor for all .ori files in the experiment."""
    try:
        cal_ori_params = experiment.get_parameter('cal_ori')
        if cal_ori_params is None:
            raise ValueError("Calibration orientation parameters not found.")

        num_cams = experiment.get_n_cam()
        ori_files = [Path(p) for p in cal_ori_params['img_ori'][:num_cams]]
        
        TabbedCodeEditor(parent, ori_files, "Orientation Files Editor")
    except Exception as e:
        messagebox.showerror("Error", f"Could not open ORI editors: {e}")

def open_addpar_editors(experiment: Experiment, parent):
    """Opens a tabbed editor for all .addpar files in the experiment."""
    try:
        cal_ori_params = experiment.get_parameter('cal_ori')
        if cal_ori_params is None:
            raise ValueError("Calibration orientation parameters not found.")

        num_cams = experiment.get_n_cam()
        addpar_files = [Path(p.replace(".ori", ".addpar")) for p in cal_ori_params['img_ori'][:num_cams]]
        
        TabbedCodeEditor(parent, addpar_files, "Additional Parameters Editor")
    except Exception as e:
        messagebox.showerror("Error", f"Could not open addpar editors: {e}")
