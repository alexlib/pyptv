"""
Copyright (c) 2008-2013, Tel Aviv University
Copyright (c) 2013 - the OpenPTV team
The software is distributed under the terms of MIT-like license
http://opensource.org/licenses/MIT
"""

import os
from pathlib import Path
import numpy as np
from skimage.io import imread
from skimage.util import img_as_ubyte
from skimage.color import rgb2gray

from traits.api import HasTraits, Str, Int, Bool, Instance, Button
from traitsui.api import View, Item, HGroup, VGroup, ListEditor
from enable.component_editor import ComponentEditor

from chaco.api import (
    Plot,
    ArrayPlotData,
    gray,
    PolygonPlot,
)

from chaco.tools.image_inspector_tool import ImageInspectorTool
from chaco.tools.better_zoom import BetterZoom as SimpleZoom

from pyptv.text_box_overlay import TextBoxOverlay
from pyptv import ptv
from pyptv.experiment import Experiment


# recognized names for the flags:
NAMES = ["cc", "xh", "yh", "k1", "k2", "k3", "p1", "p2", "scale", "shear"]
SCALE = 5000


# -------------------------------------------
class ClickerTool(ImageInspectorTool):
    left_changed = Int(1)
    right_changed = Int(1)
    x = 0
    y = 0

    def normal_left_down(self, event):
        """Handles the left mouse button being clicked.
        Fires the **new_value** event with the data (if any) from the event's
        position.
        """
        plot = self.component
        if plot is not None:
            ndx = plot.map_index((event.x, event.y))

            self.x, self.y = ndx
            print(f"Left: {self.x}, {self.y}")
            self.left_changed = 1 - self.left_changed
            self.last_mouse_position = (event.x, event.y)

    def normal_right_down(self, event):
        plot = self.component
        if plot is not None:
            ndx = plot.map_index((event.x, event.y))

            self.x, self.y = ndx

            self.right_changed = 1 - self.right_changed
            print(f"Right: {self.x}, {self.y}")

            self.last_mouse_position = (event.x, event.y)

    def normal_mouse_move(self, event):
        pass

    def __init__(self, *args, **kwargs):
        super(ClickerTool, self).__init__(*args, **kwargs)


# ----------------------------------------------------------


