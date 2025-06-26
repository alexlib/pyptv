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
from magicgui.widgets import Slider, Container, CheckBox, PushButton, Widget, Slider as MGSlider


# --- Globals ---
tpar = TargetParams()
cpar = ControlParams(1) # one image for now

# --- Napari viewer and points layer ---
viewer = napari.Viewer()


# --- 2. Preprocessing widget (Highpass/Inverse/Apply) ---

# State variable to track if detection has been run
_detection_enabled = {'value': False}

# Preprocessing widget
highpass_cb = CheckBox(text="Highpass")
inverse_cb = CheckBox(text="Inverse")
apply_btn = PushButton(text="Apply")

# --- 3. Detect dots button ---
detect_btn = PushButton(text="Detect dots")

# --- 4. Sliders for tpar (initially disabled) ---
tpar_sliders = {
    'threshold': MGSlider(label="Threshold", min=0, max=255, value=50, enabled=False),
    'min_npix': MGSlider(label="Min npix", min=0, max=100, value=5, enabled=False),
    'max_npix': MGSlider(label="Max npix", min=1, max=500, value=100, enabled=False),
    'min_npix_x': MGSlider(label="Min npix in x", min=1, max=50, value=2, enabled=False),
    'max_npix_x': MGSlider(label="Max npix in x", min=1, max=100, value=20, enabled=False),
    'min_npix_y': MGSlider(label="Min npix in y", min=1, max=50, value=2, enabled=False),
    'max_npix_y': MGSlider(label="Max npix in y", min=1, max=100, value=20, enabled=False),
    'disco': MGSlider(label="Discontinuity", min=0, max=255, value=10, enabled=False),
    'sum_of_grey': MGSlider(label="Sum of greyvalue", min=0, max=1000, value=100, enabled=False),
}

# --- Utility: get the single image layer ---
def get_single_image_layer():
    image_layers = [l for l in viewer.layers if isinstance(l, napari.layers.Image)]
    if not image_layers:
        print("No image layer found!")
        return None
    return image_layers[-1]

# --- Preprocessing logic ---
def apply_preprocessing():
    img_layer = get_single_image_layer()
    if img_layer is None:
        return
    img = img_layer.data.copy()
    if img.ndim == 3 and img.shape[2] == 3:  # RGB image
        img = rgb2gray(img)  # Convert to grayscale
    
    img = img_as_ubyte(img)  # Convert to uint8
    cpar.set_image_size([img.shape[1],img.shape[0]])  # Set image size for control parameters
    if inverse_cb.value:
        img = 255 - img
    if highpass_cb.value:
        img = preprocess_image(img, 0, cpar, 3)
    # Replace image data in the same layer
    img_layer.data = img
    # Remove all other image layers except this one
    for l in list(viewer.layers):
        if isinstance(l, napari.layers.Image) and l is not img_layer:
            viewer.layers.remove(l)
    # After preprocessing, reset detection state
    _detection_enabled['value'] = False
    for s in tpar_sliders.values():
        s.enabled = False
    # points_layer.data = np.empty((0, 2))

apply_btn.clicked.connect(apply_preprocessing)

# --- Detection logic ---
def run_detection_and_enable_sliders():
    img_layer = get_single_image_layer()
    # Check if points layer exists; if not, create it
    points_layer = None
    for l in viewer.layers:
        if isinstance(l, napari.layers.Points) and l.name == 'Detections':
            points_layer = l
            break
    if points_layer is None:
        points_layer = viewer.add_points([], size=8, face_color='orange', name='Detections')

    if img_layer is None:
        return
    img = img_layer.data
    # Set tpar from sliders
    tpar.set_grey_thresholds([tpar_sliders['threshold'].value])
    tpar.set_pixel_count_bounds([tpar_sliders['min_npix'].value, tpar_sliders['max_npix'].value])
    tpar.set_xsize_bounds([tpar_sliders['min_npix_x'].value, tpar_sliders['max_npix_x'].value])
    tpar.set_ysize_bounds([tpar_sliders['min_npix_y'].value, tpar_sliders['max_npix_y'].value])
    tpar.set_max_discontinuity(tpar_sliders['disco'].value)
    tpar.set_min_sum_grey(tpar_sliders['sum_of_grey'].value)
    try:
        targs = target_recognition(img, tpar, 0, cpar)
        targs.sort_y()
        x = [i.pos()[0] for i in targs]
        y = [i.pos()[1] for i in targs]
        points_layer.data = np.stack([y, x], axis=1) if x and y else np.empty((0, 2))
        # Enable sliders after first detection
        if not _detection_enabled['value']:
            for s in tpar_sliders.values():
                s.enabled = True
            _detection_enabled['value'] = True
    except Exception as e:
        print(f"Detection failed: {e}")
        points_layer.data = np.empty((0, 2))

    # Move points layer to the top
    if points_layer in viewer.layers:
        viewer.layers.move(viewer.layers.index(points_layer), len(viewer.layers) - 1)

detect_btn.clicked.connect(run_detection_and_enable_sliders)

# --- Slider event: auto-detect after first detection ---
def on_slider_change(event=None):
    if _detection_enabled['value']:
        run_detection_and_enable_sliders()

for s in tpar_sliders.values():
    s.changed.connect(on_slider_change)

# --- Compose the UI ---
preproc_container = Container(widgets=[highpass_cb, inverse_cb, apply_btn])
sliders_container = Container(widgets=list(tpar_sliders.values()))

main_container = Container(widgets=[preproc_container, detect_btn, sliders_container])
viewer.window.add_dock_widget(main_container, area="right", name="Detection Controls")

# --- Points layer already created above ---

# # --- Optional: mouse click to add points (if desired) ---
# def on_click(viewer, event):
#     if event.type == 'mouse_press' and event.button == 1:
#         coords = np.round(event.position).astype(int)
#         points = points_layer.data.tolist()
#         points.append(coords.tolist())
#         points_layer.data = np.array(points)


napari.run()