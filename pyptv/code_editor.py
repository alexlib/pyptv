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
    return (
        os.getcwd()
        + os.sep
        + splitted_filename[0]
        + os.sep
        + splitted_filename[1]
    )


def get_code(path: Path):
    """ Read the code from the file """

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
        """ Initialize by reading parameters and filling the editor windows """
        # load ptv_par
        ptvParams = par.PtvParams(path=path)
        ptvParams.read()
        self.n_img = ptvParams.n_img

        # load cal_ori
        calOriParams = par.CalOriParams(self.n_img)
        calOriParams.read()

        for i in range(self.n_img):
            self.oriEditors.append(
                codeEditor(Path(calOriParams.img_ori[i]))
            )


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
        """ Initialize by reading parameters and filling the editor windows """
        # load ptv_par
        ptvParams = par.PtvParams(path=path)
        ptvParams.read()
        self.n_img = ptvParams.n_img

        # load cal_ori
        calOriParams = par.CalOriParams(self.n_img, path=path)
        calOriParams.read()

        for i in range(self.n_img):
            self.addparEditors.append(
                codeEditor(Path(calOriParams.img_ori[i].replace('ori', 'addpar')))
            )
