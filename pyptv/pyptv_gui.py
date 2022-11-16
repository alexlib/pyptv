""" PyPTV_GUI is the GUI for the OpenPTV (www.openptv.net) written in
Python with Traits, TraitsUI, Numpy, Scipy and Chaco

Copyright (c) 2008-2023, Turbulence Structure Laboratory, Tel Aviv University
The software is distributed under the terms of MIT-like license
http://opensource.org/licenses/MIT

"""
from __future__ import division

import os
import pathlib
import sys
import time

import numpy as np
import optv
import traits.api
import traitsui.api
from chaco.api import (ArrayDataSource, ArrayPlotData, ImagePlot, LinearMapper,
                       Plot, gray)
from chaco.tools.api import PanTool, ZoomTool
from chaco.tools.image_inspector_tool import ImageInspectorTool
from enable.component_editor import ComponentEditor
# from pyface.api import GUI
# from threading import Thread
from skimage import img_as_ubyte
from skimage.color import rgb2gray
from skimage.io import imread
from traitsui.menu import Action, Menu, MenuBar

from pyptv import parameters as par
from pyptv import ptv
from pyptv.calibration_gui import CalibrationGUI
from pyptv.directory_editor import DirectoryEditorDialog
from pyptv.parameter_gui import Experiment, Paramset
from pyptv.quiverplot import QuiverPlot


class Clicker(ImageInspectorTool):
    """
    Clicker class handles right mouse click actions from the tree
    and menubar actions
    """

    left_changed = traits.api.Int(1)
    right_changed = traits.api.Int(1)
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
            image_data = plot.value
            self.x = x_index
            self.y = y_index
            self.data_value = image_data.data[y_index, x_index]
            self.left_changed = 1 - self.left_changed
            self.last_mouse_position = (event.x, event.y)
        return

    def normal_right_down(self, event):
        plot = self.component
        if plot is not None:
            ndx = plot.map_index((event.x, event.y))

            x_index, y_index = ndx
            # image_data=plot.value
            self.x = x_index
            self.y = y_index

            self.right_changed = 1 - self.right_changed
            print(self.x, self.y)

            self.last_mouse_position = (event.x, event.y)
        return

    def normal_mouse_move(self, event):
        pass

    def __init__(self, *args, **kwargs):
        # Clicker.__init__(self,*args, **kwargs)
        super(Clicker, self).__init__(*args, **kwargs)


