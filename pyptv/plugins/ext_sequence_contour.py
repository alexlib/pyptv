import random

import numpy as np
from imageio.v3 import imread, imwrite
from pathlib import Path

from skimage import img_as_ubyte
from skimage import filters, measure, morphology
from skimage.color import rgb2gray, label2rgb
from skimage.segmentation import clear_border
from skimage.morphology import binary_erosion, binary_dilation, disk
from skimage.util import img_as_ubyte

from optv.correspondences import correspondences, MatchedCoords
from optv.tracker import default_naming
from optv.orientation import point_positions

import matplotlib.pyplot as plt


def mask_image(imname : Path, display: bool = False) -> np.ndarray:
    """Mask the image using a simple high pass filter.
    
    Parameters
    ----------
    img : np.ndarray
        The image to be masked.
        
    Returns
    -------
    np.ndarray
        The masked image.
    """
    
    img = imread(imname)
    if img.ndim > 2:
        img = rgb2gray(img)
    
    if img.dtype != np.uint8:
        img = img_as_ubyte(img)

    # Apply Gaussian filter to smooth the image
    smoothed_frame = filters.gaussian(img, sigma=5)
    
    if display:
        plt.figure()
        plt.imshow(smoothed_frame)
        plt.show()
    
    # Apply Otsu's thresholding method to segment the object
    thresh = filters.threshold_otsu(smoothed_frame)
    # print('Threshold:', thresh)
    binary_frame = smoothed_frame > 1.1*thresh
    
    if display:
        plt.figure()
        plt.imshow(binary_frame)
        plt.show()
    
    
    # binary_frame_cleared = clear_border(binary_frame, buffer_size=20)
    binary_frame_cleared = binary_frame.copy()
    
    # plt.figure()
    # plt.imshow(binary_frame_cleared)
    # plt.show()
    
    # Remove small bright objects
    cleaned_frame = morphology.remove_small_objects(binary_frame_cleared, min_size=100000)
    
    # %%
    # Apply morphological closing to close the boundary
    closed_cleaned_frame = binary_dilation(cleaned_frame, disk(21))
    closed_cleaned_frame = binary_erosion(closed_cleaned_frame, disk(21))
    
    if display:
        # Display the result
        plt.figure()
        plt.imshow(closed_cleaned_frame, cmap='gray')
        plt.title('Closed Boundary of Cleaned Frame')
        plt.show()
    
    
    # check the size of the second largest black hole
    # labeled_frame = measure.label(~closed_cleaned_frame)
    # regions = measure.regionprops(labeled_frame)
    # areas = np.array([r.area for r in regions])
    # area_to_remove = np.sort(areas)[-2] # 2nd largest, 1st is the surrounding
    
    # %%
    # Fill holes inside the binary frame to remove large black objects
    filled_frame = morphology.remove_small_holes(closed_cleaned_frame, area_threshold=2e6)
    
    if display:
        # # Display the result
        plt.figure()
        plt.imshow(filled_frame, cmap='gray')
        plt.title('Binary Frame with Large Black Objects Removed')
        plt.show()
    
    # %%
    
    # # Remove small objects and clear the border
    # cleaned_frame = morphology.remove_small_objects(binary_frame, min_size=100000)
    # # Fill holes inside the binary frame to remove dark islands
    # filled_frame = morphology.remove_small_holes(cleaned_frame, area_threshold=100000)
    
    # filled_frame = clear_border(filled_frame)
    
    # Label the segmented regions
    labeled_frame = measure.label(filled_frame)
    
    if display:
        # Show the labeled filled frame as a color labeled image
        plt.figure()
        plt.imshow(label2rgb(labeled_frame, image=img, bg_label=0))
        plt.title('Color Labeled Frame with Filled Holes')
        plt.show()
    
    # %%
    
    # Find region properties
    regions = measure.regionprops(labeled_frame)
    
    # Assuming the largest region is the object of interest
    largest_region = max(regions, key=lambda r: r.area)
    
    
    # Find the smooth contour that surrounds the largest region
    smooth_contour = morphology.convex_hull_image(largest_region.image)
    
    # Create an empty image to draw the smooth contour
    smooth_contour_image = np.zeros_like(labeled_frame, dtype=bool)
    
    # Place the smooth contour in the correct location
    minr, minc, maxr, maxc = largest_region.bbox
    smooth_contour_image[minr:maxr, minc:maxc] = smooth_contour
    
    if display:
        # Display the smooth contour on the labeled image
        plt.figure()
        plt.imshow(labeled_frame, cmap='jet')
        plt.contour(smooth_contour_image, colors='red', linewidths=2)
        plt.title(f'Segmented Object with Smooth Contour')
        plt.show()
    
    
    # Convert the largest region to a black and white image
    bw_image = np.zeros_like(labeled_frame, dtype=bool)
    bw_image[largest_region.coords[:, 0], largest_region.coords[:, 1]] = True
    
    # plt.figure(), plt.imshow(bw_image, cmap='gray')
    
    # Apply morphological closing to remove sharp spikes
    closed_image = binary_dilation(bw_image, disk(21))
    closed_image = binary_erosion(closed_image, disk(21))
    
    if display:
        # Display the result
        plt.figure()
        plt.imshow(closed_image, cmap='gray')
        plt.title('Smooth Boundary without Sharp Spikes')
        plt.show()
    
    
    # Apply morphological operations to get the external contour
    eroded_image = binary_erosion(closed_image, disk(1))
    external_contour = closed_image & ~eroded_image
    
    imwrite(imname.with_suffix('.jpg'), img_as_ubyte(external_contour))
    
    # Dilate the external contour for better visibility
    dilated_external_contour = binary_dilation(external_contour, disk(3))
    
    # Create a masked image of the same size as the input image
    masked_image = np.zeros_like(img, dtype=np.uint8)
    # Mask out (black) everything outside of closed_image
    masked_image[closed_image] = img[closed_image]
    
    if display:
        plt.figure()
        plt.imshow(masked_image)
        plt.show()

    return masked_image

