"""
Copyright (c) 2008-2013, Tel Aviv University
Copyright (c) 2013 - the OpenPTV team
The software is distributed under the terms of MIT-like license
http://opensource.org/licenses/MIT
"""

import os
import shutil
import re
from  pathlib import Path
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
    ArrayDataSource,
    LinearMapper,
)

# from traitsui.menu import MenuBar, ToolBar, Menu, Action
from chaco.tools.image_inspector_tool import ImageInspectorTool
from chaco.tools.better_zoom import BetterZoom as SimpleZoom

# from chaco.tools.simple_zoom import SimpleZoom
from pyptv.text_box_overlay import TextBoxOverlay
from pyptv.code_editor import oriEditor, addparEditor
from pyptv.quiverplot import QuiverPlot


from optv.imgcoord import image_coordinates
from optv.transforms import convert_arr_metric_to_pixel
from optv.orientation import match_detection_to_ref
from optv.orientation import external_calibration, full_calibration
from optv.calibration import Calibration
from optv.tracking_framebuf import TargetArray


from pyptv import ptv, parameter_gui, parameters as par

from scipy.optimize import minimize

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

            x_index, y_index = ndx
            # image_data = plot.value
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
            # image_data = plot.value
            self.x = x_index
            self.y = y_index

            self.right_changed = 1 - self.right_changed
            print(self.x)
            print(self.y)

            self.last_mouse_position = (event.x, event.y)

    def normal_mouse_move(self, event):
        pass

    def __init__(self, *args, **kwargs):
        super(ClickerTool, self).__init__(*args, **kwargs)


# ----------------------------------------------------------


class PlotWindow(HasTraits):
    _plot = Instance(Plot)
    _click_tool = Instance(ClickerTool)
    _right_click_avail = 0
    name = Str
    view = View(
        Item(name="_plot", editor=ComponentEditor(), show_label=False),
    )

    def __init__(self):
        # super(HasTraits, self).__init__()
        super().__init__()
        # -------------- Initialization of plot system ----------------
        padd = 25
        self._plot_data = ArrayPlotData()
        self._x, self._y = [], []
        self.man_ori = [1, 2, 3, 4]
        self._plot = Plot(self._plot_data, default_origin="top left")
        self._plot.padding = (padd, padd, padd, padd)
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
        
        if self._plot.overlays is not None:
            self._plot.overlays.clear() # type: ignore
        self.plot_num_overlay(self._x, self._y, self.man_ori)

    def right_clicked_event(self):
        """ right click event """
        print("right clicked")
        if len(self._x) > 0:
            self._x.pop()
            self._y.pop()
            print(self._x, self._y)

            self.drawcross("coord_x", "coord_y", self._x, self._y, "red", 5)
            if self._plot.overlays is not None:
                self._plot.overlays.clear() # type: ignore
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
            xs = ArrayDataSource(x1)
            ys = ArrayDataSource(y1)

            # quiverplot = QuiverPlot(
            #     index=xs,
            #     value=ys,
            #     index_mapper=LinearMapper(range=self._plot.index_mapper.range),
            #     value_mapper=LinearMapper(range=self._plot.value_mapper.range),
            #     origin=self._plot.origin,
            #     arrow_size=0,
            #     line_color=color,
            #     line_width=linewidth,
            #     ep_index=np.array(x2) * scale,
            #     ep_value=np.array(y2) * scale,
            # )
            vectors = np.array(((np.array(x2)-np.array(x1))/scale, 
                                (np.array(y2)-np.array(y1))/scale)).T
            self._plot_data.set_data("index", x1)
            self._plot_data.set_data("value", y1)
            self._plot_data.set_data("vectors", vectors)
            # self._quiverplots.append(quiverplot)
            self._plot.quiverplot(
                ('index','value','vectors'),
                arrow_size=0,
                line_color="red"
                )
            # self._plot.overlays.append(quiverplot)
        
    def remove_short_lines(self, x1, y1, x2, y2, min_length=2):
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
        x1f, y1f, x2f, y2f = [], [], [], []
        for i in range(len(x1)):
            if (
                abs(x1[i] - x2[i]) > min_length
                or abs(y1[i] - y2[i]) > min_length
            ):
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
            self._plot_data.set_data("imagedata", image.astype(float))
        else:
            self._plot_data.set_data("imagedata", image.astype(np.uint8))
            
        # Alex added to plot the image here from update image
        self._img_plt = self._plot.img_plot("imagedata", colormap=gray)[0]

        self._plot.request_redraw()


