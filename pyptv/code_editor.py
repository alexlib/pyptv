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


# def get_path(filename):
#     splitted_filename = filename.split("/")
#     return (
#         os.getcwd()
#         + os.sep
#         + splitted_filename[0]
#         + os.sep
#         + splitted_filename[1]
#     )


def get_code(path):
    f = open(path, "r")

    retCode = f.read()
    f.close()
    return retCode


class oriEditor(HasTraits):
    file_Path = File
    ori_Code = Code()
    ori_Save = Button(label="Save")
    buttons_group = Group(
        Item(name="file_Path", style="simple", show_label=False, width=0.3),
        Item(name="ori_Save", show_label=False),
        orientation="horizontal",
    )
    traits_view = View(
        Group(
            Item(name="ori_Code", show_label=False, height=300, width=650),
            buttons_group,
        )
    )

    def _ori_Save_fired(self, filename, code):
        f = open(self.file_Path, "w")
        f.write(self.ori_Code)
        f.close()

    def __init__(self, file_path):
        self.file_Path = file_path
        self.ori_Code = get_code(file_path)


class codeEditor(HasTraits):

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

    def __init__(self, path):
        # load ptv_par
        ptvParams = par.PtvParams(path=path)
        ptvParams.read()
        self.n_img = ptvParams.n_img

        # load cal_ori
        calOriParams = par.CalOriParams(self.n_img, path=path)
        calOriParams.read()

        for i in range(self.n_img):
            self.oriEditors.append(
                oriEditor(get_path(calOriParams.img_ori[i]))
            )
