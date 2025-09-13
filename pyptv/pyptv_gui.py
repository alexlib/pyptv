import os
import sys
import json
import yaml
from pathlib import Path
import numpy as np
from traits.api import HasTraits, Int, Bool, Instance, List, Enum
from traitsui.api import View, Item, ListEditor, Handler, TreeEditor, TreeNode, Separator, VGroup, HGroup, Group, CodeEditor, VSplit
from traits.api import File
from traitsui.api import FileEditor
from traitsui.menu import Action, Menu, MenuBar
from chaco.api import ArrayDataSource, ArrayPlotData, LinearMapper, Plot, gray
from chaco.tools.api import PanTool, ZoomTool
from chaco.tools.image_inspector_tool import ImageInspectorTool
from enable.component_editor import ComponentEditor
from skimage.util import img_as_ubyte
from skimage.io import imread
from skimage.color import rgb2gray
from pyptv.experiment import Experiment, Paramset
from pyptv.quiverplot import QuiverPlot
from pyptv.detection_gui import DetectionGUI
from pyptv.mask_gui import MaskGUI
from pyptv.parameter_gui import Main_Params, Calib_Params, Tracking_Params
from pyptv import __version__, ptv
from optv.epipolar import epipolar_curve
from optv.imgcoord import image_coordinates
from optv.transforms import convert_arr_metric_to_pixel
from pyptv.calibration_gui import CalibrationGUI

"""PyPTV_GUI is the GUI for the OpenPTV (www.openptv.net) written in
Python with Traits, TraitsUI, Numpy, Scipy and Chaco

Copyright (c) 2008-2023, Turbulence Structure Laboratory, Tel Aviv University
The GUI software is distributed under the terms of MIT-like license
http://opensource.org/licenses/MIT

OpenPTV library is distributed under the terms of LGPL license
see http://www.openptv.net for more details.

"""

class FilteredFileBrowserExample(HasTraits):
    """
    An example showing how to filter for specific file types.
    """
    file_path = File()

    view = View(
        Item('file_path',
            label="Select a YAML File",
            editor=FileEditor(filter=['*.yaml','*.yml']),
        ),
        title="YAML File Browser",
        buttons=['OK', 'Cancel'],
        resizable=True
    )

class Clicker(ImageInspectorTool):
    """
    Clicker class handles right mouse click actions from the tree
    and menubar actions
    """

    left_changed = Int(0)
    right_changed = Int(0)
    x, y = 0, 0

    def __init__(self, *args, **kwargs):
        super(Clicker, self).__init__(*args, **kwargs)

    def normal_left_down(self, event):
        """Handles the left mouse button being clicked.
        Fires the **new_value** event with the data (if any) from the event's
        position.
        """
        plot = self.component
        if plot is not None:
            self.x, self.y = plot.map_index((event.x, event.y))
            self.data_value = plot.value.data[self.y, self.x]
            self.last_mouse_position = (event.x, event.y)
            self.left_changed = 1 - self.left_changed
            # print(f"left: x={self.x}, y={self.y}, I={self.data_value}, {self.left_changed}")

    def normal_right_down(self, event):
        plot = self.component
        if plot is not None:
            self.x, self.y = plot.map_index((event.x, event.y))
            self.last_mouse_position = (event.x, event.y)
            self.data_value = plot.value.data[self.y, self.x]
            #  print(f"normal right down: x={self.x}, y={self.y}, I={self.data_value}")
            self.right_changed = 1 - self.right_changed

    # def normal_mouse_move(self, event):
    #     pass


