class Tracking:
    """Tracking class defines external tracking addon for pyptv
    User needs to implement the following functions:
            do_tracking(self)
            do_back_tracking(self)
    Connection to C ptv module is given via self.ptv and provided by pyptv software
    Connection to active parameters is given via self.exp1 and provided by pyptv software.
    User responsibility is to read necessary files, make the calculations and write the files back.
    """

    def __init__(self, ptv=None, exp1=None):
        self.ptv = ptv
        self.exp1 = exp1
        # Do your initialization here

    def do_tracking(self):
        """this function is callback for "tracking without display" """
        print("inside denis_ext_tracker")
        run_info = self.ptv.py_trackcorr_init()
        print(run_info.get_sequence_range())
        for step in range(*run_info.get_sequence_range()):
            print("step %d" % step)
            self.ptv.py_trackcorr_loop(run_info, step, display=0)
            # finalize tracking
        self.ptv.py_trackcorr_finish(run_info, step + 1)

    def do_back_tracking(self):
        """this function is callback for "tracking back" """
        # do your back_tracking stuff here
        print("inside custom back tracking")