# --------------------------------------------------------------
class CameraWindow(traits.api.HasTraits):
    """CameraWindow class contains the relevant information and functions for
    a single camera window: image, zoom, pan important members:
    _plot_data  - contains image data to display (used by update_image)
    _plot - instance of Plot class to use with _plot_data
    _click_tool - instance of Clicker tool for the single camera window,
    to handle mouse processing
    """

    _plot_data = traits.api.Instance(ArrayPlotData)
    _plot = traits.api.Instance(Plot)
    _click_tool = traits.api.Instance(Clicker)
    rclicked = traits.api.Int(0)

    cam_color = ""

    name = traits.api.Str
    view = traitsui.api.View(
        traitsui.api.Item(name="_plot",
                          editor=ComponentEditor(),
                          show_label=False))

    # view = View( Item(name='_plot',show_label=False) )

    def __init__(self, color):
        """
        Initialization of plot system
        """
        traits.api.HasTraits.__init__(self)
        padd = 25
        self._plot_data = ArrayPlotData()
        self._plot = Plot(self._plot_data, default_origin="top left")
        self._plot.padding_left = padd
        self._plot.padding_right = padd
        self._plot.padding_top = padd
        self._plot.padding_bottom = padd
        (
            self.right_p_x0,
            self.right_p_y0,
            self.right_p_x1,
            self.right_p_y1,
            self._quiverplots,
        ) = ([], [], [], [], [])
        self.cam_color = color

    def attach_tools(self):
        """attach_tools(self) contains the relevant tools:
        clicker, pan, zoom"""
        self._click_tool = Clicker(self._img_plot)
        self._click_tool.on_trait_change(
            self.left_clicked_event,
            "left_changed")  # set processing events for Clicker
        self._click_tool.on_trait_change(self.right_clicked_event,
                                         "right_changed")
        self._img_plot.tools.append(self._click_tool)
        pan = PanTool(self._plot, drag_button="middle")
        zoom_tool = ZoomTool(self._plot, tool_mode="box", always_on=False)
        #       zoom_tool = BetterZoom(component=self._plot, tool_mode="box",
        #       always_on=False)
        zoom_tool.max_zoom_out_factor = 1.0  # Disable "bird view" zoom out
        self._img_plot.overlays.append(zoom_tool)
        self._img_plot.tools.append(pan)

    def left_clicked_event(
        self, ):  # TODO: why do we need the ClickerTool if we can handle mouse
        # clicks here?
        """left_clicked_event - processes left click mouse
        events and displays coordinate and grey value information
        on the screen
        """
        print("x = %d, y= %d, grey= %d " % (
            self._click_tool.x,
            self._click_tool.y,
            self._click_tool.data_value,
        ))
        # need to priny gray value

    def right_clicked_event(self):
        # flag that is tracked by main_gui, for right_click_process function of
        # main_gui
        self.rclicked = 1
        # self._click_tool.y,self.name])
        # self.drawcross("coord_x","coord_y",self._click_tool.x,self._click_tool.y,"red",5)
        # print ("right clicked, "+self.name)
        # need to print cross and manage other camera's crosses

    def update_image(self, image, is_float=False):
        """update_image - displays/updates image in the current camera window
        parameters:
            image - image data
            is_float - if true, displays an image as float array,
            else displays as byte array (B&W or gray)
        example usage:
            update_image(image,is_float=False)
        """
        # print('image shape = ', image.shape, 'is_float =', is_float)
        if image.ndim > 2:
            image = img_as_ubyte(rgb2gray(image))
            is_float = False

        if is_float:
            self._plot_data.set_data("imagedata", image.astype(np.float))
        else:
            self._plot_data.set_data("imagedata", image.astype(np.byte))

        if not hasattr(
                self,
                "_img_plot"):  # make a new plot if there is nothing to update
            self._img_plot = traits.api.Instance(ImagePlot)
            self._img_plot = self._plot.img_plot("imagedata", colormap=gray)[0]
            self.attach_tools()

        # self._plot.request_redraw()

    def drawcross(self, str_x, str_y, x, y, color1, mrk_size, marker1="plus"):
        """drawcross draws crosses at a given location (x,y) using color
        and marker in the current camera window parameters:
            str_x - label for x coordinates
            str_y - label for y coordinates
            x - array of x coordinates
            y - array of y coordinates
            mrk_size - marker size
            marker1 - type of marker, e.g "plus","circle"
        example usage:
            drawcross("coord_x","coord_y",[100,200,300],[100,200,300],2)
            draws plus markers of size 2 at points
                (100,100),(200,200),(200,300)
            :rtype:
        """
        self._plot_data.set_data(str_x, np.atleast_1d(x))
        self._plot_data.set_data(str_y, np.atleast_1d(y))
        self._plot.plot(
            (str_x, str_y),
            type="scatter",
            color=color1,
            marker=marker1,
            marker_size=mrk_size,
        )
        self._plot.request_redraw()

    def drawquiver(self, x1c, y1c, x2c, y2c, color, linewidth=1.0):
        """Draws multiple lines at once on the screen x1,y1->x2,y2 in the
        current camera window
        parameters:
            x1c - array of x1 coordinates
            y1c - array of y1 coordinates
            x2c - array of x2 coordinates
            y2c - array of y2 coordinates
            color - color of the line
            linewidth - linewidth of the line
        example usage:
            drawquiver ([100,200],[100,100],[400,400],[300,200],\
                'red',linewidth=2.0)
            draws 2 red lines with thickness = 2 :  \
                100,100->400,300 and 200,100->400,200

        """
        x1, y1, x2, y2 = self.remove_short_lines(x1c, y1c, x2c, y2c)
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
                ep_index=np.array(x2),
                ep_value=np.array(y2),
            )
            self._plot.add(quiverplot)
            # we need this to track how many quiverplots are in the current
            # plot
            self._quiverplots.append(quiverplot)

    @staticmethod
    def remove_short_lines(x1, y1, x2, y2):
        """removes short lines from the array of lines
        parameters:
            x1,y1,x2,y2 - start and end coordinates of the lines
        returns:
            x1f,y1f,x2f,y2f - start and end coordinates of the lines,
            with short lines removed example usage:
            x1,y1,x2,y2 = remove_short_lines( \
                [100,200,300],[100,200,300],[100,200,300],[102,210,320])
            3 input lines, 1 short line will be removed (100,100->100,102)
            returned coordinates:
            x1=[200,300]; y1=[200,300]; x2=[200,300]; y2=[210,320]
        """
        dx, dy = 2, 2  # minimum allowable dx,dy
        x1f, y1f, x2f, y2f = [], [], [], []
        for i in range(len(x1)):
            if abs(x1[i] - x2[i]) > dx or abs(y1[i] - y2[i]) > dy:
                x1f.append(x1[i])
                y1f.append(y1[i])
                x2f.append(x2[i])
                y2f.append(y2[i])
        return x1f, y1f, x2f, y2f

    def drawline(self, str_x, str_y, x1, y1, x2, y2, color1):
        """drawline draws 1 line on the screen by using lineplot x1,y1->x2,y2
        parameters:
            str_x - label of x coordinate
            str_y - label of y coordinate
            x1,y1,x2,y2 - start and end coordinates of the line
            color1 - color of the line
        example usage:
            drawline("x_coord","y_coord",100,100,200,200,red)
            draws a red line 100,100->200,200
        """
        # imx, imy = self._plot_data.get_data('imagedata').shape
        self._plot_data.set_data(str_x, [x1, x2])
        self._plot_data.set_data(str_y, [y1, y2])
        self._plot.plot((str_x, str_y), type="line", color=color1)
        # self._plot.index_range.low_setting = 0
        # self._plot.index_range.high_setting = imx
        # self._plot.value_range.low_setting = 0
        # self._plot.value_range.high_setting = imy

        # self._plot.request_redraw()

    def add_line(self, str_x, str_y, x1, y1, x2, y2, color1):
        """drawline draws 1 line on the screen by using lineplot x1,y1->x2,y2
        parameters:
            str_x - label of x coordinate
            str_y - label of y coordinate
            x1,y1,x2,y2 - start and end coordinates of the line
            color1 - color of the line
        example usage:
            drawline("x_coord","y_coord",100,100,200,200,red)
            draws a red line 100,100->200,200
        """
        # self._plot_data.set_data(str_x,[x1,x2])
        # self._plot_data.set_data(str_y,[y1,y2])

        self._plot_data.set_data(str_x, [x1, x2])
        self._plot_data.set_data(str_y, [y1, y2])
        self._plot.add(Plot((str_x, str_y), type="line", color=color1))


