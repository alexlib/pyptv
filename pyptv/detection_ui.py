import napari
import numpy as np
from magicgui import magicgui
from skimage.io import imread
from skimage import img_as_ubyte
from skimage.color import rgb2gray
from optv.parameters import TargetParams, ControlParams
from optv.image_processing import preprocess_image

from pathlib import Path
from optv.segmentation import target_recognition


# --- Globals ---
tpar = TargetParams()
cpar = ControlParams(num_cam=1) # one image for now
current_image = None

# --- Napari viewer and points layer ---
viewer = napari.Viewer()
points_layer = viewer.add_points([], size=8, face_color='orange', name='Detections')

# --- 1. Image path and load image ---
@magicgui(call_button="Load Image", image_path={"mode": "r"})
def load_image(image_path=Path(".")):
    global current_image
    if not image_path.exists():
        print("Image file does not exist!")
        return
    img = imread(str(image_path))
    if img.ndim == 3:
        img = rgb2gray(img)

    if img.dtype != np.uint8:
        img = img_as_ubyte(img)  # Ensure image is in uint8 format

    imx, imy = img.shape
    cpar.set_image_size(imx, imy)

    current_image = img
    # Remove previous image layers
    for l in list(viewer.layers):
        if isinstance(l, napari.layers.Image):
            viewer.layers.remove(l)
    viewer.add_image(img, name=image_path.name)
    run_detection()

viewer.window.add_dock_widget(load_image, area="right")

# --- 2. Highpass and Inverse image checkboxes ---
@magicgui(call_button="Apply", highpass={"label": "Highpass"}, inverse={"label": "Inverse"})
def image_options(highpass: bool = False, inverse: bool = False):
    global current_image
    if current_image is None:
        print("No image loaded.")
        return
    img = current_image.copy()
    # Use ptv's preprocessing for highpass/inverse
    if inverse: 
        img = 255 - img  # Inverse the image
    if highpass:
        img = preprocess_image(img, 0, cpar, 3)

    # Remove previous processed image layers
    for l in list(viewer.layers):
        if l.name == "Processed Image":
            viewer.layers.remove(l)
    processed_layer = viewer.add_image(img, name="Processed Image", visible=True)
    viewer.layers.selection.active = processed_layer  # Make it active

    run_detection()

viewer.window.add_dock_widget(image_options, area="right")

# --- 3. Detection parameter sliders (from tpar) ---
@magicgui(
    call_button="Update Parameters",
    threshold={"label": "Threshold", "min": 0, "max": 255, "widget_type": "Slider"},
    min_npix={"label": "Min npix", "min": 0, "max": 100, "widget_type": "Slider"},
    max_npix={"label": "Max npix", "min": 1, "max": 500, "widget_type": "Slider"},
    min_npix_x={"label": "Min npix in x", "min": 1, "max": 50, "widget_type": "Slider"},
    max_npix_x={"label": "Max npix in x", "min": 1, "max": 100, "widget_type": "Slider"},
    min_npix_y={"label": "Min npix in y", "min": 1, "max": 50, "widget_type": "Slider"},
    max_npix_y={"label": "Max npix in y", "min": 1, "max": 100, "widget_type": "Slider"},
    disco={"label": "Discontinuity", "min": 0, "max": 255, "widget_type": "Slider"},
    sum_of_grey={"label": "Sum of greyvalue", "min": 0, "max": 1000, "widget_type": "Slider"},
)
def tpar_controls(
    threshold=50,
    min_npix=5,
    max_npix=100,
    min_npix_x=2,
    max_npix_x=20,
    min_npix_y=2,
    max_npix_y=20,
    disco=10,
    sum_of_grey=100,
):
    # Use the correct setters as in detection_gui.py
    tpar.set_grey_thresholds([threshold])
    tpar.set_pixel_count_bounds([min_npix, max_npix])
    tpar.set_xsize_bounds([min_npix_x, max_npix_x])
    tpar.set_ysize_bounds([min_npix_y, max_npix_y])
    tpar.set_max_discontinuity(disco)
    tpar.set_min_sum_grey(sum_of_grey)
    run_detection()

viewer.window.add_dock_widget(tpar_controls, area="right")

# --- 4. Detection logic ---
def run_detection():
    image_layers = [l for l in viewer.layers if isinstance(l, napari.layers.Image)]
    if not image_layers:
        print("No image loaded!")
        return
    img = image_layers[-1].data
    # Dummy cpar, cals for demonstration; replace with real ones as needed
    try:
        targs = target_recognition(img,tpar, 0, cpar)
        targs.sort_y()
        x = [i.pos()[0] for i in targs]
        y = [i.pos()[1] for i in targs]
        points_layer.data = np.stack([y, x], axis=1) if x and y else np.empty((0, 2))
    except Exception as e:
        print(f"Detection failed: {e}")
        points_layer.data = np.empty((0, 2))

# --- 5. Manual cross addition and reset ---
@magicgui(call_button="Add Cross", x={"label": "X"}, y={"label": "Y"})
def add_cross(x: int = 0, y: int = 0):
    points = points_layer.data.tolist()
    points.append([y, x])
    points_layer.data = np.array(points)

viewer.window.add_dock_widget(add_cross, area="right")

@magicgui(call_button="Reset")
def reset_button():
    points_layer.data = []

viewer.window.add_dock_widget(reset_button, area="right")

def on_click(viewer, event):
    if event.type == 'mouse_press' and event.button == 1:
        coords = np.round(event.position).astype(int)
        points = points_layer.data.tolist()
        points.append(coords.tolist())
        points_layer.data = np.array(points)


napari.run()