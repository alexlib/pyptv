from traits.etsconfig.api import ETSConfig
import os
from pathlib import Path
import sys
import json
import numpy as np
import optv
from traits.api import HasTraits, Int, Bool, Instance, List, Enum, Any
from traitsui.api import (
    View,
    Item,
    ListEditor,
    Handler,
    TreeEditor,
    TreeNode,
    Separator,
    Group,
)

from traitsui.menu import Action, Menu, MenuBar
from chaco.api import ArrayDataSource, ArrayPlotData, LinearMapper, Plot, gray
from chaco.tools.api import PanTool, ZoomTool
from chaco.tools.image_inspector_tool import ImageInspectorTool
from enable.component_editor import ComponentEditor
from skimage.util import img_as_ubyte
from skimage.io import imread
from skimage.color import rgb2gray

from pyptv.parameter_manager import ParameterManager
from pyptv import ptv
from pyptv.calibration_gui import CalibrationGUI
from pyptv.directory_editor import DirectoryEditorDialog
from pyptv.parameter_gui import Experiment, Paramset
from pyptv.quiverplot import QuiverPlot
from pyptv.detection_gui import DetectionGUI
from pyptv.mask_gui import MaskGUI
from pyptv import __version__
import optv.orientation
import optv.epipolar

"""PyPTV_GUI is the GUI for the OpenPTV (www.openptv.net) written in
Python with Traits, TraitsUI, Numpy, Scipy and Chaco

Copyright (c) 2008-2023, Turbulence Structure Laboratory, Tel Aviv University
The GUI software is distributed under the terms of MIT-like license
http://opensource.org/licenses/MIT

OpenPTV library is distributed under the terms of LGPL license
see http://www.openptv.net for more details.

"""
ETSConfig.toolkit = "qt"


class Clicker(ImageInspectorTool):
    left_changed = Int(0)
    right_changed = Int(0)
    x, y = 0, 0

    def __init__(self, *args, **kwargs):
        super(Clicker, self).__init__(*args, **kwargs)

    def normal_left_down(self, event):
        plot = self.component
        if plot is not None:
            self.x, self.y = plot.map_index((event.x, event.y))
            self.data_value = plot.value.data[self.y, self.x]
            self.last_mouse_position = (event.x, event.y)
            self.left_changed = 1 - self.left_changed

    def normal_right_down(self, event):
        plot = self.component
        if plot is not None:
            self.x, self.y = plot.map_index((event.x, event.y))
            self.last_mouse_position = (event.x, event.y)
            self.data_value = plot.value.data[self.y, self.x]
            self.right_changed = 1 - self.right_changed