class TreeMenuHandler(traitsui.api.Handler):
    """TreeMenuHanlder contains all the callback actions of menu bar,
    processing of tree editor, and reactions of the GUI to the user clicks
    possible function declarations:
        1) to process menubar actions:
            def function(self, info):
        parameters: self - needed for member function declaration,
                info - contains pointer to calling parent class (e.g main_gui)
                To access parent class objects use info.object, for example
                info.object.exp1 gives access to exp1 member of main_gui class
        2) to process tree editor actions:
            def function(self,editor,object) - see examples below

    """

    def configure_main_par(self, editor, object):
        experiment = editor.get_parent(object)
        paramset = object
        print("Total paramsets:", len(experiment.paramsets))
        if paramset.m_params is None:
            # TODO: is it possible that control reaches here? If not, probably
            # the if should be removed.
            paramset.m_params = par.PtvParams()
        else:
            paramset.m_params._reload()
        paramset.m_params.edit_traits(kind="modal")

    def configure_cal_par(self, editor, object):
        experiment = editor.get_parent(object)
        paramset = object
        print(len(experiment.paramsets))
        if paramset.c_params is None:
            # TODO: is it possible that control reaches here? If not, probably
            # the if should be removed.
            paramset.c_params = (par.CalOriParams()
                                 )  # this is a very questionable line
        else:
            paramset.c_params._reload()
        paramset.c_params.edit_traits(kind="modal")

    def configure_track_par(self, editor, object):
        experiment = editor.get_parent(object)
        paramset = object
        print(len(experiment.paramsets))
        if paramset.t_params is None:
            # TODO: is it possible that control reaches here? If not, probably
            # the if should be removed.
            paramset.t_params = par.TrackingParams()
        paramset.t_params.edit_traits(kind="modal")

    def set_active(self, editor, object):
        """sets a set of parameters as active"""
        experiment = editor.get_parent(object)
        paramset = object
        # experiment.active_params = paramset
        experiment.setActive(paramset)
        experiment.changed_active_params = True
        # editor.object.__init__()

    def copy_set_params(self, editor, object):
        experiment = editor.get_parent(object)
        paramset = object
        i = 1
        new_name = None
        new_dir_path = None
        flag = False
        while not flag:
            new_name = "%s (%d)" % (paramset.name, i)
            new_dir_path = "%s%s" % (par.par_dir_prefix, new_name)
            if not os.path.isdir(new_dir_path):
                flag = True
            else:
                i = i + 1

        os.mkdir(new_dir_path)
        par.copy_params_dir(paramset.par_path, new_dir_path)
        experiment.addParamset(new_name, new_dir_path)

    @staticmethod
    def rename_set_params(editor, object):
        """rename_set_params renames the node name on the tree and also
        the folder of parameters"""
        experiment = editor.get_parent(object)
        paramset = object
        # rename
        # import pdb; pdb.set_trace()
        editor._menu_rename_node()
        new_name = object.name
        new_dir_path = par.par_dir_prefix + new_name
        os.mkdir(new_dir_path)
        par.copy_params_dir(paramset.par_path, new_dir_path)
        [
            os.remove(os.path.join(paramset.par_path, f))
            for f in os.listdir(paramset.par_path)
        ]
        os.rmdir(paramset.par_path)
        experiment.removeParamset(paramset)
        experiment.addParamset(new_name, new_dir_path)

    @staticmethod
    def delete_set_params(editor, object):
        """delete_set_params deletes the node and the folder of parameters"""
        # experiment = editor.get_parent(object)
        paramset = object
        # delete node
        editor._menu_delete_node()
        # delete all the parameter files
        [
            os.remove(os.path.join(paramset.par_path, f))
            for f in os.listdir(paramset.par_path)
        ]
        # remove folder
        os.rmdir(paramset.par_path)

    # ------------------------------------------
    # Menubar actions
    # ------------------------------------------
    def new_action(self, info):
        print("not implemented")

    def open_action(self, info):
        directory_dialog = DirectoryEditorDialog()
        directory_dialog.edit_traits()
        exp_path = directory_dialog.dir_name
        print(f"Changing experimental path to {exp_path}")
        os.chdir(exp_path)
        info.object.exp1.populate_runs(exp_path)

    def exit_action(self, info):
        print("not implemented")

    def saveas_action(self, info):
        print("not implemented")

    def showimg_action(self, info):
        print("not implemented")

        info.object.update_plots(info.object.orig_image)

    def highpass_action(self, info):
        """highpass_action - calls ptv.py_pre_processing_c() binding which
        does highpass on working images (object.orig_image) that were set
        with init action
        """
        print("highpass started")
        info.object.orig_image = ptv.py_pre_processing_c(
            info.object.orig_image, info.object.cpar)
        info.object.update_plots(info.object.orig_image)
        print("highpass finished")

    def img_coord_action(self, info):
        """
        img_coord_action - runs detection function by using
        ptv.py_detection_proc_c()
        binding. results are extracted with help of ptv.py_get_pix(x,y) binding
        and plotted on the screen
        """
        print("detection proc started")
        (
            info.object.detections,
            info.object.corrected,
        ) = ptv.py_detection_proc_c(
            info.object.orig_image,
            info.object.cpar,
            info.object.tpar,
            info.object.cals,
        )
        print("detection proc finished")
        x = [[i.pos()[0] for i in row] for row in info.object.detections]
        y = [[i.pos()[1] for i in row] for row in info.object.detections]
        info.object.drawcross("x", "y", x, y, "blue", 3)

    def _clean_correspondences(self, tmp):
        """arr is a (n_cams,N,2) array that contains four lists of
        correspondences (each per camera)
        """
        x1, y1 = [], []
        for x in tmp:
            tmp = x[(x != -999).any(axis=1)]  # remove all rows with -999
            x1.append(tmp[:, 0])
            y1.append(tmp[:, 1])

        return x1, y1

    def corresp_action(self, info):
        """corresp_action calls ptv.py_correspondences_proc_c()
        Result of correspondence action is filled to quadriplets, triplets,
        pairs, and unused arrays
        """

        # if info.object.n_cams  > 1: # single camera is not checked
        print("correspondence proc started")
        (
            info.object.sorted_pos,
            info.object.sorted_corresp,
            info.object.num_targs,
        ) = ptv.py_correspondences_proc_c(info.object)

        # we will always use from pairs or the last iter in sorted_pos
        # and go upwards. so we'll stop at either triplets or quadruplets
        names = ["pair", "tripl", "quad"]
        use_colors = ["yellow", "green", "red"]

        if (len(info.object.camera_list) > 1
                and len(info.object.sorted_pos) > 0):
            # this is valid only if there are 4 cameras
            # quadruplets = info.object.sorted_pos[0]
            # triplets = info.object.sorted_pos[1]
            # pairs = info.object.sorted_pos[2]
            # unused = []  # temporary solution

            # if there are less than 4 cameras, then
            # there are no quadruplets
            # only triplets and pairs if 3
            # only pairs if 2

            # import pdb; pdb.set_trace()
            # info.object.clear_plots(remove_background=False)
            for i, subset in enumerate(reversed(info.object.sorted_pos)):
                x, y = self._clean_correspondences(subset)
                info.object.drawcross(names[i] + "_x", names[i] + "_y", x, y,
                                      use_colors[i], 3)

        # x, y = self._clean_correspondences(triplets)
        # info.object.drawcross("tripl_x", "tripl_y", x, y, "green", 3)
        # x, y = self._clean_correspondences(pairs)
        # info.object.drawcross("pair_x", "pair_y", x, y, "yellow", 3)
        # info.object.drawcross("unused_x","unused_y",unused[:,0],unused[:,1],"blue",3)

    def init_action(self, info):
        """init_action - clears existing plots from the camera windows,
        initializes C image arrays with mainGui.orig_image and
        calls appropriate start_proc_c
         by using ptv.py_start_proc_c()
        """
        mainGui = info.object
        # synchronize the active run params dir with the temp params dir
        mainGui.exp1.syncActiveDir()

        for i in range(len(mainGui.camera_list)):
            try:
                im = imread(
                    getattr(
                        mainGui.exp1.active_params.m_params,
                        "Name_{}_Image".format(i + 1),
                    ))
                if im.ndim > 2:
                    im = rgb2gray(im)

                mainGui.orig_image[i] = img_as_ubyte(im)
            except IOError:
                print("Error reading image, setting zero image")
                h_img = mainGui.exp1.active_params.m_params.imx
                v_img = mainGui.exp1.active_params.m_params.imy
                temp_img = img_as_ubyte(np.zeros((h_img, v_img)))
                print(f"setting images of size {temp_img.shape}")
                exec(f"mainGui.orig_image[{i}] = temp_img")
            if hasattr(mainGui.camera_list[i], "_img_plot"):
                del mainGui.camera_list[i]._img_plot
        mainGui.clear_plots()
        print("\n Init action \n")
        mainGui.update_plots(mainGui.orig_image, is_float=False)
        # mainGui.set_images(mainGui.orig_image)

        (
            info.object.cpar,
            info.object.spar,
            info.object.vpar,
            info.object.track_par,
            info.object.tpar,
            info.object.cals,
            info.object.epar,
        ) = ptv.py_start_proc_c(info.object.n_cams)
        mainGui.pass_init = True
        print("Read all the parameters and calibrations successfully ")

    def calib_action(self, info):
        """calib_action - initializes calib class with appropriate number of
        plot windows, passes to calib class pointer to ptv module and to
        exp1 class, invokes the calibration GUI
        """
        print("\n Starting calibration dialog \n")

        # reset the main GUI so the user will have to press Start again
        info.object.pass_init = False
        print("Active parameters set \n")
        print(info.object.exp1.active_params.par_path)
        calib_gui = CalibrationGUI(info.object.exp1.active_params.par_path)
        calib_gui.configure_traits()

    def sequence_action(self, info):
        """sequence action - implements binding to C sequence function.
           Original function was split into 2 parts:
        1) initialization - bonded by ptv.py_sequence_init(..) function
        2) main loop processing - bonded by ptv.py_sequence_loop(..) function
        """

        extern_sequence = info.object.plugins.sequence_alg
        if extern_sequence != "default":
            try:
                # change to pyptv folder, look for tracking module
                sys.path.append(info.exp1.object.software_path)
                # import chosen tracker from software dir
                seq = __import__(extern_sequence)
            except ImportError:
                print("Error loading or running " + extern_sequence +
                      ". Falling back to default sequence algorithm")

            print("Sequence by using " + extern_sequence)
            sequence = seq.Sequence(
                ptv=ptv,
                exp1=info.object.exp1,
                camera_list=info.object.camera_list,
            )
            sequence.do_sequence()
            # print("Sequence by using "+extern_sequence+" has failed."

        else:
            ptv.py_sequence_loop(info.object)

    def track_no_disp_action(self, info):
        """track_no_disp_action uses ptv.py_trackcorr_loop(..) binding to
        call tracking without display"""
        extern_tracker = info.object.plugins.track_alg
        if extern_tracker != "default":
            try:
                os.chdir(info.exp1.object.software_path
                         )  # change to software path, to load tracking module
                track = __import__(
                    extern_tracker)  # import choosen tracker from software dir
            except BaseException:
                print("Error loading " + extern_tracker +
                      ". Falling back to default tracker")
                extern_tracker = "default"
            os.chdir(info.exp1.object.exp_path)  # change back to working path
        if extern_tracker == "default":
            print("Using default liboptv tracker")
            info.object.tracker = ptv.py_trackcorr_init(info.object)
            info.object.tracker.full_forward()
        else:
            print("Tracking by using " + extern_tracker)
            tracker = track.Tracking(ptv=ptv, exp1=info.object.exp1)
            tracker.do_tracking()

        print("tracking without display finished")

    def track_disp_action(self, info):
        """tracking with display is handled by TrackThread which does
        processing step by step and waits for GUI to update before
        proceeding to the next step

        This was not implemented in PyPTV
        """
        info.object.clear_plots(remove_background=False)
        # info.object.tr_thread = TrackThread()
        # info.object.tr_thread.start()

    def track_back_action(self, info):
        """tracking back action is handled by ptv.py_trackback_c() binding"""
        print("Starting back tracking")
        info.object.tracker.full_backward()

    def three_d_positions(self, info):
        """Extracts and saves 3D positions from the list of correspondences"""
        ptv.py_determination_proc_c(
            info.object.n_cams,
            info.object.sorted_pos,
            info.object.sorted_corresp,
            info.object.corrected,
        )

    # def multigrid_demo(self, info):
    #     demo_window = DemoGUI(ptv=ptv, exp1=info.object.exp1)
    #     demo_window.configure_traits()

    def detect_part_track(self, info):
        """track detected particles is handled by 2 bindings:
        1) tracking_framebuf.read_targets(..)
        2) ptv.py_get_mark_track_c(..)
        """
        info.object.clear_plots(remove_background=False)  # clear everything
        info.object.update_plots(info.object.orig_image, is_float=False)

        prm = info.object.exp1.active_params.m_params
        seq_first = prm.Seq_First  # get sequence parameters
        seq_last = prm.Seq_Last
        base_names = [
            prm.Basename_1_Seq,
            prm.Basename_2_Seq,
            prm.Basename_3_Seq,
            prm.Basename_4_Seq,
        ]

        # load first seq image and set appropriate C array
        info.object.load_set_seq_image(seq_first)

        print("Starting detect_part_track")
        x1_a, x2_a, y1_a, y2_a = [], [], [], []
        for i in range(info.object.n_cams):  # initialize result arrays
            x1_a.append([])
            x2_a.append([])
            y1_a.append([])
            y2_a.append([])

        imx, imy = info.object.cpar.get_image_size()
        # some old stuff that is probably obsolete, left for the future
        # see jw_ptv.c for the origins
        # zoomx = imx / 2
        # zoomy = imx / 2
        # zoomf = 1

        for i_seq in range(seq_first, seq_last + 1):  # loop over sequences
            for i_img in range(info.object.n_cams):
                intx_green, inty_green = [], []
                targets = optv.tracking_framebuf.read_targets(
                    base_names[i_img], i_seq)

                for t in targets:
                    if t.tnr() > -1:
                        # intx_green.append(int(imx/2 + zoomf*(tx - zoomx)))
                        # inty_green.append(int(imy/2 + zoomf*(ty - zoomy)))
                        intx_green.append(t.pos()[0])
                        inty_green.append(t.pos()[1])
                #   else:
                #       intx_blue.append(int(imx/2 + zoomf*(tx - zoomx)))
                #       inty_blue.append(int(imy/2 + zoomf*(ty - zoomy)))

                x1_a[i_img] = (x1_a[i_img] + intx_green
                               )  # add current step to result array
                #                x2_a[i_img]=x2_a[i_img]+intx_blue
                y1_a[i_img] = y1_a[i_img] + inty_green
        #   y2_a[i_img]=y2_a[i_img]+inty_blue
        #   info.object.camera_list[i_img].drawcross(str(i_seq) + \
        #       "x_tr_gr",str(i_seq)+"y_tr_gr",intx_green,inty_green,"green",3)
        #   info.object.camera_list[i_img].drawcross(str(i_seq) + \
        #       "x_tr_bl",str(i_seq)+"y_tr_bl",intx_blue,inty_blue,"blue",2)
        # plot result arrays
        for i_img in range(info.object.n_cams):
            info.object.camera_list[i_img].drawcross("x_tr_gr", "y_tr_gr",
                                                     x1_a[i_img], y1_a[i_img],
                                                     "green", 3)
            # info.object.camera_list[i_img].drawcross("x_tr_bl",
            #                   "y_tr_bl",x2_a[i_img],y2_a[i_img],"blue",2)
            info.object.camera_list[i_img]._plot.request_redraw()

        print("Finished detect_part_track")

    # @staticmethod
    def traject_action(self, info):
        """
        show trajectories is handled by ptv.py_traject_loop(..)
        which returns data to be plotted.
        traject_action collects data to be plotted from all
        the steps and plots it at once.
        """
        print("Starting show trajectories\n")
        info.object.clear_plots(remove_background=False)
        seq_first = info.object.exp1.active_params.m_params.Seq_First
        seq_last = info.object.exp1.active_params.m_params.Seq_Last
        info.object.load_set_seq_image(seq_first, display_only=True)

        # borrowed from flowtracks that does much better job on this
        # I think it's too much to import also postptv here, later
        # we will make a single conda package for the full stack

        fmt = np.dtype([("prev", "i4"), ("next", "i4"), ("pos", "3f8")])

        def _read_frame(fix):
            return np.atleast_1d(
                np.loadtxt("res/ptv_is.%d" % fix, dtype=fmt, skiprows=1))

        x1_a, x2_a, y1_a, y2_a = [], [], [], []
        for i in range(info.object.n_cams):  # initialize result arrays
            x1_a.append([])
            x2_a.append([])
            y1_a.append([])
            y2_a.append([])

        for i_seq in range(seq_first, seq_last):
            for i_cam in range(info.object.n_cams):  # initialize result arrays
                x1, y1 = [], []
                frame = _read_frame(i_seq)
                for row in frame:
                    if row["next"] > -1:
                        projected = optv.imgcoord.image_coordinates(
                            np.atleast_2d(row["pos"]),
                            info.object.cals[i_cam],
                            info.object.cpar.get_multimedia_params(),
                        )
                        pos = optv.transforms.convert_arr_metric_to_pixel(
                            projected, info.object.cpar)
                        # import pdb; pdb.set_trace()

                        x1.append(pos[0][0])
                        y1.append(pos[0][1])

                # add current step to result array
                x1_a[i_cam] = x1_a[i_cam] + x1
                #                x2_a[i_img]=x2_a[i_img]+intx_blue
                y1_a[i_cam] = y1_a[i_cam] + y1
            # for i in range(info.object.n_cams):
        for i_img in range(info.object.n_cams):
            info.object.camera_list[i_img].drawcross("trajx1", "trajy1",
                                                     x1_a[i_img], y1_a[i_img],
                                                     "red", 2)
            # info.object.camera_list[i_img]._plot.request_redraw()

        print("Show trajectories finished")

    def plugin_action(self, info):
        """Configure plugins by using GUI"""
        info.object.plugins.read()
        info.object.plugins.configure_traits()

    def ptv_is_to_paraview(self, info):
        """ Button that runs the ptv_is.# conversion to Paraview """

        print("Saving trajectories for Paraview\n")
        info.object.clear_plots(remove_background=False)
        seq_first = info.object.exp1.active_params.m_params.Seq_First
        seq_last = info.object.exp1.active_params.m_params.Seq_Last
        info.object.load_set_seq_image(seq_first, display_only=True)

        # borrowed from flowtracks that does much better job on this
        # I think it's too much to import also postptv here, later
        # we will make a single conda package for the full stack

        # Example notebook translating OpenPTV files for Paraview using flowtracks
        import pandas as pd
        from flowtracks.io import trajectories_ptvis

        dataset = trajectories_ptvis('res/ptv_is.%d',xuap=False)


        dataframes = []
        for traj in dataset:
            dataframes.append(
                pd.DataFrame.from_records(
                    traj,
                    columns=['x','y','z','dx','dy','dz','frame','particle']
                )
            )


        df = pd.concat(dataframes, ignore_index=True)
        df['particle'] = df['particle'].astype(np.int32)

        # Paraview does not recognize it as a set without _000001.txt, so we the first 10000
        # ptv_is.10001 is becoming ptv_00001.txt

        df['frame'] = df['frame'].astype(np.int32) - 10000


        df.reset_index(inplace=True, drop=True)
        print(df.head())


        df_grouped = df.reset_index().groupby('frame')
        for index, group in df_grouped:
            group.to_csv(
                f'./res/ptv_{int(index):05d}.txt',
                mode='w',
                columns=['particle','x','y','z','dx','dy','dz'], 
                index=False
                )

        print("Saving trajectories to Paraview finished\n")