# --------------------------------------------------------------
class CameraWindow(HasTraits):
    """CameraWindow class contains the relevant information and functions for
    a single camera window: image, zoom, pan important members:
    _plot_data  - contains image data to display (used by update_image)
    _plot - instance of Plot class to use with _plot_data
    _click_tool - instance of Clicker tool for the single camera window,
    to handle mouse processing
    """

    _plot = Instance(Plot)
    # _click_tool = Instance(Clicker)
    rclicked = Int(0)

    cam_color = ""
    name = ""
    view = View(Item(name="_plot", editor=ComponentEditor(), show_label=False))

    def __init__(self, color, name):
        """
        Initialization of plot system
        """
        super(HasTraits, self).__init__()
        padd = 25
        self._plot_data = ArrayPlotData()  # we need set_data
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
        self.name = name

    def attach_tools(self):
        """attach_tools(self) contains the relevant tools:
        clicker, pan, zoom"""

        print(f" Attaching clicker to camera {self.name}")
        self._click_tool = Clicker(component=self._img_plot)
        self._click_tool.on_trait_change(self.left_clicked_event, "left_changed")
        self._click_tool.on_trait_change(self.right_clicked_event, "right_changed")
        # self._img_plot.tools.clear()
        self._img_plot.tools.append(self._click_tool)

        pan = PanTool(self._plot, drag_button="middle")
        zoom_tool = ZoomTool(self._plot, tool_mode="box", always_on=False)
        # zoom_tool.max_zoom_out_factor = 1.0  # Disable "bird view" zoom out
        self._img_plot.overlays.append(zoom_tool)
        self._img_plot.tools.append(pan)
        # print(self._img_plot.tools)

    def left_clicked_event(
        self,
    ):  # TODO: why do we need the ClickerTool if we can handle mouse
        # clicks here?
        """left_clicked_event - processes left click mouse
        events and displays coordinate and grey value information
        on the screen
        """
        print(
            f"left click in {self.name} x={self._click_tool.x} pix,y={self._click_tool.y} pix,I={self._click_tool.data_value}"
        )

    def right_clicked_event(self):
        """right mouse button click event flag"""
        # # self._click_tool.right_changed = 1
        print(
            f"right click in {self.name}, x={self._click_tool.x},y={self._click_tool.y}, I={self._click_tool.data_value}, {self.rclicked}"
        )
        self.rclicked = 1

    def create_image(self, image, is_float=False):
        """create_image - displays/updates image in the current camera window
        parameters:
            image - image data
            is_float - if true, displays an image as float array,
            else displays as byte array (B&W or gray)
        example usage:
            create_image(image,is_float=False)
        """
        # print('image shape = ', image.shape, 'is_float =', is_float)
        # if image.ndim > 2:
        #     image = img_as_ubyte(rgb2gray(image))
        #     is_float = False

        if is_float:
            self._plot_data.set_data("imagedata", image.astype(np.float32))
        else:
            self._plot_data.set_data("imagedata", image.astype(np.uint8))

        # if not hasattr(
        #         self,
        #         "img_plot"):  # make a new plot if there is nothing to update
        #     self.img_plot = Instance(ImagePlot)

        self._img_plot = self._plot.img_plot("imagedata", colormap=gray)[0]
        self.attach_tools()

    def update_image(self, image, is_float=False):
        """update_image - displays/updates image in the current camera window
        parameters:
            image - image data
            is_float - if true, displays an image as float array,
            else displays as byte array (B&W or gray)
        example usage:
            update_image(image,is_float=False)
        """

        if is_float:
            self._plot_data.set_data("imagedata", image.astype(np.float32))
        else:
            self._plot_data.set_data("imagedata", image)

        # Seems that update data is already updating the content

        # self._plot.img_plot("imagedata", colormap=gray)[0]
        # self._plot.img_plot("imagedata", colormap=gray)
        self._plot.request_redraw()

    def drawcross(self, str_x, str_y, x, y, color, mrk_size, marker="plus"):
        """drawcross draws crosses at a given location (x,y) using color
        and marker in the current camera window parameters:
            str_x - label for x coordinates
            str_y - label for y coordinates
            x - array of x coordinates
            y - array of y coordinates
            mrk_size - marker size
            marker - type of marker, e.g "plus","circle"
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
            color=color,
            marker=marker,
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
            # Seems to be incorrect use of .add
            # self._plot.add(quiverplot)
            self._plot.overlays.append(quiverplot)

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


# ------------------------------------------
# Message Window System for capturing print statements
# ------------------------------------------

class TreeMenuHandler(Handler):
    """TreeMenuHandler handles the menu actions and tree node actions"""

    def configure_main_par(self, editor, object):
        experiment = editor.get_parent(object)
        print("Configure main parameters via ParameterManager")
        
        # Create Main_Params GUI with current experiment
        main_params_gui = Main_Params(experiment=experiment)
        if main_params_gui is None:
            raise RuntimeError("Failed to create Main_Params GUI (main_params_gui is None)")
        
        # Show the GUI in modal dialog
        result = main_params_gui.edit_traits(view='Main_Params_View', kind='livemodal')
        
        if result:
            print("Main parameters updated and saved to YAML")
        else:
            print("Main parameters dialog cancelled")

    def configure_cal_par(self, editor, object):
        experiment = editor.get_parent(object)
        print("Configure calibration parameters via ParameterManager")
        
        # Create Calib_Params GUI with current experiment
        calib_params_gui = Calib_Params(experiment=experiment)
        
        # Show the GUI in modal dialog
        result = calib_params_gui.edit_traits(view='Calib_Params_View', kind='livemodal')
        
        if result:
            print("Calibration parameters updated and saved to YAML")
        else:
            print("Calibration parameters dialog cancelled")

    def configure_track_par(self, editor, object):
        experiment = editor.get_parent(object)
        print("Configure tracking parameters via ParameterManager")
        
        # Create Tracking_Params GUI with current experiment
        tracking_params_gui = Tracking_Params(experiment=experiment)
        
        # Show the GUI in modal dialog
        result = tracking_params_gui.edit_traits(view='Tracking_Params_View', kind='livemodal')
        
        if result:
            print("Tracking parameters updated and saved to YAML")
        else:
            print("Tracking parameters dialog cancelled")

    def set_active(self, editor, object):
        """sets a set of parameters as active"""
        experiment = editor.get_parent(object)
        paramset = object
        experiment.set_active(paramset)
        
        # Invalidate parameter cache since we switched parameter sets
        # The main GUI will need to get a reference to invalidate its cache
        # This could be done through the experiment or by adding a callback

    def copy_set_params(self, editor, object):
        experiment = editor.get_parent(object)
        paramset = object
        print("Copying set of parameters")
        print(f"paramset is {paramset.name}")

        # Find the next available run number above the largest one
        parent_dir = paramset.yaml_path.parent
        existing_yamls = list(parent_dir.glob("parameters_*.yaml"))
        numbers = [
            int(yaml_file.stem.split("_")[-1]) for yaml_file in existing_yamls
            if yaml_file.stem.split("_")[-1].isdigit()
        ]
        next_num = max(numbers, default=0) + 1
        new_name = f"{paramset.name}_{next_num}"
        new_yaml_path = parent_dir / f"parameters_{new_name}.yaml"

        print(f"New parameter set: {new_name}, {new_yaml_path}")
        
        # Copy YAML file
        import shutil
        shutil.copy(paramset.yaml_path, new_yaml_path)
        print(f"Copied {paramset.yaml_path} to {new_yaml_path}")
            
        experiment.addParamset(new_name, new_yaml_path)

    def rename_set_params(self, editor, object):
        print("Warning: This method is not implemented.")
        print("Please open a folder, copy/paste the parameters directory, and rename it manually.")

    def delete_set_params(self, editor, object):
        """delete_set_params deletes the node and the YAML file of parameters"""
        experiment = editor.get_parent(object)
        paramset = object
        print(f"Deleting parameter set: {paramset.name}")
        
        # Use the experiment's delete method which handles YAML files and validation
        try:
            experiment.delete_paramset(paramset)
            
            # The tree view should automatically update when the paramsets list changes
            # Force a trait change event to ensure the GUI updates
            experiment.trait_set(paramsets=experiment.paramsets)
            
            print(f"Successfully deleted parameter set: {paramset.name}")
        except ValueError as e:
            # Handle case where we try to delete the active parameter set
            print(f"Cannot delete parameter set: {e}")
        except Exception as e:
            print(f"Error deleting parameter set: {e}")

    # ------------------------------------------
    # Menubar actions
    # ------------------------------------------
    def new_action(self, info):
        print("not implemented")

    def open_action(self, info):

        filtered_browser_instance = FilteredFileBrowserExample()
        filtered_browser_instance.configure_traits()
        if filtered_browser_instance.file_path:
            print(f"\nYou selected the YAML file: {filtered_browser_instance.file_path}")
            yaml_path = Path(filtered_browser_instance.file_path)
            if yaml_path.is_file() and yaml_path.suffix in {".yaml", ".yml"}:
                print(f"Initializing MainGUI with selected YAML: {yaml_path}")
                os.chdir(yaml_path.parent)  # Change to the directory of the YAML file
                main_gui = MainGUI(yaml_path)
                main_gui.configure_traits()
            else:
                print("\nNo file was selected.")


    def exit_action(self, info):
        print("not implemented")

    def saveas_action(self, info):
        print("not implemented")

    def init_action(self, info):
        """init_action - initializes the system using ParameterManager"""
        mainGui = info.object       
        
        if mainGui.exp1.active_params is None:
            print("Warning: No active parameter set found, setting to default.")
            mainGui.exp1.set_active(0)


        ptv_params = mainGui.get_parameter('ptv')
    
        
        if ptv_params.get('splitter', False):
            print("Using Splitter mode")
            imname = ptv_params['img_name'][0]
            if Path(imname).exists():
                temp_img = imread(imname)
                if temp_img.ndim > 2:
                    temp_img = rgb2gray(temp_img)                
                splitted_images = ptv.image_split(temp_img)
                for i in range(len(mainGui.camera_list)):
                    mainGui.orig_images[i] = img_as_ubyte(splitted_images[i])
        else:
            for i in range(len(mainGui.camera_list)):
                imname = ptv_params['img_name'][i]
                if Path(imname).exists():
                    print(f"Reading image {imname}")
                    im = imread(imname)
                    if im.ndim > 2:
                        im = rgb2gray(im)
                else:
                    print(f"Image {imname} does not exist, setting zero image")
                    h_img = ptv_params['imx']
                    v_img = ptv_params['imy']
                    im = np.zeros((v_img, h_img), dtype=np.uint8)
                    
                mainGui.orig_images[i] = img_as_ubyte(im)

        
        # Reload YAML and Cython
        (mainGui.cpar, 
         mainGui.spar, 
         mainGui.vpar, 
         mainGui.track_par, 
         mainGui.tpar, 
         mainGui.cals, 
         mainGui.epar
         ) = ptv.py_start_proc_c(mainGui.exp1.pm)
        

        # Centralized: get target_filenames from ParameterManager
        mainGui.target_filenames = mainGui.exp1.pm.get_target_filenames()

            

        mainGui.clear_plots()
        print("Init action")
        mainGui.create_plots(mainGui.orig_images, is_float=False)

        # Initialize Cython parameter objects on demand when needed for processing
        # The parameter data is now managed centrally by ParameterManager
        # Individual functions can call py_start_proc_c when they need C objects
        
        mainGui.pass_init = True
        print("Read all the parameters and calibrations successfully")

    def draw_mask_action(self, info):
        """drawing masks GUI"""
        print("Opening drawing mask GUI")
        info.object.pass_init = False
        print("Active parameters set")
        print(info.object.exp1.active_params.yaml_path)
        mask_gui = MaskGUI(info.object.exp1)
        mask_gui.configure_traits()

    def highpass_action(self, info):
        """highpass_action - calls ptv.py_pre_processing_c()"""
        mainGui = info.object
        ptv_params = mainGui.get_parameter('ptv')
        
        # Check invert setting
        if ptv_params.get('inverse', False):
            print("Invert image")
            for i, im in enumerate(mainGui.orig_images):
                mainGui.orig_images[i] = ptv.negative(im)

        # Check mask flag
        # masking_params = mainGui.get_parameter('masking')
        masking_params = mainGui.get_parameter('masking') or {}
        if masking_params.get('mask_flag', False):
            print("Subtracting mask")
            try:
                for i, im in enumerate(mainGui.orig_images):
                    background_name = masking_params['mask_base_name'].replace("#", str(i))
                    print(f"Subtracting {background_name}")
                    background = imread(background_name)
                    mainGui.orig_images[i] = np.clip(
                        mainGui.orig_images[i] - background, 0, 255
                    ).astype(np.uint8)
            except ValueError as exc:
                raise ValueError("Failed subtracting mask") from exc

        print("highpass started")
        mainGui.orig_images = ptv.py_pre_processing_c(
            mainGui.num_cams,
            mainGui.orig_images, 
            ptv_params
        )
        mainGui.update_plots(mainGui.orig_images)
        print("highpass finished")

    def img_coord_action(self, info):
        """img_coord_action - runs detection function"""
        mainGui = info.object
    
        
        ptv_params = mainGui.get_parameter('ptv')
        targ_rec_params = mainGui.get_parameter('targ_rec')
        
        # Format target_params correctly for _populate_tpar
        target_params = {'targ_rec': targ_rec_params}

        print("Start detection")
        (
            mainGui.detections,
            mainGui.corrected,
        ) = ptv.py_detection_proc_c(
            mainGui.num_cams,
            mainGui.orig_images,
            ptv_params,
            target_params,
        )
        print("Detection finished")
        x = [[i.pos()[0] for i in row] for row in mainGui.detections]
        y = [[i.pos()[1] for i in row] for row in mainGui.detections]
        mainGui.drawcross_in_all_cams("x", "y", x, y, "blue", 3)

    def _clean_correspondences(self, tmp):
        """Clean correspondences array"""
        x1, y1 = [], []
        for x in tmp:
            tmp = x[(x != -999).any(axis=1)]
            x1.append(tmp[:, 0])
            y1.append(tmp[:, 1])
        return x1, y1

    def corresp_action(self, info):
        """corresp_action calls ptv.py_correspondences_proc_c()"""
        mainGui = info.object
        
        print("correspondence proc started")
        (
            mainGui.sorted_pos,
            mainGui.sorted_corresp,
            mainGui.num_targs,
        ) = ptv.py_correspondences_proc_c(mainGui)

        names = ["pair", "tripl", "quad"]
        use_colors = ["yellow", "green", "red"]

        if len(mainGui.camera_list) > 1 and len(mainGui.sorted_pos) > 0:
            for i, subset in enumerate(reversed(mainGui.sorted_pos)):
                x, y = self._clean_correspondences(subset)
                mainGui.drawcross_in_all_cams(
                    names[i] + "_x", names[i] + "_y", x, y, use_colors[i], 3
                )

    def calib_action(self, info):
        """calib_action - initializes calibration GUI"""
        print("Starting calibration dialog")
        info.object.pass_init = False
        print("Active parameters set")
        print(info.object.exp1.active_params.yaml_path)
        calib_gui = CalibrationGUI(info.object.exp1.active_params.yaml_path)
        calib_gui.configure_traits()

    def detection_gui_action(self, info):
        """activating detection GUI"""
        print("Starting detection GUI dialog")
        info.object.pass_init = False
        print("Active parameters set")
        print(info.object.exp1.active_params.yaml_path)
        detection_gui = DetectionGUI(info.object.exp_path)
        detection_gui.configure_traits()

    def sequence_action(self, info):
        """sequence action - implements binding to C sequence function"""
        mainGui = info.object

        
        extern_sequence = mainGui.plugins.sequence_alg
        if extern_sequence != "default":
            ptv.run_sequence_plugin(mainGui)
        else:
            ptv.py_sequence_loop(mainGui)

    def track_no_disp_action(self, info):
        """track_no_disp_action uses ptv.py_trackcorr_loop(..) binding"""
        import contextlib
        import io
        mainGui = info.object
        
        extern_tracker = mainGui.plugins.track_alg
        if extern_tracker != "default":
            # If plugin is a batch script, run as subprocess and capture output
            # plugin_script = getattr(mainGui.plugins, 'tracking_plugin_script', None)
            # if plugin_script:
            #     cmd = [sys.executable, plugin_script]  # Add args as needed
            #     self.run_subprocess_and_capture(cmd, mainGui, description="Tracking plugin")
            # else:
            ptv.run_tracking_plugin(mainGui)
            print("After plugin tracker")
        else:
            print("Using default liboptv tracker")
            mainGui.tracker = ptv.py_trackcorr_init(mainGui)
            mainGui.tracker.full_forward()
            print("tracking without display finished")

    def track_disp_action(self, info):
        """tracking with display - not implemented"""
        info.object.clear_plots(remove_background=False)

    def track_back_action(self, info):
        """tracking back action"""
        mainGui = info.object
        print("Starting back tracking")
        if hasattr(mainGui, 'tracker') and mainGui.tracker is not None:
            mainGui.tracker.full_backward()
        else:
            print("No tracker initialized. Please run forward tracking first.")

    def three_d_positions(self, info):
        """Extracts and saves 3D positions from the list of correspondences"""
        
        ptv.py_determination_proc_c(
            info.object.num_cams,
            info.object.sorted_pos,
            info.object.sorted_corresp,
            info.object.corrected,
            info.object.cpar,
            info.object.vpar,
            info.object.cals,
        )

    def detect_part_track(self, info):
        """track detected particles"""
        info.object.clear_plots(remove_background=False)
        
        # Get sequence parameters from ParameterManager
        seq_params = info.object.get_parameter('sequence')
        seq_first = seq_params['first']
        seq_last = seq_params['last']
        base_names = seq_params['base_name']
        short_base_names = info.object.target_filenames

        info.object.overlay_set_images(base_names, seq_first, seq_last)
        
        print("Starting detect_part_track")
        x1_a, x2_a, y1_a, y2_a = [], [], [], []
        for i in range(info.object.num_cams):
            x1_a.append([])
            x2_a.append([])
            y1_a.append([])
            y2_a.append([])

        for i_cam in range(info.object.num_cams):
            for i_seq in range(seq_first, seq_last + 1):
                intx_green, inty_green = [], []
                intx_blue, inty_blue = [], []

                # print('Inside detected particles plot', short_base_names[i_cam])

                targets = ptv.read_targets(short_base_names[i_cam], i_seq)

                for t in targets:
                    if t.tnr() > -1:
                        intx_green.append(t.pos()[0])
                        inty_green.append(t.pos()[1])
                    else:
                        intx_blue.append(t.pos()[0])
                        inty_blue.append(t.pos()[1])

                x1_a[i_cam] = x1_a[i_cam] + intx_green
                x2_a[i_cam] = x2_a[i_cam] + intx_blue
                y1_a[i_cam] = y1_a[i_cam] + inty_green
                y2_a[i_cam] = y2_a[i_cam] + inty_blue

        for i_cam in range(info.object.num_cams):
            info.object.camera_list[i_cam].drawcross(
                "x_tr_gr", "y_tr_gr", x1_a[i_cam], y1_a[i_cam], "green", 3
            )
            info.object.camera_list[i_cam].drawcross(
                "x_tr_bl", "y_tr_bl", x2_a[i_cam], y2_a[i_cam], "blue", 2
            )
            info.object.camera_list[i_cam]._plot.request_redraw()

        print("Finished detect_part_track")

    def traject_action_flowtracks(self, info):
        """Shows trajectories reading and organizing by flowtracks (calls shared utility)."""
        info.object.clear_plots(remove_background=False)

        # Compute trajectories using flowtracks utility
        from pyptv.flowtracks_utils import compute_flowtracks_trajectories_from_guiobj
        results = compute_flowtracks_trajectories_from_guiobj(info.object)
        
        # Draw trajectories on camera views
        for i_cam in range(info.object.num_cams):
            info.object.camera_list[i_cam].drawcross(
                "heads_x", "heads_y", results['heads_x'][i_cam], results['heads_y'][i_cam], "red", 3
            )
            info.object.camera_list[i_cam].drawcross(
                "tails_x", "tails_y", results['tails_x'][i_cam], results['tails_y'][i_cam], "green", 2
            )
            info.object.camera_list[i_cam].drawcross(
                "ends_x", "ends_y", results['ends_x'][i_cam], results['ends_y'][i_cam], "orange", 3
            )

    def plugin_action(self, info):
        """Configure plugins by using GUI"""
        info.object.plugins.read()
        result = info.object.plugins.configure_traits()
        
        # Save plugin selections back to parameters if user clicked OK
        if result:
            info.object.plugins.save()
            print("Plugin configuration saved to parameters")

    def ptv_is_to_paraview(self, info):
        """Button that runs the ptv_is.# conversion to Paraview"""
        print("Saving trajectories for Paraview")
        info.object.clear_plots(remove_background=False)
        
        seq_params = info.object.get_parameter('sequence')
        seq_first = seq_params['first']
        info.object.load_set_seq_image(seq_first, display_only=True)

        import pandas as pd
        from flowtracks.io import trajectories_ptvis

        dataset = trajectories_ptvis("res/ptv_is.%d", xuap=False)

        dataframes = []
        for traj in dataset:
            dataframes.append(
                pd.DataFrame.from_records(
                    traj, columns=["x", "y", "z", "dx", "dy", "dz", "frame", "particle"]
                )
            )

        df = pd.concat(dataframes, ignore_index=True)
        df["particle"] = df["particle"].astype(np.int32)
        df["frame"] = df["frame"].astype(np.int32)
        df.reset_index(inplace=True, drop=True)
        print(df.head())

        df_grouped = df.reset_index().groupby("frame")
        for index, group in df_grouped:
            group.to_csv(
                f"./res/ptv_{index:05d}.txt",
                mode="w",
                columns=["particle", "x", "y", "z", "dx", "dy", "dz"],
                index=False,
            )

        print("Saving trajectories to Paraview finished")


