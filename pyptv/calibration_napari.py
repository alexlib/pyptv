# import napari
# from skimage.io import imread
# from magicgui import magicgui
# from napari.types import ImageData, LabelsData


# import optv
# import pathlib
# import os
# import matplotlib.pyplot as plt


# from optv.imgcoord import image_coordinates  # type: ignore
# from optv.transforms import convert_arr_metric_to_pixel  # type: ignore
# from optv.orientation import match_detection_to_ref  # type: ignore
# from optv.orientation import external_calibration, full_calibration  # type: ignore
# from optv.calibration import Calibration  # type: ignore
# from optv.tracking_framebuf import TargetArray  # type: ignore


# working_folder = pathlib.Path('/home/user/Downloads/test_8/')
# os.chdir(working_folder)

# working_folder = pathlib.Path('.')
# par_path = working_folder / "parameters"

# with open(par_path / "ptv.par", "r", encoding="utf8") as f:
#     n_cams = int(f.readline())
    
    

# def flood(image: ImageData, delta: float=0, new_level: int=0) -> LabelsData:
#     new_level = int(delta*85)
#     label_image = image <= new_level
#     label_image = label_image.astype(int)*13 # label 13 is blue in napari
#     return(label_image)

# viewer = napari.Viewer()
# napari_image = imread((working_folder / 'cal/cam1.tif'))    # Reads an image from file
# viewer.add_image(napari_image, name='cam1')              # Adds the image to the viewer and give the image layer a name 

# flood_widget = magicgui(flood)                                    # Create GUI with magicgui
# viewer.window.add_dock_widget(flood_widget, area='right')         # Add our gui instance to napari viewer

# napari.run()


# import numpy as np
# import napari

# viewer = napari.Viewer()
# viewer.add_image(np.random.random((5, 5, 5)), colormap='red', opacity=0.8)
# viewer.text_overlay.visible = True

# @viewer.dims.events.current_step.connect
# def update_slider(event):
#     time = viewer.dims.current_step[0]
#     viewer.text_overlay.text = f"{time:1.1f} time"

# napari.run()