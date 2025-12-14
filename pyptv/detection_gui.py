"""
Copyright (c) 2008-2013, Tel Aviv University
Copyright (c) 2013 - the OpenPTV team
The GUI software is distributed under the terms of MIT-like license
http://opensource.org/licenses/MIT
"""

import os
import sys
from pathlib import Path
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
        if self.component is not None:
            if hasattr(self.component, "map_index"):
                ndx = self.component.map_index((event.x, event.y)) # type: ignore
                if ndx is not None:
                    x_index, y_index = ndx
                    self.x = x_index
                    self.y = y_index
                    print(self.x)
                    print(self.y)
                    self.left_changed = 1 - self.left_changed
                    self.last_mouse_position = (event.x, event.y)

    def normal_right_down(self, event):
        if self.component is not None:
            ndx = self.component.map_index((event.x, event.y)) # type: ignore

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
        # self.py_rclick_delete = ptv.py_rclick_delete
        # self.py_get_pix_N = ptv.py_get_pix_N

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
        # else:
        #     # if self._right_click_avail:
        #     #     print("deleting point")
        #     #     self.py_rclick_delete(
        #     #         self._click_tool.x, self._click_tool.y, self.cameraN
        #     #     )
        #     #     x = []
        #     #     y = []
        #     #     self.py_get_pix_N(x, y, self.cameraN)
        #     #     self.drawcross("x", "y", x[0], y[0], "blue", 4)
        #     print("This part of rclicked_event is not implemented yet")

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
        for x1_val, y1_val, x2_val, y2_val in zip(x1, y1, x2, y2):
            if abs(x1_val - x2_val) > min_length or abs(y1_val - y2_val) > min_length:
                x1f.append(x1_val)
                y1f.append(y1_val)
                x2f.append(x2_val)
                y2f.append(y2_val)
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
    button_load_params = Button(label="Load Parameters")
    image_name = Str("cal/cam1.tif", label="Image file name")
    button_load_image = Button(label="Load Image")
    hp_flag = Bool(False, label="highpass")
    inverse_flag = Bool(False, label="inverse")
    button_detection = Button(label="Detect dots")
    
    # Default traits that will be updated when parameters are loaded
    grey_thresh = Range(1, 255, 40, mode="slider", label="Grey threshold")
    min_npix = Range(1, 100, 25, mode="slider", label="Min pixels")
    min_npix_x = Range(1, 20, 5, mode="slider", label="min npix in x")
    min_npix_y = Range(1, 20, 5, mode="slider", label="min npix in y")
    max_npix = Range(1, 500, 400, mode="slider", label="max npix")
    max_npix_x = Range(1, 100, 50, mode="slider", label="max npix in x")
    max_npix_y = Range(1, 100, 50, mode="slider", label="max npix in y")
    disco = Range(0, 255, 100, mode="slider", label="Discontinuity")
    sum_of_grey = Range(50, 200, 100, mode="slider", label="Sum of greyvalue")
    
    # Range control fields - allow users to adjust slider limits
    # grey_thresh_min = Int(1, label="Min")