class CameraWindow(HasTraits):
    _plot = Instance(Plot)
    rclicked = Int(0)
    cam_color = ""
    name = ""
    view = View(Item(name="_plot", editor=ComponentEditor(), show_label=False))

    def __init__(self, color, name):
        super(HasTraits, self).__init__()
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
        self.name = name

    def attach_tools(self):
        print(f" Attaching clicker to camera {self.name}")
        self._click_tool = Clicker(component=self._img_plot)
        self._click_tool.on_trait_change(self.left_clicked_event, "left_changed")
        self._click_tool.on_trait_change(self.right_clicked_event, "right_changed")
        self._img_plot.tools.append(self._click_tool)

        pan = PanTool(self._plot, drag_button="middle")
        zoom_tool = ZoomTool(self._plot, tool_mode="box", always_on=False)
        zoom_tool.max_zoom_out_factor = 1.0
        self._img_plot.overlays.append(zoom_tool)
        self._img_plot.tools.append(pan)

    def left_clicked_event(self):
        print(
            f"left click in {self.name} x={self._click_tool.x} pix,y={self._click_tool.y} pix,I={self._click_tool.data_value}"
        )

    def right_clicked_event(self):
        print(
            f"right click in {self.name}, x={self._click_tool.x},y={self._click_tool.y}, I={self._click_tool.data_value}, {self.rclicked}"
        )
        self.rclicked = 1

    def create_image(self, image, is_float=False):
        if is_float:
            self._plot_data.set_data("imagedata", image.astype(np.float32))
        else:
            self._plot_data.set_data("imagedata", image.astype(np.uint8))
        self._img_plot = self._plot.img_plot("imagedata", colormap=gray)[0]
        self.attach_tools()

    def update_image(self, image, is_float=False):
        if is_float:
            self._plot_data.set_data("imagedata", image.astype(np.float32))
        else:
            self._plot_data.set_data("imagedata", image)
        self._plot.request_redraw()

    def drawcross(self, str_x, str_y, x, y, color, mrk_size, marker="plus"):
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
            self._plot.overlays.append(quiverplot)
            self._quiverplots.append(quiverplot)

    @staticmethod
    def remove_short_lines(x1, y1, x2, y2):
        dx, dy = 2, 2
        x1f, y1f, x2f, y2f = [], [], [], []
        for i in range(len(x1)):
            if abs(x1[i] - x2[i]) > dx or abs(y1[i] - y2[i]) > dy:
                x1f.append(x1[i])
                y1f.append(y1[i])
                x2f.append(x2[i])
                y2f.append(y2[i])
        return x1f, y1f, x2f, y2f

    def drawline(self, str_x, str_y, x1, y1, x2, y2, color1):
        self._plot_data.set_data(str_x, [x1, x2])
        self._plot_data.set_data(str_y, [y1, y2])
        self._plot.plot((str_x, str_y), type="line", color=color1)


