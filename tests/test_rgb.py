import os
from optv.parameters import ControlParams
from optv.image_processing import preprocess_image
from skimage.io import imread
from skimage.color import rgb2gray
from skimage import img_as_ubyte

images = ['../rgb/cam1.png','../rgb/cam1.jpg','../rgb/cam1.tiff']



def test_rgb():
    print(os.path.abspath(os.curdir))

    with open('./parameters/ptv.par','r') as f:
        n_cams = int(f.readline())

    # Control parameters
    cpar = ControlParams(n_cams)
    cpar.read_control_par('./parameters/ptv.par')

    for imname in images:
        img = imread(imname)
        print(img.shape)
        if img.ndim > 2:
            img = img_as_ubyte(rgb2gray(img))
        # time.sleep(.1) # I'm not sure we need it here
        preprocess_image(img, 0, cpar, 12)
