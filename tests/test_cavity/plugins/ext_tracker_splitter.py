from pathlib import Path
from optv.tracker import Tracker, default_naming

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

        img_base_name = self.exp.spar.get_img_base_name(0)

        for cam_id in range(self.exp.cpar.get_num_cams()):
            short_name = Path(img_base_name).parent / f'cam{cam_id+1}.'
            
            # print(short_name)
            print(f" Renaming {img_base_name} to {short_name} before C library tracker")
            self.exp.spar.set_img_base_name(cam_id, str(short_name))

        tracker = Tracker(
            self.exp.cpar, 
            self.exp.vpar, 
            self.exp.track_par, 
            self.exp.spar, 
            self.exp.cals, 
            default_naming
        )

    # return tracker


        
        tracker.full_forward()

    # def do_back_tracking(self):
    #     """this function is callback for "tracking back" """
    #     # do your back_tracking stuff here
    #     print("inside custom back tracking")