class TreeMenuHandler(Handler):
    def configure_main_par(self, editor, object):
        paramset = object
        paramset.m_params.edit_traits(kind="modal")

    def configure_cal_par(self, editor, object):
        paramset = object
        paramset.c_params.edit_traits(kind="modal")

    def configure_track_par(self, editor, object):
        paramset = object
        paramset.t_params.edit_traits(kind="modal")

    def set_active(self, editor, object):
        experiment = editor.get_parent(object)
        paramset = object
        experiment.setActive(paramset)
        experiment.changed_active_params = True

    def copy_set_params(self, editor, object):
        experiment = editor.get_parent(object)
        paramset = object
        i = 1
        new_name = None
        new_dir_path = None
        flag = False
        while not flag:
            new_name = f"{paramset.name}_{i}"
            new_dir_path = Path(f"parameters{new_name}")
            if not new_dir_path.is_dir():
                flag = True
            else:
                i = i + 1
        
        pm = ParameterManager()
        pm.from_directory(paramset.par_path)
        pm.to_directory(new_dir_path)
        experiment.addParamset(new_name, new_dir_path)

    def rename_set_params(self, editor, object):
        print("Warning: This method is not implemented.")

    def delete_set_params(self, editor, object):
        paramset = object
        editor._menu_delete_node()
        [
            os.remove(os.path.join(paramset.par_path, f))
            for f in os.listdir(paramset.par_path)
        ]
        os.rmdir(paramset.par_path)

    def new_action(self, info):
        print("not implemented")

    def open_action(self, info):
        directory_dialog = DirectoryEditorDialog()
        directory_dialog.edit_traits()
        exp_path = str(directory_dialog.dir_name)
        print(f"Changing experimental path to {exp_path}")
        os.chdir(exp_path)
        info.object.exp1.populate_runs(exp_path)

    def exit_action(self, info):
        print("not implemented")

    def saveas_action(self, info):
        print("not implemented")

    def init_action(self, info):
        mainGui = info.object
        mainGui.exp1.syncActiveDir()

        if mainGui.pm.get_parameter('ptv').get('splitter', False):
            print("Using Splitter, add plugins")
            imname = mainGui.pm.get_parameter('ptv')['img_name'][0]
            if Path(imname).exists():
                temp_img = imread(imname)
                if temp_img.ndim > 2:
                    im = rgb2gray(temp_img)                
                splitted_images = ptv.image_split(temp_img)
                for i in range(len(mainGui.camera_list)):
                    mainGui.orig_images[i] = img_as_ubyte(splitted_images[i])
        else:
            for i in range(len(mainGui.camera_list)):
                imname = mainGui.pm.get_parameter('ptv')['img_name'][i]
                if Path(imname).exists():
                    print(f"Reading image {imname}")
                    im = imread(imname)
                    if im.ndim > 2:
                        im = rgb2gray(im)
                else:
                    print(f"Image {imname} does not exist, setting zero image")
                    im = np.zeros(
                        (mainGui.pm.get_parameter('ptv')['imy'], 
                        mainGui.pm.get_parameter('ptv')['imx']),
                            dtype=np.uint8
                                )
                    
                mainGui.orig_images[i] = img_as_ubyte(im)

        mainGui.clear_plots()
        print("\n Init action \n")
        mainGui.create_plots(mainGui.orig_images, is_float=False)

        (
            info.object.cpar,
            info.object.spar,
            info.object.vpar,
            info.object.track_par,
            info.object.tpar,
            info.object.cals,
            info.object.epar,
        ) = ptv.py_start_proc_c(info.object.pm.parameters)
        mainGui.pass_init = True
        print("Read all the parameters and calibrations successfully ")

    def draw_mask_action(self, info):
        print("\n Opening drawing mask GUI \n")
        info.object.pass_init = False
        mask_gui = MaskGUI(info.object.exp1.active_params.par_path)
        mask_gui.configure_traits()

    def highpass_action(self, info):
        if info.object.pm.get_parameter('ptv').get('inverse', False):
            print("Invert image")
            for i, im in enumerate(info.object.orig_images):
                info.object.orig_images[i] = ptv.negative(im)

        if info.object.pm.get_parameter('masking').get('mask_flag', False):
            print("Subtracting mask")
            try:
                for i, im in enumerate(info.object.orig_images):
                    background_name = (
                        info.object.pm.get_parameter('masking')['mask_base_name'].replace(
                            "#", str(i)
                        )
                    )
                    print(f"Subtracting {background_name}")
                    background = imread(background_name)
                    info.object.orig_images[i] = np.clip(
                        info.object.orig_images[i] - background, 0, 255
                    ).astype(np.uint8)

            except ValueError as exc:
                raise ValueError("Failed subtracting mask") from exc

        print("highpass started")
        info.object.orig_images = ptv.py_pre_processing_c(
            info.object.orig_images, info.object.cpar
        )
        info.object.update_plots(info.object.orig_images)
        print("highpass finished")

    def img_coord_action(self, info):
        print("Start detection")
        (
            info.object.detections,
            info.object.corrected,
        ) = ptv.py_detection_proc_c(
            info.object.orig_images,
            info.object.cpar,
            info.object.tpar,
            info.object.cals,
        )
        print("Detection finished")
        x = [[i.pos()[0] for i in row] for row in info.object.detections]
        y = [[i.pos()[1] for i in row] for row in info.object.detections]
        info.object.drawcross_in_all_cams("x", "y", x, y, "blue", 3)

    def _clean_correspondences(self, tmp):
        x1, y1 = [], []
        for x in tmp:
            tmp = x[(x != -999).any(axis=1)]
            x1.append(tmp[:, 0])
            y1.append(tmp[:, 1])
        return x1, y1

    def corresp_action(self, info):
        print("correspondence proc started")
        (
            info.object.sorted_pos,
            info.object.sorted_corresp,
            info.object.num_targs,
        ) = ptv.py_correspondences_proc_c(info.object)

        names = ["pair", "tripl", "quad"]
        use_colors = ["yellow", "green", "red"]

        if len(info.object.camera_list) > 1 and len(info.object.sorted_pos) > 0:
            for i, subset in enumerate(reversed(info.object.sorted_pos)):
                x, y = self._clean_correspondences(subset)
                info.object.drawcross_in_all_cams(
                    names[i] + "_x", names[i] + "_y", x, y, use_colors[i], 3
                )

    def calib_action(self, info):
        print("\n Starting calibration dialog \n")
        info.object.pass_init = False
        calib_gui = CalibrationGUI(info.object.exp1.active_params.par_path)
        calib_gui.configure_traits()

    def detection_gui_action(self, info):
        print("\n Starting detection GUI dialog \n")
        info.object.pass_init = False
        detection_gui = DetectionGUI(info.object.exp1.active_params.par_path)
        detection_gui.configure_traits()

    def sequence_action(self, info):
        extern_sequence = info.object.plugins.sequence_alg
        if extern_sequence != "default":
            ptv.run_sequence_plugin(info.object)
        else:
            ptv.py_sequence_loop(info.object)

    def track_no_disp_action(self, info):
        extern_tracker = info.object.plugins.track_alg
        if extern_tracker != "default":
            ptv.run_tracking_plugin(info.object)
            print("After plugin tracker")
        else:
            print("Using default liboptv tracker")
            info.object.tracker = ptv.py_trackcorr_init(info.object)
            info.object.tracker.full_forward()
            print("tracking without display finished")

    def track_disp_action(self, info):
        info.object.clear_plots(remove_background=False)

    def track_back_action(self, info):
        print("Starting back tracking")
        info.object.tracker.full_backward()

    def three_d_positions(self, info):
        ptv.py_determination_proc_c(
            info.object.n_cams,
            info.object.sorted_pos,
            info.object.sorted_corresp,
            info.object.corrected,
        )

    def detect_part_track(self, info):
        info.object.clear_plots(remove_background=False)
        prm = info.object.pm.get_parameter('sequence')
        seq_first = prm['first']
        seq_last = prm['last']
        base_names = prm['base_name']

        info.object.overlay_set_images(base_names, seq_first, seq_last)

        print("Starting detect_part_track")
        x1_a, x2_a, y1_a, y2_a = [], [], [], []
        for i in range(info.object.n_cams):
            x1_a.append([])
            x2_a.append([])
            y1_a.append([])
            y2_a.append([])

        for i_cam in range(info.object.n_cams):
            for i_seq in range(seq_first, seq_last + 1):
                intx_green, inty_green = [], []
                intx_blue, inty_blue = [], []

                simple_base_name = str(Path(base_names[0]).parent / f'cam{i_cam + 1}')
                print('Inside detected particles plot', simple_base_name)

                targets = ptv.read_targets(simple_base_name, i_seq)

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

        for i_cam in range(info.object.n_cams):
            info.object.camera_list[i_cam].drawcross(
                "x_tr_gr", "y_tr_gr", x1_a[i_cam], y1_a[i_cam], "green", 3
            )
            info.object.camera_list[i_cam].drawcross(
                "x_tr_bl", "y_tr_bl", x2_a[i_cam], y2_a[i_cam], "blue", 2
            )
            info.object.camera_list[i_cam]._plot.request_redraw()

        print("Finished detect_part_track")

    def traject_action_flowtracks(self, info):
        info.object.clear_plots(remove_background=False)
        prm = info.object.pm.get_parameter('sequence')
        seq_first = prm['first']
        seq_last = prm['last']
        base_names = prm['base_name']

        info.object.overlay_set_images(base_names, seq_first, seq_last)

        from flowtracks.io import trajectories_ptvis

        dataset = trajectories_ptvis(
            "res/ptv_is.%d", first=seq_first, last=seq_last, xuap=False, traj_min_len=3
        )

        heads_x, heads_y = [], []
        tails_x, tails_y = [], []
        ends_x, ends_y = [], []
        for i_cam in range(info.object.n_cams):
            head_x, head_y = [], []
            tail_x, tail_y = [], []
            end_x, end_y = [], []
            for traj in dataset:
                projected = optv.imgcoord.image_coordinates(
                    np.atleast_2d(traj.pos() * 1000),
                    info.object.cals[i_cam],
                    info.object.cpar.get_multimedia_params(),
                )
                pos = optv.transforms.convert_arr_metric_to_pixel(
                    projected, info.object.cpar
                )

                head_x.append(pos[0, 0])
                head_y.append(pos[0, 1])
                tail_x.extend(list(pos[1:-1, 0]))
                tail_y.extend(list(pos[1:-1, 1]))
                end_x.append(pos[-1, 0])
                end_y.append(pos[-1, 1])

            heads_x.append(head_x)
            heads_y.append(head_y)
            tails_x.append(tail_x)
            tails_y.append(tail_y)
            ends_x.append(end_x)
            ends_y.append(end_y)

        for i_cam in range(info.object.n_cams):
            info.object.camera_list[i_cam].drawcross(
                "heads_x", "heads_y", heads_x[i_cam], heads_y[i_cam], "red", 3
            )
            info.object.camera_list[i_cam].drawcross(
                "tails_x", "tails_y", tails_x[i_cam], tails_y[i_cam], "green", 2
            )
            info.object.camera_list[i_cam].drawcross(
                "ends_x", "ends_y", ends_x[i_cam], ends_y[i_cam], "orange", 3
            )

    def plugin_action(self, info):
        info.object.plugins.read()
        info.object.plugins.configure_traits()

    def ptv_is_to_paraview(self, info):
        print("Saving trajectories for Paraview\n")
        info.object.clear_plots(remove_background=False)
        seq_first = info.object.pm.get_parameter('sequence')['first']
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
                f"./res/ptv_{int(index):05d}.txt",
                mode="w",
                columns=["particle", "x", "y", "z", "dx", "dy", "dz"],
                index=False,
            )

        print("Saving trajectories to Paraview finished\n")


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