# ----------------------------------------------------------------
# Actions associated with right mouse button clicks (treeeditor)
# ---------------------------------------------------------------
ConfigMainParams = Action(
    name="Main parameters", action="handler.configure_main_par(editor,object)"
)
ConfigCalibParams = Action(
    name="Calibration parameters",
    action="handler.configure_cal_par(editor,object)",
)
ConfigTrackParams = Action(
    name="Tracking parameters",
    action="handler.configure_track_par(editor,object)",
)
SetAsDefault = Action(name="Set as active", action="handler.set_active(editor,object)")
CopySetParams = Action(
    name="Copy set of parameters",
    action="handler.copy_set_params(editor,object)",
)
RenameSetParams = Action(
    name="Rename run", action="handler.rename_set_params(editor,object)"
)
DeleteSetParams = Action(
    name="Delete run", action="handler.delete_set_params(editor,object)"
)

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
    Menu(Action(name="Init / Reload", action="init_action"), name="Start"),
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
            action="three_d_positions",
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
        Action(
            name="Tracking backwards",
            action="track_back_action",
            enabled_when="pass_init",
        ),
        Action(
            name="Show trajectories",
            action="traject_action_flowtracks",
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
    Menu(
        Action(name="Detection GUI demo", action="detection_gui_action"),
        name="Detection demo",
    ),
    Menu(
        Action(
            name="Draw mask",
            action="draw_mask_action",
            enabled_when="pass_init",
        ),
        name="Drawing mask",
    ),
)

