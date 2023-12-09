"""
Copyright (c) 2008-2013, Tel Aviv University
Copyright (c) 2013 - the OpenPTV team
The software is distributed under the terms of MIT-like license
http://opensource.org/licenses/MIT
"""

import os
import shutil
import re
from pathlib import Path
import numpy as np
from skimage.io import imread
from skimage.util import img_as_ubyte
from skimage import color

from traits.api import HasTraits, Str, Bool, Instance, Button
from traitsui.api import View, Item, HGroup, VGroup, ListEditor

from enable.api import ComponentEditor

from chaco.api import (
    Plot,
    ArrayPlotData,
    gray,
)

# from traitsui.menu import MenuBar, ToolBar, Menu, Action
from chaco.tools.image_inspector_tool import ImageInspectorTool
from chaco.tools.better_zoom import BetterZoom as SimpleZoom

# from chaco.tools.simple_zoom import SimpleZoom
from pyptv.text_box_overlay import TextBoxOverlay
from pyptv.code_editor import codeEditor


# first replacement
# from optv.imgcoord import image_coordinates
from openptv_python.imgcoord import image_coordinates
# Control parameters
from openptv_python.parameters import (
    ControlPar,
    TargetPar,
    OrientPar,
    VolumePar, 
    CalibrationPar,
    ExaminePar,
    MultiPlanesPar,
    TrackPar,
    read_control_par,
)
from openptv_python.sortgrid import sortgrid
from openptv_python.orientation import raw_orient, full_calibration
from openptv_python.tracking_frame_buf import Target
from openptv_python.calibration import Calibration
from openptv_python.image_processing import prepare_image
from openptv_python.segmentation import target_recognition
from openptv_python.trafo import arr_metric_to_pixel


# from pyptv import ptv, parameter_gui, parameters as par
from pyptv import parameters as par
from pyptv import parameter_gui



# -------------------------------------------
class ClickerTool(ImageInspectorTool):
    left_changed = Bool(True)
    right_changed = Bool(True)
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

            x_index, y_index = ndx
            # image_data = plot.value
            self.x = x_index
            self.y = y_index
            print(self.x)
            print(self.y)
            self.left_changed = not self.left_changed
            self.last_mouse_position = (event.x, event.y)

    def normal_right_down(self, event):
        """ Handles the right mouse button being clicked."""
        plot = self.component
        if plot is not None:
            ndx = plot.map_index((event.x, event.y))

            x_index, y_index = ndx
            # image_data = plot.value
            self.x = x_index
            self.y = y_index

            self.right_changed = not self.right_changed
            print(self.x)
            print(self.y)

            self.last_mouse_position = (event.x, event.y)

    def normal_mouse_move(self, event):
        pass

    def __init__(self, *args, **kwargs):
        super(ClickerTool, self).__init__(*args, **kwargs)


# ----------------------------------------------------------


