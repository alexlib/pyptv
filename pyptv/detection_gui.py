#!/Users/alex/anaconda3/envs/py27/bin/pythonw
"""
Copyright (c) 2008-2013, Tel Aviv University
Copyright (c) 2013 - the OpenPTV team
The GUI software is distributed under the terms of MIT-like license
http://opensource.org/licenses/MIT
"""


from traits.api \
    import HasTraits, Str, Int, List, Bool, Instance, Button, Range, Enum 
from traitsui.api import View, Item, HGroup, VGroup, ListEditor
from enable.component_editor import ComponentEditor
from chaco.api import Plot, ArrayPlotData, gray, \
    ImagePlot, ArrayDataSource, LinearMapper
# from traitsui.menu import MenuBar, ToolBar, Menu, Action
from chaco.tools.image_inspector_tool import ImageInspectorTool
from chaco.tools.simple_zoom import SimpleZoom
from text_box_overlay import TextBoxOverlay
from code_editor import codeEditor
from quiverplot import QuiverPlot

import numpy as np
from skimage.io import imread
from skimage import img_as_ubyte
from skimage.color import rgb2gray
import os
import shutil
import re

from optv.imgcoord import image_coordinates
from optv.transforms import convert_arr_metric_to_pixel
from optv.orientation import match_detection_to_ref
from optv.segmentation import target_recognition
from optv.orientation import external_calibration, full_calibration
from optv.calibration import Calibration
from optv.tracking_framebuf import TargetArray


import ptv as ptv
import parameter_gui as pargui
import parameters as par


