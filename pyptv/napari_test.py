import napari
import imageio

# create a `Viewer` and `Image` layer here
viewer, image_layer = napari.imshow(imageio.v3.imread('tests/test_cavity/cal/cam1.tif'))

# print shape of image datas
print(image_layer.data.shape)

# start the event loop and show the viewer
napari.run()