class PlotWindow(HasTraits):
    """ PlotWindow class """
    plot_window = Instance(Plot)
    # plot_window = Instance(Component)
    _click_tool = Instance(ClickerTool)
    _right_click_avail = 0
    _name = f"Cam {1}"
    view = View(
        Item(name="plot_window", editor=ComponentEditor(), show_label=False),
    )

    def __init__(self):
        # super(HasTraits, self).__init__()
        super().__init__()
        # -------------- Initialization of plot system ----------------
        padd = 25
        self.plot_data = ArrayPlotData()
        self._x, self._y = [], []
        self.man_ori = [1, 2, 3, 4]
        self.plot_window = Plot(self.plot_data, default_origin="top left")

        self.plot_window.padding_top = padd
        self.plot_window.padding_left = padd
        self.plot_window.padding_bottom = padd
        self.plot_window.padding_right = padd

        self.plot_window.overlays.clear()  # type: ignore

        self._zoom_tool = SimpleZoom(
            component=self.plot_window, tool_mode="box", always_on=False
        )
        # self._quiverplots = []

        # -------------------------------------------------------------

    def left_clicked_event(self):
        """ left click event """
        print("left clicked")
        if len(self._x) < 4:
            self._x.append(self._click_tool.x)
            self._y.append(self._click_tool.y)
        print(self._x, self._y)

        self.drawcross("coord_x", "coord_y", self._x, self._y, "red", 5)

        if self.plot_window.overlays is not None:
            self.plot_window.overlays.clear()  # type: ignore
        self.plot_num_overlay(self._x, self._y, self.man_ori)

    def right_clicked_event(self):
        """ right click event """
        print("right clicked")
        if len(self._x) > 0:
            self._x.pop()
            self._y.pop()
            print(self._x, self._y)

            self.drawcross("coord_x", "coord_y", self._x, self._y, "red", 5)
            if self.plot_window.overlays is not None:
                self.plot_window.overlays.clear()  # type: ignore
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
        """ Attaches the necessary tools to the plot """
        self._click_tool = ClickerTool(self._img_plot)
        self._click_tool.on_trait_change(
            self.left_clicked_event, "left_changed"
        )
        self._click_tool.on_trait_change(
            self.right_clicked_event, "right_changed"
        )
        self._img_plot.tools.append(self._click_tool)
        self._zoom_tool = SimpleZoom(
            component=self.plot_window, tool_mode="box", always_on=False
        )
        self._zoom_tool.max_zoom_out_factor = 1.0
        self._img_plot.tools.append(self._zoom_tool)
        if self.plot_window.index_mapper is not None:
            self.plot_window.index_mapper.on_trait_change(
                self.handle_mapper, "updated", remove=False
            )
        if self.plot_window.value_mapper is not None:
            self.plot_window.value_mapper.on_trait_change(
                self.handle_mapper, "updated", remove=False
            )

    def drawcross(self, str_x, str_y, x, y, color1="blue", mrk_size=1, marker="plus"):
        """
        Draws crosses on images
        """
        self.plot_data.set_data(str_x, x)
        self.plot_data.set_data(str_y, y)
        self.plot_window.plot(
            (str_x, str_y),
            type="scatter",
            color=color1,
            marker=marker,
            marker_size=mrk_size,
        )
        self.plot_window.request_redraw()

    def drawline(self, str_x, str_y, x1, y1, x2, y2, color1):
        """ drawline draws multiple lines at once on the screen x1,y1->x2,y2 in the current camera window """
        self.plot_data.set_data(str_x, [x1, x2])
        self.plot_data.set_data(str_y, [y1, y2])
        self.plot_window.plot((str_x, str_y), type="line", color=color1)
        self.plot_window.request_redraw()

    def drawquiver(self, x1c, y1c, x2c, y2c, color='red', linewidth=1.0, scale=1.0):
        """drawquiver draws multiple lines at once on the screen x1,y1->x2,y2 in the current camera window
        parameters:
            x1c - array of x1 coordinates
            y1c - array of y1 coordinates
            x2c - array of x2 coordinates
            y2c - array of y2 coordinates
            color - color of the line
            linewidth - linewidth of the line
        example usage:
            drawquiver ([100,200],[100,100],[400,400],[300,200],'red',linewidth=2.0)
            draws 2 red lines with thickness = 2 :  100,100->400,300 and 200,100->400,200

        """
        x1, y1, x2, y2 = self.remove_short_lines(
            x1c, y1c, x2c, y2c, min_length=0
        )
        if len(x1) > 0:
            #     xs = ArrayDataSource(np.array(x1))
            #     ys = ArrayDataSource(np.array(y1))

            # quiverplot = QuiverPlot(
            #     index=xs,
            #     value=ys,
            #     index_mapper=LinearMapper(range=self.plot_window.index_mapper.range),
            #     value_mapper=LinearMapper(range=self.plot_window.value_mapper.range),
            #     origin=self.plot_window.origin,
            #     arrow_size=0,
            #     line_color=color,
            #     line_width=linewidth,
            #     ep_index=np.array(x2) * scale,
            #     ep_value=np.array(y2) * scale,
            # )
            vectors = np.array(((np.array(x2)-np.array(x1))/scale,
                                (np.array(y2)-np.array(y1))/scale)).T
            self.plot_data.set_data("index", x1)
            self.plot_data.set_data("value", y1)
            self.plot_data.set_data("vectors", vectors)
            # self._quiverplots.append(quiverplot)
            self.plot_window.quiverplot(
                ('index', 'value', 'vectors'),
                arrow_size=0,
                line_color=color,
                linewidth=linewidth,
            )
            # self.plot_window.overlays.append(quiverplot)

    def remove_short_lines(self, x1: list[int], y1: list[int], x2: list[int], y2: list[int], min_length=2):
        """removes short lines from the array of lines
        parameters:
            x1,y1,x2,y2 - start and end coordinates of the lines
        returns:
            x1f,y1f,x2f,y2f - start and end coordinates of the lines, with short lines removed
        example usage:
            x1,y1,x2,y2=remove_short_lines([100,200,300],[100,200,300],[100,200,300],[102,210,320])
            3 input lines, 1 short line will be removed (100,100->100,102)
            returned coordinates:
            x1=[200,300]; y1=[200,300]; x2=[200,300]; y2=[210,320]
        """
        # dx, dy = 2, 2  # minimum allowable dx,dy
        # x1f, y1f, x2f, y2f = [], [], [], []
        # for i in range(len(x1)):
        #     if (
        #         abs(x1[i] - x2[i]) > min_length
        #         or abs(y1[i] - y2[i]) > min_length
        #     ):
        #         x1f.append(x1[i])
        #         y1f.append(y1[i])
        #         x2f.append(x2[i])
        #         y2f.append(y2[i])
        x1f, y1f, x2f, y2f = zip(*[(x1i, y1i, x2i, y2i) for x1i, y1i, x2i, y2i in zip(
            x1, y1, x2, y2) if abs(x1i - x2i) > min_length or abs(y1i - y2i) > min_length])

        return x1f, y1f, x2f, y2f

    def handle_mapper(self):
        """ Handles the mapper being updated. """
        for plot_overlay in self.plot_window.overlays:  # type: ignore
            if hasattr(plot_overlay, "real_position"):
                coord_x1, coord_y1 = self.plot_window.map_screen(
                    [plot_overlay.real_position]
                )[0]
                plot_overlay.alternate_position = (
                    coord_x1,
                    coord_y1,
                )

    def plot_num_overlay(self, x, y, txt):
        for i in range(len(x)):
            coord_x, coord_y = self.plot_window.map_screen([(x[i], y[i])])[0]
            ovlay = TextBoxOverlay(
                component=self.plot_window,
                text=str(txt[i]),
                alternate_position=(coord_x, coord_y),
                real_position=(x[i], y[i]),
                text_color="white",
                border_color="red",
            )
            self.plot_window.overlays.append(ovlay) # type: ignore

    def update_image(self, image, is_float):
        if is_float:
            self.plot_data.set_data("imagedata", image.astype(float))
        else:
            self.plot_data.set_data("imagedata", image.astype(np.uint8))

        # Alex added to plot the image here from update image
        self._img_plt = self.plot_window.imgplot_window("imagedata", colormap=gray)[0]

        self.plot_window.request_redraw()