# -------------------------------------------
class ClickerTool(ImageInspectorTool):
    left_changed = Int(1)
    right_changed = Int(1)
    x = 0
    y = 0

    def normal_left_down(self, event):
        """ Handles the left mouse button being clicked.
        Fires the **new_value** event with the data (if any) from the event's
        position.
        """
        plot = self.component
        if plot is not None:
            ndx = plot.map_index((event.x, event.y))

            x_index, y_index = ndx
            # image_data = plot.value
            self.x = (x_index)
            self.y = (y_index)
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
            self.x = (x_index)
            self.y = (y_index)

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
    _plot_data = Instance(ArrayPlotData)
    _plot = Instance(Plot)
    _click_tool = Instance(ClickerTool)
    _img_plot = Instance(ImagePlot)
    _right_click_avail = 0
    name = Str
    view = View(
        Item(name='_plot', editor=ComponentEditor(), show_label=False),

    )

    def __init__(self):
        super(HasTraits, self).__init__()
        # -------------- Initialization of plot system ----------------
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

        # -------------------------------------------------------------

    def left_clicked_event(self):
        print ("left clicked")
        if len(self._x) < 4:
            self._x.append(self._click_tool.x)
            self._y.append(self._click_tool.y)
        print(self._x, self._y)

        self.drawcross("coord_x", "coord_y", self._x, self._y, "red", 5)
        self._plot.overlays = []
        self.plot_num_overlay(self._x, self._y, self.man_ori)

    def right_clicked_event(self):
        print ("right clicked")
        if len(self._x) > 0:
            self._x.pop()
            self._y.pop()
            print(self._x, self._y)

            self.drawcross("coord_x", "coord_y", self._x, self._y, "red", 5)
            self._plot.overlays = []
            self.plot_num_overlay(self._x, self._y, self.man_ori)
        else:
            if (self._right_click_avail):
                print("deleting point")
                self.py_rclick_delete(self._click_tool.x,
                                      self._click_tool.y, self.cameraN)
                x = []
                y = []
                self.py_get_pix_N(x, y, self.cameraN)
                self.drawcross("x", "y", x[0], y[0], "blue", 4)

    def attach_tools(self):
        self._click_tool = ClickerTool(self._img_plot)
        self._click_tool.on_trait_change(
            self.left_clicked_event, 'left_changed')
        self._click_tool.on_trait_change(
            self.right_clicked_event, 'right_changed')
        self._img_plot.tools.append(self._click_tool)
        self._zoom_tool = SimpleZoom(
            component=self._plot, tool_mode="box", always_on=False)
        self._zoom_tool.max_zoom_out_factor = 1.0
        self._img_plot.tools.append(self._zoom_tool)
        if self._plot.index_mapper is not None:
            self._plot.index_mapper.on_trait_change(
                self.handle_mapper, 'updated', remove=False)
        if self._plot.value_mapper is not None:
            self._plot.value_mapper.on_trait_change(
                self.handle_mapper, 'updated', remove=False)

    def drawcross(self, str_x, str_y, x, y, color1, mrk_size):
        """
        Draws crosses on images
        """
        self._plot_data.set_data(str_x, x)
        self._plot_data.set_data(str_y, y)
        self._plot.plot((str_x, str_y), type="scatter",
                        color=color1, marker="plus", marker_size=mrk_size)
        self._plot.request_redraw()

    def drawline(self, str_x, str_y, x1, y1, x2, y2, color1):
        self._plot_data.set_data(str_x, [x1, x2])
        self._plot_data.set_data(str_y, [y1, y2])
        self._plot.plot((str_x, str_y), type="line", color=color1)
        self._plot.request_redraw()

    def drawquiver(self, x1c, y1c, x2c, y2c, color, linewidth=1.0, scale=1.0):
        """ drawquiver draws multiple lines at once on the screen x1,y1->x2,y2 in the current camera window
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
        x1, y1, x2, y2 = self.remove_short_lines(x1c, y1c, x2c, y2c, min_length=0)
        if len(x1) > 0:
            xs = ArrayDataSource(x1)
            ys = ArrayDataSource(y1)

            quiverplot = QuiverPlot(index=xs, value=ys,
                                    index_mapper=LinearMapper(
                                        range=self._plot.index_mapper.range),
                                    value_mapper=LinearMapper(
                                        range=self._plot.value_mapper.range),
                                    origin=self._plot.origin, arrow_size=0,
                                    line_color=color, line_width=linewidth,
                                    ep_index=np.array(x2) * scale,
                                    ep_value=np.array(y2) * scale
                                    )
            self._plot.add(quiverplot)
            # we need this to track how many quiverplots are in the current
            # plot
            self._quiverplots.append(quiverplot)
            # import pdb; pdb.set_trace()

    def remove_short_lines(self, x1, y1, x2, y2, min_length=2):
        """ removes short lines from the array of lines
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
            if abs(x1[i] - x2[i]) > min_length or abs(y1[i] - y2[i]) > min_length:
                x1f.append(x1[i])
                y1f.append(y1[i])
                x2f.append(x2[i])
                y2f.append(y2[i])
        return x1f, y1f, x2f, y2f

    def handle_mapper(self):
        for i in range(0, len(self._plot.overlays)):
            if hasattr(self._plot.overlays[i], 'real_position'):
                coord_x1, coord_y1 = self._plot.map_screen(
                    [self._plot.overlays[i].real_position])[0]
                self._plot.overlays[i].alternate_position = (
                    coord_x1, coord_y1)

    def plot_num_overlay(self, x, y, txt):
        for i in range(0, len(x)):
            coord_x, coord_y = self._plot.map_screen([(x[i], y[i])])[0]
            ovlay = TextBoxOverlay(component=self._plot,
                                   text=str(txt[i]), alternate_position=(coord_x, coord_y),
                                   real_position=(x[i], y[i]),
                                   text_color="white",
                                   border_color="red"
                                   )
            self._plot.overlays.append(ovlay)

    def update_image(self, image, is_float):
        if is_float:
            self._plot_data.set_data('imagedata', image.astype(np.float))
        else:
            self._plot_data.set_data('imagedata', image.astype(np.byte))

        self._plot.request_redraw()


# ---------------------------------------------------------