#   # grey_thresh_max = Int(255, label="Max")
    min_npix_min = Int(1, label="Min")
    min_npix_max = Int(100, label="Max")
    max_npix_min = Int(1, label="Min")
    max_npix_max = Int(500, label="Max")
    disco_min = Int(0, label="Min")
    disco_max = Int(255, label="Max")
    sum_of_grey_min = Int(10, label="Min")
    sum_of_grey_max = Int(500, label="Max")
    
    # Buttons to apply range changes
    button_update_ranges = Button(label="Update Slider Ranges")

    def __init__(self, working_directory=Path("tests/test_cavity")):
        super(DetectionGUI, self).__init__()

        self.working_directory = Path(working_directory)
        
        # Initialize state variables
        self.parameters_loaded = False
        self.image_loaded = False
        self.raw_image = None
        self.processed_image = None
        
        # Parameter structures (will be initialized when parameters are loaded)
        self.cpar = None
        self.tpar = None
        
        # Detection parameters (hardcoded defaults)
        self.thresholds = [40, 0, 0, 0]
        self.pixel_count_bounds = [25, 400]
        self.xsize_bounds = [5, 50]
        self.ysize_bounds = [5, 50]
        self.sum_grey = 100
        self.disco = 100

        self.camera = [PlotWindow()]

    def _button_load_params(self):
        """Load parameters from working directory"""

        try:
            if not self.working_directory.exists():
                self.status_text = f"Error: Working directory {self.working_directory} does not exist"
                return
            
            # Set working directory
            os.chdir(self.working_directory)
            print(f"Working directory: {self.working_directory}")

            # 1. load the image using imread and self.image_name
            self.image_loaded = False
            try: 
                self.raw_image = imread(self.image_name)
                if self.raw_image.ndim > 2:
                    self.raw_image = rgb2gray(self.raw_image) 
                
                self.raw_image = img_as_ubyte(self.raw_image)
                self.image_loaded = True
            except Exception as e:
                self.status_text = f"Error reading image: {str(e)}"
                print(f"Error reading image {self.image_name}: {e}")
                return

            # Set up control parameters for detection:
            self.cpar = ptv.ControlParams(1)
            self.cpar.set_image_size((self.raw_image.shape[1], self.raw_image.shape[0]))        
            self.cpar.set_pixel_size((0.01, 0.01))  # Default pixel size, can be overridden later
            self.cpar.set_hp_flag(self.hp_flag) 

            # Initialize target parameters for detection
            self.tpar = ptv.TargetParams()
            
            # Set hardcoded detection parameters
            self.tpar.set_grey_thresholds([10, 0, 0, 0])
            self.tpar.set_pixel_count_bounds([1, 50])
            self.tpar.set_xsize_bounds([1,15])
            self.tpar.set_ysize_bounds([1,15])
            self.tpar.set_min_sum_grey(100)
            self.tpar.set_max_discontinuity(100)
            
            # Update trait ranges for real-time parameter adjustment
            if not self.parameters_loaded:
                self._update_parameter_trait_ranges()
            else:
                # Update existing trait values
                self._update_trait_values()
            
            self.parameters_loaded = True
            self.status_text = f"Parameters loaded for working directory {self.working_directory}"
            
        except Exception as e:
            self.status_text = f"Error loading parameters: {str(e)}"
            print(f"Error loading parameters: {e}")

    def _update_parameter_trait_ranges(self):
        """Update dynamic traits for parameter adjustment based on loaded parameters"""
        # Update existing trait ranges based on loaded parameter bounds
        self.trait("grey_thresh").handler.low = 1
        self.trait("grey_thresh").handler.high = 255
        self.grey_thresh = self.thresholds[0]
        # Update range control fields
        self.grey_thresh_min = 1
        self.grey_thresh_max = 255
        
        self.trait("min_npix").handler.low = 0
        self.trait("min_npix").handler.high = self.pixel_count_bounds[0] + 50
        self.min_npix = self.pixel_count_bounds[0]
        self.min_npix_min = 1
        self.min_npix_max = self.pixel_count_bounds[0] + 50
        
        self.trait("max_npix").handler.low = 1
        self.trait("max_npix").handler.high = self.pixel_count_bounds[1] + 100
        self.max_npix = self.pixel_count_bounds[1]
        self.max_npix_min = 1
        self.max_npix_max = self.pixel_count_bounds[1] + 100
        
        self.trait("min_npix_x").handler.low = 1
        self.trait("min_npix_x").handler.high = self.xsize_bounds[0] + 20
        self.min_npix_x = self.xsize_bounds[0]
        
        self.trait("max_npix_x").handler.low = 1
        self.trait("max_npix_x").handler.high = self.xsize_bounds[1] + 50
        self.max_npix_x = self.xsize_bounds[1]
        
        self.trait("min_npix_y").handler.low = 1
        self.trait("min_npix_y").handler.high = self.ysize_bounds[0] + 20
        self.min_npix_y = self.ysize_bounds[0]
        
        self.trait("max_npix_y").handler.low = 1
        self.trait("max_npix_y").handler.high = self.ysize_bounds[1] + 50
        self.max_npix_y = self.ysize_bounds[1]
        
        self.trait("disco").handler.low = 0
        self.trait("disco").handler.high = 255
        self.disco = self.disco
        self.disco_min = 0
        self.disco_max = 255
        
        self.trait("sum_of_grey").handler.low = self.sum_grey // 2
        self.trait("sum_of_grey").handler.high = self.sum_grey * 2
        self.sum_of_grey = self.sum_grey
        self.sum_of_grey_min = self.sum_grey // 2
        self.sum_of_grey_max = self.sum_grey * 2

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

        self._button_load_params()
            
        try:
            
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
            if self.hp_flag:
                im = ptv.preprocess_image(im, 0, self.cpar, 25)
            
            self.processed_image = im.copy()
            
        except Exception as e:
            self.status_text = f"Error processing image: {str(e)}"
            print(f"Error processing image: {e}")

    view = View(
        HGroup(
            VGroup(
                VGroup(
                    Item(name="image_name", width=200),
                    Item(name="button_load_image"),
                    "_",  # Separator
                    Item(name="hp_flag"),
                    Item(name="inverse_flag"),
                    Item(name="button_detection", enabled_when="image_loaded"),
                    "_",  # Separator
                    # Detection parameter sliders
                    HGroup(
                        Item(name="grey_thresh", enabled_when="parameters_loaded"),
                        # Item(name="grey_thresh_max", width=60),
                    ),
                    HGroup(
                        Item(name="min_npix", enabled_when="parameters_loaded"),
                        HGroup(Item(name="min_npix_min", width=20), Item(name="min_npix_max", width=60)),
                    ),
                    Item(name="min_npix_x", enabled_when="parameters_loaded"),
                    Item(name="min_npix_y", enabled_when="parameters_loaded"),
                    HGroup(
                        Item(name="max_npix", enabled_when="parameters_loaded"),
                        VGroup(
                            HGroup(Item(name="max_npix_min", width=60), Item(name="max_npix_max", width=60)),
                            label="Range",
                        ),
                    ),
                    Item(name="max_npix_x", enabled_when="parameters_loaded"),
                    Item(name="max_npix_y", enabled_when="parameters_loaded"),
                    HGroup(
                        Item(name="disco", enabled_when="parameters_loaded"),
                        VGroup(
                            HGroup(Item(name="disco_min", width=60), Item(name="disco_max", width=60)),
                            label="Range",
                        ),
                    ),
                    HGroup(
                        Item(name="sum_of_grey", enabled_when="parameters_loaded"),
                        VGroup(
                            HGroup(Item(name="sum_of_grey_min", width=60), Item(name="sum_of_grey_max", width=60)),
                            label="Range",
                        ),
                    ),
                    "_",  # Separator
                    Item(name="button_update_ranges", enabled_when="parameters_loaded"),
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
        title="Detection GUI - Load Image and Detect Particles",
        id="view1",
        width=1.0,
        height=1.0,
        resizable=True,
        statusbar="status_text",
    )



    def _hp_flag_changed(self):
        """Handle highpass flag change"""       
        self._update_processed_image()
        self.reset_show_images()


    def _inverse_flag_changed(self):
        """Handle inverse flag change"""
        if self.image_loaded:
            self._update_processed_image()
            self.reset_show_images()

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

    # def _load_raw_image(self):
    #     """Load the raw image from file (called only once per image)"""
    #     try:
    #         self.raw_image = imread(self.image_name)
    #         if self.raw_image.ndim > 2:
    #             self.raw_image = rgb2gray(self.raw_image)
    #         self.raw_image = img_as_ubyte(self.raw_image)
    #     except Exception as e:
    #         self.status_text = f"Error reading image: {str(e)}"
    #         raise

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
            if self.hp_flag and self.cpar is not None:
                im = ptv.preprocess_image(im, 0, self.cpar, 25)

            self.processed_image = im.copy()
            
        except Exception as e:
            self.status_text = f"Error processing image: {str(e)}"
            raise

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
        for quiver in self.camera[0]._quiverplots:
            self.camera[0]._plot.remove(quiver)
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

    def _button_update_ranges_fired(self):
        """Update slider ranges based on user input"""
        try:
            # Update grey threshold range
            self.trait("grey_thresh").handler.low = self.grey_thresh_min
            self.trait("grey_thresh").handler.high = self.grey_thresh_max
            # Ensure current value is within new range
            if self.grey_thresh < self.grey_thresh_min:
                self.grey_thresh = self.grey_thresh_min
            elif self.grey_thresh > self.grey_thresh_max:
                self.grey_thresh = self.grey_thresh_max
            
            # Update min_npix range
            self.trait("min_npix").handler.low = self.min_npix_min
            self.trait("min_npix").handler.high = self.min_npix_max
            if self.min_npix < self.min_npix_min:
                self.min_npix = self.min_npix_min
            elif self.min_npix > self.min_npix_max:
                self.min_npix = self.min_npix_max
            
            # Update max_npix range
            self.trait("max_npix").handler.low = self.max_npix_min
            self.trait("max_npix").handler.high = self.max_npix_max
            if self.max_npix < self.max_npix_min:
                self.max_npix = self.max_npix_min
            elif self.max_npix > self.max_npix_max:
                self.max_npix = self.max_npix_max
            
            # Update disco range
            self.trait("disco").handler.low = self.disco_min
            self.trait("disco").handler.high = self.disco_max
            if self.disco < self.disco_min:
                self.disco = self.disco_min
            elif self.disco > self.disco_max:
                self.disco = self.disco_max
            
            # Update sum_of_grey range
            self.trait("sum_of_grey").handler.low = self.sum_of_grey_min
            self.trait("sum_of_grey").handler.high = self.sum_of_grey_max
            if self.sum_of_grey < self.sum_of_grey_min:
                self.sum_of_grey = self.sum_of_grey_min
            elif self.sum_of_grey > self.sum_of_grey_max:
                self.sum_of_grey = self.sum_of_grey_max
            
            self.status_text = "Slider ranges updated successfully"
            
        except Exception as e:
            self.status_text = f"Error updating ranges: {str(e)}"

if __name__ == "__main__":
    if len(sys.argv) == 1:
        # Default to test_cavity directory
        working_dir = Path().absolute() / "tests" / "test_cavity"
    else:
        # Use provided working directory path
        working_dir = Path(sys.argv[1])
    
    print(f"Loading PyPTV Detection GUI with working directory: {working_dir}")
    
    detection_gui = DetectionGUI(working_dir)
    detection_gui.configure_traits()