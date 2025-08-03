
import numpy as np
from imageio.v3 import imread
from pathlib import Path

from optv.correspondences import correspondences, MatchedCoords
from optv.tracker import default_naming
from optv.orientation import point_positions



class Sequence:
    """Sequence class defines external tracking addon for pyptv
    User needs to implement the following functions:
            do_sequence(self)

    Connection to C ptv module is given via self.ptv and provided by pyptv software
    Connection to active parameters is given via self.exp1 and provided by pyptv software.

    User responsibility is to read necessary files, make the calculations and write the files back.
    """

    def __init__(self, ptv=None, exp=None):
        
        if ptv is None:
            from pyptv import ptv
        self.ptv = ptv
        self.exp = exp

    def do_sequence(self):
        """Copy of the sequence loop with one change we call everything as
        self.ptv instead of ptv.
        """
        # Ensure we have an experiment object
        if self.exp is None:
            raise ValueError("No experiment object provided")
            
        # Ensure parameter objects are initialized
        if hasattr(self.exp, 'ensure_parameter_objects'):
            self.exp.ensure_parameter_objects()
        
        # Verify splitter mode is enabled
        if hasattr(self.exp, 'pm'):
            ptv_params = self.exp.pm.get_parameter('ptv')
            if not ptv_params.get('splitter', False):
                raise ValueError("Splitter mode must be enabled for this sequence processor")
            
            # Get processing parameters
            masking_params = self.exp.pm.get_parameter('masking')
            inverse_flag = ptv_params.get('inverse', False)
        else:
            # Fallback for older experiment objects
            masking_params = {}
            inverse_flag = False
        
        # Get parameter objects with safety checks
        if not all(hasattr(self.exp, attr) for attr in ['cpar', 'spar', 'vpar', 'tpar', 'cals']):
            raise ValueError("Experiment object missing required parameter objects")
            
        num_cams = len(self.exp.cals)
        cpar = self.exp.cpar
        spar = self.exp.spar
        vpar = self.exp.vpar
        tpar = self.exp.tpar
        cals = self.exp.cals

        # # Sequence parameters
        # spar = SequenceParams(num_cams=num_cams)
        # spar.read_sequence_par(b"parameters/sequence.par", num_cams)

        # sequence loop for all frames
        first_frame = spar.get_first()
        last_frame = spar.get_last()
        print(f" From {first_frame = } to {last_frame = }")

        for frame in range(first_frame, last_frame + 1):
            print(f"Processing frame {frame}")

            detections = []
            corrected = []

            # when we work with splitter, we read only one image
            base_image_name = spar.get_img_base_name(0)
            
            # Handle bytes vs string issue
            if isinstance(base_image_name, bytes):
                base_image_name = base_image_name.decode('utf-8')
            
            print(f"Base image name: '{base_image_name}' (type: {type(base_image_name)}) for frame {frame}")
            
            # Safe string formatting - handle cases where format specifier might be missing
            try:
                imname = Path(base_image_name % frame)  # works with jumps from 1 to 10
                print(f"Formatted image name: {imname}")
            except (TypeError, ValueError) as e:
                print(f"String formatting failed for '{base_image_name}' with frame {frame}: {e}")
                # Fallback: assume base_image_name is already formatted or needs frame appended
                if '%' not in base_image_name:
                    # No format specifier, try appending frame number
                    base_path = Path(base_image_name)
                    imname = base_path.parent / f"{base_path.stem}_{frame:04d}{base_path.suffix}"
                    print(f"Using fallback image name: {imname}")
                else:
                    raise ValueError(f"String formatting error with base_image_name '{base_image_name}': {e}")
            
            if not imname.exists():
                raise FileNotFoundError(f"{imname} does not exist")
            
            # now we read and split 
            full_image = imread(imname)
            if full_image.ndim > 2:
                from skimage.color import rgb2gray
                full_image = rgb2gray(full_image)
            
            # Apply inverse if needed
            if inverse_flag:
                full_image = self.ptv.negative(full_image)
            
            # Split image using configurable order
            list_of_images = self.ptv.image_split(full_image, order=[0,1,3,2])  # HI-D specific order

            for i_cam in range(num_cams):  # Use dynamic camera count
                
                masked_image = list_of_images[i_cam].copy()
                
                # Apply masking if enabled
                if masking_params.get('mask_flag', False):
                    try:
                        mask_base_name = masking_params.get('mask_base_name', '')
                        if not mask_base_name:
                            print(f"Warning: mask_flag is True but mask_base_name is empty")
                            continue
                            
                        if '%' in mask_base_name:
                            background_name = mask_base_name % (i_cam + 1)
                        else:
                            # Fallback: assume mask_base_name needs camera number appended
                            mask_path = Path(mask_base_name)
                            background_name = str(mask_path.parent / f"{mask_path.stem}_cam{i_cam + 1}{mask_path.suffix}")
                        
                        background = imread(background_name)
                        if background.ndim > 2:
                            from skimage.color import rgb2gray
                            background = rgb2gray(background)
                        masked_image = np.clip(masked_image - background, 0, 255).astype(np.uint8)
                    except (ValueError, FileNotFoundError, TypeError) as e:
                        print(f"Failed to read/apply mask for camera {i_cam}: {e}")

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
            for i_cam in range(num_cams):  # Use dynamic camera count
                # base_name = spar.get_img_base_name(i_cam).decode()
                # base_name = replace_format_specifiers(base_name) # %d to %04d
                # base_name = str(Path(base_image_name).parent / f'cam{i_cam+1}')  # Convert Path to string
                base_name = self.exp.target_filenames[i_cam]  # Use the short file base names
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

            # Handle fewer than 4 cameras case
            if len(cals) < 4:
                print_corresp = -1 * np.ones((4, sorted_corresp.shape[1]))
                print_corresp[: len(cals), :] = sorted_corresp
            else:
                print_corresp = sorted_corresp

            # Save rt_is
            rt_is_filename = default_naming["corres"].decode()
            rt_is_filename = rt_is_filename + f".{frame}"
            with open(rt_is_filename, "w", encoding="utf8") as rt_is:
                rt_is.write(str(pos.shape[0]) + "\n")
                for pix, pt in enumerate(pos):
                    try:
                        pt_args = (pix + 1,) + tuple(pt) + tuple(print_corresp[:, pix])
                        # Debug: check if we have the right number of arguments
                        if len(pt_args) != 8:
                            print(f"Warning: pt_args has {len(pt_args)} elements, expected 8")
                            print(f"pt_args = {pt_args}")
                        rt_is.write("%4d %9.3f %9.3f %9.3f %4d %4d %4d %4d\n" % pt_args)
                    except (TypeError, ValueError) as e:
                        print(f"String formatting error at frame {frame}, pixel {pix}: {e}")
                        print(f"pt = {pt}, print_corresp[:, {pix}] = {print_corresp[:, pix]}")
                        raise

        
        print("Sequence completed successfully")
