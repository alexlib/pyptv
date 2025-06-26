"""
Editor for editing the cameras ori files
"""

# Imports:
from traits.api import (
    HasTraits,
    Code,
    Int,
    List,
    Button,
    File,
)

from traitsui.api import Item, Group, View, Handler, ListEditor

from pathlib import Path
from pyptv import parameters as par


def get_path(filename):
    splitted_filename = filename.split("/")
    return os.getcwd() + os.sep + splitted_filename[0] + os.sep + splitted_filename[1]


def get_code(path: Path):
    """Read the code from the file"""

    # print(f"Read from {path}: {path.exists()}")
    with open(path, "r", encoding="utf-8") as f:
        retCode = f.read()

    # print(retCode)

    return retCode


class codeEditor(HasTraits):
    file_Path = Path
    _Code = Code()
    save_button = Button(label="Save")
    buttons_group = Group(
        Item(name="file_Path", style="simple", show_label=True, width=0.3),
        Item(name="save_button", show_label=True),
        orientation="horizontal",
    )
    traits_view = View(
        Group(
            Item(name="_Code", show_label=False, height=300, width=650),
            buttons_group,
        )
    )

    def _save_button_fired(self):
        with open(self.file_Path, "w", encoding="utf-8") as f:
            # print(f"Saving to {self.file_Path}")
            # print(f"Code: {self._Code}")
            f.write(self._Code)

        print(f"Saved to {self.file_Path}")

    def __init__(self, file_path: Path):
        self.file_Path = file_path
        self._Code = get_code(file_path)


class oriEditor(HasTraits):
    # number of images
    n_img = Int()

    oriEditors = List

    # view
    traits_view = View(
        Item(
            "oriEditors",
            style="custom",
            editor=ListEditor(
                use_notebook=True,
                deletable=False,
                dock_style="tab",
                page_name=".file_Path",
            ),
            show_label=False,
        ),
        buttons=["Cancel"],
        title="Camera's orientation files",
    )

    def __init__(self, path: Path):
        """Initialize by reading parameters and filling the editor windows"""
        # load ptv_par
        ptvParams = par.PtvParams(path=path)
        ptvParams.read()
        self.n_img = ptvParams.n_img

        # load cal_ori
        calOriParams = par.CalOriParams(self.n_img)
        calOriParams.read()

        for i in range(self.n_img):
            self.oriEditors.append(codeEditor(Path(calOriParams.img_ori[i])))


class addparEditor(HasTraits):
    # number of images
    n_img = Int()

    addparEditors = List

    # view
    traits_view = View(
        Item(
            "addparEditors",
            style="custom",
            editor=ListEditor(
                use_notebook=True,
                deletable=False,
                dock_style="tab",
                page_name=".file_Path",
            ),
            show_label=False,
        ),
        buttons=["Cancel"],
        title="Camera's additional parameters files",
    )

    def __init__(self, path):
        """Initialize by reading parameters and filling the editor windows"""
        # load ptv_par
        ptvParams = par.PtvParams(path=path)
        ptvParams.read()
        self.n_img = ptvParams.n_img

        # load cal_ori
        calOriParams = par.CalOriParams(self.n_img, path=path)
        calOriParams.read()

        for i in range(self.n_img):
            self.addparEditors.append(
                codeEditor(Path(calOriParams.img_ori[i].replace("ori", "addpar")))
            )


def minimal_napari():
    """Create napari viewer with minimal interface - only central image viewer"""
    import napari
    from qtpy.QtWidgets import QTabWidget
    
    # Create viewer with minimal interface
    viewer = napari.Viewer(show=False)  # Don't show yet
    
    # Hide default widgets/panels
    viewer.window._qt_window.dockwidgets = {}  # Clear existing dock widgets
    
    # Remove default layer controls, console, etc.
    for dock_widget in viewer.window._qt_window.findChildren(object):
        if hasattr(dock_widget, 'setVisible') and hasattr(dock_widget, 'objectName'):
            name = dock_widget.objectName()
            if any(default in name.lower() for default in ['layer', 'console', 'activity']):
                dock_widget.setVisible(False)
    
    # Create custom tab widget for all controls
    tab_widget = QTabWidget()
    
    # Add orientation editor tab
    ori_widget = open_ori_editor.Gui()
    tab_widget.addTab(ori_widget.native, "Orientation Files")
    
    # Add additional parameters editor tab
    addpar_widget = open_addpar_editor.Gui()
    tab_widget.addTab(addpar_widget.native, "Additional Parameters")
    
    # Add the tab widget to the right side
    viewer.window.add_dock_widget(
        tab_widget, 
        area='right', 
        name='PTV Controls',
        allowed_areas=['right', 'left']
    )
    
    # Show the viewer
    viewer.show()
    
    return viewer, tab_widget


def custom_napari_app():
    """Run napari with custom tabbed interface"""
    import sys
    
    # Create minimal napari viewer
    viewer, tab_widget = minimal_napari()
    
    # If path provided as command line argument
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        project_path = Path(sys.argv[1])
        if project_path.exists():
            print(f"Opening project: {project_path}")
            # Set default paths in the tab widgets
            ori_widget = tab_widget.widget(0)  # Orientation tab
            addpar_widget = tab_widget.widget(1)  # Addpar tab
            
            if hasattr(ori_widget, 'path'):
                ori_widget.path.value = project_path
            if hasattr(addpar_widget, 'path'):
                addpar_widget.path.value = project_path
    
    # Start napari
    napari.run()
    
    return viewer


def main():
    """Main function to run the code editor"""
    import sys
    
    # Check run mode
    standalone = "--standalone" in sys.argv or "-s" in sys.argv
    minimal = "--minimal" in sys.argv or "-m" in sys.argv
    
    if standalone:
        # ...existing code...
        print("Running in standalone mode...")
        # ...existing standalone code...
        
    elif minimal:
        # Run napari with minimal interface and custom tabs
        print("Running napari with minimal interface...")
        custom_napari_app()
        
    else:
        # ...existing code...
        print("Running with napari...")
        # ...existing napari code...


# Alternative approach - completely custom napari setup
def create_clean_napari():
    """Create napari viewer with completely clean interface"""
    import napari
    from qtpy.QtWidgets import QTabWidget, QWidget, QVBoxLayout
    
    # Create viewer
    viewer = napari.Viewer(show=False)
    
    # Access the main window
    main_window = viewer.window._qt_window
    
    # Remove all default dock widgets
    for dock in main_window.findChildren(object):
        if hasattr(dock, 'setVisible') and 'dock' in str(type(dock)).lower():
            dock.setVisible(False)
            dock.deleteLater()
    
    # Create main container for custom widgets
    custom_container = QWidget()
    custom_layout = QVBoxLayout(custom_container)
    
    # Create tab widget
    tabs = QTabWidget()
    
    # Add custom tabs
    ori_tab = open_ori_editor.Gui()
    tabs.addTab(ori_tab.native, "Orientation")
    
    addpar_tab = open_addpar_editor.Gui()  
    tabs.addTab(addpar_tab.native, "Parameters")
    
    # You can add more custom tabs here
    # tabs.addTab(some_other_widget, "Analysis")
    # tabs.addTab(another_widget, "Calibration")
    
    custom_layout.addWidget(tabs)
    
    # Add to napari as single dock widget
    viewer.window.add_dock_widget(
        custom_container,
        area='right',
        name='PTV Tools'
    )
    
    viewer.show()
    return viewer, tabs
