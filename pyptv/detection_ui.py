import napari
import numpy as np
from magicgui import magicgui
from skimage.io import imread
from skimage.color import rgb2gray
from pyptv import ptv, parameters as par
from pathlib import Path

# --- Load parameters (adjust path as needed) ---
par_path = Path("tests/test_cavity/parameters")  # or your actual parameters path

# Read number of cameras from ptv.par
with open(par_path / "ptv.par", "r", encoding="utf-8") as f:
    n_cams = int(f.readline())

# Load all parameter objects
cpar, spar, vpar, track_par, tpar, cals, epar = ptv.py_start_proc_c(n_cams)
tpar.read(str(par_path / "detect_plate.par"))

# --- Load and preprocess image ---
def load_image(path, inverse=False, highpass=False):
    im = imread(path)
    if im.ndim > 2:
        im = rgb2gray(im)
    # TODO: Add highpass filter if needed
    return im

image_path = str(par_path.parent / "img" / "cam1.tif")  # Example image path
image = load_image(image_path)

# --- Start Napari viewer ---
viewer = napari.Viewer()
image_layer = viewer.add_image(image, name="Image")

# --- Points layer for detected dots ---
points_layer = viewer.add_points(
    [], size=8, face_color='orange', name='Detections'
)

# --- Shapes layer for lines/quivers (optional) ---
shapes_layer = viewer.add_shapes(
    [], shape_type='line', edge_color='blue', name='Lines'
)

# --- Text layer for labels (optional) ---
text_layer = viewer.add_text(
    [], text='', color='yellow', name='Labels'
)

# --- Detection function using ptv.py_detection_proc_c ---
def detect_particles(image):
    detections, _ = ptv.py_detection_proc_c([image], cpar, tpar, cals)
    targs = detections[0]
    targs.sort_y()
    x = [i.pos()[0] for i in targs]
    y = [i.pos()[1] for i in targs]
    return np.stack([y, x], axis=1)  # napari uses (row, col)

# --- Magicgui widget for parameter control (expand as needed) ---
@magicgui(call_button="Detect Dots")
def detect_button():
    points_layer.data = detect_particles(image_layer.data)

viewer.window.add_dock_widget(detect_button, area="right")

# --- Magicgui widget for adding crosses manually ---
@magicgui(call_button="Add Cross", x={"label": "X"}, y={"label": "Y"})
def add_cross(x: int = 0, y: int = 0):
    points = points_layer.data.tolist()
    points.append([y, x])  # napari uses (row, col)
    points_layer.data = np.array(points)

viewer.window.add_dock_widget(add_cross, area="right")

# --- Mouse click callback to add crosses interactively ---
@viewer.mouse_drag_callbacks.append
def on_click(viewer, event):
    if event.type == 'mouse_press' and event.button == 1:
        coords = np.round(event.position).astype(int)
        points = points_layer.data.tolist()
        points.append(coords)
        points_layer.data = np.array(points)

# --- Optional: Reset button ---
@magicgui(call_button="Reset")
def reset_button():
    points_layer.data = []

viewer.window.add_dock_widget(reset_button, area="right")

# --- Show the viewer ---
napari.run()