class PlotWindow(HasTraits):
    _plot = Instance(Plot)
    plot_data = Instance(ArrayPlotData)
    polygon_plot = Instance(PolygonPlot)

    _click_tool = Instance(ClickerTool)
    _right_click_avail = 0
    name = Str
    view = View(
        Item(name="_plot", editor=ComponentEditor(), show_label=False),
    )

    def __init__(self):
        super().__init__()
        padd = 25
        self.plot_data = ArrayPlotData(px=np.array([]), py=np.array([]))
        self._x, self._y = [], []
        self.man_ori = range(50)
        self._plot = Plot(self.plot_data, default_origin="top left")

        self._plot.padding = (padd, padd, padd, padd)
        self.face_alpha = 0.5
        self.edge_alpha = 0.5
        self.edge_style = "solid"

    def left_clicked_event(self):
        """left click event"""
        print("left clicked")
        self._x.append(self._click_tool.x)
        self._y.append(self._click_tool.y)
        print(self._x, self._y)

        self.drawcross("coord_x", "coord_y", self._x, self._y, "red", 5)

        if self._plot.overlays is not None:
            self._plot.overlays.clear()

        self.plot_num_overlay(self._x, self._y, self.man_ori)

    def right_clicked_event(self):
        """right click event"""
        print("right clicked")
        if len(self._x) > 0:
            self._x.pop()
            self._y.pop()
            print(self._x, self._y)

            self.drawcross("coord_x", "coord_y", self._x, self._y, "red", 5)
            if self._plot.overlays is not None:
                self._plot.overlays.clear()
            self.plot_num_overlay(self._x, self._y, self.man_ori)
        # else:
        #     if self._right_click_avail:
        #         print("deleting point")
        #         self.py_rclick_delete(
        #             self._click_tool.x, self._click_tool.y, self.cameraN
        #         )
        #         x = []
        #         y = []
        #         self.py_get_pix_N(x, y, self.cameraN)
        #         self.drawcross("x", "y", x[0], y[0], "blue", 4)

    def attach_tools(self):
        """Attaches the necessary tools to the plot"""
        self._click_tool = ClickerTool(self._img_plot)
        self._click_tool.on_trait_change(self.left_clicked_event, "left_changed")
        self._click_tool.on_trait_change(self.right_clicked_event, "right_changed")
        self._img_plot.tools.append(self._click_tool)
        self._zoom_tool = SimpleZoom(
            component=self._plot, tool_mode="box", always_on=False
        )
        self._zoom_tool.max_zoom_out_factor = 1.0
        self._img_plot.tools.append(self._zoom_tool)
        if self._plot.index_mapper is not None:
            self._plot.index_mapper.on_trait_change(
                self.handle_mapper, "updated", remove=False
            )
        if self._plot.value_mapper is not None:
            self._plot.value_mapper.on_trait_change(
                self.handle_mapper, "updated", remove=False
            )

    def drawcross(self, str_x, str_y, x, y, color1="blue", mrk_size=1, marker="plus"):
        """
        Draws crosses on images
        """
        self.plot_data.set_data(str_x, x)
        self.plot_data.set_data(str_y, y)
        self._plot.plot(
            (str_x, str_y),
            type="scatter",
            color=color1,
            marker=marker,
            marker_size=mrk_size,
        )
        self._plot.request_redraw()

    def drawline(self, str_x, str_y, x1, y1, x2, y2, color1):
        self.plot_data.set_data(str_x, [x1, x2])
        self.plot_data.set_data(str_y, [y1, y2])
        self._plot.plot((str_x, str_y), type="line", color=color1)
        self._plot.request_redraw()

    def drawquiver(self, x1c, y1c, x2c, y2c, color, linewidth=1.0, scale=1.0):
        x1, y1, x2, y2 = self.remove_short_lines(x1c, y1c, x2c, y2c, min_length=0)
        if len(x1) > 0:
            vectors = np.array(
                (
                    (np.array(x2) - np.array(x1)) / scale,
                    (np.array(y2) - np.array(y1)) / scale,
                )
            ).T
            self.plot_data.set_data("index", x1)
            self.plot_data.set_data("value", y1)
            self.plot_data.set_data("vectors", vectors)
            self._plot.quiverplot(
                ("index", "value", "vectors"), arrow_size=0, line_color="red"
            )

    def remove_short_lines(self, x1, y1, x2, y2, min_length=2):
        x1f, y1f, x2f, y2f = [], [], [], []
        for i in range(len(x1)):
            if abs(x1[i] - x2[i]) > min_length or abs(y1[i] - y2[i]) > min_length:
                x1f.append(x1[i])
                y1f.append(y1[i])
                x2f.append(x2[i])
                y2f.append(y2[i])
        return x1f, y1f, x2f, y2f

    def handle_mapper(self):
        for i in range(0, len(self._plot.overlays)):
            if hasattr(self._plot.overlays[i], "real_position"):
                coord_x1, coord_y1 = self._plot.map_screen(
                    [self._plot.overlays[i].real_position]
                )[0]
                self._plot.overlays[i].alternate_position = (
                    coord_x1,
                    coord_y1,
                )

    def plot_num_overlay(self, x, y, txt, text_color="white", border_color="red"):
        for i in range(len(x)):
            coord_x, coord_y = self._plot.map_screen([(x[i], y[i])])[0]
            ovlay = TextBoxOverlay(
                component=self._plot,
                text=str(txt[i]),
                alternate_position=(coord_x, coord_y),
                real_position=(x[i], y[i]),
                text_color=text_color,
                border_color=border_color,
            )
            self._plot.overlays.append(ovlay)

    def update_image(self, image, is_float=False):
        if is_float:
            self.plot_data.set_data("imagedata", image.astype(float))
        else:
            self.plot_data.set_data("imagedata", image.astype(np.uint8))

        self._img_plt = self._plot.img_plot("imagedata", colormap=gray)[0]
        self._plot.request_redraw()


