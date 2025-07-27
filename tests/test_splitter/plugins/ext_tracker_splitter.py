from pathlib import Path
from optv.tracker import Tracker, default_naming
import sys

class Tracking:
    """Tracking class defines external tracking addon for pyptv
    User needs to implement the following functions:
            do_tracking(self)
            do_back_tracking(self)
    Connection to C ptv module is given via self.ptv and provided by pyptv software
    Connection to active parameters is given via self.exp1 and provided by pyptv software.
    User responsibility is to read necessary files, make the calculations and write the files back.
    """

    def __init__(self, ptv=None, exp=None):
        if ptv is None:
            from pyptv import ptv
        self.ptv = ptv
        self.exp = exp

    def do_tracking(self):
        """this function is callback for "tracking without display" """
        print("inside plugin tracker")
        sys.stdout.flush()

        # Safety check
        if self.exp is None:
            print("Error: No experiment object available")
            sys.stdout.flush()
            return


        print(f"Number of cameras: {self.exp.cpar.get_num_cams()}")
        sys.stdout.flush()


        img_base_names = [self.exp.spar.get_img_base_name(i) for i in range(self.exp.cpar.get_num_cams())]
        self.exp.short_file_bases = self.exp.target_filenames

        for cam_id, short_name in enumerate(self.exp.short_file_bases):
            # print(f"Setting tracker image base name for cam {cam_id+1}: {Path(short_name).resolve()}")
            self.exp.spar.set_img_base_name(cam_id, str(Path(short_name).resolve())+'.')

        try:
            tracker = Tracker(
                self.exp.cpar,
                self.exp.vpar,
                self.exp.track_par,
                self.exp.spar,
                self.exp.cals,
                default_naming
            )
            
            tracker.full_forward()
        except Exception as e:
            print(f"Error during tracking: {e}")
            sys.stdout.flush()
            raise

    def do_back_tracking(self):
        """this function is callback for "tracking back" """
        print("inside custom back tracking")
        
        # Safety check
        if self.exp is None:
            print("Error: No experiment object available")
            return
            
        # Implement back tracking logic here
        # This is a placeholder - actual back tracking implementation would go here
        print("Back tracking functionality not yet implemented")
        # TODO: Implement actual back tracking algorithm
