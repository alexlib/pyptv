"""DearPyGui-based PyPTV GUI prototype with backend integration.

This module provides a practical DearPyGui copy of the classic PyPTV GUI:
- top menu bar with core actions
- left tree-like parameter-set panel
- camera tabs with image display and overlays
- bottom message/log area
- image click events (left/right) with overlay primitives
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

import dearpygui.dearpygui as dpg
import numpy as np
from skimage.color import rgb2gray
from skimage.io import imread
from skimage.util import img_as_ubyte

from pyptv import __version__, ptv
from pyptv.experiment import Experiment, Paramset
from pyptv.parameter_manager import ParameterManager


class DearPyPTVGUI:
    def __init__(self, yaml_file: Path, experiment: Experiment):
        self.yaml_file = yaml_file
        self.exp = experiment
        self.exp_path = yaml_file.parent

        self.pass_init = False
        self.log_lines: list[str] = []

        self.num_cams = max(1, int(self.exp.get_n_cam()))
        self.orig_images: list[np.ndarray] = []

        self.current_camera = 0
        self.active_camera_id = "cam1"

        self.selected_paramset_index = 0

        self.camera_tags: dict[str, dict[str, str]] = {}
        self.overlay_data: dict[str, list[dict]] = {}
        self.view_state: dict[str, dict[str, float | bool]] = {}
        self.imx = 640
        self.imy = 480

        self.cpar = None
        self.spar = None
        self.vpar = None
        self.track_par = None
        self.tpar = None
        self.cals = None
        self.epar = None

        self.detections = None
        self.corrected = None
        self.sorted_pos = None
        self.sorted_corresp = None
        self.num_targs = None
        self.target_filenames = []

        self._refresh_geometry_from_params()
        self.orig_images = [self._blank_image() for _ in range(self.num_cams)]

    def _refresh_geometry_from_params(self) -> None:
        ptv_params = self.exp.get_parameter("ptv") or {}
        self.imx = int(ptv_params.get("imx", 640))
        self.imy = int(ptv_params.get("imy", 480))

    def _blank_image(self) -> np.ndarray:
        return img_as_ubyte(np.zeros((self.imy, self.imx), dtype=np.uint8))

    def _append_log(self, message: str) -> None:
        self.log_lines.append(message)
        if len(self.log_lines) > 300:
            self.log_lines = self.log_lines[-300:]

        if dpg.does_item_exist("message_bar"):
            dpg.set_value("message_bar", message)
        if dpg.does_item_exist("log_box"):
            dpg.set_value("log_box", "\n".join(self.log_lines))

    def _gray_to_rgba_texture(self, gray: np.ndarray) -> list[float]:
        image = gray.astype(np.float32) / 255.0
        rgba = np.zeros((gray.shape[0], gray.shape[1], 4), dtype=np.float32)
        rgba[..., 0] = image
        rgba[..., 1] = image
        rgba[..., 2] = image
        rgba[..., 3] = 1.0
        return rgba.ravel().tolist()

    def _ensure_gray_size(self, image: np.ndarray) -> np.ndarray:
        h, w = image.shape[:2]
        if h == self.imy and w == self.imx:
            return image

        out = np.zeros((self.imy, self.imx), dtype=np.uint8)
        copy_h = min(self.imy, h)
        copy_w = min(self.imx, w)
        out[:copy_h, :copy_w] = image[:copy_h, :copy_w]
        return out

    def _load_gray_image(self, image_path: str) -> np.ndarray:
        path = Path(image_path)
        if not path.exists():
            self._append_log(f"Image not found: {path}")
            return self._blank_image()

        im = imread(path)
        if im.ndim > 2:
            im = rgb2gray(im)
        im = img_as_ubyte(im)
        return self._ensure_gray_size(im)

    def _draw_cross(self, cam_id: str, x: float, y: float, color=(255, 0, 0, 255), size: int = 4) -> None:
        self.overlay_data.setdefault(cam_id, []).append(
            {
                "kind": "cross",
                "x": float(x),
                "y": float(y),
                "color": color,
                "size": int(size),
            }
        )
        self._render_camera(cam_id)

    def _draw_line(self, cam_id: str, x1: float, y1: float, x2: float, y2: float, color=(0, 255, 0, 255)) -> None:
        self.overlay_data.setdefault(cam_id, []).append(
            {
                "kind": "line",
                "x1": float(x1),
                "y1": float(y1),
                "x2": float(x2),
                "y2": float(y2),
                "color": color,
            }
        )
        self._render_camera(cam_id)

    def _draw_text(self, cam_id: str, x: float, y: float, txt: str, color=(255, 255, 0, 255)) -> None:
        self.overlay_data.setdefault(cam_id, []).append(
            {
                "kind": "text",
                "x": float(x),
                "y": float(y),
                "text": str(txt),
                "color": color,
            }
        )
        self._render_camera(cam_id)

    def _canvas_size(self, cam_id: str) -> tuple[float, float]:
        view_tag = f"view_{cam_id}"
        if dpg.does_item_exist(view_tag):
            width, height = dpg.get_item_rect_size(view_tag)
            if width > 1 and height > 1:
                return float(width), float(height)

        canvas_tag = f"canvas_{cam_id}"
        if dpg.does_item_exist(canvas_tag):
            width, height = dpg.get_item_rect_size(canvas_tag)
            if width > 1 and height > 1:
                return float(width), float(height)
        state = self.view_state.setdefault(cam_id, {})
        return float(state.get("canvas_w", self.imx)), float(state.get("canvas_h", self.imy))

    def _view_transform(self, cam_id: str) -> tuple[float, float, float, float, float]:
        state = self.view_state.setdefault(
            cam_id,
            {
                "zoom": 1.0,
                "pan_x": 0.0,
                "pan_y": 0.0,
                "fit": True,
                "canvas_w": float(self.imx),
                "canvas_h": float(self.imy),
            },
        )

        canvas_w, canvas_h = self._canvas_size(cam_id)
        state["canvas_w"] = canvas_w
        state["canvas_h"] = canvas_h

        if bool(state.get("fit", True)):
            scale = min(canvas_w / max(1.0, float(self.imx)), canvas_h / max(1.0, float(self.imy)))
            pan_x = (canvas_w - (self.imx * scale)) / 2.0
            pan_y = (canvas_h - (self.imy * scale)) / 2.0
        else:
            scale = float(state.get("zoom", 1.0))
            pan_x = float(state.get("pan_x", 0.0))
            pan_y = float(state.get("pan_y", 0.0))

        return scale, pan_x, pan_y, canvas_w, canvas_h

    def _to_canvas(self, cam_id: str, x: float, y: float) -> tuple[float, float]:
        scale, pan_x, pan_y, _, _ = self._view_transform(cam_id)
        return (pan_x + (x * scale), pan_y + (y * scale))

    def _render_camera(self, cam_id: str) -> None:
        canvas_tag = f"canvas_{cam_id}"
        draw_tag = f"draw_{cam_id}"
        texture_tag = f"tex_{cam_id}"
        if not (dpg.does_item_exist(canvas_tag) and dpg.does_item_exist(texture_tag)):
            return

        canvas_w, canvas_h = self._canvas_size(cam_id)
        if canvas_w > 1 and canvas_h > 1:
            dpg.configure_item(canvas_tag, width=int(canvas_w), height=int(canvas_h))

        dpg.delete_item(canvas_tag, children_only=True)

        scale, pan_x, pan_y, _, _ = self._view_transform(cam_id)
        dpg.draw_image(
            texture_tag,
            (pan_x, pan_y),
            (pan_x + (self.imx * scale), pan_y + (self.imy * scale)),
            parent=canvas_tag,
            tag=f"image_{cam_id}",
        )

        dpg.add_draw_layer(parent=canvas_tag, tag=draw_tag)
        for item in self.overlay_data.get(cam_id, []):
            if item["kind"] == "cross":
                cx, cy = self._to_canvas(cam_id, float(item["x"]), float(item["y"]))
                size = max(2.0, float(item["size"]) * scale)
                color = item["color"]
                dpg.draw_circle((cx, cy), size, color=color, fill=(color[0], color[1], color[2], 90), parent=draw_tag)
            elif item["kind"] == "line":
                x1, y1 = self._to_canvas(cam_id, float(item["x1"]), float(item["y1"]))
                x2, y2 = self._to_canvas(cam_id, float(item["x2"]), float(item["y2"]))
                dpg.draw_line((x1, y1), (x2, y2), color=item["color"], thickness=max(1.0, 2.0 * scale), parent=draw_tag)
            elif item["kind"] == "text":
                tx, ty = self._to_canvas(cam_id, float(item["x"]), float(item["y"]))
                dpg.draw_text((tx, ty), item["text"], color=item["color"], parent=draw_tag)

    def _set_fit(self, cam_id: str) -> None:
        state = self.view_state.setdefault(cam_id, {})
        state["fit"] = True
        self._render_camera(cam_id)

    def _set_zoom_100(self, cam_id: str) -> None:
        state = self.view_state.setdefault(cam_id, {})
        state["fit"] = False
        state["zoom"] = 1.0
        state["pan_x"] = 0.0
        state["pan_y"] = 0.0
        self._render_camera(cam_id)

    def _zoom(self, cam_id: str, factor: float) -> None:
        state = self.view_state.setdefault(cam_id, {})
        old_scale, old_pan_x, old_pan_y, canvas_w, canvas_h = self._view_transform(cam_id)
        state["fit"] = False

        new_scale = float(np.clip(old_scale * factor, 0.1, 20.0))
        cx = canvas_w / 2.0
        cy = canvas_h / 2.0

        ix = (cx - old_pan_x) / max(old_scale, 1e-8)
        iy = (cy - old_pan_y) / max(old_scale, 1e-8)

        state["zoom"] = new_scale
        state["pan_x"] = cx - (ix * new_scale)
        state["pan_y"] = cy - (iy * new_scale)
        self._render_camera(cam_id)

    def _pan(self, cam_id: str, dx: float, dy: float) -> None:
        state = self.view_state.setdefault(cam_id, {})
        state["fit"] = False
        state["pan_x"] = float(state.get("pan_x", 0.0)) + dx
        state["pan_y"] = float(state.get("pan_y", 0.0)) + dy
        if "zoom" not in state:
            state["zoom"] = 1.0
        self._render_camera(cam_id)

    def _clear_all_overlays(self) -> None:
        for cam_idx in range(self.num_cams):
            cam_id = f"cam{cam_idx + 1}"
            self.overlay_data[cam_id] = []
            self._render_camera(cam_id)

    def _update_texture(self, cam_idx: int, image: np.ndarray) -> None:
        cam_id = f"cam{cam_idx + 1}"
        texture_tag = f"tex_{cam_id}"
        if dpg.does_item_exist(texture_tag):
            dpg.set_value(texture_tag, self._gray_to_rgba_texture(image))
        self._render_camera(cam_id)

    def _update_all_textures(self) -> None:
        for i, image in enumerate(self.orig_images):
            self._update_texture(i, image)

    def _image_local_pos(self, cam_id: str) -> tuple[float, float]:
        mouse_x, mouse_y = dpg.get_mouse_pos(local=False)
        min_x, min_y = dpg.get_item_rect_min(f"canvas_{cam_id}")
        cx = float(mouse_x - min_x)
        cy = float(mouse_y - min_y)
        scale, pan_x, pan_y, _, _ = self._view_transform(cam_id)
        local_x = float(np.clip((cx - pan_x) / max(scale, 1e-8), 0, self.imx - 1))
        local_y = float(np.clip((cy - pan_y) / max(scale, 1e-8), 0, self.imy - 1))
        return local_x, local_y

    def _on_left_click(self, sender, app_data, user_data) -> None:
        cam_id = user_data
        self.active_camera_id = cam_id
        self.current_camera = int(cam_id.replace("cam", "")) - 1

        x, y = self._image_local_pos(cam_id)
        self._draw_cross(cam_id, x, y, color=(255, 0, 0, 255), size=5)
        self._draw_text(cam_id, x + 8, y + 8, f"({int(x)}, {int(y)})")
        self._append_log(f"Left click in {cam_id}: x={int(x)}, y={int(y)}")

    def _on_right_click(self, sender, app_data, user_data) -> None:
        cam_id = user_data
        self.active_camera_id = cam_id
        self.current_camera = int(cam_id.replace("cam", "")) - 1

        x, y = self._image_local_pos(cam_id)
        x2 = min(self.imx - 1, x + 120)
        y2 = min(self.imy - 1, y + 35)
        self._draw_line(cam_id, x, y, x2, y2, color=(0, 255, 0, 255))
        self._draw_text(cam_id, x2 + 6, y2 + 2, "right-click line", color=(0, 255, 255, 255))
        self._append_log(f"Right click in {cam_id}: x={int(x)}, y={int(y)}")

    def _clean_correspondences(self, tmp):
        x1, y1 = [], []
        for x in tmp:
            arr = x[(x != -999).any(axis=1)]
            x1.append(arr[:, 0])
            y1.append(arr[:, 1])
        return x1, y1

    def _draw_points_in_all_cams(self, xs, ys, color=(0, 0, 255, 255), size: int = 3) -> None:
        for cam_idx in range(self.num_cams):
            cam_id = f"cam{cam_idx + 1}"
            if cam_idx >= len(xs) or cam_idx >= len(ys):
                continue
            for x, y in zip(xs[cam_idx], ys[cam_idx]):
                self._draw_cross(cam_id, x, y, color=color, size=size)

    def _refresh_paramset_list(self) -> None:
        if not dpg.does_item_exist("paramset_container"):
            return

        dpg.delete_item("paramset_container", children_only=True)
        if not self.exp.paramsets:
            dpg.add_text("No parameter sets", parent="paramset_container")
            return

        for idx, paramset in enumerate(self.exp.paramsets):
            label = f"{paramset.name} ({paramset.yaml_path.name})"
            selected = idx == 0
            dpg.add_selectable(
                label=label,
                default_value=selected,
                parent="paramset_container",
                callback=self._on_select_paramset,
                user_data=idx,
            )

        self.selected_paramset_index = 0

    def _on_select_paramset(self, sender, app_data, user_data) -> None:
        self.selected_paramset_index = int(user_data)
        if 0 <= self.selected_paramset_index < len(self.exp.paramsets):
            p = self.exp.paramsets[self.selected_paramset_index]
            self._append_log(f"Selected paramset: {p.name}")

    def _set_active_paramset(self) -> None:
        if not self.exp.paramsets:
            self._append_log("No paramset available")
            return
        try:
            self.exp.set_active(self.selected_paramset_index)
            self._refresh_geometry_from_params()
            self._append_log(f"Active paramset set: {self.exp.active_params.name}")
            self._refresh_paramset_list()
        except Exception as exc:
            self._append_log(f"Failed to set active paramset: {exc}")

    def _copy_paramset(self) -> None:
        if not self.exp.paramsets:
            self._append_log("No paramset available")
            return

        src = self.exp.paramsets[self.selected_paramset_index]
        parent_dir = src.yaml_path.parent
        existing = list(parent_dir.glob("parameters_*.yaml"))
        numbers = []
        for yf in existing:
            parts = yf.stem.split("_")
            if parts and parts[-1].isdigit():
                numbers.append(int(parts[-1]))
        next_num = max(numbers, default=0) + 1

        new_name = f"{src.name}_{next_num}"
        new_yaml = parent_dir / f"parameters_{new_name}.yaml"

        try:
            shutil.copy(src.yaml_path, new_yaml)
            self.exp.addParamset(new_name, new_yaml)
            self._append_log(f"Copied paramset to {new_yaml.name}")
            self._refresh_paramset_list()
        except Exception as exc:
            self._append_log(f"Copy paramset failed: {exc}")

    def _delete_paramset(self) -> None:
        if not self.exp.paramsets:
            self._append_log("No paramset available")
            return
        try:
            target = self.exp.paramsets[self.selected_paramset_index]
            self.exp.delete_paramset(target)
            self._append_log(f"Deleted paramset: {target.name}")
            self._refresh_paramset_list()
        except Exception as exc:
            self._append_log(f"Delete paramset failed: {exc}")

    def action_init_reload(self) -> None:
        try:
            if self.exp.active_params is None and self.exp.paramsets:
                self.exp.set_active(0)

            self._refresh_geometry_from_params()
            ptv_params = self.exp.get_parameter("ptv") or {}
            img_names = ptv_params.get("img_name", [])

            new_images = [self._blank_image() for _ in range(self.num_cams)]

            if ptv_params.get("splitter", False):
                if img_names:
                    source = Path(img_names[0])
                    if source.exists():
                        tmp_img = imread(source)
                        if tmp_img.ndim > 2:
                            tmp_img = rgb2gray(tmp_img)
                        split_imgs = ptv.image_split(tmp_img)
                        for i in range(min(self.num_cams, len(split_imgs))):
                            new_images[i] = self._ensure_gray_size(img_as_ubyte(split_imgs[i]))
            else:
                for i in range(self.num_cams):
                    if i < len(img_names):
                        new_images[i] = self._load_gray_image(img_names[i])

            self.orig_images = new_images
            (
                self.cpar,
                self.spar,
                self.vpar,
                self.track_par,
                self.tpar,
                self.cals,
                self.epar,
            ) = ptv.py_start_proc_c(self.exp.pm)

            self.target_filenames = self.exp.pm.get_target_filenames()
            self._update_all_textures()
            self._clear_all_overlays()
            self.pass_init = True
            self._append_log("Init / Reload completed")
        except Exception as exc:
            self._append_log(f"Init / Reload failed: {exc}")

    def action_highpass(self) -> None:
        if not self.pass_init:
            self._append_log("Please run Init / Reload first")
            return
        try:
            ptv_params = self.exp.get_parameter("ptv") or {}
            masking = self.exp.get_parameter("masking") or {}

            if ptv_params.get("negative", False):
                self.orig_images = [ptv.negative(im) for im in self.orig_images]

            if masking.get("mask_flag", False):
                base = masking.get("mask_base_name", "")
                for i in range(self.num_cams):
                    bg_name = base.replace("#", str(i))
                    bg_path = Path(bg_name)
                    if bg_path.exists():
                        bg = imread(bg_path)
                        if bg.ndim > 2:
                            bg = rgb2gray(bg)
                        bg = img_as_ubyte(bg)
                        bg = self._ensure_gray_size(bg)
                        self.orig_images[i] = np.clip(self.orig_images[i].astype(np.int16) - bg.astype(np.int16), 0, 255).astype(np.uint8)

            self.orig_images = ptv.py_pre_processing_c(self.num_cams, self.orig_images, ptv_params)
            self._update_all_textures()
            self._append_log("High pass finished")
        except Exception as exc:
            self._append_log(f"High pass failed: {exc}")

    def action_image_coord(self) -> None:
        if not self.pass_init:
            self._append_log("Please run Init / Reload first")
            return
        try:
            ptv_params = self.exp.get_parameter("ptv") or {}
            targ_rec = self.exp.get_parameter("targ_rec") or {}
            target_params = {"targ_rec": targ_rec}

            self.detections, self.corrected = ptv.py_detection_proc_c(
                self.num_cams,
                self.orig_images,
                ptv_params,
                target_params,
            )

            xs = [[t.pos()[0] for t in row] for row in self.detections]
            ys = [[t.pos()[1] for t in row] for row in self.detections]
            self._draw_points_in_all_cams(xs, ys, color=(0, 0, 255, 255), size=3)
            self._append_log("Image coord detection completed")
        except Exception as exc:
            self._append_log(f"Image coord failed: {exc}")

    def action_correspondences(self) -> None:
        if self.detections is None or self.corrected is None:
            self._append_log("Run Image coord first")
            return
        if self.cals is None or self.vpar is None or self.cpar is None:
            self._append_log("Init processing state is incomplete")
            return

        try:
            self.sorted_pos, self.sorted_corresp, self.num_targs = ptv.py_correspondences_proc_c(self)

            names = ["pair", "tripl", "quad"]
            colors = [(255, 255, 0, 255), (0, 255, 0, 255), (255, 0, 0, 255)]

            if self.num_cams > 1 and self.sorted_pos is not None and len(self.sorted_pos) > 0:
                for i, subset in enumerate(reversed(self.sorted_pos)):
                    if i >= len(names):
                        break
                    xvals, yvals = self._clean_correspondences(subset)
                    self._draw_points_in_all_cams(xvals, yvals, color=colors[i], size=3)

            self._append_log("Correspondences completed")
        except Exception as exc:
            self._append_log(f"Correspondences failed: {exc}")

    def _build_menu(self) -> None:
        with dpg.menu_bar():
            with dpg.menu(label="File"):
                dpg.add_menu_item(label="Open", callback=lambda: self._append_log("Use CLI argument to open YAML"))
                dpg.add_menu_item(label="Save Parameters", callback=lambda: self.exp.save_parameters())
                dpg.add_menu_item(label="Exit", callback=lambda: dpg.stop_dearpygui())

            with dpg.menu(label="Start"):
                dpg.add_menu_item(label="Init / Reload", callback=lambda: self.action_init_reload())

            with dpg.menu(label="Preprocess"):
                dpg.add_menu_item(label="High pass filter", callback=lambda: self.action_highpass())
                dpg.add_menu_item(label="Image coord", callback=lambda: self.action_image_coord())
                dpg.add_menu_item(label="Correspondences", callback=lambda: self.action_correspondences())

            with dpg.menu(label="View"):
                dpg.add_menu_item(label="Clear overlays", callback=lambda: self._clear_all_overlays())

    def _build_left_panel(self) -> None:
        with dpg.child_window(width=320, height=760, border=True):
            dpg.add_text("Experiment")
            with dpg.tree_node(label="Parameter Sets", default_open=True):
                dpg.add_child_window(tag="paramset_container", width=-1, height=220, border=True)

            dpg.add_spacer(height=6)
            dpg.add_button(label="Set active", width=-1, callback=lambda: self._set_active_paramset())
            dpg.add_button(label="Copy set", width=-1, callback=lambda: self._copy_paramset())
            dpg.add_button(label="Delete set", width=-1, callback=lambda: self._delete_paramset())
            dpg.add_spacer(height=8)
            dpg.add_button(label="Init / Reload", width=-1, callback=lambda: self.action_init_reload())
            dpg.add_button(label="High pass", width=-1, callback=lambda: self.action_highpass())
            dpg.add_button(label="Image coord", width=-1, callback=lambda: self.action_image_coord())
            dpg.add_button(label="Correspondences", width=-1, callback=lambda: self.action_correspondences())

            dpg.add_spacer(height=8)
            dpg.add_input_text(tag="log_box", multiline=True, readonly=True, height=350, width=-1)

    def _build_camera_tabs(self) -> None:
        with dpg.child_window(width=-1, height=760, border=True):
            with dpg.texture_registry(show=False, tag="texture_registry"):
                for i in range(self.num_cams):
                    cam_id = f"cam{i + 1}"
                    dpg.add_dynamic_texture(
                        self.imx,
                        self.imy,
                        self._gray_to_rgba_texture(self.orig_images[i]),
                        tag=f"tex_{cam_id}",
                    )

            with dpg.tab_bar(tag="camera_tabs"):
                for i in range(self.num_cams):
                    cam_id = f"cam{i + 1}"
                    with dpg.tab(label=f"Camera {i + 1}"):
                        with dpg.group(horizontal=True):
                            dpg.add_button(label="Zoom +", callback=lambda s, a, c=cam_id: self._zoom(c, 1.25))
                            dpg.add_button(label="Zoom -", callback=lambda s, a, c=cam_id: self._zoom(c, 0.8))
                            dpg.add_button(label="Fit", callback=lambda s, a, c=cam_id: self._set_fit(c))
                            dpg.add_button(label="100%", callback=lambda s, a, c=cam_id: self._set_zoom_100(c))
                            dpg.add_button(label="◀", callback=lambda s, a, c=cam_id: self._pan(c, -40.0, 0.0))
                            dpg.add_button(label="▶", callback=lambda s, a, c=cam_id: self._pan(c, 40.0, 0.0))
                            dpg.add_button(label="▲", callback=lambda s, a, c=cam_id: self._pan(c, 0.0, -40.0))
                            dpg.add_button(label="▼", callback=lambda s, a, c=cam_id: self._pan(c, 0.0, 40.0))

                        with dpg.child_window(tag=f"view_{cam_id}", width=-1, height=-1, border=False, no_scrollbar=True):
                            dpg.add_drawlist(width=10, height=10, tag=f"canvas_{cam_id}")
                            self.overlay_data[cam_id] = []
                            self.view_state[cam_id] = {
                                "zoom": 1.0,
                                "pan_x": 0.0,
                                "pan_y": 0.0,
                                "fit": True,
                                "canvas_w": float(self.imx),
                                "canvas_h": float(self.imy),
                            }
                            self._render_camera(cam_id)

                            handler_tag = f"handler_{cam_id}"
                            with dpg.item_handler_registry(tag=handler_tag):
                                dpg.add_item_clicked_handler(button=dpg.mvMouseButton_Left, callback=self._on_left_click, user_data=cam_id)
                                dpg.add_item_clicked_handler(button=dpg.mvMouseButton_Right, callback=self._on_right_click, user_data=cam_id)
                            dpg.bind_item_handler_registry(f"canvas_{cam_id}", handler_tag)

                            self.camera_tags[cam_id] = {
                                "texture": f"tex_{cam_id}",
                                "image": f"image_{cam_id}",
                                "canvas": f"canvas_{cam_id}",
                                "draw": f"draw_{cam_id}",
                            }

    def build(self) -> None:
        dpg.create_context()
        dpg.create_viewport(title=f"pyPTV DearPyGui {__version__}", width=1420, height=920)

        with dpg.window(tag="main_window", label=f"pyPTV DearPyGui {__version__}", width=1400, height=890):
            self._build_menu()
            with dpg.group(horizontal=True):
                self._build_left_panel()
                self._build_camera_tabs()
            dpg.add_separator()
            dpg.add_text("Ready", tag="message_bar")

        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("main_window", True)

        self._refresh_paramset_list()
        self._append_log(f"Loaded experiment from {self.yaml_file}")

        dpg.start_dearpygui()
        dpg.destroy_context()


def _create_experiment_from_args(argv: list[str]) -> tuple[Path, Experiment, Path]:
    software_path = Path.cwd().resolve()

    yaml_file: Path
    exp: Experiment
    exp_path: Path

    if len(argv) == 2:
        arg_path = Path(argv[1]).resolve()
        if arg_path.is_file() and arg_path.suffix in {".yaml", ".yml"}:
            pm = ParameterManager()
            pm.from_yaml(arg_path)
            exp = Experiment(pm=pm)
            exp.populate_runs(arg_path.parent)
            yaml_file = arg_path
            exp_path = arg_path.parent
        elif arg_path.is_dir():
            exp = Experiment()
            exp.populate_runs(arg_path)
            if exp.active_params is None:
                raise OSError(f"No parameter sets found in {arg_path}")
            yaml_file = exp.active_params.yaml_path
            exp_path = arg_path
        else:
            raise OSError(f"Argument must be a directory or YAML file, got: {arg_path}")
    else:
        exp_path = software_path / "tests" / "test_cavity"
        exp = Experiment()
        exp.populate_runs(exp_path)
        if exp.active_params is None:
            raise OSError(f"No parameter sets found in default folder {exp_path}")
        yaml_file = exp.active_params.yaml_path

    if not yaml_file.exists():
        raise OSError(f"YAML parameter file does not exist: {yaml_file}")

    return yaml_file, exp, software_path


def main() -> None:
    yaml_file, exp, software_path = _create_experiment_from_args(sys.argv)

    try:
        os.chdir(yaml_file.parent)
        gui = DearPyPTVGUI(yaml_file=yaml_file, experiment=exp)
        gui.build()
    finally:
        os.chdir(software_path)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Error: {exc}")
        sys.exit(1)
