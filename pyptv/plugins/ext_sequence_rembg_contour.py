import random

import numpy as np
from imageio.v3 import imread, imwrite
from pathlib import Path

from skimage import img_as_ubyte
from skimage import filters, measure, morphology
from skimage.color import rgb2gray, label2rgb, rgba2rgb
from skimage.segmentation import clear_border
from skimage.morphology import binary_erosion, binary_dilation, disk
from skimage.util import img_as_ubyte

from optv.correspondences import correspondences, MatchedCoords
from optv.tracker import default_naming
from optv.orientation import point_positions

import matplotlib.pyplot as plt

from rembg import remove, new_session
session = new_session('u2net')


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
    # session = new_session('u2net')
    input_data = imread(imname)
    result = remove(input_data, session=session)
    result = img_as_ubyte(rgb2gray(result[:,:,:3]))

    # plt.figure()
    # plt.imshow(result, cmap='gray')
    # plt.show()

    return result

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
       