class Plugins(HasTraits):
    track_alg = Enum('default')
    sequence_alg = Enum('default')
    
    view = View(
        Item(name="track_alg", label="Tracking:"),
        Item(name="sequence_alg", label="Sequence:"),
        buttons=["OK"],
        title="Plugins",
    )

    def __init__(self):
        self.read()

    def read(self):
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
                
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error reading plugins.json: {e}")
                self._set_defaults()
        else:
            self._create_default_json()
    
    def _set_defaults(self):
        self.track_alg = 'default'
        self.sequence_alg = 'default'
    
    def _create_default_json(self):
        default_config = {
            "tracking": ["default"],
            "sequence": ["default"]
        }
        
        with open('plugins.json', 'w') as f:
            json.dump(default_config, f, indent=2)
        

class MainGUI(HasTraits):
    """MainGUI is the main class under which the Model-View-Control
    (MVC) model is defined"""

    camera_list = List
    pass_init = Bool(False)
    update_thread_plot = Bool(False)
    selected = Any

    def _selected_changed(self):
        self.current_camera = int(self.selected.name.split(" ")[1]) - 1

    def __init__(self, exp_path: Path, software_path: Path):
        super(MainGUI, self).__init__()

        colors = ["yellow", "green", "red", "blue"]
        self.exp1 = Experiment()
        self.exp1.populate_runs(exp_path)
        self.plugins = Plugins()
        
        self.pm = ParameterManager()
        self.pm.from_yaml(self.exp1.active_params.par_path / 'parameters.yaml')
        
        self.n_cams = self.pm.get_parameter('ptv')['n_img']
        self.orig_images = self.n_cams * [[]]
        self.current_camera = 0
        self.camera_list = [
            CameraWindow(colors[i], f"Camera {i + 1}") for i in range(self.n_cams)
        ]
        self.software_path = software_path
        self.exp_path = exp_path
        for i in range(self.n_cams):
            self.camera_list[i].on_trait_change(self.right_click_process, "rclicked")
        
        self.view = View(
            Group(
                Group(
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
                    orientation="horizontal",
                    show_left=False,
                ),
                orientation="vertical",
            ),
            title="pyPTV" + __version__,
            id="main_view",
            width=1.0,
            height=1.0,
            resizable=True,
            handler=TreeMenuHandler(),
            menubar=menu_bar,
        )

    def right_click_process(self):
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

            for pos_type in self.sorted_pos:
                distances = np.linalg.norm(pos_type[i] - point, axis=1)
                if len(distances) > 0 and np.min(distances) < 5:
                    point = pos_type[i][np.argmin(distances)]

            if not np.allclose(point, [0.0, 0.0]):
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
        print("inside update plots, images changed\n")
        for i in range(self.n_cams):
            self.camera_list[i].create_image(images[i], is_float)
            self.camera_list[i]._plot.request_redraw()

    def update_plots(self, images, is_float=False) -> None:
        print("Update plots, images changed\n")
        for cam, image in zip(self.camera_list, images):
            cam.update_image(image, is_float)

    def drawcross_in_all_cams(self, str_x, str_y, x, y, color1, size1, marker="plus"):
        for i, cam in enumerate(self.camera_list):
            cam.drawcross(str_x, str_y, x[i], y[i], color1, size1, marker=marker)

    def clear_plots(self, remove_background=True):
        if not remove_background:
            index = "plot0"
        else:
            index = None

        for i in range(self.n_cams):
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
        h_img = self.pm.get_parameter('ptv')['imx']
        v_img = self.pm.get_parameter('ptv')['imy']

        if self.pm.get_parameter('ptv').get('splitter', False):
            temp_img = img_as_ubyte(np.zeros((v_img*2, h_img*2)))
            for seq in range(seq_first, seq_last):
                _ = imread(base_names[0] % seq)
                if _.ndim > 2:
                    _ = rgb2gray(_)
                temp_img = np.max([temp_img, _], axis=0)

            list_of_images = ptv.image_split(temp_img)
            for cam_id in range(self.n_cams):
                self.camera_list[cam_id].update_image(list_of_images[cam_id])
        else: 
            for cam_id in range(self.n_cams):
                temp_img = img_as_ubyte(np.zeros((v_img, h_img)))
                for seq in range(seq_first, seq_last):
                    _ = imread(base_names[cam_id] % seq)
                    if _.ndim > 2:
                        _ = rgb2gray(_)
                    temp_img = np.max([temp_img, _], axis=0)
                self.camera_list[cam_id].update_image(temp_img)

    def load_disp_image(self, img_name: str, j: int, display_only: bool = False):
        try:
            temp_img = imread(img_name)
            if temp_img.ndim > 2:
                temp_img = rgb2gray(temp_img)
            temp_img = img_as_ubyte(temp_img)
        except IOError:
            print("Error reading file, setting zero image")
            h_img = self.pm.get_parameter('ptv')['imx']
            v_img = self.pm.get_parameter('ptv')['imy']
            temp_img = img_as_ubyte(np.zeros((v_img, h_img)))

        if len(temp_img) > 0:
            self.camera_list[j].update_image(temp_img)


def printException():
    import traceback
    print("=" * 50)
    print("Exception:", sys.exc_info()[1])
    print(f"{Path.cwd()}")
    print("Traceback:")
    traceback.print_tb(sys.exc_info()[2])
    print("=" * 50)


def main():
    software_path = Path.cwd().resolve()
    print(f"Software path is {software_path}")

    if len(sys.argv) > 1:
        exp_path = Path(sys.argv[1]).resolve()
        print(f"Experimental path is {exp_path}")
    else:
        exp_path = software_path / "tests" / "test_splitter"
        print(f"Without input, PyPTV fallbacks to a default {exp_path} \n")

    if not exp_path.is_dir() or not exp_path.exists():
        raise OSError(f"Wrong experimental directory {exp_path}")

    os.chdir(exp_path)

    try:
        main_gui = MainGUI(exp_path, software_path)
        main_gui.configure_traits()
    except OSError:
        print("something wrong with the software or folder")
        printException()

    os.chdir(software_path)


if __name__ == "__main__":
    main()
