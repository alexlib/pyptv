import marimo

__generated_with = "0.19.9"
app = marimo.App()


@app.cell
def _():
    # Jupyter notebook version of calibration
    return


@app.cell
def _():
    # from Yosef Meller's PBI
    import os
    import shutil
    import numpy as np
    from pathlib import Path
    import pyptv.parameter_manager as pm

    os.chdir(Path(__file__).parent.absolute())
    param_file = Path("../tests/test_cavity/parameters_Run1.yaml")
    param_file.exists()
    par = pm.ParameterManager()
    par.from_yaml(param_file)
    print(f"number of cameras is {par.get_n_cam()}")
    return Path, np, os, par, pm


@app.cell
def _(Calibration, convert_arr_metric_to_pixel, image_coordinates, np):
    def get_pos(inters, R, angs):
        # Transpose of http://planning.cs.uiuc.edu/node102.html
        # Also consider the angles are reversed when moving from camera frame to
        # global frame.
        s = np.sin(angs)
        c = np.cos(angs)
        pos = inters + R * np.r_[s[1], -c[1] * s[0], c[1] * c[0]]
        return pos


    def get_polar_rep(pos, angs):
        """
        Returns the point of intersection with zero Z plane, and distance from it.
        """
        s = np.sin(angs)
        c = np.cos(angs)
        zdir = -np.r_[s[1], -c[1] * s[0], c[1] * c[0]]

        c = -pos[2] / zdir[2]
        inters = pos + c * zdir
        R = np.linalg.norm(inters - pos)

        return inters[:2], R


    def gen_calib(inters, R, angs, glass_vec, prim_point, radial_dist, decent):
        pos = get_pos(inters, R, angs)
        return Calibration(
            pos, angs, prim_point, radial_dist, decent, np.r_[1, 0], glass_vec
        )


    def fitness(solution, calib_targs, calib_detect, glass_vec, cpar):
        """
        Checks the fitness of an evolutionary solution of calibration values to
        target points. Fitness is the sum of squares of the distance from each
        guessed point to the closest neighbor.

        Arguments:
        solution - array, concatenated: position of intersection with Z=0 plane; 3
            angles of exterior calibration; primary point (xh,yh,cc); 3 radial
            distortion parameters; 2 decentering parameters.
        calib_targs - a (p,3) array of p known points on the calibration target.
        calib_detect - a (d,2) array of d detected points in the calibration
            target.
        cpar - a ControlParams object with image data.
        """
        # Breakdown of of agregate solution vector:
        inters = np.zeros(3)
        inters[:2] = solution[:2]
        R = solution[2]
        angs = solution[3:6]
        prim_point = solution[6:9]
        rad_dist = solution[9:12]
        decent = solution[12:14]

        # Compare known points' projections to detections:
        cal = gen_calib(inters, R, angs, glass_vec, prim_point, rad_dist, decent)
        known_proj = image_coordinates(
            calib_targs, cal, cpar.get_multimedia_params()
        )
        known_2d = convert_arr_metric_to_pixel(known_proj, cpar)
        dists = np.linalg.norm(
            known_2d[None, :, :] - calib_detect[:, None, :], axis=2
        ).min(axis=0)

        return np.sum(dists**2)

    return


@app.cell
def _(Path, os):
    working_folder = Path("/home/user/Documents/GitHub/pyptv/tests/test_cavity")
    if Path.cwd() != working_folder:
        # working_folder = Path("../tests/test_cavity").resolve()
        working_folder.exists()
        os.chdir(working_folder)
        print(os.getcwd())
    return


@app.cell
def _(par):
    cal_ori = par.parameters.get("cal_ori", {})
    print(cal_ori["fixp_name"])
    return


@app.cell
def _(par):
    #  recognized names for the flags:
    op = par.parameters.get("orient")
    print(op)
    names = [
        "cc",
        "xh",
        "yh",
        "k1",
        "k2",
        "k3",
        "p1",
        "p2",
        "scale",
        "shear",
    ]
    op_names = [
        op["cc"],
        op["xh"],
        op["yh"],
        op["k1"],
        op["k2"],
        op["k3"],
        op["p1"],
        op["p2"],
        op["scale"],
        op["shear"],
    ]

    flags = []
    for name, op_name in zip(names, op_names):
        if op_name == 1:
            flags.append(name)

    print(flags)
    return (flags,)


@app.cell
def _(TargetArray, flags, full_calibration, np, re, self):
    for i_cam in range(self.num_cams):  # iterate over all cameras
        if self.epar.Combine_Flag:
            self.status_text = "Multiplane calibration."
            """ Performs multiplane calibration, in which for all cameras the
            pre-processed planes in multi_plane.par combined.
            Overwrites the ori and addpar files of the cameras specified
            in cal_ori.par of the multiplane parameter folder
            """

            all_known = []
            all_detected = []

            for i in range(self.MultiParams.n_planes):  # combine all single planes
                # c = self.calParams.img_ori[i_cam][-9] # Get camera id
                # not all ends with a number
                c = re.findall("\\d+", self.calParams.img_ori[i_cam])[0]

                file_known = self.MultiParams.plane_name[i] + c + ".tif.fix"
                file_detected = self.MultiParams.plane_name[i] + c + ".tif.crd"

                # Load calibration point information from plane i
                try:
                    known = np.loadtxt(file_known)
                    detected = np.loadtxt(file_detected)
                except BaseException:
                    raise IOError(
                        "reading {} or {} failed".format(file_known, file_detected)
                    )

                if np.any(detected == -999):
                    raise ValueError(
                        (
                            "Using undetected points in {} will cause "
                            + "silliness. Quitting."
                        ).format(file_detected)
                    )

                num_known = len(known)
                num_detect = len(detected)

                if num_known != num_detect:
                    raise ValueError(
                        f"Number of detected points {num_known} does not match"
                        " number of known points {num_detect} for \
                            {file_known}, {file_detected}"
                    )

                if len(all_known) > 0:
                    detected[:, 0] = (
                        all_detected[-1][-1, 0] + 1 + np.arange(len(detected))
                    )

                # Append to list of total known and detected points
                all_known.append(known)
                all_detected.append(detected)

            # Make into the format needed for full_calibration.
            all_known = np.vstack(all_known)[:, 1:]
            all_detected = np.vstack(all_detected)

            # this is the main difference in the multiplane mode
            # that we fill the targs and cal_points by the
            # combined information

            targs = TargetArray(len(all_detected))
            for tix in range(len(all_detected)):
                targ = targs[tix]
                det = all_detected[tix]

                targ.set_pnr(tix)
                targ.set_pos(det[1:])

            self.cal_points = np.empty((all_known.shape[0],)).astype(
                dtype=[("id", "i4"), ("pos", "3f8")]
            )
            self.cal_points["pos"] = all_known
        else:
            targs = self.sorted_targs[i_cam]

        residuals, targ_ix, err_est = full_calibration(
            self.cals[i_cam],
            self.cal_points["pos"],
            targs,
            self.cpar,
            flags,
        )
    return


@app.cell
def _(Path):
    [p.name for p in Path("tests/test_cavity").iterdir()]
    return


@app.cell
def _(Path):
    [p.name for p in Path("tests/test_cavity/parameters").iterdir()]
    return


@app.cell
def _():
    import pyptv

    dir(pyptv)
    return


@app.cell
def _():
    import pyptv.legacy_parameters as legacy_parameters

    dir(legacy_parameters)
    return


@app.cell
def _(pm):
    help(pm.ParameterManager)
    return


@app.cell
def _(pm):
    help(pm.ParameterManager)
    return


if __name__ == "__main__":
    app.run()