# ---------------------------------------------------------


class CalibrationGUI(HasTraits):
    
    status_text = Str("")
    ori_img_name = []
    ori_img = []
    pass_init = Bool(False)
    pass_sortgrid = Bool(False)
    pass_raw_orient = Bool(False)
    pass_init_disabled = Bool(False)
    # -------------------------------------------------------------
    button_edit_cal_parameters = Button()
    button_showimg = Button()
    button_detection = Button()
    button_manual = Button()
    button_file_orient = Button()
    button_init_guess = Button()
    button_sort_grid = Button()
    button_sort_grid_init = Button()
    button_raw_orient = Button()
    button_fine_orient = Button()
    button_orient_part = Button()
    button_orient_shaking = Button()
    button_orient_dumbbell = Button()
    button_restore_orient = Button()
    button_checkpoint = Button()
    button_ap_figures = Button()
    button_edit_ori_files = Button()
    button_test = Button()

    active_path: Path = Path()
    cpar: ControlPar = ControlPar()
    spar: OrientPar = OrientPar()
    vpar: VolumePar = VolumePar()
    track_par: TrackPar = TrackPar()
    tpar: TargetPar = TargetPar()
    cals: list[Calibration] = []
    epar: ExaminePar = ExaminePar()
    MultiParams: MultiPlanesPar = MultiPlanesPar()
    
    cal_points = np.empty(0, dtype=[("id", int), ("pos", float, 3)])
    cal_images = []
    detections = []
    camera = []
    
    # ---------------------------------------------------
    # Constructor
    # ---------------------------------------------------

    def __init__(self, active_path: Path):
        """Initialize CalibrationGUI

        Inputs:
            active_path is the path to the folder of prameters
            active_path is a subfolder of a working folder with a
            structure of /parameters, /res, /cal, /img and so on
        """

        super(CalibrationGUI, self).__init__()
        self.need_reset = 0

        self.active_path = active_path  # path to some parameters set in a separate folder
        self.working_folder = self.active_path.parent  # the experimental directory
        # self.par_path = self.working_folder / \
        #     "parameters"  # the default parameters folder
        
        # we shall work inside this folder and save everything locally
        # after we finish the calibration, we have to press start 
        # in the pyptv_gui and then the parameters will be copied
        # to the default parameters folder
        
        self.par_path = self.active_path

        self.man_ori_dat_path = self.working_folder / "man_ori.dat"

        # print(" Copying parameters inside Calibration GUI: \n")
        # par.copy_params_dir(self.active_path, self.par_path)

        os.chdir(self.working_folder)
        print(f"Inside a folder: {Path.cwd()}")

        # read parameters
        with open(self.par_path / "ptv.par", "r", encoding="utf-8") as f:
            self.n_cams = int(f.readline())

        self.camera = [PlotWindow() for i in range(self.n_cams)]
        for i in range(self.n_cams):
            self.camera[i]._name = f"Cam {i+1}"
            self.camera[i].cameraN = i
            # self.camera[i].py_rclick_delete = ptv.py_rclick_delete
            # self.camera[i].py_get_pix_N = ptv.py_get_pix_N

    # Defines GUI view --------------------------

    view = View(
        HGroup(
            VGroup(
                VGroup(
                    Item(
                        name="button_showimg",
                        label="Load/Show Images",
                        show_label=False,
                    ),
                    Item(
                        name="button_detection",
                        label="Detection",
                        show_label=False,
                        enabled_when="pass_init",
                    ),
                    Item(
                        name="button_manual",
                        label="Manual orient.",
                        show_label=False,
                        enabled_when="pass_init",
                    ),
                    Item(
                        name="button_file_orient",
                        label="Orient. with file",
                        show_label=False,
                        enabled_when="pass_init",
                    ),
                    Item(
                        name="button_init_guess",
                        label="Show initial guess",
                        show_label=False,
                        enabled_when="pass_init",
                    ),
                    Item(
                        name="button_sort_grid",
                        label="Sortgrid",
                        show_label=False,
                        enabled_when="pass_init",
                    ),
                    # Item(name='button_sort_grid_init',
                    # label='Sortgrid = initial guess',
                    # show_label=False, enabled_when='pass_init'),
                    Item(
                        name="button_raw_orient",
                        label="Raw orientation",
                        show_label=False,
                        enabled_when="pass_sortgrid",
                    ),
                    Item(
                        name="button_fine_orient",
                        label="Fine tuning",
                        show_label=False,
                        enabled_when="pass_raw_orient",
                    ),
                    Item(
                        name="button_orient_part",
                        label="Orientation with particles",
                        show_label=False,
                        enabled_when="pass_init",
                    ),
                    Item(
                        name="button_orient_dumbbell",
                        label="Orientation from dumbbell",
                        show_label=False,
                        enabled_when="pass_init",
                    ),
                    Item(
                        name="button_restore_orient",
                        label="Restore ori files",
                        show_label=False,
                        enabled_when="pass_init",
                    ),
                    Item(
                        name="button_checkpoint",
                        label="Checkpoints",
                        show_label=False,
                        enabled_when="pass_init_disabled",
                    ),
                    Item(
                        name="button_ap_figures",
                        label="Ap figures",
                        show_label=False,
                        enabled_when="pass_init_disabled",
                    ),
                    show_left=False,
                ),
                VGroup(
                    Item(
                        name="button_edit_cal_parameters",
                        label="Edit calibration parameters",
                        show_label=False,
                    ),
                    Item(
                        name="button_edit_ori_files",
                        label="Edit ori files",
                        show_label=False,
                    ),
                    show_left=False,
                ),
            ),
            Item(
                "camera",
                style="custom",
                editor=ListEditor(
                    use_notebook=True,
                    deletable=False,
                    dock_style="tab",
                    page_name="._name",
                ),
                show_label=False,
            ),
            orientation="horizontal",
        ),
        title="Calibration",
        id="view1",
        width=1.0,
        height=1.0,
        resizable=True,
        statusbar="status_text",
    )

    # --------------------------------------------------

    def _button_edit_cal_parameters_fired(self):
        cp = parameter_gui.Calib_Params(par_path=self.par_path)
        cp.edit_traits(kind="modal")
        # at the end of a modification, copy the parameters

        self.cpar = ControlPar(self.n_cams).from_file(
            os.path.join(self.par_path, "ptv.par"))

        self.cals = []
        for i_cam in range(self.n_cams):
            self.cals.append(Calibration().from_file(
                self.cpar.cal_img_base_name[i_cam] + ".ori",
                self.cpar.cal_img_base_name[i_cam] + ".addpar"
            )
            )

    def _button_showimg_fired(self):

        print("Loading images/parameters \n")

        # Initialize what is needed, copy necessary things

        print("\n Copying man_ori.dat \n")
        if os.path.isfile(os.path.join(self.par_path, "man_ori.dat")):
            shutil.copyfile(
                os.path.join(self.par_path, "man_ori.dat"),
                os.path.join(self.working_folder, "man_ori.dat"),
            )
            print("\n Copied man_ori.dat \n")

        # copy parameters from active to default folder parameters/
        # par.copy_params_dir(self.active_path, self.par_path)

        # read from parameters
        # (
        #     self.cpar,
        #     self.spar,
        #     self.vpar,
        #     self.track_par,
        #     self.tpar,
        #     self.cals,
        #     self.epar,
        # ) = ptv.py_start_proc_c(self.n_cams)

        self.cpar = ControlPar(self.n_cams).from_file(
            os.path.join(self.par_path, "ptv.par"))

        self.n_cams = self.cpar.num_cams

        self.tpar = TargetPar().from_file(os.path.join(self.par_path,"detect_plate.par"))

        print(f" Thresholds are {self.tpar.gvthresh}")

        self.calParams = CalibrationPar().from_file(
            os.path.join(self.par_path, "cal_ori.par"), self.n_cams)

        self.epar = ExaminePar().from_file(os.path.join(self.par_path, "examine.par"))
        print(self.epar.examine_flag, self.epar.combine_flag)

        if self.epar.combine_flag is True:
            print("Combine flag is True \n")
            self.MultiParams = MultiPlanesPar().from_file(os.path.join(self.par_path, "multi_planes.par"))
            print(self.MultiParams.filename)

            self.pass_raw_orient = True
            self.status_text = "Multiplane calibration."

        # read calibration images
        self.cal_images = []
        for i in range(self.n_cams):
            imname = self.calParams.img_name[i]
            im = imread(imname)
            # im = ImageData.fromfile(imname).data
            if im.ndim > 2:
                im = color.rgb2gray(im[:, :, :3])

            self.cal_images.append(img_as_ubyte(im))

        self.cals = []
        for i_cam in range(self.n_cams):
            self.cals.append(Calibration().from_file(
                self.cpar.cal_img_base_name[i_cam] + ".ori",
                self.cpar.cal_img_base_name[i_cam] + ".addpar"
            )
            )

        self.reset_show_images()

        # Loading manual parameters here

        man_ori_par_file = os.path.join(self.par_path, "man_ori.par")
        if not os.path.exists(man_ori_par_file):
            raise FileNotFoundError("Could not load man_ori.par file from parameters")
        
        with open(man_ori_par_file, "r", encoding="utf-8") as f:
            for i in range(self.n_cams):
                self.camera[i].man_ori = [int(f.readline().strip()) for _ in range(4)]

        self.pass_init = True
        self.status_text = "Initialization finished."

    def _button_detection_fired(self):
        if self.need_reset:
            self.reset_show_images()
            self.need_reset = False
        print(" Detection procedure \n")
        self.status_text = "Detection procedure"

        if self.cpar.get_hp_flag():
            for img in self.cal_images:
                img = prepare_image(img, 1, 0)
                
        self.detections = []
        for img in self.cal_images:
            target_array = target_recognition(img, self.tpar, 0, self.cpar)
            target_array.sort(key=lambda t: t.y)
            self.detections.append(target_array)
            
        x = [[_.x for _ in cam] for cam in self.detections]
        y = [[_.y for _ in cam] for cam in self.detections]

        self.drawcross("x", "y", x, y, "blue", 4)

        for i in range(self.n_cams):
            self.camera[i]._right_click_avail = 1

    def _button_manual_fired(self):
        print('Start manual orientation, use clicks and then press this button again')
        points_set = True
        for i in range(self.n_cams):
            if len(self.camera[i]._x) < 4:
                print(f"Camera {i} less than 4 points: {self.camera[i]._x}")
                points_set = False
            else:
                print(f"Camera {i} has 4 points: {self.camera[i]._x}")

        if points_set:
            print(f'Manual orientation file is {self.man_ori_dat_path}')
            with open(self.man_ori_dat_path, "w", encoding="utf-8") as f:
                if f is None:
                    self.status_text = "Error saving man_ori.dat."
                else:
                    for i in range(self.n_cams):
                        for j in range(4):
                            f.write(
                                "%f %f\n"
                                % (self.camera[i]._x[j], self.camera[i]._y[j])
                            )

                    self.status_text = "man_ori.dat saved."
                    # f.close()
        else:
            self.status_text = (
                "Click on 4 points on each calibration image for manual orientation"
            )

    def _button_file_orient_fired(self):
        if self.need_reset:
            self.reset_show_images()
            self.need_reset = 0

        with open(self.man_ori_dat_path, "r", encoding="utf-8") as f:
            for i in range(self.n_cams):
                self.camera[i]._x = []
                self.camera[i]._y = []
                for j in range(4):  # 4 orientation points
                    line = f.readline().split()
                    self.camera[i]._x.append(float(line[0]))
                    self.camera[i]._y.append(float(line[1]))

        self.status_text = "man_ori.dat loaded."
        shutil.copyfile(
            self.man_ori_dat_path,
            self.par_path / "man_ori.dat",
        )

        # TODO: rewrite using Parameters subclass
        man_ori_par_path = os.path.join(self.par_path, "man_ori.par")
        f = open(man_ori_par_path, "r", encoding="utf-8")
        if f is None:
            self.status_text = "Error loading man_ori.par."
        else:
            for i in range(self.n_cams):
                for j in range(4):
                    self.camera[i].man_ori[j] = int(f.readline().split()[0])
                self.status_text = "man_ori.par loaded."
                self.camera[i].left_clicked_event()
            f.close()

        self.status_text = "Loading orientation data from file finished."

    def _button_init_guess_fired(self):
        if self.need_reset:
            self.reset_show_images()
            self.need_reset = 0

        self.cal_points = self._read_cal_points()

        self.cals = []
        for i_cam in range(self.n_cams):
            self.cals.append(Calibration().from_file(
                self.cpar.cal_img_base_name[i_cam] + ".ori",
                self.cpar.cal_img_base_name[i_cam] + ".addpar"
                )
            )

        for i_cam in range(self.n_cams):
            self._project_cal_points(i_cam)

    def _project_cal_points(self, i_cam, color="yellow"):
        """ Projects the calibration points on the image """ 
        out = image_coordinates(
            self.cal_points["pos"], self.cals[i_cam], self.cpar.mm)
        
        pos = arr_metric_to_pixel(out, self.cpar)

        self.drawcross("init_x", "init_y", pos[:, 0].tolist(
        ), pos[:, 1].tolist(), color, 3, i_cam=i_cam)
        self.status_text = "Initial guess finished."

    def _button_sort_grid_fired(self):
        """
        Uses sortgrid function of liboptv to match between the
        calibration points in the fixp target file and the targets
        detected in the images
        """
        if self.need_reset:
            self.reset_show_images()
            self.need_reset = 0

        self.cal_points = self._read_cal_points()
        self.sorted_targs = []

        print("_button_sort_grid_fired")

        for i_cam in range(self.n_cams):

            # if len(self.cal_points) > len(self.detections[i_cam]):
            #     raise ValueError("Insufficient detected points, need at \
            #                       least as many as fixed points")

            targs = sortgrid(
                self.cals[i_cam],
                self.cpar,
                len(self.cal_points),
                self.cal_points["pos"],
                25,  # pixels I guess
                self.detections[i_cam],
            )

            x, y, pnr = [], [], []
            for t in targs:
                if t.pnr != -999:
                    pnr.append(self.cal_points["id"][t.pnr])
                    x.append(t.x)
                    y.append(t.y)

            self.sorted_targs.append(targs)
            self.camera[i_cam].plot_window.overlays.clear()
            self.camera[i_cam].plot_num_overlay(x, y, pnr)

        self.status_text = "Sort grid finished."
        self.pass_sortgrid = True


    def _button_raw_orient_fired(self):
        """
        update the external calibration with results of raw orientation, i.e.
        the iterative process that adjust the initial guess' external
        parameters (position and angle of cameras) without internal or
        distortions.

        See: https://github.com/openptv/openptv/liboptv/src/orientation.c#L591
        """
        if self.need_reset:
            self.reset_show_images()
            self.need_reset = 0

        # backup the ORI/ADDPAR files first
        self.backup_ori_files()

        # get manual points from cal_points and use ids from man_ori.par

        for i_cam in range(self.n_cams):
            selected_points = np.zeros((4, 3))
            for i, cp_id in enumerate(self.cal_points["id"]):
                for j in range(4):
                    if cp_id == self.camera[i_cam].man_ori[j]:
                        selected_points[j, :] = self.cal_points["pos"][i, :]
                        continue

            # in pixels:
            manual_detection_points = [Target(pnr=-999, x=x, y=y) for x, y in zip(
                self.camera[i_cam]._x, self.camera[i_cam]._y)]

            success = raw_orient(
                self.cals[i_cam],
                self.cpar,
                len(selected_points),
                selected_points,
                manual_detection_points
            )

            if success is False:
                print("Initial guess has not been successful\n")
            else:
                self.camera[i_cam].plot_window.overlays.clear() # type: ignore
                self._project_cal_points(i_cam, color="red")
                self._write_ori(i_cam)

        self.status_text = "Orientation finished"
        self.pass_raw_orient = True

    def _button_fine_orient_fired(self):
        """ Fine tuning of ORI and ADDPAR using full calibration."""
        scale = 5000

        if self.need_reset:
            self.reset_show_images()
            self.need_reset = 0

        # backup the ORI/ADDPAR files first
        self.backup_ori_files()

        self.cpar = read_control_par(os.path.join(self.par_path, "ptv.par"))
        orient_par = OrientPar().from_file(os.path.join(self.par_path, "orient.par"))

        for i_cam in range(self.n_cams):  # iterate over all cameras

            if self.epar.combine_flag:

                self.status_text = "Multiplane calibration."
                # """ Performs multiplane calibration, in which for all cameras the
                # pre-processed planes in multi_plane.par combined.
                # Overwrites the ori and addpar files of the cameras specified
                # in cal_ori.par of the multiplane parameter folder
                # """

                all_known = []
                all_detected = []

                for i in range(self.MultiParams.num_planes):
                    # combine all single planes

                    # c = self.calParams.img_ori[i_cam][-9] # Get camera id
                    # not all ends with a number
                    c = re.findall("\\d+", self.calParams.img_ori0[i_cam])[0]

                    file_known = (
                        self.MultiParams.filename[i] + c + ".tif.fix"
                    )
                    file_detected = (
                        self.MultiParams.filename[i] + c + ".tif.crd"
                    )

                    # Load calibration point information from plane i
                    try:
                        known = np.loadtxt(file_known)
                        detected = np.loadtxt(file_detected)
                    except BaseException as exc:
                        raise IOError(
                            f"reading {file_known} or {file_detected} failed" 
                            ) from exc

                    if np.any(detected == -999):
                        raise ValueError(
                            (
                                f"Using undetected points in {file_detected} is prohibited "
                            )
                        )

                    num_known = len(known)
                    num_detect = len(detected)

                    if num_known != num_detect:
                        raise ValueError(
                            f"Number of detected points {num_known} does not match"
                            " number of known points {num_detect} for \
                                {file_known}, {file_detected}")

                    if len(all_known) > 0:
                        detected[:, 0] = (
                            all_detected[-1][-1, 0]
                            + 1
                            + np.arange(len(detected))
                        )

                    # Append to list of total known and detected points
                    all_known.append(known)
                    all_detected.append(detected)

                # Make into the format needed for full_calibration.
                all_known = np.vstack(all_known)[:, 1:]
                all_detected = np.vstack(all_detected)

                # this is the main difference in the multiplane mode
                # that we fill the targs and cal_points by the
                # combined information

                # targs = TargetArray(len(all_detected))
                targs = [Target() for _ in range(len(all_detected))]
                for tix, det in enumerate(all_detected):
                    targ = targs[tix]
                    # det = all_detected[tix]

                    targ.set_pnr(tix)
                    targ.set_pos(det[1:])

                self.cal_points = np.empty((all_known.shape[0],)).astype(
                    dtype=[("id", "i4"), ("pos", "3f8")]
                )
                self.cal_points["pos"] = all_known
            else:
                targs = self.sorted_targs[i_cam]

            try:
                residuals, targ_ix, err_est = full_calibration(
                    self.cals[i_cam],
                    self.cal_points["pos"],
                    targs,
                    self.cpar,
                    orient_par,
                )
                print(residuals)
                print(err_est)
                
            except BaseException as exc:
                raise ValueError("full calibration failed\n") from exc
            # save the results
            self._write_ori(i_cam, addpar_flag=True)

            # Plot the output
            # self.resetplot_windows()

            x, y = [], []
            for r, t in zip(residuals, targ_ix):
                if t != -999:
                    pos = targs[t].pos()
                    x.append(pos[0])
                    y.append(pos[1])

            self.camera[i_cam].plot_window.overlays.clear() # type: ignore
            self.drawcross(
                "orient_x", "orient_y", x, y, "orange", 5, i_cam=i_cam
            )

            # self.camera[i].plot_data.set_data(
            #     'imagedata', self.ori_img[i].astype(np.float))
            # self.camera[i]._img_plot = self.camera[
            #     i].plot_window.imgplot_window('imagedata', colormap=gray)[0]
            self.camera[i_cam].drawquiver(
                x,
                y,
                x + scale * residuals[: len(x), 0],
                y + scale * residuals[: len(x), 1],
                "red",
            )
            # self.camera[i].plot_window.index_mapper.range.set_bounds(0, self.h_pixel)
            # self.camera[i].plot_window.value_mapper.range.set_bounds(0, self.v_pixel)

        self.status_text = "Orientation finished."

    def _write_ori(self, i_cam: int, addpar_flag=False):
        """Writes ORI and ADDPAR files for a single calibration result
        of i_cam
        addpar_flag is a boolean that allows to keep previous addpar
        otherwise external_calibration overwrites zeros
        """

        ori = self.calParams.img_ori0[i_cam]
        if addpar_flag:
            addpar = ori.replace("ori", "addpar")
        else:
            addpar = "tmp.addpar"

        print("Saving:", ori, addpar)
        self.cals[i_cam].write(ori, addpar)
        if self.epar.examine_flag and not self.epar.combine_flag:
            self.save_point_sets(i_cam)

    def save_point_sets(self, i_cam):
        """
        Saves detected and known calibration points in crd and fix format, respectively.
        These files are needed for multiplane calibration.
        """

        ori = self.calParams.img_ori0[i_cam]
        txt_detected = ori.replace("ori", "crd")
        txt_matched = ori.replace("ori", "fix")

        detected, known = [], []
        targs = self.sorted_targs[i_cam]
        for i, t in enumerate(targs):
            if t.pnr != -999:
                detected.append(np.array([t.x, t.y]))
                known.append(self.cal_points["pos"][i])
        nums = np.arange(len(detected))
        # for pnr in nums:
        #     print(targs[pnr].pnr())
        #     print(targs[pnr].pos())
        #   detected[pnr] = targs[pnr].pos()

        detected = np.hstack((nums[:, None], np.array(detected)))
        known = np.hstack((nums[:, None], np.array(known)))

        np.savetxt(txt_detected, detected, fmt="%9.5f")
        np.savetxt(txt_matched, known, fmt="%10.5f")

    # def _button_orient_part_fired(self):

    #     self.backup_ori_files()
    #     # x1, y1, x2, y2 = [], [], [], []
    #     # ptv.py_get_from_orient(x1, y1, x2, y2)

    #     self.resetplot_windows()
    #     for i in range(len(self.camera)):
    #         self.camera[i].plot_data.set_data(
    #             "imagedata", self.ori_img[i].astype(np.float)
    #         )
    #         self.camera[i]._img_plot = self.camera[i].plot_window.imgplot_window(
    #             "imagedata", colormap=gray
    #         )[0]
    #         self.camera[i].drawquiver(x1[i], y1[i], x2[i], y2[i], "red")
    #         self.camera[i].plot_window.index_mapper.range.set_bounds(0, self.h_pixel)
    #         self.camera[i].plot_window.value_mapper.range.set_bounds(0, self.v_pixel)
    #         self.drawcross("orient_x", "orient_y", x1, y1, "orange", 4)

        self.status_text = "Orientation with particles finished."

    def _button_restore_orient_fired(self):
        print("Restoring ORI files\n")
        self.restore_ori_files()

    def resetplot_windows(self):
        for i in range(len(self.camera)):
            self.camera[i].plot_window.delplot(
                *self.camera[i].plot_window.plots.keys()[0:]
            )
            self.camera[i].plot_window.overlays.clear() # type: ignore
            # for j in range(len(self.camera[i]._quiverplots)):
            #     self.camera[i].plot_window.remove(self.camera[i]._quiverplots[j])
            # self.camera[i]._quiverplots = []

    def reset_show_images(self):
        for i, cam in enumerate(self.camera):
            cam.plot_window.delplot(*list(cam.plot_window.plots.keys())[0:])
            cam.plot_window.overlays.clear() # type: ignore
            # self.camera[i].plot_data.set_data('imagedata',self.ori_img[i].astype(np.byte))
            cam.plot_data.set_data(
                "imagedata", self.cal_images[i].astype(np.uint8)
            )

            cam._img_plot = cam.plot_window.img_plot("imagedata", colormap=gray)[0]
            cam._x = []
            cam._y = []
            cam._img_plot.tools = []

            # for j in range(len(cam._quiverplots)):
            #     cam.plot_window.remove(cam._quiverplots[j])
            # cam._quiverplots = []

            cam.attach_tools()
            cam.plot_window.request_redraw()

    def _button_edit_ori_files_fired(self):
        editor = codeEditor(path=self.par_path)
        editor.edit_traits(kind="livemodal")

    def drawcross(self, str_x, str_y, x, y, color1, size1, i_cam=-1):
        """

        :rtype: None
        """
        if i_cam == -1:
            for i in range(self.n_cams):
                self.camera[i].drawcross(
                    str_x, str_y, x[i], y[i], color1, size1
                )
        else:
            self.camera[i_cam].drawcross(str_x, str_y, x, y, color1, size1)

    def backup_ori_files(self):
        """ Backup ORI/ADDPAR files to the backup_cal directory."""
        calOriParams = CalibrationPar().from_file(os.path.join(self.par_path,"cal_ori.par"), self.n_cams)

        for f in calOriParams.img_ori0:
            print(f"Backing up {f}")
            shutil.copyfile(f, f + ".bck")
            g = f.replace("ori", "addpar")
            shutil.copyfile(g, g + ".bck")

    def restore_ori_files(self):
        """ Backup ORI/ADDPAR files to the backup_cal directory."""
       
        calOriParams = CalibrationPar().from_file(os.path.join(self.par_path,"cal_ori.par"), self.n_cams)

        for f in calOriParams.img_ori0[: self.n_cams]:
            print(f"Restoring {f}")
            shutil.copyfile(f + ".bck", f)
            g = f.replace("ori", "addpar")
            shutil.copyfile(g + ".bck", g)

    def protect_ori_files(self):
        # backup ORI/ADDPAR files to the backup_cal directory
        cal_ori_par = CalibrationPar().from_file(os.path.join(self.par_path,"cal_ori.par"), self.n_cams)
        for f in cal_ori_par.img_ori0[: self.n_cams]:
            with open(f, "r",encoding="utf-8") as d:
                d.read().split()
                if not np.all(
                    np.isfinite(np.asarray(d).astype("f"))
                ):  # if there NaN for instance
                    print("protected ORI file %s " % f)
                    shutil.copyfile(f + ".bck", f)

    # def updateplot_windows(self, images):
    #     for i in range(len(images)):
    #         self.camera[i].update_image(images[i])

    def _read_cal_points(self) -> np.ndarray:
        return np.atleast_1d(
            np.loadtxt(
                self.calParams.fixp_name,
                delimiter=',',
                dtype=[("id", "i4"), ("pos", "3f8")],
                skiprows=0,
            )
        )


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1:
        # active_path = Path("../test_cavity/parametersRun1")
        active_path = Path(
            "/home/user/Downloads/1024_15/proPTV_OpenPTV_MyPTV_Test_case_1024_15/parametersMultiPlane")
    else:
        active_path = Path(sys.argv[0])

    calib_gui = CalibrationGUI(active_path)
    calib_gui.configure_traits()