# ----------------------------------------
# tree editor for the Experiment() class
#
tree_editor_exp = TreeEditor(
    nodes=[
        TreeNode(
            node_for=[Experiment],
            auto_open=True,
            children="",
            label="=Experiment",
        ),
        TreeNode(
            node_for=[Experiment],
            auto_open=True,
            children="paramsets",
            label="=Parameters",
            add=[Paramset],
            menu=Menu(CopySetParams),
        ),
        TreeNode(
            node_for=[Paramset],
            auto_open=True,
            children="",
            label="name",
            menu=Menu(
                CopySetParams,
                DeleteSetParams,
                Separator(),
                ConfigMainParams,
                ConfigCalibParams,
                ConfigTrackParams,
                Separator(),
                SetAsDefault,
            ),
        ),
    ],
    editable=False,
)

# -------------------------------------------------------------------------
class Plugins(HasTraits):
    track_alg = Enum('default')
    sequence_alg = Enum('default')
    
    view = View(
        Item(name="track_alg", label="Tracking:"),
        Item(name="sequence_alg", label="Sequence:"),
        buttons=["OK"],
        title="Plugins",
    )

    def __init__(self, experiment=None):
        self.experiment = experiment
        self.read()

    def read(self):
        """Read plugin configuration from experiment parameters (YAML) with fallback to plugins.json"""
        if self.experiment is not None:
            # Primary source: YAML parameters
            plugins_params = self.experiment.get_parameter('plugins')
            if plugins_params is not None:
                try:
                    track_options = plugins_params.get('available_tracking', ['default'])
                    seq_options = plugins_params.get('available_sequence', ['default'])
                    
                    self.add_trait('track_alg', Enum(*track_options))
                    self.add_trait('sequence_alg', Enum(*seq_options))
                    
                    # Set selected algorithms from YAML
                    self.track_alg = plugins_params.get('selected_tracking', track_options[0])
                    self.sequence_alg = plugins_params.get('selected_sequence', seq_options[0])
                    
                    print(f"Loaded plugins from YAML: tracking={self.track_alg}, sequence={self.sequence_alg}")
                    return
                    
                except Exception as e:
                    print(f"Error reading plugins from YAML: {e}")
        
        # Fallback to plugins.json for backward compatibility
        self._read_from_json()
    
    def _read_from_json(self):
        """Fallback method to read from plugins.json"""
        config_file = Path.cwd() / "plugins.json"
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                track_options = config.get('tracking', ['default'])
                seq_options = config.get('sequence', ['default'])
                
                self.add_trait('track_alg', Enum(*track_options))
                self.add_trait('sequence_alg', Enum(*seq_options))
                
                self.track_alg = track_options[0]
                self.sequence_alg = seq_options[0]
                
                print(f"Loaded plugins from plugins.json: tracking={self.track_alg}, sequence={self.sequence_alg}")
                
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error reading plugins.json: {e}")
                self._set_defaults()
        else:
            print("No plugins.json found, using defaults")
            self._set_defaults()
    
    def save(self):
        """Save plugin selections back to experiment parameters"""
        if self.experiment is not None:
            plugins_params = self.experiment.get_parameter('plugins', {})
            plugins_params['selected_tracking'] = self.track_alg
            plugins_params['selected_sequence'] = self.sequence_alg
            
            # Update the parameter manager
            self.experiment.pm.parameters['plugins'] = plugins_params
            print(f"Saved plugin selections: tracking={self.track_alg}, sequence={self.sequence_alg}")
    
    def _set_defaults(self):
        self.add_trait('track_alg', Enum('default'))
        self.add_trait('sequence_alg', Enum('default'))
        self.track_alg = 'default'
        self.sequence_alg = 'default'
        