class DetectionGUI(HasTraits):
    status_text = Str(" status ")
    ori_img_name = []
    ori_img = []
    pass_init = Bool(False)
    pass_sortgrid = Bool(False)
    pass_raw_orient = Bool(False)
    pass_init_disabled = Bool(False)
    # -------------------------------------------------------------
    i_cam = gain = Enum(1, 2, 3, 4)
    grey_thresh= Range(1,255,5,mode='slider')
    min_npix = Range(0,100, method='slider',label='min npix')
    min_npix_x = Range(1,100,1, label='min npix in x')
    min_npix_y = Range(1,100,1, label='min npix in y')
    max_npix = Range(1,100,1, label='max npix')
    max_npix_x = Range(1,100,1, label='max npix in x')
    max_npix_y = Range(1,100,1, label='max npix in y')
    sum_of_grey = Range(1,100,1, label='Sum of greyvalue')
    size_of_crosses = Int(4, label='Size of crosses')
    # button_edit_cal_parameters = Button()
    button_showimg = Button(label='Load image')
    hp_flag = Bool(False,label='highpass')
    button_detection = Button(label='Detect dots')
    # button_manual = Button()
    # button_file_orient = Button()
    # button_init_guess = Button()
    # button_sort_grid = Button()
    # button_sort_grid_init = Button()
    # button_raw_orient = Button()
    # button_fine_orient = Button()
    # button_orient_part = Button()
    # button_orient_shaking = Button()
    # button_orient_dumbbell = Button()
    # button_restore_orient = Button()
    # button_checkpoint = Button()
    # button_ap_figures = Button()
    # button_edit_ori_files = Button()
    # button_test = Button()

    # ---------------------------------------------------
    # Constructor
    # ---------------------------------------------------
    def __init__(self, active_path):
        """ Initialize DetectionGUI

            Inputs:
                active_path is the path to the folder of prameters
                active_path is a subfolder of a working folder with a
                structure of /parameters, /res, /cal, /img and so on
        """

        super(DetectionGUI, self).__init__()
        self.need_reset = 0

        self.active_path = active_path
        self.working_folder = os.path.split(self.active_path)[0]
        self.par_path = os.path.join(self.working_folder, 'parameters')

        par.copy_params_dir(self.active_path, self.par_path)

        os.chdir(os.path.abspath(self.working_folder))
        print("Inside a folder: ", os.getcwd())
        # read parameters
        with open(os.path.join(self.par_path, 'ptv.par'), 'r') as f:
            self.n_cams = int(f.readline())

        # Detection will work one by one for the beginning
        # self.n_cams = 1

        self.camera = [PlotWindow()]
        self.camera_name = 'Camera' + str(self.i_cam + 1)
        self.camera[0].py_rclick_delete = ptv.py_rclick_delete
        self.camera[0].py_get_pix_N = ptv.py_get_pix_N
        

        # self.camera = [PlotWindow() for i in xrange(self.n_cams)]
        # for i in xrange(self.n_cams):
        #     self.camera[i].name = "Camera" + str(i + 1)
        #     self.camera[i].cameraN = i
        #     self.camera[i].py_rclick_delete = ptv.py_rclick_delete
        #     self.camera[i].py_get_pix_N = ptv.py_get_pix_N

    # Defines GUI view --------------------------

    view = View(
        HGroup(
            VGroup(
                VGroup(
                    Item(name='i_cam'),
                    Item(name='button_showimg'),
                    Item(name='button_detection'),
                    Item(name='hp_flag'),
                    Item(name='grey_thresh'),
                    Item(name='min_npix'),
                    Item(name='min_npix_x'),
                    Item(name='min_npix_y'),
                    Item(name='max_npix'),
                    Item(name='max_npix_x'),
                    Item(name='max_npix_y'),
                    Item(name='sum_of_grey'),
                    ),
            ),
            Item('camera', style='custom',
                 editor=ListEditor(use_notebook=True,
                                   deletable=False,
                                   dock_style='tab',
                                   page_name='.name',
                                   ),
                 show_label=False
                 ),

            orientation='horizontal'
        ),
        title='Detection',
        id='view1',
        width=1.,
        height=1.,
        resizable=True,
        statusbar='status_text'
    )

    # --------------------------------------------------

    def _button_edit_cal_parameters_fired(self):
        cp = pargui.Calib_Params(par_path=self.par_path)
        cp.edit_traits(kind='modal')
        # at the end of a modification, copy the parameters
        par.copy_params_dir(self.par_path, self.active_path)
        self.cpar, self.spar, self.vpar, self.track_par, self.tpar, \
        self.cals, self.epar = ptv.py_start_proc_c(self.n_cams)

    def _button_showimg_fired(self):

        print("Loading images/parameters \n")

        # Initialize what is needed, copy necessary things

        print("\n Copying man_ori.dat \n")
        if os.path.isfile(os.path.join(self.par_path, 'man_ori.dat')):
            shutil.copyfile(os.path.join(self.par_path, 'man_ori.dat'),
                            os.path.join(self.working_folder, 'man_ori.dat'))
            print("\n Copied man_ori.dat \n")

        # copy parameters from active to default folder parameters/
        par.copy_params_dir(self.active_path, self.par_path)

        # read from parameters
        self.cpar, self.spar, self.vpar, self.track_par, self.tpar, \
        self.cals, self.epar = ptv.py_start_proc_c(self.n_cams)

        self.tpar.read('parameters/detect_plate.par')

        print(self.tpar.get_grey_thresholds())


        self.calParams = par.CalOriParams(self.n_cams, self.par_path)
        self.calParams.read()
        
        if self.epar.Combine_Flag is True : 
            print("Combine Flag")
            self.MultiParams = par.MultiPlaneParams()
            self.MultiParams.read()
            for i in range(self.MultiParams.n_planes):
                print(self.MultiParams.plane_name[i])

            self.pass_raw_orient = True
            self.status_text = "Multiplane Detection."

        
        # read Detection images
        self.cal_images = []
        for i in range(len(self.camera)):
            imname = self.calParams.img_cal_name[i]
        # for imname in self.calParams.img_cal_name:
            # self.cal_images.append(imread(imname))
            im = imread(imname)
            if im.ndim > 2:
                im = rgb2gray(im)

            self.cal_images.append(img_as_ubyte(im))

        self.reset_show_images()

        # Loading manual parameters here
        man_ori_path = os.path.join(self.par_path, 'man_ori.par')

        f = open(man_ori_path, 'r')
        if f is None:
            print('\n Error loading man_ori.par')
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
            self.cal_images = ptv.py_pre_processing_c(self.cal_images, self.cpar)

        self.detections, corrected = \
            ptv.py_detection_proc_c(self.cal_images, self.cpar, self.tpar, self.cals)

        x = [[i.pos()[0] for i in row] for row in self.detections]
        y = [[i.pos()[1] for i in row] for row in self.detections]

        self.drawcross("x", "y", x, y, "blue", 4)

        for i in range(self.n_cams):
            self.camera[i]._right_click_avail = 1


    def reset_plots(self):
        for i in range(len(self.camera)):
            self.camera[i]._plot.delplot(
                *self.camera[i]._plot.plots.keys()[0:])
            self.camera[i]._plot.overlays = []
            for j in range(len(self.camera[i]._quiverplots)):
                self.camera[i]._plot.remove(self.camera[i]._quiverplots[j])
            self.camera[i]._quiverplots = []

    def reset_show_images(self):
        for i,cam in enumerate(self.camera):
            cam._plot.delplot(*cam._plot.plots.keys()[0:])
            cam._plot.overlays = []
            # self.camera[i]._plot_data.set_data('imagedata',self.ori_img[i].astype(np.byte))
            cam._plot_data.set_data('imagedata', self.cal_images[i].astype(np.byte))

            cam._img_plot = cam._plot.img_plot('imagedata', colormap=gray)[0]
            cam._x = []
            cam._y = []
            cam._img_plot.tools = []
            cam.attach_tools()
            cam._plot.request_redraw()
            for j in range(len(cam._quiverplots)):
                cam._plot.remove(cam._quiverplots[j])
            cam._quiverplots = []

    def _button_edit_ori_files_fired(self):
        editor = codeEditor(path=self.par_path)
        editor.edit_traits(kind='livemodal')

    def drawcross(self, str_x, str_y, x, y, color1, size1, i_cam=None):
        """

        :rtype: None
        """
        if i_cam is None:
            for i in range(self.n_cams):
                self.camera[i].drawcross(str_x, str_y, x[i], y[i], color1, size1)
        else:
            self.camera[i_cam].drawcross(str_x, str_y, x, y, color1, size1)

    def backup_ori_files(self):
        """ backup ORI/ADDPAR files to the backup_cal directory """
        calOriParams = par.CalOriParams(self.n_cams, path=self.par_path)
        calOriParams.read()
        for f in calOriParams.img_ori[:self.n_cams]:
            shutil.copyfile(f, f + '.bck')
            g = f.replace('ori', 'addpar')
            shutil.copyfile(g, g + '.bck')

    def restore_ori_files(self):
        # backup ORI/ADDPAR files to the backup_cal directory
        calOriParams = par.CalOriParams(self.n_cams, path=self.par_path)
        calOriParams.read()

        for f in calOriParams.img_ori[:self.n_cams]:
            print('restored %s ' % f)
            shutil.copyfile(f + '.bck', f)
            g = f.replace('ori', 'addpar')
            shutil.copyfile(g + '.bck', g)

    def protect_ori_files(self):
        # backup ORI/ADDPAR files to the backup_cal directory
        calOriParams = par.CalOriParams(self.n_cams, path=self.par_path)
        calOriParams.read()
        for f in calOriParams.img_ori[:self.n_cams]:
            with open(f, 'r') as d:
                d.read().split()
                if not np.all(np.isfinite(np.asarray(d).astype('f'))):  # if there NaN for instance
                    print("protected ORI file %s " % f)
                    shutil.copyfile(f + '.bck', f)

    def update_plots(self, images, is_float=0):
        for i in range(len(images)):
            self.camera[i].update_image(images[i], is_float)

    def _read_cal_points(self):
        # type: () -> numpy.ndarray
        return np.atleast_1d(np.loadtxt(self.calParams.fixp_name, dtype=[('id', 'i4'), ('pos', '3f8')], skiprows=0))


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1:
        active_path = '/Users/alex/Documents/OpenPTV/test_cavity/parametersRun1'
    else:
        active_path = sys.argv[0]

    detection_gui = DetectionGUI(active_path)
    detection_gui.configure_traits()
