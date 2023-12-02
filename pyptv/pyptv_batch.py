""" PyPTV_BATCH is the script for the 3D-PTV (http://ptv.origo.ethz.ch)
    written in Python with Enthought Traits GUI/Numpy/Chaco

Example:
>> python pyptv_batch.py experiments/exp1 10001 10022

where 10001 is the first file in sequence and 10022 is the last one
the present "active" parameters are kept intact except the sequence


"""


# from scipy.misc import imread
from pathlib import Path
import os
import sys
import time

from pyptv.ptv import py_start_proc_c, py_trackcorr_init, py_sequence_loop


# project specific inputs
# import pdb; pdb.set_trace()

class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self

def run_batch(new_seq_first: int, new_seq_last: int):
    """this file runs inside exp_path, so the other names are
    prescribed by the OpenPTV type of a folder:
        /parameters
        /img
        /cal
        /res
    """
    # read the number of cameras
    with open("parameters/ptv.par", "r") as f:
        n_cams = int(f.readline())
    
    cpar, spar, vpar, track_par, tpar, cals, epar = py_start_proc_c(n_cams=n_cams)
    
    spar.set_first(first)
    spar.set_last(last)
    
    exp = {
    'cpar':cpar,
    'spar':spar,
    'vpar':vpar,
    'track_par':track_par,
    'tpar':tpar,
    'cals':cals,
    'epar':epar,
    'n_cams':n_cams,
        }
    
    # use dataclass to convert dictionary keys to attributes
    exp = AttrDict(exp)
    
    py_sequence_loop(exp)
    tracker = py_trackcorr_init(exp)
    tracker.full_forward()

#


def main(exp_path, first, last, repetitions=1):
    """runs the batch
    Usage:
        main([exp_dir, first, last], [repetitions])

    Parameters:
        list of 3 parameters in this order:
        exp_dir : directory with the experiment data
        first, last : integer, number of a first and last frame
        repetitions : int, default = 1, optional
    """
    start = time.time()

    try:
        exp_path = Path(exp_path).resolve()
        print(f"Inside main of pyptv_batch, exp_path is {exp_path} \n")
        os.chdir(exp_path)
        
        print(f"double checking that its inside {Path.cwd()} \n")
    except Exception:
        raise ValueError(f"Wrong experimental directory {exp_path}")

    # RON - make a res dir if it not found

    res_path = exp_path / "res"
    
    if not res_path.is_dir():
        print(" 'res' folder not found. creating one")
        res_path.mkdir(parents=True, exist_ok=True)

    for i in range(repetitions):
        seq_first = int(first)
        seq_last = int(last)

        try:
            print((seq_first, seq_last))
            run_batch(seq_first, seq_last)
        except Exception:
            print("something wrong with the batch or the folder")

    end = time.time()
    print("time lapsed %f sec" % (end - start))


if __name__ == "__main__":
    """pyptv_batch.py enables to run a sequence without GUI
    It can run from a command shell:
    python pyptv_batch.py ~/test_cavity 10000 10004

    or from Python:

    import sys, os
    sys.path.append(os.path.abspath('openptv/openptv-python/pyptv_gui'))
    from pyptv_batch import main
    batch_command = '/openptv/openptv-python/pyptv_gui/pyptv_batch.py'
    PyPTV_working_directory = '/openptv/Working_folder/'
    mi,mx = 65119, 66217
    main([batch_command,PyPTV_working_directory, mi, mx])
    """
    # directory from which we run the software
    print("inside pyptv_batch.py\n")
    print(sys.argv)

    if len(sys.argv) < 4:
        print(
            "Wrong number of inputs, usage: python pyptv_batch.py \
        experiments/exp1 seq_first seq_last"
        )
        # raise ValueError("wrong number of inputs")
        
        exp_path = Path('tests/test_cavity').resolve()
        first = 10000
        last = 10004
    else:
        exp_path = sys.argv[1]
        first = sys.argv[2]
        last = sys.argv[3]

    main(exp_path, first, last)
