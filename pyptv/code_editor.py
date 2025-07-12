"""
Editor for editing the cameras ori files
"""
import os

# Imports:
from traits.api import (
    HasTraits,
    Code,
    Int,
    List,
    Button,
)

from traitsui.api import Item, Group, View, ListEditor

from pathlib import Path
from pyptv.experiment import Experiment


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


class CodeEditor(HasTraits):
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
        with open(str(self.file_Path), "w", encoding="utf-8") as f:
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

    oriEditors = List()

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

    def __init__(self, experiment: Experiment):
        """Initialize by reading parameters and filling the editor windows"""
        ptv_params = experiment.get_parameter('ptv')
        cal_ori_params = experiment.get_parameter('cal_ori')
        
        if ptv_params is None or cal_ori_params is None:
            raise ValueError("Failed to load required parameters")
            
        self.n_img = int(experiment.get_n_cam())
        img_ori = cal_ori_params['img_ori']

        for i in range(self.n_img):
            self.oriEditors.append(CodeEditor(Path(img_ori[i])))


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

    def __init__(self, experiment: Experiment):
        """Initialize by reading parameters and filling the editor windows"""
        ptv_params = experiment.get_parameter('ptv')
        cal_ori_params = experiment.get_parameter('cal_ori')
        
        if ptv_params is None or cal_ori_params is None:
            raise ValueError("Failed to load required parameters")
            
        self.n_img = int(experiment.get_n_cam())
        img_ori = cal_ori_params['img_ori']

        for i in range(self.n_img):
            self.addparEditors.append(
                codeEditor(Path(img_ori[i].replace("ori", "addpar")))
            )