# ----------------------------------------------------------------
# Actions associated with right mouse button clicks (treeeditor)
# ---------------------------------------------------------------
ConfigMainParams = Action(name="Main parameters",
                          action="handler.configure_main_par(editor,object)")
ConfigCalibParams = Action(
    name="Calibration parameters",
    action="handler.configure_cal_par(editor,object)",
)
ConfigTrackParams = Action(
    name="Tracking parameters",
    action="handler.configure_track_par(editor,object)",
)
SetAsDefault = Action(name="Set as active",
                      action="handler.set_active(editor,object)")
CopySetParams = Action(
    name="Copy set of parameters",
    action="handler.copy_set_params(editor,object)",
)
RenameSetParams = Action(name="Rename run",
                         action="handler.rename_set_params(editor,object)")
DeleteSetParams = Action(name="Delete run",
                         action="handler.delete_set_params(editor,object)")

# -----------------------------------------
# Defines the menubar
# ------------------------------------------
menu_bar = MenuBar(
    Menu(
        Action(name="New", action="new_action"),
        Action(name="Open", action="open_action"),
        Action(name="Save As", action="saveas_action"),
        Action(name="Exit", action="exit_action"),
        name="File",
    ),
    Menu(Action(name="Init / Restart", action="init_action"), name="Start"),
    Menu(
        Action(
            name="High pass filter",
            action="highpass_action",
            enabled_when="pass_init",
        ),
        Action(
            name="Image coord",
            action="img_coord_action",
            enabled_when="pass_init",
        ),
        Action(
            name="Correspondences",
            action="corresp_action",
            enabled_when="pass_init",
        ),
        name="Preprocess",
    ),
    Menu(
        Action(
            name="3D positions",
            action="threed_positions",
            enabled_when="pass_init",
        ),
        name="3D Positions",
    ),
    Menu(
        Action(
            name="Create calibration",
            action="calib_action",
            enabled_when="pass_init",
        ),
        name="Calibration",
    ),
    Menu(
        Action(
            name="Sequence without display",
            action="sequence_action",
            enabled_when="pass_init",
        ),
        name="Sequence",
    ),
    Menu(
        Action(
            name="Detected Particles",
            action="detect_part_track",
            enabled_when="pass_init",
        ),
        Action(
            name="Tracking without display",
            action="track_no_disp_action",
            enabled_when="pass_init",
        ),
        # not implemented Action(name='Tracking with
        # display',action='track_disp_action',enabled_when='pass_init'),
        Action(
            name="Tracking backwards",
            action="track_back_action",
            enabled_when="pass_init",
        ),
        Action(
            name="Show trajectories",
            action="traject_action",
            enabled_when="pass_init",
        ),
        Action(
            name="Save Paraview files",
            action="ptv_is_to_paraview",
            enabled_when="pass_init",
        ),
        name="Tracking",
    ),
    Menu(Action(name="Select plugin", action="plugin_action"), name="Plugins"),
    Menu(Action(name="Run multigrid demo", action="multigrid_demo"),
         name="Demo"),
)

