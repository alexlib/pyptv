"""
Copyright (c) 2008-2013, Tel Aviv University
Copyright (c) 2013 - the OpenPTV team
The GUI software is distributed under the terms of MIT-like license
http://opensource.org/licenses/MIT
"""

import os
import sys
import pathlib
import numpy as np

from traits.api import HasTraits, Str, Int, Bool, Instance, Button, Range
from traitsui.api import View, Item, HGroup, VGroup, ListEditor
from enable.component_editor import ComponentEditor
from chaco.api import (
    Plot,
    ArrayPlotData,
    gray,
    ImagePlot,
    ArrayDataSource,
    LinearMapper,
)

from chaco.tools.image_inspector_tool import ImageInspectorTool
from chaco.tools.better_zoom import BetterZoom as SimpleZoom

from skimage.io import imread
from skimage.util import img_as_ubyte
from skimage.color import rgb2gray

from optv.segmentation import target_recognition
from pyptv import ptv
from pyptv.experiment import Experiment
from pyptv.text_box_overlay import TextBoxOverlay
from pyptv.quiverplot import QuiverPlot


# -------------------------------------------
class ClickerTool(ImageInspectorTool):
    left_changed = Int(1)
    right_changed = Int(1)
    x = 0
    y = 0

    def __init__(self, *args, **kwargs):
        super(ClickerTool, self).__init__(*args, **kwargs)

    def normal_left_down(self, event):
        """Handles the left mouse button being clicked.
        Fires the **new_value** event with the data (if any) from the event's
        position.
        """
        plot = self.component
        if plot is not None:
            ndx = plot.map_index((event.x, event.y))

            x_index, y_index = ndx
            self.x = x_index
            self.y = y_index
            print(self.x)
            print(self.y)
            self.left_changed = 1 - self.left_changed
            self.last_mouse_position = (event.x, event.y)

    def normal_right_down(self, event):
        plot = self.component
        if plot is not None:
            ndx = plot.map_index((event.x, event.y))

            x_index, y_index = ndx
            self.x = x_index
            self.y = y_index

            self.right_changed = 1 - self.right_changed
            print(self.x)
            print(self.y)

            self.last_mouse_position = (event.x, event.y)

    def normal_mouse_move(self, event):
        pass


# ----------------------------------------------------------


class PlotWindow(HasTraits):
    """Plot window traits component"""

    _plot_data = Instance(ArrayPlotData)
    _plot = Instance(Plot)
    _click_tool = Instance(ClickerTool)
    _img_plot = Instance(ImagePlot)
    _right_click_avail = 0
    name = Str
    view = View(
        Item(name="_plot", editor=ComponentEditor(), show_label=False),
    )

    def __init__(self):
        super(HasTraits, self).__init__()
        padd = 25
        self._plot_data = ArrayPlotData()
        self._x = []
        self._y = []
        self.man_ori = [1, 2, 3, 4]
        self._plot = Plot(self._plot_data, default_origin="top left")
        self._plot.padding_left = padd
        self._plot.padding_right = padd
        self._plot.padding_top = padd
        self._plot.padding_bottom = padd
        self._quiverplots = []
        self.py_rclick_delete = ptv.py_rclick_delete
        self.py_get_pix_N = ptv.py_get_pix_N

    def left_clicked_event(self):
        """
        Adds x,y position to a list and draws a cross

        """
        self._x.append(self._click_tool.x)
        self._y.append(self._click_tool.y)
        print(self._x, self._y)

        self.drawcross("coord_x", "coord_y", self._x, self._y, "red", 5)
        self._plot.overlays = []
        self.plot_num_overlay(self._x, self._y, self.man_ori)

    def right_clicked_event(self):
        print("right clicked")
        if len(self._x) > 0:
            self._x.pop()
            self._y.pop()
            print(self._x, self._y)

            self.drawcross("coord_x", "coord_y", self._x, self._y, "red", 5)
            self._plot.overlays = []
            self.plot_num_overlay(self._x, self._y, self.man_ori)
        else:
            if self._right_click_avail:
                print("deleting point")
                self.py_rclick_delete(
                    self._click_tool.x, self._click_tool.y, self.cameraN
                )
                x = []
                y = []
                self.py_get_pix_N(x, y, self.cameraN)
                self.drawcross("x", "y", x[0], y[0], "blue", 4)

    def attach_tools(self):
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

    def drawcross(self, str_x, str_y, x, y, color1, mrk_size, marker="plus"):
        """
        Draws crosses on images
        """
        self._plot_data.set_data(str_x, x)
        self._plot_data.set_data(str_y, y)
        self._plot.plot(
            (str_x, str_y),
            type="scatter",
            color=color1,
            marker=marker,
            marker_size=mrk_size,
        )
        self._plot.request_redraw()

    def drawline(self, str_x, str_y, x1, y1, x2, y2, color1):
        self._plot_data.set_data(str_x, [x1, x2])
        self._plot_data.set_data(str_y, [y1, y2])
        self._plot.plot((str_x, str_y), type="line", color=color1)
        self._plot.request_redraw()

    def drawquiver(self, x1c, y1c, x2c, y2c, color, linewidth=1.0, scale=1.0):
        x1, y1, x2, y2 = self.remove_short_lines(x1c, y1c, x2c, y2c, min_length=0)
        if len(x1) > 0:
            xs = ArrayDataSource(x1)
            ys = ArrayDataSource(y1)

            quiverplot = QuiverPlot(
                index=xs,
                value=ys,
                index_mapper=LinearMapper(range=self._plot.index_mapper.range),
                value_mapper=LinearMapper(range=self._plot.value_mapper.range),
                origin=self._plot.origin,
                arrow_size=0,
                line_color=color,
                line_width=linewidth,
                ep_index=np.array(x2) * scale,
                ep_value=np.array(y2) * scale,
            )
            self._plot.add(quiverplot)
            self._quiverplots.append(quiverplot)

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
                self._plot.overlays[i].alternate_position = (coord_x1, coord_y1)

    def plot_num_overlay(self, x, y, txt, text_color="white", border_color="red"):
        for i in range(0, len(x)):
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
            self._plot_data.set_data("imagedata", image.astype(np.float))
        else:
            self._plot_data.set_data("imagedata", image.astype(np.byte))

        self._plot.request_redraw()


