
import numpy as np
from imageio.v3 import imread
from pathlib import Path


from optv.correspondences import correspondences, MatchedCoords
from optv.tracker import default_naming
from optv.orientation import point_positions

import matplotlib.pyplot as plt

from rembg import remove, new_session

session = new_session("u2net")


def save_mask_areas(areas_data: list, output_file: Path) -> None:
    """Save mask areas to CSV file.

    Parameters
    ----------
    areas_data : list
        List of dictionaries containing camera number, frame number, and area
    output_file : Path
        Path to output CSV file
    """
    import pandas as pd

    df = pd.DataFrame(areas_data)
    df.to_csv(output_file, index=False)


def mask_image(imname: Path, display: bool = False) -> tuple[np.ndarray, float]:
    """Mask the image using rembg and keep the entire mask.

    Parameters
    ----------
    imname : Path
        Path to the image file
    display : bool
        Whether to display debug plots

    Returns
    -------
    tuple[np.ndarray, float]
        Masked image and the area of the mask below row 600 in pixels
    """
    input_data = imread(imname)
    mask = remove(input_data, session=session, only_mask=True)

    # Set ROI threshold
    y_threshold = 600

    # Create ROI mask below threshold
    roi_mask = np.zeros_like(mask, dtype=bool)
    roi_mask[y_threshold:, :] = True

    # Calculate area in ROI
    mask_in_roi = np.where(roi_mask, mask, False)
    area = np.sum(mask_in_roi)

    if display:
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))

        # Original image
        ax1.imshow(input_data)
        ax1.axhline(y=y_threshold, color="r", linestyle="--")
        ax1.set_title("Original image")

        # Full mask
        ax2.imshow(mask)
        ax2.axhline(y=y_threshold, color="r", linestyle="--")
        ax2.set_title("Full mask")

        # Masked image
        ax3.imshow(np.where(mask, input_data, 0))
        ax3.axhline(y=y_threshold, color="r", linestyle="--")
        ax3.set_title("Masked image")

        # ROI masked image
        ax4.imshow(np.where(mask_in_roi, input_data, 0))
        ax4.set_title(f"ROI mask (area: {area} pixels)")

        plt.tight_layout()
        plt.show()

    # Apply the mask to the input image
    masked_image = np.where(mask, input_data, 0)
    return masked_image, area


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
        self.areas_data = []  # Store areas data during processing

    def do_sequence(self):
        """Copy of the sequence loop with one change we call everything as
        self.ptv instead of ptv.

        """
        # Sequence parameters

        num_cams, cpar, spar, vpar, tpar, cals = (
            self.exp.num_cams,
            self.exp.cpar,
            self.exp.spar,
            self.exp.vpar,
            self.exp.tpar,
            self.exp.cals,
        )

        # # Sequence parameters
        # spar = SequenceParams(num_cams=num_cams)
        # spar.read_sequence_par(b"parameters/sequence.par", num_cams)

        # sequence loop for all frames
        first_frame = spar.get_first()
        last_frame = spar.get_last()
        print(f" From {first_frame = } to {last_frame = }")

        for frame in range(first_frame, last_frame + 1):
            # print(f"processing {frame = }")

            detections = []
            corrected = []
            for i_cam in range(num_cams):
                base_image_name = spar.get_img_base_name(i_cam)
                imname = Path(base_image_name % frame)  # works with jumps from 1 to 10
                masked_image, area = mask_image(imname, display=False)

                # Store area data
                self.areas_data.append({"camera": i_cam, "frame": frame, "area": area})

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
                detections, corrected, cals, vpar, cpar
            )

            # Save targets only after they've been modified:
            # this is a workaround of the proper way to construct _targets name
            for i_cam in range(num_cams):
                base_name = spar.get_img_base_name(i_cam)
                # base_name = replace_format_specifiers(base_name) # %d to %04d
                self.ptv.write_targets(detections[i_cam], base_name, frame)

            print(
                "Frame "
                + str(frame)
                + " had "
                + repr([s.shape[1] for s in sorted_pos])
                + " correspondences."
            )

            # Distinction between quad/trip irrelevant here.
            sorted_pos = np.concatenate(sorted_pos, axis=1)
            sorted_corresp = np.concatenate(sorted_corresp, axis=1)

            flat = np.array(
                [corrected[i].get_by_pnrs(sorted_corresp[i]) for i in range(len(cals))]
            )
            pos, _ = point_positions(flat.transpose(1, 0, 2), cpar, cals, vpar)

            # if len(cals) == 1: # single camera case
            #     sorted_corresp = np.tile(sorted_corresp,(4,1))
            #     sorted_corresp[1:,:] = -1

            if len(cals) < 4:
                print_corresp = -1 * np.ones((4, sorted_corresp.shape[1]))
                print_corresp[: len(cals), :] = sorted_corresp
            else:
                print_corresp = sorted_corresp

            # Save rt_is
            rt_is_filename = default_naming["corres"]
            rt_is_filename = rt_is_filename + f".{frame}"
            with open(rt_is_filename, "w", encoding="utf8") as rt_is:
                rt_is.write(str(pos.shape[0]) + "\n")
                for pix, pt in enumerate(pos):
                    pt_args = (pix + 1,) + tuple(pt) + tuple(print_corresp[:, pix])
                    rt_is.write("%4d %9.3f %9.3f %9.3f %4d %4d %4d %4d\n" % pt_args)

        # After processing all frames, save the areas data
        output_file = Path("res/mask_areas.csv")
        save_mask_areas(self.areas_data, output_file)
        print(f"Mask areas saved to {output_file}")