# ----------------------------------------------
class MainGUI(HasTraits):
    """MainGUI is the main class under which the Model-View-Control
    (MVC) model is defined"""

    camera_list = List(Instance(CameraWindow))
    pass_init = Bool(False)
    update_thread_plot = Bool(False)
    selected = Instance(CameraWindow)
    exp1 = Instance(Experiment)
    yaml_file = Path()
    exp_path = Path()
    num_cams = Int(0)
    orig_names = List()
    orig_images = List()
    
    # Defines GUI view --------------------------
    view = View(
        VSplit(
            VGroup(
                HGroup(
                    Item(
                        name="exp1",
                        editor=tree_editor_exp,
                        show_label=False,
                        width=-400,
                        resizable=False,
                    ),
                    Item(
                        "camera_list",
                        style="custom",
                        editor=ListEditor(
                            use_notebook=True,
                            deletable=False,
                            dock_style="tab",
                            page_name=".name",
                            selected="selected",
                        ),
                        show_label=False,
                    ),
                    show_left=False,
                ),
            ),
            # Removed message_window from view
        ),
        title="pyPTV" + __version__,
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
    def __init__(self, yaml_file: Path, experiment: Experiment):
        super(MainGUI, self).__init__()
        if not yaml_file.is_file() or yaml_file.suffix not in {".yaml", ".yml"}:
            raise ValueError("yaml_file must be a valid YAML file")
        self.exp_path = yaml_file.parent
        self.exp1 = experiment
        self.plugins = Plugins(experiment=self.exp1)

        # Set the active paramset to the provided YAML file
        # for idx, paramset in enumerate(self.exp1.paramsets):
        #     if hasattr(paramset, 'yaml_path') and Path(paramset.yaml_path).resolve() == yaml_file.resolve():
        #         self.exp1.set_active(idx)
        #         print(f"Set active parameter set to: {paramset.name}")
        #         break

        # Get configuration from Experiment's ParameterManager
        print(f"Initializing MainGUI with parameters from {yaml_file}")
        ptv_params = self.exp1.get_parameter('ptv')
        if ptv_params is None:
            raise ValueError("PTV parameters not found in the provided YAML file")

        
        self.num_cams = self.exp1.get_n_cam()
        self.orig_names = ptv_params['img_name']
        self.orig_images = [
                img_as_ubyte(np.zeros((ptv_params['imy'], ptv_params['imx'])))
                for _ in range(self.num_cams)
            ]
        
        self.current_camera = 0
        # Restore the four colors for camera windows
        colors = ["yellow", "green", "red", "blue"]
        # If more than 4 cameras, repeat colors as needed
        cam_colors = (colors * ((self.num_cams + 3) // 4))[:self.num_cams]
        self.camera_list = [
            CameraWindow(cam_colors[i], f"Camera {i + 1}") for i in range(self.num_cams)
        ]
             
        for i in range(self.num_cams):
            self.camera_list[i].on_trait_change(
                self.right_click_process, 
                "rclicked")
        
        # Ensure the active parameter set is the first in the paramsets list for correct tree display
        if hasattr(self.exp1, "active_params") and self.exp1.active_params is not None:
            active_yaml = Path(self.exp1.active_params.yaml_path)
            # Find the index of the active paramset
            idx = next(
                (i for i, p in enumerate(self.exp1.paramsets)
                 if hasattr(p, "yaml_path") and Path(p.yaml_path).resolve() == active_yaml.resolve()),
                None
            )
            if idx is not None and idx != 0:
                # Move active paramset to the front
                self.exp1.paramsets.insert(0, self.exp1.paramsets.pop(idx))
                self.exp1.set_active(0)

    def get_parameter(self, key):
        """Delegate parameter access to experiment"""
        return self.exp1.get_parameter(key)
        
    def right_click_process(self):
        """Shows a line in camera color code corresponding to a point on another camera's view plane"""
        num_points = 2

        if hasattr(self, "sorted_pos") and self.sorted_pos is not None:
            plot_epipolar = True
        else:
            plot_epipolar = False

        if plot_epipolar:
            i = self.current_camera
            point = np.array(
                [
                    self.camera_list[i]._click_tool.x,
                    self.camera_list[i]._click_tool.y,
                ],
                dtype="float64",
            )

            # find closest point in the sorted_pos
            for pos_type in self.sorted_pos:  # quadruplet, triplet, pair
                distances = np.linalg.norm(pos_type[i] - point, axis=1)
                # next test prevents failure with empty quadruplets or triplets
                if len(distances) > 0 and np.min(distances) < 5:
                    point = pos_type[i][np.argmin(distances)]

            if not np.allclose(point, [0.0, 0.0]):
                # mark the point with a circle
                c = str(np.random.rand())[2:]
                self.camera_list[i].drawcross(
                    "right_p_x0" + c,
                    "right_p_y0" + c,
                    point[0],
                    point[1],
                    "cyan",
                    3,
                    marker="circle",
                )

                # look for points along epipolars for other cameras
                for j in range(self.num_cams):
                    if i == j:
                        continue
                    pts = epipolar_curve(
                        point,
                        self.cals[i],
                        self.cals[j],
                        num_points,
                        self.cpar,
                        self.vpar,
                    )

                    if len(pts) > 1:
                        self.camera_list[j].drawline(
                            "right_cl_x" + c,
                            "right_cl_y" + c,
                            pts[0, 0],
                            pts[0, 1],
                            pts[-1, 0],
                            pts[-1, 1],
                            self.camera_list[i].cam_color,
                        )

                self.camera_list[i].rclicked = 0

    def create_plots(self, images, is_float=False) -> None:
        """Create plots with images

        Args:
            images (_type_): images to update
            is_float (bool, optional): _description_. Defaults to False.
        """
        print("inside create plots, images changed\n")
        for i in range(self.num_cams):
            self.camera_list[i].create_image(images[i], is_float)
            self.camera_list[i]._plot.request_redraw()

    def update_plots(self, images, is_float=False) -> None:
        """Update plots with new images

        Args:
            images (_type_): images to update
            is_float (bool, optional): _description_. Defaults to False.
        """
        print("Update plots, images changed\n")
        for cam, image in zip(self.camera_list, images):
            cam.update_image(image, is_float)

    def drawcross_in_all_cams(self, str_x, str_y, x, y, color1, size1, marker="plus"):
        """
        Draws crosses in all cameras
        """
        for i, cam in enumerate(self.camera_list):
            cam.drawcross(str_x, str_y, x[i], y[i], color1, size1, marker=marker)

    def clear_plots(self, remove_background=True):
        # this function deletes all plots except basic image plot

        if not remove_background:
            index = "plot0" 
        else:
            index = None

        for i in range(self.num_cams):
            plot_list = list(self.camera_list[i]._plot.plots.keys())
            if index in plot_list:
                plot_list.remove(index)
            self.camera_list[i]._plot.delplot(*plot_list[0:])
            self.camera_list[i]._plot.tools = []
            self.camera_list[i]._plot.request_redraw()
            for j in range(len(self.camera_list[i]._quiverplots)):
                self.camera_list[i]._plot.remove(self.camera_list[i]._quiverplots[j])
            self.camera_list[i]._quiverplots = []
            self.camera_list[i].right_p_x0 = []
            self.camera_list[i].right_p_y0 = []
            self.camera_list[i].right_p_x1 = []
            self.camera_list[i].right_p_y1 = []

    def overlay_set_images(self, base_names: List, seq_first: int, seq_last: int):
        """Overlay set of images"""
        ptv_params = self.get_parameter('ptv')
        h_img = ptv_params['imx'] # type: ignore
        v_img = ptv_params['imy'] # type: ignore

        if ptv_params.get('splitter', False):
            temp_img = img_as_ubyte(np.zeros((v_img*2, h_img*2)))
            for seq in range(seq_first, seq_last):
                imname = Path(base_names[0] % seq) # type: ignore
                if imname.exists():
                    _ = imread(imname)
                    if _.ndim > 2:
                        _ = rgb2gray(_)
                    temp_img = np.max([temp_img, _], axis=0)

            list_of_images = ptv.image_split(temp_img)
            for cam_id in range(self.num_cams):
                self.camera_list[cam_id].update_image(img_as_ubyte(list_of_images[cam_id])) # type: ignore
        else: 
            for cam_id in range(self.num_cams):
                temp_img = img_as_ubyte(np.zeros((v_img, h_img)))
                for seq in range(seq_first, seq_last):
                    base_name = base_names[cam_id]
                    if base_name in ("--", "---", None):
                        continue
                    if "%" in base_name:
                        imname = Path(base_name % seq)
                    else:
                        imname = Path(base_name)
                    if imname.exists():
                        _ = imread(imname)
                        if _.ndim > 2:
                            _ = rgb2gray(_)
                        temp_img = np.max([temp_img, _], axis=0)
                self.camera_list[cam_id].update_image(temp_img) # type: ignore

    def load_disp_image(self, img_name: str, j: int, display_only: bool = False):
        """Load and display single image"""
        try:
            temp_img = imread(img_name)
            if temp_img.ndim > 2:
                temp_img = rgb2gray(temp_img)
            temp_img = img_as_ubyte(temp_img)
        except IOError:
            print("Error reading file, setting zero image")
            ptv_params = self.get_parameter('ptv')
            h_img = ptv_params['imx']
            v_img = ptv_params['imy']
            temp_img = img_as_ubyte(np.zeros((v_img, h_img)))

        if len(temp_img) > 0:
            self.camera_list[j].update_image(temp_img)

    def load_set_seq_image(self, seq_num: int, display_only: bool = False):
        """Load and display sequence image for a specific sequence number"""
        seq_params = self.get_parameter('sequence')
        if seq_params is None:
            print("No sequence parameters found")
            return
            
        base_names = seq_params['base_name']
        ptv_params = self.get_parameter('ptv')
        
        if ptv_params.get('splitter', False):
            # Splitter mode - load one image and split it
            imname = base_names[0] % seq_num
            if Path(imname).exists():
                temp_img = imread(imname)
                if temp_img.ndim > 2:
                    temp_img = rgb2gray(temp_img)
                splitted_images = ptv.image_split(temp_img)
                for i in range(self.num_cams):
                    self.camera_list[i].update_image(img_as_ubyte(splitted_images[i]))
            else:
                print(f"Image {imname} does not exist")
        else:
            # Normal mode - load separate images for each camera
            for i in range(self.num_cams):
                imname = base_names[i] % seq_num
                self.load_disp_image(imname, i, display_only)

    def save_parameters(self):
        """Save current parameters to YAML"""
        self.exp1.save_parameters()
        print("Parameters saved")


def printException():
    import traceback

    print("=" * 50)
    print("Exception:", sys.exc_info()[1])
    print(f"{Path.cwd()}")
    print("Traceback:")
    traceback.print_tb(sys.exc_info()[2])
    print("=" * 50)


def main():
    """main function"""
    software_path = Path.cwd().resolve()
    print(f"Running PyPTV from {software_path}")

    yaml_file = None
    exp_path = None
    exp = None

    if len(sys.argv) == 2:
        arg_path = Path(sys.argv[1]).resolve()
        # first option - suppy YAML file path and this would be your experiment
        # we will also see what are additional parameter sets exist and 
        # initialize the Experiment() object
        if arg_path.is_file() and arg_path.suffix in {".yaml", ".yml"}:
            yaml_file = arg_path
            print(f"YAML parameter file provided: {yaml_file}")
            from pyptv.parameter_manager import ParameterManager
            pm = ParameterManager()
            pm.from_yaml(yaml_file)

            # prepare additional yaml files for other runs if not existing
            print(f"Initialize  Experiment from {yaml_file.parent}")
            exp_path = yaml_file.parent
            exp = Experiment(pm=pm) # ensures pm is an active parameter set
            exp.populate_runs(exp_path)
            # exp.pm.from_yaml(yaml_file)
        elif arg_path.is_dir(): # second option - supply directory
            exp = Experiment()
            exp.populate_runs(arg_path)
            yaml_file = exp.active_params.yaml_path
            # exp.pm.from_yaml(yaml_file)
            print(f"Using top YAML file found: {yaml_file}")
        else:
            raise OSError(f"Argument must be a directory or YAML file, got: {arg_path}")
    else:
        # Fallback to default test directory
        exp_path = software_path / "tests" / "test_cavity"
        exp = Experiment()
        exp.populate_runs(exp_path)
        yaml_file = exp.active_params.yaml_path
        # exp.pm.from_yaml(yaml_file)
        print(f"Without inputs, PyPTV uses default case {yaml_file}")
        print("Tip: in PyPTV use File -> Open to select another YAML file")

    if not yaml_file or not yaml_file.exists():
        raise OSError(f"YAML parameter file does not exist: {yaml_file}")

    print(f"Changing directory to the working folder {yaml_file.parent}")

    print(f"YAML file to be used in GUI: {yaml_file}")
    # Optional: Quality check on the YAML file
    try:
        with open(yaml_file) as f:
            ydata = yaml.safe_load(f)
            print('\n--- YAML OUTPUT ---')
            print(yaml.dump(ydata, default_flow_style=False, sort_keys=False))

        # print('\n--- ParameterManager parameters ---')
        # print(dict(exp.pm.parameters))
    except Exception as exc:
        print(f"Error reading or validating YAML file: {exc}")
    

    try:
        os.chdir(yaml_file.parent)
        main_gui = MainGUI(yaml_file, exp)
        main_gui.configure_traits()
    except OSError:
        print("Something wrong with the software or folder")
        printException()
    finally:
        print(f"Changing back to the original {software_path}")
        os.chdir(software_path)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("An error occurred in the main function:")
        print(e)
        printException()
        sys.exit(1)