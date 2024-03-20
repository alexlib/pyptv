#!/usr/bin/env python
# coding: utf-8

# prepare static background images for the series using Python
# this works with the branch called remove_static_background on pyptv github
# https://github.com/alexlib/pyptv/

import numpy as np
import matplotlib.pyplot as plt
import skimage.io as skio
import pathlib

# Create static median background and store for PyPTV use as a mask
# How to use in PyPTV: 
# 1) checkmark Subtract mask
# 2) insert the name of the file as background_mask_# ( will replaced by camera id, 0...N-1)

# We can create any length, for large series, 10 images shall be sufficient

N = 10

# Read N images per camera
for cam_num in range(4):
    
    filelist = list(pathlib.Path(f'img/Camera_{cam_num+1}/').rglob('*.tif')) # in some sets we use Camera_1, 2, 3, 4
    filelist.sort()
    print(filelist[:3], filelist[-3:])
    

    image_array = []
    for i, file in enumerate(filelist[:N]):
        image_array.append(skio.imread(file))
        
    image_array = np.array(image_array)
    
    # Create median 
    median_image = np.median(image_array, axis=0)
    plt.figure()
    plt.imshow(median_image, cmap='gray')
    plt.show()
    
    

    plt.figure()
    plt.imshow(np.clip(image_array[0,:,:] - median_image, 0, 255).astype(np.uint8), cmap='gray')
    plt.show()


    # Store median image in the top directory
    skio.imsave(f'background_mask_{cam_num}.tif', median_image)