# ----------------------------------------
# tree editor for the Experiment() class
#
tree_editor_exp = traitsui.api.TreeEditor(
    nodes=[
        traitsui.api.TreeNode(
            node_for=[Experiment],
            auto_open=True,
            children="",
            label="=Experiment",
        ),
        traitsui.api.TreeNode(
            node_for=[Experiment],
            auto_open=True,
            children="paramsets",
            label="=Parameters",
            add=[Paramset],
            menu=Menu(CopySetParams),
        ),
        traitsui.api.TreeNode(
            node_for=[Paramset],
            auto_open=True,
            children="",
            label="name",
            menu=Menu(
                # NewAction,
                CopySetParams,
                RenameSetParams,
                DeleteSetParams,
                traitsui.api.Separator(),
                ConfigMainParams,
                ConfigCalibParams,
                ConfigTrackParams,
                traitsui.api.Separator(),
                SetAsDefault,
            ),
        ),
    ],
    editable=False,
)


# -------------------------------------------------------------------------
class Plugins(traits.api.HasTraits):
    track_list = traits.api.List
    seq_list = traits.api.List
    track_alg = traits.api.Enum(values="track_list")
    sequence_alg = traits.api.Enum(values="seq_list")
    view = traitsui.api.View(
        traitsui.api.Group(
            traitsui.api.Item(name="track_alg",
                              label="Choose tracking algorithm:"),
            traitsui.api.Item(name="sequence_alg",
                              label="Choose sequence algorithm:"),
        ),
        buttons=["OK"],
        title="External plugins configuration",
    )

    def __init__(self):
        self.read()

    def read(self):
        # reading external tracking
        if os.path.exists(
                os.path.join(os.path.abspath(os.curdir),
                             "external_tracker_list.txt")):
            with open(
                    os.path.join(os.path.abspath(os.curdir),
                                 "external_tracker_list.txt"),
                    "r",
            ) as f:
                trackers = f.read().split("\n")
                trackers.insert(0, "default")
                self.track_list = trackers
        else:
            self.track_list = ["default"]
        # reading external sequence
        if os.path.exists(
                os.path.join(os.path.abspath(os.curdir),
                             "external_sequence_list.txt")):
            with open(
                    os.path.join(os.path.abspath(os.curdir),
                                 "external_sequence_list.txt"),
                    "r",
            ) as f:
                seq = f.read().split("\n")
                seq.insert(0, "default")
                self.seq_list = seq
        else:
            self.seq_list = ["default"]