class Sequence:
    """Sequence class defines external tracking addon for pyptv
    User needs to implement the following functions:
            do_sequence(self)

    Connection to C ptv module is given via self.ptv and provided by pyptv software
    Connection to active parameters is given via self.exp1 and provided by pyptv software.

    User responsibility is to read necessary files, make the calculations and write the files back.
    """

    def __init__(self, ptv=None, exp=None):
        self.ptv = ptv
        self.exp = exp

    def do_sequence(self):
        """ Copy of the sequence loop with one change we call everything as 
        self.ptv instead of ptv. 
        
        """
        # Sequence parameters    

        n_cams, cpar, spar, vpar, tpar, cals = (
            self.exp.n_cams,
            self.exp.cpar,
            self.exp.spar,
            self.exp.vpar,
            self.exp.tpar,
            self.exp.cals,
        )

        # # Sequence parameters
        # spar = SequenceParams(num_cams=n_cams)
        # spar.read_sequence_par(b"parameters/sequence.par", n_cams)


        # sequence loop for all frames
        first_frame = spar.get_first()
        last_frame = spar.get_last()
        print(f" From {first_frame = } to {last_frame = }")
        
        for frame in range(first_frame, last_frame + 1):
            # print(f"processing {frame = }")

            detections = []
            corrected = []
            for i_cam in range(n_cams):
                base_image_name = spar.get_img_base_name(i_cam).decode()
                imname = Path(base_image_name % frame) # works with jumps from 1 to 10 
                masked_image = mask_image(imname)

                # img = imread(imname)
                # if img.ndim > 2:
                #     img = rgb2gray(img)
                    
                # if img.dtype != np.uint8:
                #     img = img_as_ubyte(img)

                        
                
                high_pass = self.ptv.simple_highpass(masked_image, cpar)
                targs = self.ptv.target_recognition(high_pass, tpar, i_cam, cpar)

                targs.sort_y()
                detections.append(targs)
                masked_coords = MatchedCoords(targs, cpar, cals[i_cam])
                pos, _ = masked_coords.as_arrays()
                corrected.append(masked_coords)

            #        if any([len(det) == 0 for det in detections]):
            #            return False

            # Corresp. + positions.
            sorted_pos, sorted_corresp, _ = correspondences(
                detections, corrected, cals, vpar, cpar)

            # Save targets only after they've been modified:
            # this is a workaround of the proper way to construct _targets name
            for i_cam in range(n_cams):
                base_name = spar.get_img_base_name(i_cam).decode()
                # base_name = replace_format_specifiers(base_name) # %d to %04d
                self.ptv.write_targets(detections[i_cam], base_name, frame)

            print("Frame " + str(frame) + " had " +
                repr([s.shape[1] for s in sorted_pos]) + " correspondences.")

            # Distinction between quad/trip irrelevant here.
            sorted_pos = np.concatenate(sorted_pos, axis=1)
            sorted_corresp = np.concatenate(sorted_corresp, axis=1)

            flat = np.array([
                corrected[i].get_by_pnrs(sorted_corresp[i])
                for i in range(len(cals))
            ])
            pos, _ = point_positions(flat.transpose(1, 0, 2), cpar, cals, vpar)

            # if len(cals) == 1: # single camera case
            #     sorted_corresp = np.tile(sorted_corresp,(4,1))
            #     sorted_corresp[1:,:] = -1

            if len(cals) < 4:
                print_corresp = -1 * np.ones((4, sorted_corresp.shape[1]))
                print_corresp[:len(cals), :] = sorted_corresp
            else:
                print_corresp = sorted_corresp

            # Save rt_is
            rt_is_filename = default_naming["corres"]
            rt_is_filename = rt_is_filename + f'.{frame}'
            with open(rt_is_filename, "w", encoding="utf8") as rt_is:
                rt_is.write(str(pos.shape[0]) + "\n")
                for pix, pt in enumerate(pos):
                    pt_args = (pix + 1, ) + tuple(pt) + tuple(print_corresp[:, pix])
                    rt_is.write("%4d %9.3f %9.3f %9.3f %4d %4d %4d %4d\n" % pt_args)
       