class MaskGUI(HasTraits):
    status_text = Str("")
    ori_cam_name = []
    ori_cam = []
    pass_init = Bool(False)
    pass_sortgrid = Bool(False)
    pass_raw_orient = Bool(False)
    pass_init_disabled = Bool(False)
    button_showimg = Button()
    button_detection = Button()
    button_manual = Button()

    def __init__(self, experiment: Experiment):
        super(MaskGUI, self).__init__()
        self.need_reset = 0
        self.experiment = experiment
        self.active_path = Path(experiment.active_params.yaml_path).parent
        self.working_folder = self.active_path.parent
        
        os.chdir(self.working_folder)
        print(f"Inside a folder: {Path.cwd()}")

        ptv_params = experiment.get_parameter('ptv')
        if ptv_params is None:
            raise ValueError("Failed to load PTV parameters")
        self.num_cams = experiment.get_n_cam()
        self.camera = [PlotWindow() for i in range(self.num_cams)]
        for i in range(self.num_cams):
            self.camera[i].name = "Camera" + str(i + 1)
            self.camera[i].cameraN = i
            # self.camera[i].py_rclick_delete = ptv.py_rclick_delete
            # self.camera[i].py_get_pix_N = ptv.py_get_pix_N

    view = View(
        HGroup(
            VGroup(
                Item(
                    name="button_showimg",
                    label="Load images/parameters",
                    show_label=False,
                ),
                Item(
                    name="button_manual",
                    label="Draw and store mask",
                    show_label=False,
                    enabled_when="pass_init",
                ),
            ),
            Item(
                "camera",
                style="custom",
                editor=ListEditor(
                    use_notebook=True,
                    deletable=False,
                    dock_style="tab",
                    page_name=".name",
                ),
                show_label=False,
            ),
            orientation="horizontal",
        ),
        title="Mask",
        id="view1",
        width=1.0,
        height=1.0,
        resizable=True,
        statusbar="status_text",
    )

    def _button_showimg_fired(self):
        print("Loading images \n")
        ptv_params = self.experiment.get_parameter('ptv')
        (
            self.cpar,
            self.spar,
            self.vpar,
            self.track_par,
            self.tpar,
            self.cals,
            self.epar,
        ) = ptv.py_start_proc_c(self.experiment.pm)

        self.images = []
        for i in range(len(self.camera)):
            ptv_params = self.experiment.get_parameter('ptv')
            imname = ptv_params['img_name'][i] if ptv_params else ""
            im = imread(imname)
            if im.ndim > 2:
                im = rgb2gray(im[:, :, :3])

            self.images.append(img_as_ubyte(im))

        self.reset_show_images()
        self.pass_init = True
        self.status_text = "Initialization finished."

    def _button_manual_fired(self):
        self.mask_files = [f"mask_{cam}.txt" for cam in range(self.num_cams)]
        print(self.mask_files)

        print("Start mask drawing click in some order in each camera")

        points_set = True
        for i in range(self.num_cams):
            if len(self.camera[i]._x) < 4:
                print(f"Camera {i} less than 4 points: {self.camera[i]._x}")
                points_set = False
            else:
                print(
                    f"Camera {i} has {len(self.camera[i]._x)} points: {self.camera[i]._x}"
                )
                self.camera[i].plot_data.set_data("px", np.array(self.camera[i]._x))
                self.camera[i].plot_data.set_data("py", np.array(self.camera[i]._y))
                self.camera[i]._plot.plot(
                    ("px", "py"),
                    type="polygon",
                    face_color=(0, 0.8, 1),
                    edge_color=(0, 0, 0),
                    edge_style="solid",
                    alpha=0.5,
                )

        if points_set:
            for cam in range(self.num_cams):
                with open(self.mask_files[cam], "w", encoding="utf-8") as f:
                    for x, y in zip(self.camera[cam]._x, self.camera[cam]._y):
                        f.write("%f %f\n" % (x, y))

                self.status_text = f"{self.mask_files[cam]} saved."

        else:
            self.status_text = (
                "Use left button to draw points on each image, avoid crossing lines"
            )

    def reset_plots(self):
        for i in range(self.num_cams):
            self.camera[i]._plot.delplot(*self.camera[i]._plot.plots.keys()[0:])
            self.camera[i]._plot.overlays.clear()

    def reset_show_images(self):
        for i, cam in enumerate(self.camera):
            cam._plot.delplot(*list(cam._plot.plots.keys())[0:])
            cam._plot.overlays = []
            cam.plot_data.set_data("imagedata", self.images[i].astype(np.uint8))

            cam._img_plot = cam._plot.img_plot("imagedata", colormap=gray)[0]
            cam._x = []
            cam._y = []
            cam._img_plot.tools = []

            cam.attach_tools()
            cam._plot.request_redraw()

    def drawcross(self, str_x, str_y, x, y, color1, size1, i_cam=None):
        if i_cam is None:
            for i in range(self.num_cams):
                self.camera[i].drawcross(str_x, str_y, x[i], y[i], color1, size1)
        else:
            self.camera[i_cam].drawcross(str_x, str_y, x, y, color1, size1)


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1:
        active_path = Path("../test_cavity/parametersRun3")
    else:
        active_path = Path(sys.argv[0])

    mask_gui = MaskGUI(active_path)
    mask_gui.configure_traits()