class DetectionGUI(HasTraits):
    """detection GUI"""

    status_text = Str(" status ")
    size_of_crosses = Int(4, label="Size of crosses")
    button_showimg = Button(label="Load image")
    hp_flag = Bool(False, label="highpass")
    inverse_flag = Bool(False, label="inverse")
    button_detection = Button(label="Detect dots")
    image_name = Str("cal/cam1.tif", label="Image file name")

    def __init__(self, experiment: Experiment):
        super(DetectionGUI, self).__init__()
        self.need_reset = 0

        self.experiment = experiment
        self.working_folder = pathlib.Path(experiment.active_params.yaml_path).parent
        os.chdir(self.working_folder)
        print(f"Inside a folder: {pathlib.Path()}")
        
        ptv_params = experiment.get_parameter('ptv')
        if ptv_params is None:
            raise ValueError("Failed to load PTV parameters")
        self.n_cams = experiment.get_n_cam()

        (
            self.cpar,
            self.spar,
            self.vpar,
            self.track_par,
            self.tpar,
            self.cals,
            self.epar,
        ) = ptv.py_start_proc_c(experiment.parameter_manager)

        self.tpar.read("parameters/detect_plate.par")

        self.thresholds = self.tpar.get_grey_thresholds()
        self.pixel_count_bounds = list(self.tpar.get_pixel_count_bounds())
        self.xsize_bounds = list(self.tpar.get_xsize_bounds())
        self.ysize_bounds = list(self.tpar.get_ysize_bounds())
        self.sum_grey = self.tpar.get_min_sum_grey()
        self.disco = self.tpar.get_max_discontinuity()

        self.add_trait("grey_thresh", Range(1, 255, self.thresholds[0], mode="slider"))
        self.add_trait(
            "min_npix",
            Range(
                0,
                self.pixel_count_bounds[0] + 50,
                self.pixel_count_bounds[0],
                method="slider",
                label="min npix",
            ),
        )
        self.add_trait(
            "min_npix_x",
            Range(
                1,
                self.xsize_bounds[0] + 20,
                self.xsize_bounds[0],
                mode="slider",
                label="min npix in x",
            ),
        )
        self.add_trait(
            "min_npix_y",
            Range(
                1,
                self.ysize_bounds[0] + 20,
                self.ysize_bounds[0],
                mode="slider",
                label="min npix in y",
            ),
        )
        self.add_trait(
            "max_npix",
            Range(
                1,
                self.pixel_count_bounds[1] + 100,
                self.pixel_count_bounds[1],
                mode="slider",
                label="max npix",
            ),
        )
        self.add_trait(
            "max_npix_x",
            Range(
                1,
                self.xsize_bounds[1] + 50,
                self.xsize_bounds[1],
                mode="slider",
                label="max npix in x",
            ),
        )
        self.add_trait(
            "max_npix_y",
            Range(
                1,
                self.ysize_bounds[1] + 50,
                self.ysize_bounds[1],
                mode="slider",
                label="max npix in y",
            ),
        )
        self.add_trait(
            "disco",
            Range(
                0,
                255,
                self.disco,
                mode="slider",
                label="Discontinuity",
            ),
        )        
        self.add_trait(
            "sum_of_grey",
            Range(
                self.sum_grey / 2,
                self.sum_grey * 2,
                self.sum_grey,
                mode="slider",
                label="Sum of greyvalue",
            ),
        )

        self.camera = [PlotWindow()]

    view = View(
        HGroup(
            VGroup(
                VGroup(
                    Item(name="image_name", width=150),
                    Item(name="button_showimg"),
                    Item(name="hp_flag"),
                    Item(name="inverse_flag"),
                    Item(name="button_detection"),
                    Item(name="grey_thresh"),
                    Item(name="min_npix"),
                    Item(name="min_npix_x"),
                    Item(name="min_npix_y"),
                    Item(name="max_npix"),
                    Item(name="max_npix_x"),
                    Item(name="max_npix_y"),
                    Item(name="disco"),
                    Item(name="sum_of_grey"),
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
        title="Detection",
        id="view1",
        width=1.0,
        height=1.0,
        resizable=True,
        statusbar="status_text",
    )

    def _inverse_flag_changed(self):
        self._read_cal_image()
        self.status_text = "Negative image"
        self.reset_show_images()

    def _hp_flag_changed(self):
        self._read_cal_image()
        self.status_text = "Highpassed image"
        self.reset_show_images()

    def _grey_thresh_changed(self):
        self.thresholds[0] = self.grey_thresh
        self.tpar.set_grey_thresholds(self.thresholds)
        self._button_detection_fired()

    def _min_npix_changed(self):
        self.pixel_count_bounds[0] = self.min_npix
        self.tpar.set_pixel_count_bounds(self.pixel_count_bounds)
        self._button_detection_fired()

    def _max_npix_changed(self):
        self.pixel_count_bounds[1] = self.max_npix
        self.tpar.set_pixel_count_bounds(self.pixel_count_bounds)
        self._button_detection_fired()

    def _min_npix_x_changed(self):
        self.xsize_bounds[0] = self.min_npix_x
        self.tpar.set_xsize_bounds(self.xsize_bounds)
        self._button_detection_fired()

    def _max_npix_x_changed(self):
        self.xsize_bounds[1] = self.max_npix_x
        self.tpar.set_xsize_bounds(self.xsize_bounds)
        self._button_detection_fired()

    def _min_npix_y_changed(self):
        self.ysize_bounds[0] = self.min_npix_y
        self.tpar.set_ysize_bounds(self.ysize_bounds)

    def _max_npix_y_changed(self):
        self.ysize_bounds[1] = self.max_npix_y
        self.tpar.set_ysize_bounds(self.ysize_bounds)
        self._button_detection_fired()

    def _sum_of_grey_changed(self):
        self.tpar.set_min_sum_grey(self.sum_of_grey)
        self._button_detection_fired()

    def _disco_changed(self):
        self.tpar.set_max_discontinuity(self.disco)
        self._button_detection_fired()

    def _button_showimg_fired(self):
        self._read_cal_image()
        self.reset_show_images()

    def _read_cal_image(self):
        im = imread(self.image_name)
        if im.ndim > 2:
            im = rgb2gray(im)

        if self.inverse_flag is True:
            im = 255 - im

        if self.hp_flag is True:
            tmp = [img_as_ubyte(im)]
            tmp = ptv.py_pre_processing_c(tmp, self.cpar)
            im = tmp[0]
        else:
            im = img_as_ubyte(im)

        self.cal_image = im.copy()

    def _button_detection_fired(self):
        self.status_text = " Detection procedure "
        targs = target_recognition(self.cal_image, self.tpar, 0, self.cpar)
        targs.sort_y()

        x = [i.pos()[0] for i in targs]
        y = [i.pos()[1] for i in targs]

        self.camera[0].drawcross("x", "y", np.array(x), np.array(y), "orange", 8)
        self.camera[0]._right_click_avail = 1

    def reset_plots(self):
        """Resets all the images and overlays"""
        self.camera[0]._plot.delplot(*self.camera[0]._plot.plots.keys())
        self.camera[0]._plot.overlays = []
        for j in range(len(self.camera[0]._quiverplots)):
            self.camera[0]._plot.remove(self.camera[0]._quiverplots[j])
        self.camera[0]._quiverplots = []

    def reset_show_images(self):
        self.reset_plots()
        self.camera[0]._plot_data.set_data("imagedata", self.cal_image)
        self.camera[0]._img_plot = self.camera[0]._plot.img_plot(
            "imagedata", colormap=gray
        )[0]
        self.camera[0]._x = []
        self.camera[0]._y = []
        self.camera[0]._img_plot.tools = []
        self.camera[0].attach_tools()
        self.camera[0]._plot.request_redraw()


if __name__ == "__main__":
    if len(sys.argv) == 1:
        par_path = pathlib.Path().absolute() / "tests" / "test_cavity" / "parameters"
    else:
        par_path = pathlib.Path(sys.argv[1]) / "parameters"

    experiment = Experiment()
    experiment.populate_runs(par_path)

    detection_gui = DetectionGUI(experiment)
    detection_gui.configure_traits()