# ----------------------------------------------
class MainGUI(traits.api.HasTraits):
    """MainGUI is the main class under which the Model-View-Control
    (MVC) model is defined"""

    camera_list = traits.api.List
    imgplt_flag = 0
    pass_init = traits.api.Bool(False)
    update_thread_plot = traits.api.Bool(False)
    # tr_thread = traits.api.Instance(TrackThread)
    selected = traits.api.Any

    # Defines GUI view --------------------------
    view = traitsui.api.View(
        traitsui.api.Group(
            traitsui.api.Group(
                traitsui.api.Item(
                    name="exp1",
                    editor=tree_editor_exp,
                    show_label=False,
                    width=-400,
                    resizable=False,
                ),
                traitsui.api.Item(
                    "camera_list",
                    style="custom",
                    editor=traitsui.api.ListEditor(
                        use_notebook=True,
                        deletable=False,
                        dock_style="tab",
                        page_name=".name",
                        selected="selected",
                    ),
                    show_label=False,
                ),
                orientation="horizontal",
                show_left=False,
            ),
            orientation="vertical",
        ),
        title="pyPTV",
        id="main_view",
        width=1.0,
        height=1.0,
        resizable=True,
        handler=TreeMenuHandler(),  # <== Handler class is attached
        menubar=menu_bar,
    )

    def _selected_changed(self):
        self.current_camera = int(self.selected.name.split(" ")[1]) - 1

    # ---------------------------------------------------
    # Constructor and Chaco windows initialization
    # ---------------------------------------------------
    def __init__(self, exp_path, software_path):
        super(MainGUI, self).__init__()
        colors = ["yellow", "green", "red", "blue"]
        self.exp1 = Experiment()
        self.exp1.populate_runs(exp_path)
        self.plugins = Plugins()
        self.n_cams = self.exp1.active_params.m_params.Num_Cam
        self.orig_image = []
        self.current_camera = 0
        self.camera_list = []
        self.software_path = software_path
        self.exp_path = exp_path
        for i in range(self.n_cams):
            self.camera_list.append(CameraWindow(colors[i]))
            self.camera_list[i].name = "Camera " + str(i + 1)
            self.camera_list[i].on_trait_change(self.right_click_process,
                                                "rclicked")
            self.orig_image.append(np.array([], dtype=np.ubyte))

    def right_click_process(self):
        """
        Shows a line in camera color code corresponding to a point on another
        camera's view plane.
        """
        num_points = 2

        for i in range(self.n_cams):
            # get the clicked point
            # (i guess it won't exist in cameras not clicked)
            point = np.array(
                [
                    self.camera_list[i]._click_tool.x,
                    self.camera_list[i]._click_tool.y,
                ],
                dtype="float64",
            )

            if not np.allclose(point, [0.0, 0.0]):
                # mark the point with a circle
                c = str(np.random.rand())[2:]
                self.camera_list[i].rclicked = 0
                self.camera_list[i].drawcross(
                    "right_p_x0" + c,
                    "right_p_y0" + c,
                    point[0],
                    point[1],
                    "cyan",
                    3,
                    marker1="circle",
                )
                # self.camera_list[i]._plot.request_redraw()
                # look for points along epipolars for other cameras
                for j in range(self.n_cams):
                    if i == j:
                        continue
                    pts = optv.epipolar.epipolar_curve(
                        point,
                        self.cals[i],
                        self.cals[j],
                        num_points,
                        self.cpar,
                        self.vpar,
                    )

                    if len(pts) > 1:
                        # for p in xrange(pts.shape[0]-1):
                        #     self.camera_list[j].drawline("right_cl_x",
                        # "right_cl_y",pts[p,0],pts[p,1],\
                        #  pts[p+1,0],pts[p+1,1],color_camera[j])
                        self.camera_list[j].drawline(
                            "right_cl_x" + c,
                            "right_cl_y" + c,
                            pts[0, 0],
                            pts[0, 1],
                            pts[-1, 0],
                            pts[-1, 1],
                            self.camera_list[i].cam_color,
                        )

    def update_plots(self, images, is_float=False):
        print("inside update plots, images changed\n")
        for i in range(len(images)):
            self.camera_list[i].update_image(images[i], is_float)
            self.camera_list[i]._plot.request_redraw()

    # # set_images sets ptv's C module img[] array
    # def set_images(self,images):
    #     for i in range(len(images)):
    #         ptv.py_set_img(images[i],i)
    #
    # def get_images(self,plot_index,images):
    #     for i in plot_index:
    #         ptv.py_get_img(images[i],i)

    def drawcross(self, str_x, str_y, x, y, color1, size1):
        """
        Draws crosses
        """
        for i, cam in enumerate(self.camera_list):
            cam.drawcross(str_x, str_y, x[i], y[i], color1, size1)

    def clear_plots(self, remove_background=True):
        # this function deletes all plotes except basic image plot

        if not remove_background:
            index = "plot0"
        else:
            index = None

        for i in range(len(self.camera_list)):
            plot_list = list(self.camera_list[i]._plot.plots.keys())
            # if not remove_background:
            #   index=None
            if index in plot_list:
                # try:
                plot_list.remove(index)
            # except:
            # pass
            self.camera_list[i]._plot.delplot(*plot_list[0:])
            self.camera_list[i]._plot.tools = []
            self.camera_list[i]._plot.request_redraw()
            for j in range(len(self.camera_list[i]._quiverplots)):
                self.camera_list[i]._plot.remove(
                    self.camera_list[i]._quiverplots[j])
            self.camera_list[i]._quiverplots = []
            self.camera_list[i].right_p_x0 = []
            self.camera_list[i].right_p_y0 = []
            self.camera_list[i].right_p_x1 = []
            self.camera_list[i].right_p_y1 = []

    def _update_thread_plot_changed(self):
        n_cams = len(self.camera_list)

        if self.update_thread_plot and self.tr_thread:
            print("updating plots..\n")
            step = self.tr_thread.track_step

            x0, x1, x2, y0, y1, y2 = (
                self.tr_thread.intx0,
                self.tr_thread.intx1,
                self.tr_thread.intx2,
                self.tr_thread.inty0,
                self.tr_thread.inty1,
                self.tr_thread.inty2,
            )
            for i in range(n_cams):
                self.camera_list[i].drawcross(
                    str(step) + "x0",
                    str(step) + "y0",
                    x0[i],
                    y0[i],
                    "green",
                    2,
                )
                self.camera_list[i].drawcross(
                    str(step) + "x1",
                    str(step) + "y1",
                    x1[i],
                    y1[i],
                    "yellow",
                    2,
                )
                self.camera_list[i].drawcross(
                    str(step) + "x2",
                    str(step) + "y2",
                    x2[i],
                    y2[i],
                    "white",
                    2,
                )
                self.camera_list[i].drawquiver(x0[i], y0[i], x1[i], y1[i],
                                               "orange")
                self.camera_list[i].drawquiver(x1[i], y1[i], x2[i], y2[i],
                                               "white")
            # for j in range (m_tr):
            # str_plt=str(step)+"_"+str(j)
            ##
            # self.camera_list[i].drawline\
            # (str_plt+"vec_x0",str_plt+"vec_y0",x0[i][j],y0[i][j],x1[i][j],y1[i][j],"orange")
            # self.camera_list[i].drawline\
            # (str_plt+"vec_x1",str_plt+"vec_y1",x1[i][j],y1[i][j],x2[i][j],y2[i][j],"white")
            self.load_set_seq_image(step, update_all=False, display_only=True)
            self.camera_list[self.current_camera]._plot.request_redraw()
            time.sleep(0.1)
            self.tr_thread.can_continue = True
            self.update_thread_plot = False

    def load_set_seq_image(self, seq: int, update_all=True, display_only=False):
        """ load and set sequence image

        Args:
            seq (_type_): sequance properties 
            update_all (bool, optional): _description_. Defaults to True.
            display_only (bool, optional): _description_. Defaults to False.
        """
        n_cams = len(self.camera_list)
        if not hasattr(self, "base_name"):
            self.base_name = []
            for i in range(n_cams):
                exec("self.base_name.append" +
                     f"(self.exp1.active_params.m_params.Basename_{i+1}_Seq)")
                print(f' base name in GUI is {self.base_name[i]}')

        # i = seq
        seq_ch = f'{seq:04d}'

        if not update_all:
            j = self.current_camera
            # img_name = self.base_name[j] + seq_ch
            img_name = self.base_name[j].replace('#',seq_ch)
            print(f'Image name in load_set_seq is {img_name}')
            self.load_disp_image(img_name, j, display_only)
        else:
            for j in range(n_cams):
                # img_name = self.base_name[j] + seq_ch
                img_name = self.base_name[j].replace('#',seq_ch)
                print(f'Image name in load_set_seq is {img_name}')
                self.load_disp_image(img_name, j, display_only)

    def load_disp_image(self, img_name: str, j: int, display_only: bool=False):
        """load and display image

        Args:
            img_name (_type_): filename of the image
            j (_type_): integer counter 
            display_only (bool, optional): display only. Defaults to False.
        """
        print(f'Setting image: {img_name}')
        try:
            temp_img = img_as_ubyte(imread(img_name))
        except IOError:
            print("Error reading file, setting zero image")
            h_img = self.exp1.active_params.m_params.imx
            v_img = self.exp1.active_params.m_params.imy
            temp_img = img_as_ubyte(np.zeros((h_img, v_img)))
        if not display_only:
            ptv.py_set_img(temp_img, j)
        if len(temp_img) > 0:
            self.camera_list[j].update_image(temp_img)


def printException():
    import traceback

    print("=" * 50)
    print("Exception:", sys.exc_info()[1])
    print("getcwd()=%s; curdir=%s" % (os.getcwd(), os.curdir))
    print("Traceback:") 
    traceback.print_tb(sys.exc_info()[2])
    print("=" * 50)


# -------------------------------------------------------------
def main():
    """ main ()

    Raises:
        OSError: if software or folder path are missing 
    """
    # Parse inputs:
    software_path = pathlib.Path().absolute()
    print(f"Software path is {software_path}")

    # Path to the experiment
    if len(sys.argv) > 1:
        exp_path = os.path.abspath(sys.argv[1])
    else:
        print(
            "Please provide an experimental directory as an input,            "
            " fallback to a default\n")
        exp_path = software_path.parent / "test_cavity"

    if not os.path.isdir(exp_path):
        raise OSError(f"Wrong experimental directory {exp_path}")
    os.chdir(exp_path)

    try:
        main_gui = MainGUI(exp_path, software_path)
        main_gui.configure_traits()
    except OSError:
        print("something wrong with the software or folder")
        printException()

    os.chdir(software_path)  # get back to the original workdir


if __name__ == "__main__":
    main()
