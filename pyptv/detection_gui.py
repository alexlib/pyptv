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

    status_text = Str("Ready - Load parameters and image to start")
    yaml_path = Str("tests/test_cavity/parameters_Run1.yaml", label="YAML parameters file")
    button_load_params = Button(label="Load Parameters")
    image_name = Str("cal/cam1.tif", label="Image file name")
    button_load_image = Button(label="Load Image")
    hp_flag = Bool(False, label="highpass")
    inverse_flag = Bool(False, label="inverse")
    button_detection = Button(label="Detect dots")

    def __init__(self):
        super(DetectionGUI, self).__init__()
        
        # Initialize state variables
        self.parameters_loaded = False
        self.image_loaded = False
        self.raw_image = None
        self.processed_image = None
        self.experiment = None
        
        # Working directory will be set when parameters are loaded
        self.working_folder = None
        
        # Parameter structures (will be initialized when parameters are loaded)
        self.cpar = None
        self.tpar = None
        
        # Detection parameters (will be loaded from YAML)
        self.thresholds = [40]
        self.pixel_count_bounds = [25, 400]
        self.xsize_bounds = [5, 50]
        self.ysize_bounds = [5, 50]
        self.sum_grey = 100
        self.disco = 500

        self.camera = [PlotWindow()]

    def _button_load_params_fired(self):
        """Load parameters from YAML file"""
        try:
            yaml_file = pathlib.Path(self.yaml_path)
            if not yaml_file.exists():
                self.status_text = f"Error: YAML file {self.yaml_path} does not exist"
                return
            
            # Load experiment from YAML file
            self.experiment = Experiment()
            self.experiment.parameter_manager.from_yaml(self.yaml_path)
            
            # Set working directory to YAML file location
            self.working_folder = yaml_file.parent
            os.chdir(self.working_folder)
            print(f"Working directory: {self.working_folder}")
            
            # Get parameters from YAML
            ptv_params = self.experiment.get_parameter('ptv')
            if ptv_params is None:
                raise ValueError("Failed to load PTV parameters from YAML")
            
            # Initialize C parameter structures for single camera detection
            self.n_cams = 1
            self.cpar = ptv.ControlParams(self.n_cams)
            
            # Set basic camera parameters from YAML
            self.cpar.set_image_size((ptv_params.get('imx', 1280), ptv_params.get('imy', 1024)))
            self.cpar.set_pixel_size((ptv_params.get('pix_x', 0.012), ptv_params.get('pix_y', 0.012)))
            self.cpar.set_hp_flag(ptv_params.get('hp_flag', False))
            self.cpar.set_tiff_flag(ptv_params.get('tiff_flag', True))
            
            # Initialize target parameters for detection
            self.tpar = ptv.TargetParams()
            
            # Get detection parameters from YAML
            detect_params = self.experiment.get_parameter('detect_plate')
            if detect_params is None:
                raise ValueError("Failed to load detection parameters from YAML")
            
            # Load detection parameters from YAML
            self.thresholds = [detect_params.get('gvth_1', 40)]
            self.pixel_count_bounds = [
                detect_params.get('min_npix', 25),
                detect_params.get('max_npix', 400)
            ]
            self.xsize_bounds = [
                detect_params.get('min_npix_x', 5),
                detect_params.get('max_npix_x', 50)
            ]
            self.ysize_bounds = [
                detect_params.get('min_npix_y', 5),
                detect_params.get('max_npix_y', 50)
            ]
            self.sum_grey = detect_params.get('sum_grey', 100)
            self.disco = detect_params.get('tol_dis', 500)
            
            # Apply parameters to C structures
            self.tpar.set_grey_thresholds(self.thresholds)
            self.tpar.set_pixel_count_bounds(self.pixel_count_bounds)
            self.tpar.set_xsize_bounds(self.xsize_bounds)
            self.tpar.set_ysize_bounds(self.ysize_bounds)
            self.tpar.set_min_sum_grey(self.sum_grey)
            self.tpar.set_max_discontinuity(self.disco)
            
            # Create dynamic traits for real-time parameter adjustment
            if not self.parameters_loaded:
                self._create_parameter_traits()
            else:
                # Update existing trait values
                self._update_trait_values()
            
            self.parameters_loaded = True
            self.status_text = f"Parameters loaded from {self.yaml_path}"
            
        except Exception as e:
            self.status_text = f"Error loading parameters: {str(e)}"
            print(f"Error loading parameters: {e}")

    def _create_parameter_traits(self):
        """Create dynamic traits for parameter adjustment"""
        self.add_trait("grey_thresh", Range(1, 255, self.thresholds[0], mode="slider"))
        self.add_trait(
            "min_npix",
            Range(
                0,
                self.pixel_count_bounds[0] + 50,
                self.pixel_count_bounds[0],
                mode="slider",
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
                self.sum_grey // 2,
                self.sum_grey * 2,
                self.sum_grey,
                mode="slider",
                label="Sum of greyvalue",
            ),
        )

    def _update_trait_values(self):
        """Update existing trait values when parameters are reloaded"""
        if hasattr(self, 'grey_thresh'):
            self.grey_thresh = self.thresholds[0]
        if hasattr(self, 'min_npix'):
            self.min_npix = self.pixel_count_bounds[0]
        if hasattr(self, 'max_npix'):
            self.max_npix = self.pixel_count_bounds[1]
        if hasattr(self, 'min_npix_x'):
            self.min_npix_x = self.xsize_bounds[0]
        if hasattr(self, 'max_npix_x'):
            self.max_npix_x = self.xsize_bounds[1]
        if hasattr(self, 'min_npix_y'):
            self.min_npix_y = self.ysize_bounds[0]
        if hasattr(self, 'max_npix_y'):
            self.max_npix_y = self.ysize_bounds[1]
        if hasattr(self, 'disco'):
            self.disco = self.disco
        if hasattr(self, 'sum_of_grey'):
            self.sum_of_grey = self.sum_grey

    def _button_load_image_fired(self):
        """Load raw image from file"""
        if not self.parameters_loaded:
            self.status_text = "Load parameters first"
            return
            
        try:
            # Load raw image
            image_path = pathlib.Path(self.image_name)
            if not image_path.is_absolute():
                if self.working_folder is not None:
                    image_path = self.working_folder / self.image_name
                else:
                    self.status_text = "Error: Working folder is not set. Load parameters first."
                    return

            if not image_path.exists():
                self.status_text = f"Error: Image {image_path} does not exist"
                return
                
            self.raw_image = imread(str(image_path))
            if self.raw_image.ndim > 2:
                self.raw_image = rgb2gray(self.raw_image)
            self.raw_image = img_as_ubyte(self.raw_image)
            
            # Process image with current filter settings
            self._update_processed_image()
            
            # Display image
            self.reset_show_images()
            
            self.image_loaded = True
            self.status_text = f"Image loaded: {self.image_name}"
            
            # Run initial detection
            self._run_detection()
            
        except Exception as e:
            self.status_text = f"Error loading image: {str(e)}"
            print(f"Error loading image {self.image_name}: {e}")

    def _update_processed_image(self):
        """Update processed image based on current filter settings"""
        if self.raw_image is None:
            return
            
        try:
            # Start with raw image
            im = self.raw_image.copy()
            
            # Apply inverse flag
            if self.inverse_flag:
                im = 255 - im
            
            # Apply highpass filter if enabled
            if self.hp_flag and self.experiment is not None:
                ptv_params = self.experiment.get_parameter('ptv')
                if ptv_params is not None:
                    tmp = [im]
                    tmp = ptv.py_pre_processing_c(tmp, ptv_params)
                    im = tmp[0]
            
            self.processed_image = im.copy()
            
        except Exception as e:
            self.status_text = f"Error processing image: {str(e)}"
            print(f"Error processing image: {e}")

    def _inverse_flag_changed(self):
        """Handle inverse flag change"""
        if self.image_loaded:
            self._update_processed_image()
            self.reset_show_images()
            self._run_detection()
            self.status_text = "Inverse filter applied" if self.inverse_flag else "Inverse filter removed"

    def _hp_flag_changed(self):
        """Handle highpass flag change"""
        if self.parameters_loaded:
            self.cpar.set_hp_flag(self.hp_flag)
        
        if self.image_loaded:
            self._update_processed_image()
            self.reset_show_images()
            self._run_detection()
            self.status_text = "Highpass filter applied" if self.hp_flag else "Highpass filter removed"

    view = View(
        HGroup(
            VGroup(
                VGroup(
                    Item(name="yaml_path", width=300),
                    Item(name="button_load_params"),
                    "_",  # Separator
                    Item(name="image_name", width=200),
                    Item(name="button_load_image"),
                    "_",  # Separator
                    Item(name="hp_flag"),
                    Item(name="inverse_flag"),
                    Item(name="button_detection"),
                    "_",  # Separator
                    Item(name="grey_thresh", enabled_when="parameters_loaded"),
                    Item(name="min_npix", enabled_when="parameters_loaded"),
                    Item(name="min_npix_x", enabled_when="parameters_loaded"),
                    Item(name="min_npix_y", enabled_when="parameters_loaded"),
                    Item(name="max_npix", enabled_when="parameters_loaded"),
                    Item(name="max_npix_x", enabled_when="parameters_loaded"),
                    Item(name="max_npix_y", enabled_when="parameters_loaded"),
                    Item(name="disco", enabled_when="parameters_loaded"),
                    Item(name="sum_of_grey", enabled_when="parameters_loaded"),
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
        title="Detection GUI - Load Parameters and Image",
        id="view1",
        width=1.0,
        height=1.0,
        resizable=True,
        statusbar="status_text",
    )

    def _inverse_flag_changed(self):
        """Handle inverse flag change"""
        if self.image_loaded:
            self._update_processed_image()
            self.reset_show_images()
            self._run_detection()
            self.status_text = "Inverse filter applied" if self.inverse_flag else "Inverse filter removed"

    def _hp_flag_changed(self):
        """Handle highpass flag change"""
        if self.parameters_loaded:
            self.cpar.set_hp_flag(self.hp_flag)
        
        if self.image_loaded:
            self._update_processed_image()
            self.reset_show_images()
            self._run_detection()
            self.status_text = "Highpass filter applied" if self.hp_flag else "Highpass filter removed"

    def _grey_thresh_changed(self):
        """Update grey threshold parameter"""
        if self.parameters_loaded:
            self.thresholds[0] = self.grey_thresh
            self.tpar.set_grey_thresholds(self.thresholds)
            self.status_text = f"Grey threshold: {self.grey_thresh}"
            self._run_detection()

    def _min_npix_changed(self):
        """Update minimum pixel count parameter"""
        if self.parameters_loaded:
            self.pixel_count_bounds[0] = self.min_npix
            self.tpar.set_pixel_count_bounds(self.pixel_count_bounds)
            self.status_text = f"Min pixels: {self.min_npix}"
            self._run_detection()

    def _max_npix_changed(self):
        """Update maximum pixel count parameter"""
        if self.parameters_loaded:
            self.pixel_count_bounds[1] = self.max_npix
            self.tpar.set_pixel_count_bounds(self.pixel_count_bounds)
            self.status_text = f"Max pixels: {self.max_npix}"
            self._run_detection()

    def _min_npix_x_changed(self):
        """Update minimum X pixel count parameter"""
        if self.parameters_loaded:
            self.xsize_bounds[0] = self.min_npix_x
            self.tpar.set_xsize_bounds(self.xsize_bounds)
            self.status_text = f"Min pixels X: {self.min_npix_x}"
            self._run_detection()

    def _max_npix_x_changed(self):
        """Update maximum X pixel count parameter"""
        if self.parameters_loaded:
            self.xsize_bounds[1] = self.max_npix_x
            self.tpar.set_xsize_bounds(self.xsize_bounds)
            self.status_text = f"Max pixels X: {self.max_npix_x}"
            self._run_detection()

    def _min_npix_y_changed(self):
        """Update minimum Y pixel count parameter"""
        if self.parameters_loaded:
            self.ysize_bounds[0] = self.min_npix_y
            self.tpar.set_ysize_bounds(self.ysize_bounds)
            self.status_text = f"Min pixels Y: {self.min_npix_y}"
            self._run_detection()

    def _max_npix_y_changed(self):
        """Update maximum Y pixel count parameter"""
        if self.parameters_loaded:
            self.ysize_bounds[1] = self.max_npix_y
            self.tpar.set_ysize_bounds(self.ysize_bounds)
            self.status_text = f"Max pixels Y: {self.max_npix_y}"
            self._run_detection()

    def _sum_of_grey_changed(self):
        """Update sum of grey parameter"""
        if self.parameters_loaded:
            self.tpar.set_min_sum_grey(self.sum_of_grey)
            self.status_text = f"Sum of grey: {self.sum_of_grey}"
            self._run_detection()

    def _disco_changed(self):
        """Update discontinuity parameter"""
        if self.parameters_loaded:
            self.tpar.set_max_discontinuity(self.disco)
            self.status_text = f"Discontinuity: {self.disco}"
            self._run_detection()

    def _run_detection(self):
        """Run detection if image is loaded"""
        if self.image_loaded:
            self._button_detection_fired()

    def _run_detection_if_image_loaded(self):
        """Run detection if an image is loaded"""
        if hasattr(self, 'processed_image') and self.processed_image is not None:
            self._button_detection_fired()

    def _button_showimg_fired(self):
        """Load and display the specified image"""
        try:
            self._load_raw_image()
            self._reprocess_current_image()
            self.reset_show_images()
            self.status_text = f"Loaded image: {self.image_name}"
            # Run initial detection
            self._button_detection_fired()
        except Exception as e:
            self.status_text = f"Error loading image: {str(e)}"
            print(f"Error loading image {self.image_name}: {e}")

    def _load_raw_image(self):
        """Load the raw image from file (called only once per image)"""
        try:
            self.raw_image = imread(self.image_name)
            if self.raw_image.ndim > 2:
                self.raw_image = rgb2gray(self.raw_image)
            self.raw_image = img_as_ubyte(self.raw_image)
        except Exception as e:
            self.status_text = f"Error reading image: {str(e)}"
            raise

    def _reprocess_current_image(self):
        """Reprocess the current raw image with current filter settings"""
        if not hasattr(self, 'raw_image') or self.raw_image is None:
            return
        
        try:
            # Start with the raw image
            im = self.raw_image.copy()

            # Apply inverse flag
            if self.inverse_flag:
                im = 255 - im

            # Apply highpass filter if enabled
            if self.hp_flag:
                # Get ptv parameters as dictionary for preprocessing
                ptv_params = self.experiment.get_parameter('ptv')
                if ptv_params is None:
                    self.status_text = "Error: PTV parameters not found"
                    raise ValueError("PTV parameters not found")
                tmp = [im]
                tmp = ptv.py_pre_processing_c(tmp, ptv_params)
                im = tmp[0]

            self.processed_image = im.copy()
            
        except Exception as e:
            self.status_text = f"Error processing image: {str(e)}"
            raise

    def _read_image(self):
        """Legacy method - now just calls the new methods"""
        self._load_raw_image()
        self._reprocess_current_image()

    def _button_detection_fired(self):
        """Run particle detection on the current image"""
        if not hasattr(self, 'processed_image') or self.processed_image is None:
            self.status_text = "No image loaded - load parameters and image first"
            return
        
        if not self.parameters_loaded:
            self.status_text = "Parameters not loaded - load parameters first"
            return
        
        self.status_text = "Running detection..."
        
        try:
            # Run detection using current parameters
            targs = target_recognition(self.processed_image, self.tpar, 0, self.cpar)
            targs.sort_y()

            # Extract particle positions
            x = [i.pos()[0] for i in targs]
            y = [i.pos()[1] for i in targs]

            # Clear previous detection results
            self.camera[0].drawcross("x", "y", np.array(x), np.array(y), "orange", 8)
            self.camera[0]._right_click_avail = 1

            # Update status with detection results
            self.status_text = f"Detected {len(x)} particles"
            
        except Exception as e:
            self.status_text = f"Detection error: {str(e)}"
            print(f"Detection error: {e}")

    def reset_plots(self):
        """Resets all the images and overlays"""
        self.camera[0]._plot.delplot(*self.camera[0]._plot.plots.keys())
        self.camera[0]._plot.overlays = []
        for j in range(len(self.camera[0]._quiverplots)):
            self.camera[0]._plot.remove(self.camera[0]._quiverplots[j])
        self.camera[0]._quiverplots = []

    def reset_show_images(self):
        """Reset and show the current processed image"""
        if not hasattr(self, 'processed_image') or self.processed_image is None:
            return
            
        self.reset_plots()
        self.camera[0]._plot_data.set_data("imagedata", self.processed_image)
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
        # Default to test_cavity YAML file
        yaml_path = pathlib.Path().absolute() / "tests" / "test_cavity" / "parameters_Run1.yaml"
    else:
        # Use provided YAML file path
        yaml_path = pathlib.Path(sys.argv[1])
    
    print(f"Loading PyPTV Detection GUI")
    
    detection_gui = DetectionGUI()
    if yaml_path.exists():
        detection_gui.yaml_path = str(yaml_path)
        print(f"Default YAML file: {yaml_path}")
    else:
        print(f"Warning: Default YAML file {yaml_path} does not exist")
    
    detection_gui.configure_traits()