import random

import numpy as np
from skimage.io import imread


class Sequence:
    """Sequence class defines external tracking addon for pyptv
    User needs to implement the following functions:
            do_sequence(self)

    Connection to C ptv module is given via self.ptv and provided by pyptv software
    Connection to active parameters is given via self.exp1 and provided by pyptv software.

    User responsibility is to read necessary files, make the calculations and write the files back.
    """

    def __init__(self, ptv=None, exp1=None, camera_list=None):
        self.ptv = ptv
        self.exp1 = exp1
        self.camera_list = camera_list
        # Do your initialization here

    def do_sequence(self):
        """this function is callback for "tracking without display" """
        print("inside denis_ext_sequence")
        n_camera = self.exp1.active_params.m_params.Num_Cam
        print("Starting sequence action")
        seq_first = self.exp1.active_params.m_params.Seq_First
        seq_last = self.exp1.active_params.m_params.Seq_Last
        print(seq_first, seq_last)
        base_name = []
        for i in range(n_camera):
            exec(
                "base_name.append(self.exp1.active_params.m_params.Basename_%d_Seq)" %
                (i + 1))
            print(base_name[i])

        self.ptv.py_sequence_init(0)  # init C sequence function
        # get parameters and pass to main loop
        stepshake = self.ptv.py_get_from_sequence_init()
        if not stepshake:
            stepshake = 1
        print(stepshake)
        temp_img = np.array([], dtype=np.ubyte)
        # main loop - format image name, read it and call
        # v.py_sequence_loop(..) for current step
        for i in range(seq_first, seq_last + 1, stepshake):
            if i < 10:
                seq_ch = "%01d" % i
            elif i < 100:
                seq_ch = "%02d" % i
            else:
                seq_ch = "%03d" % i
            for j in range(n_camera):
                img_name = base_name[j] + seq_ch
                # print("Setting image: ", img_name)
                try:
                    temp_img = imread(img_name).astype(np.ubyte)
                except BaseException:
                    print("Error reading file")

                self.ptv.py_set_img(temp_img, j)
            self.ptv.py_sequence_loop(0, i)
            self.camera_list[0].drawquiver(
                [int(300 * random.random())],
                [int(300 * random.random())],
                [int(300 * random.random())],
                [int(300 * random.random())],
                "green",
                linewidth=3.0,
            )
            self.camera_list[0]._plot.request_redraw()