# ---------------------------------------------------------


class CalibrationGUI(HasTraits):
    status_text = Str("")
    ori_cam_name = []
    ori_cam = []
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
    # button_orient_shaking = Button()
    button_orient_dumbbell = Button()
    button_restore_orient = Button()
    button_checkpoint = Button()
    button_ap_figures = Button()
    button_edit_ori_files = Button()
    button_edit_addpar_files = Button()
    button_test = Button()

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

        self.active_path = active_path
        self.working_folder = self.active_path.parent
        self.par_path = self.working_folder / "parameters"
        
        self.man_ori_dat_path = self.working_folder / "man_ori.dat"

        print(" Copying parameters inside Calibration GUI: \n")
        par.copy_params_dir(self.active_path, self.par_path)

        
        os.chdir(self.working_folder)
        print(f"Inside a folder: {Path.cwd()}")
        
        # read parameters
        with open(self.par_path / "ptv.par", "r") as f:
            self.n_cams = int(f.readline())

        self.calParams = par.CalOriParams(self.n_cams, path=self.par_path)
        self.calParams.read()

        self.camera = [PlotWindow() for i in range(self.n_cams)]
        for i in range(self.n_cams):
            self.camera[i].name = "Camera" + str(i + 1)
            self.camera[i].cameraN = i
            self.camera[i].py_rclick_delete = ptv.py_rclick_delete
            self.camera[i].py_get_pix_N = ptv.py_get_pix_N

    # Defines GUI view --------------------------

    view = View(
        HGroup(
            VGroup(
                VGroup(
                    Item(
                        name="button_showimg",
                        label="Load images/parameters",
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
                    # Item(
                    #     name="button_checkpoint",
                    #     label="Checkpoints",
                    #     show_label=False,
                    #     enabled_when="pass_init_disabled",
                    # ),
                    # Item(
                    #     name="button_ap_figures",
                    #     label="Ap figures",
                    #     show_label=False,
                    #     enabled_when="pass_init_disabled",
                    # ),
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
                    Item(
                        name="button_edit_addpar_files",
                        label="Edit addpar files",
                        show_label=False,
                    ),
                    Item(
                        name='_',
                        label = '',
                        show_label=False,
                    ),
                    Item(
                        name="button_orient_part",
                        label="Orientation with particles",
                        show_label=False,
                        enabled_when="pass_init",
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
                    page_name=".name",
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
        par.copy_params_dir(self.par_path, self.active_path)
        # and read again from the disk
        (
            self.cpar,
            self.spar,
            self.vpar,
            self.track_par,
            self.tpar,
            self.cals,
            self.epar,
        ) = ptv.py_start_proc_c(self.n_cams)

    def _button_showimg_fired(self):

        print("Loading images/parameters \n")

        # Initialize what is needed, copy necessary things

        # copy parameters from active to default folder parameters/
        par.copy_params_dir(self.active_path, self.par_path)

        print("\n Copying man_ori.dat \n")
        if os.path.isfile(os.path.join(self.par_path, "man_ori.dat")):
            print("Warning - copying man_ori.dat from the /parameters\n")
            shutil.copyfile(
                os.path.join(self.par_path, "man_ori.dat"),
                os.path.join(self.working_folder, "man_ori.dat"),
            )
            print("\n Copied man_ori.dat \n")

        # read from parameters
        (
            self.cpar,
            self.spar,
            self.vpar,
            self.track_par,
            self.tpar,
            self.cals,
            self.epar,
        ) = ptv.py_start_proc_c(self.n_cams)

        print("reset grey scale thresholds for calibration:\n")
        self.tpar.read("parameters/detect_plate.par")
        print(self.tpar.get_grey_thresholds())


        if self.epar.Combine_Flag is True:
            print("Combine Flag is On")
            self.MultiParams = par.MultiPlaneParams()
            self.MultiParams.read()
            for i in range(self.MultiParams.n_planes):
                print(self.MultiParams.plane_name[i])

            self.pass_raw_orient = True
            self.status_text = "Multiplane calibration."

        # read calibration images
        self.cal_images = []
        for i in range(len(self.camera)):
            imname = self.cpar.get_cal_img_base_name(i)
            im = imread(imname)
            # im = ImageData.fromfile(imname).data
            if im.ndim > 2:
                im = rgb2gray(im[:,:,:3])

            self.cal_images.append(img_as_ubyte(im))

        self.reset_show_images()

        # Loading manual parameters here

        f = open(os.path.join(self.par_path, "man_ori.par"), "r")
        if f is None:
            print("\n Error loading man_ori.par from parameters")
        else:
            for i in range(len(self.camera)):
                for j in range(4):
                    self.camera[i].man_ori[j] = int(f.readline().strip())
        f.close()

        self.pass_init = True
        self.status_text = "Initialization finished."

    def _button_detection_fired(self):
        if self.need_reset:
            self.reset_show_images()
            self.need_reset = False
        print(" Detection procedure \n")
        self.status_text = "Detection procedure"

        if self.cpar.get_hp_flag():
            self.cal_images = ptv.py_pre_processing_c(
                self.cal_images, self.cpar
            )

        self.detections, corrected = ptv.py_detection_proc_c(
            self.cal_images, self.cpar, self.tpar, self.cals
        )

        x = [[i.pos()[0] for i in row] for row in self.detections]
        y = [[i.pos()[1] for i in row] for row in self.detections]

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

        
        with open(self.man_ori_dat_path, "r") as f:
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
        f = open(man_ori_par_path, "r")
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
            cal = Calibration()
            tmp = self.cpar.get_cal_img_base_name(i_cam)
            cal.from_file(tmp + ".ori", tmp + ".addpar")
            self.cals.append(cal)

        for i_cam in range(self.n_cams):
            self._project_cal_points(i_cam)

    def _project_cal_points(self, i_cam, color="orange"):
        x, y, pnr = [], [], []
        for row in self.cal_points:
            projected = image_coordinates(
                np.atleast_2d(row["pos"]),
                self.cals[i_cam],
                self.cpar.get_multimedia_params(),
            )
            pos = convert_arr_metric_to_pixel(projected, self.cpar)

            x.append(pos[0][0])
            y.append(pos[0][1])
            pnr.append(row["id"])

        # x.append(x1)
        # y.append(y1)
        self.drawcross("init_x", "init_y", x, y, color, 3, i_cam=i_cam)
        self.camera[i_cam].plot_num_overlay(x, y, pnr)
    
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

            targs = match_detection_to_ref(
                self.cals[i_cam],
                self.cal_points["pos"],
                self.detections[i_cam],
                self.cpar,
            )
            x, y, pnr = [], [], []
            for t in targs:
                if t.pnr() != -999:
                    pnr.append(self.cal_points["id"][t.pnr()])
                    x.append(t.pos()[0])
                    y.append(t.pos()[1])

            self.sorted_targs.append(targs)
            self.camera[i_cam]._plot.overlays = []
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
            manual_detection_points = np.array(
                (self.camera[i_cam]._x, self.camera[i_cam]._y)
            ).T

            success = external_calibration(
                self.cals[i_cam],
                selected_points,
                manual_detection_points,
                self.cpar,
            )

            if success is False:
                print("Initial guess has not been successful\n")
            else:
                self.camera[i_cam]._plot.overlays = []
                self._project_cal_points(i_cam, color="red")
                self._write_ori(i_cam)

        self.status_text = "Orientation finished"
        self.pass_raw_orient = True

    def _button_fine_orient_fired(self):
        """
        fine tuning of ORI and ADDPAR

        """
        if self.need_reset:
            self.reset_show_images()
            self.need_reset = 0

        # backup the ORI/ADDPAR files first
        self.backup_ori_files()

        op = par.OrientParams()
        op.read()

        flags = [name for name in NAMES if getattr(op, name) == 1]

        for i_cam in range(self.n_cams):  # iterate over all cameras

            if self.epar.Combine_Flag:

                self.status_text = "Multiplane calibration."
                """ Performs multiplane calibration, in which for all cameras the
                pre-processed planes in multi_plane.par combined.
                Overwrites the ori and addpar files of the cameras specified
                in cal_ori.par of the multiplane parameter folder
                """

                all_known = []
                all_detected = []

                for i in range(
                    self.MultiParams.n_planes
                ):  # combine all single planes

                    # c = self.calParams.img_ori[i_cam][-9] # Get camera id
                    # not all ends with a number
                    # c = re.findall("\\d+", self.calParams.img_ori[i_cam])[0]
                    match = re.search(r'cam[_-]?(\d)', self.calParams.img_ori[i_cam])
                    if match:
                        c = match.group(1)
                        print(f'Camera number found: {c} in {self.calParams.img_ori[i_cam]}')
                    else:
                        raise ValueError("Camera number not found in {}".format(self.calParams.img_ori[i_cam]))


                    file_known = (
                        self.MultiParams.plane_name[i] + c + ".tif.fix"
                    )
                    file_detected = (
                        self.MultiParams.plane_name[i] + c + ".tif.crd"
                    )

                    # Load calibration point information from plane i
                    try:
                        known = np.loadtxt(file_known)
                        detected = np.loadtxt(file_detected)
                    except BaseException:
                        raise IOError(
                            "reading {} or {} failed".format(
                                file_known, file_detected
                            )
                        )

                    if np.any(detected == -999):
                        raise ValueError(
                            (
                                "Using undetected points in {} will cause "
                                + "silliness. Quitting."
                            ).format(file_detected)
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

                targs = TargetArray(len(all_detected))
                for tix in range(len(all_detected)):
                    targ = targs[tix]
                    det = all_detected[tix]

                    targ.set_pnr(tix)
                    targ.set_pos(det[1:])

                self.cal_points = np.empty((all_known.shape[0],)).astype(
                    dtype=[("id", "i4"), ("pos", "3f8")]
                )
                self.cal_points["pos"] = all_known
            else:
                targs = self.sorted_targs[i_cam]

            # end of multiplane calibration loop that combines planes

            try:
                print(f"Calibrating external (6DOF) and flags: {flags} \n")
                residuals, targ_ix, err_est = full_calibration(
                    self.cals[i_cam],
                    self.cal_points["pos"],
                    targs,
                    self.cpar,
                    flags,
                )
            except BaseException:
                print("Error in OPTV full_calibration, attempting Scipy")
                # raise
                # Now project and estimate full residuals
                self._project_cal_points(i_cam)
                
                residuals = ptv.full_scipy_calibration(
                                self.cals[i_cam],
                                self.cal_points["pos"],
                                targs,
                                self.cpar,
                                flags=flags)

                targ_ix = [t.pnr() for t in targs if t.pnr() != -999]
                # targ_ix = np.arange(len(all_detected))
            
            # save the results from self.cals[i_cam]
            self._write_ori(i_cam, addpar_flag=True)

            # x, y = [], []
            # for r, t in zip(residuals, targ_ix):
            #     if t != -999:
            #         pos = targs[t].pos()
            #         x.append(pos[0])
            #         y.append(pos[1])

            x, y = [], []
            for t in targ_ix:
                if t != -999:
                    pos = targs[t].pos()
                    x.append(pos[0])
                    y.append(pos[1])

            self.camera[i_cam]._plot.overlays.clear()
            self.drawcross(
                "orient_x", "orient_y", x, y, "orange", 5, i_cam=i_cam
            )

            # self.camera[i]._plot_data.set_data(
            #     'imagedata', self.ori_cam[i].astype(np.float))
            # self.camera[i]._img_plot = self.camera[
            #     i]._plot.img_plot('imagedata', colormap=gray)[0]
            self.camera[i_cam].drawquiver(
                x,
                y,
                x + SCALE * residuals[: len(x), 0],
                y + SCALE * residuals[: len(x), 1],
                "red",
            )
            # self.camera[i]._plot.index_mapper.range.set_bounds(0, self.h_pixel)
            # self.camera[i]._plot.value_mapper.range.set_bounds(0, self.v_pixel)

        self.status_text = "Orientation finished."

    # def _error_function(self, x, cal, XYZ, xy, cpar):
    #     """Error function for scipy.optimize.minimize.

    #     Args:
    #         x (array-like): Array of parameters.
    #         cal (Calibration): Calibration object.
    #         XYZ (array-like): 3D coordinates.
    #         xy (array-like): 2D image coordinates.
    #         cpar (CPar): Camera parameters.

    #     Returns:
    #         float: Error value.
    #     """
    #     residuals = self._residuals_radial(x, cal, XYZ, xy, cpar)
    #     return np.sum(residuals**2)
    
    def _residuals_k(self, x, cal, XYZ, xy, cpar):
        """Residuals due to radial distortion

        Args:
            x (array-like): Array of parameters.
            cal (Calibration): Calibration object.
            XYZ (array-like): 3D coordinates.
            xy (array-like): 2D image coordinates.
            cpar (CPar): Camera parameters.


args=(self.cals[i_cam], 
                                        self.cal_points["pos"], 
                                        targs,
                                        self.cpar
                                        )


        Returns:
            residuals: Distortion in pixels
        """

        cal.set_radial_distortion(x)
        targets = convert_arr_metric_to_pixel(
            image_coordinates(XYZ, cal, cpar.get_multimedia_params()),
            cpar
        )
        xyt = np.array([t.pos() if t.pnr() != -999 else [np.nan, np.nan] for t in xy])
        residuals = np.nan_to_num(xyt - targets)
        # residuals = xy[:,1:] - targets
        return np.sum(residuals**2)

    def _residuals_p(self, x, cal, XYZ, xy, cpar):
        """Residuals due to decentering """
        cal.set_decentering(x)
        targets = convert_arr_metric_to_pixel(
            image_coordinates(XYZ, cal, cpar.get_multimedia_params()),
            cpar
        )
        xyt = np.array([t.pos() if t.pnr() != -999 else [np.nan, np.nan] for t in xy])
        residuals = np.nan_to_num(xyt - targets)
        return np.sum(residuals**2)
    
    def _residuals_s(self, x, cal, XYZ, xy, cpar):
        """Residuals due to decentering """
        cal.set_affine_trans(x)
        targets = convert_arr_metric_to_pixel(
            image_coordinates(XYZ, cal, cpar.get_multimedia_params()),
            cpar
        )
        xyt = np.array([t.pos() if t.pnr() != -999 else [np.nan, np.nan] for t in xy])
        residuals = np.nan_to_num(xyt - targets)
        return np.sum(residuals**2)    

    def _residuals_combined(self, x, cal, XYZ, xy, cpar):
        """Combined residuals  """

        cal.set_radial_distortion(x[:3])
        cal.set_decentering(x[3:5])
        cal.set_affine_trans(x[5:])

        targets = convert_arr_metric_to_pixel(
            image_coordinates(XYZ, cal, cpar.get_multimedia_params()),
            cpar
        )
        xyt = np.array([t.pos() if t.pnr() != -999 else [np.nan, np.nan] for t in xy])
        residuals = np.nan_to_num(xyt - targets)
        return residuals           

    def _write_ori(self, i_cam, addpar_flag=False):
        """Writes ORI and ADDPAR files for a single calibration result
        of i_cam
        addpar_flag is a boolean that allows to keep previous addpar
        otherwise external_calibration overwrites zeros
        """
        # protect ORI files from NaNs
        # Check for NaNs in self.cals[i_cam]
        tmp  = np.array([
            self.cals[i_cam].get_pos(),
            self.cals[i_cam].get_angles(),
            self.cals[i_cam].get_affine(),
            self.cals[i_cam].get_decentering(),
            self.cals[i_cam].get_radial_distortion(),
        ],dtype=object)

        if np.any(np.isnan(np.hstack(tmp))):
            raise ValueError(f"Calibration parameters for camera {i_cam} contain NaNs. Aborting write operation.")

        ori = self.calParams.img_ori[i_cam]
        if addpar_flag:
            addpar = ori.replace("ori", "addpar")
        else:
            addpar = "tmp.addpar"

        print("Saving:", ori, addpar)
        self.cals[i_cam].write(ori.encode(), addpar.encode())
        if self.epar.Examine_Flag and not self.epar.Combine_Flag:
            self.save_point_sets(i_cam)

    def save_point_sets(self, i_cam):
        """
        Saves detected and known calibration points in crd and fix format, respectively.
        These files are needed for multiplane calibration.
        """

        ori = self.calParams.img_ori[i_cam]
        txt_detected = ori.replace("ori", "crd")
        txt_matched = ori.replace("ori", "fix")

        detected, known = [], []
        targs = self.sorted_targs[i_cam]
        for i, t in enumerate(targs):
            if t.pnr() != -999:
                detected.append(t.pos())
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

    def _button_orient_part_fired(self):
        """ Orientation with particles """

        self.backup_ori_files()
        targs_all, targ_ix_all, residuals_all = ptv.py_calibration(10, self)


        # Graphics:
        # parameters:

        from pyptv.parameters import ShakingParams
        sp = ShakingParams()
        sp.read()
        seq_first = sp.shaking_first_frame
        seq_last = sp.shaking_last_frame

        base_names = [self.spar.get_img_base_name(i).decode() for i in range(self.n_cams)]


        for i_cam in range(self.n_cams):

            targ_ix = targ_ix_all[i_cam]
            targs = targs_all[i_cam]
            residuals = residuals_all[i_cam]

            x, y = zip(*[targs[t].pos() for t in targ_ix if t != -999])

            # Remove points where either x or y is zero
            x, y = zip(*[(xi, yi) for xi, yi in zip(x, y) if xi != 0 and yi != 0])

            
            # clear previous crosses
            self.camera[i_cam]._plot.overlays.clear()
            
            # create overlay images for each camera
            if os.path.exists(base_names[i_cam] % seq_first):

                # read images and create overlay
                for i_seq in range(seq_first, seq_last + 1):  # loop over sequences                    
                        temp_img = []
                        for seq in range(seq_first, seq_last):
                            _ = imread(base_names[i_cam] % seq)
                            temp_img.append(img_as_ubyte(_))

                        temp_img = np.array(temp_img)
                        temp_img = np.max(temp_img, axis=0)

                
                self.camera[i_cam].update_image(temp_img)
                
                
            self.drawcross(
                "orient_x", "orient_y", x, y, "orange", 5, i_cam=i_cam
            )
            
            self.camera[i_cam].drawquiver(
                x,
                y,
                x + 5*residuals[: len(x), 0],
                y + 5*residuals[: len(x), 1],
                "red",
            )
        

        self.status_text = "Orientation with particles finished."

    def _button_restore_orient_fired(self):
        print("Restoring ORI files\n")
        self.restore_ori_files()

    def reset_plots(self):
        for i in range(len(self.camera)):
            self.camera[i]._plot.delplot(
                *self.camera[i]._plot.plots.keys()[0:]
            )
            self.camera[i]._plot.overlays.clear()
            # for j in range(len(self.camera[i]._quiverplots)):
            #     self.camera[i]._plot.remove(self.camera[i]._quiverplots[j])
            # self.camera[i]._quiverplots = []

    def reset_show_images(self):
        for i, cam in enumerate(self.camera):
            cam._plot.delplot(*list(cam._plot.plots.keys())[0:])
            cam._plot.overlays = []
            cam._plot_data.set_data(
                "imagedata", self.cal_images[i].astype(np.uint8)
            )

            cam._img_plot = cam._plot.img_plot("imagedata", colormap=gray)[0]
            cam._x = []
            cam._y = []
            cam._img_plot.tools = []
            
            
            cam.attach_tools()
            cam._plot.request_redraw()
           

    def _button_edit_ori_files_fired(self):
        editor = oriEditor(path=self.par_path)
        editor.edit_traits(kind="livemodal")

    def _button_edit_addpar_files_fired(self):
        editor = addparEditor(path=self.par_path)
        editor.edit_traits(kind="livemodal")


    def drawcross(self, str_x, str_y, x, y, color1, size1, i_cam=None):
        """

        :rtype: None
        """
        if i_cam is None:
            for i in range(self.n_cams):
                self.camera[i].drawcross(
                    str_x, str_y, x[i], y[i], color1, size1
                )
        else:
            self.camera[i_cam].drawcross(str_x, str_y, x, y, color1, size1)

    def backup_ori_files(self):
        """backup ORI/ADDPAR files to the backup_cal directory"""
        calOriParams = par.CalOriParams(self.n_cams, path=self.par_path)
        calOriParams.read()
        for f in calOriParams.img_ori[: self.n_cams]:
            print(f"Backing up {f}")
            shutil.copyfile(f, f + ".bck")
            g = f.replace("ori", "addpar")
            shutil.copyfile(g, g + ".bck")

    def restore_ori_files(self):
        # backup ORI/ADDPAR files to the backup_cal directory
        calOriParams = par.CalOriParams(self.n_cams, path=self.par_path)
        calOriParams.read()

        for f in calOriParams.img_ori[: self.n_cams]:
            print(f"Restoring {f}")
            shutil.copyfile(f + ".bck", f)
            g = f.replace("ori", "addpar")
            shutil.copyfile(g + ".bck", g)

    def protect_ori_files(self):
        # backup ORI/ADDPAR files to the backup_cal directory

        for f in calOriParams.img_ori[: self.n_cams]:
            with open(f, "r") as d:
                d.read().split()
                if not np.all(
                    np.isfinite(np.asarray(d).astype("f"))
                ):  # if there NaN for instance
                    print("protected ORI file %s " % f)
                    shutil.copyfile(f + ".bck", f)


    def _read_cal_points(self):



        return np.atleast_1d(
            np.loadtxt(
                self.calParams.fixp_name,
                # delimiter='\t',
                dtype=[("id", "i4"), ("pos", "3f8")],
                skiprows=0,
            )
        )


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1:
        active_path = Path("../test_cavity/parametersRun3")
    else:
        active_path = Path(sys.argv[0])

    calib_gui = CalibrationGUI(active_path)
    calib_gui.configure_traits()
