"""
Parameter GUI for PyPTV - Schema-driven implementation.

This module provides TraitsUI forms for editing parameters.
The schema-based approach reduces code duplication and ensures consistency.
"""

from typing import Any
from pathlib import Path

from traits.api import HasTraits, Str, Float, Int, Bool, List
from traitsui.api import View, Item, HGroup, VGroup, Handler, Group, Tabbed, spring

from pyptv.experiment import Experiment
from pyptv.parameter_schema import ALL_SCHEMAS, get_schema_defaults


class ParamHandler(Handler):
    def closed(self, info, is_ok):
        if is_ok:
            main_params = info.object
            experiment = main_params.experiment
            num_cams = main_params.Num_Cam

            experiment.pm.parameters["num_cams"] = num_cams

            img_name = [
                getattr(main_params, f"Name_{i + 1}_Image", "") for i in range(num_cams)
            ]
            img_cal = [
                getattr(main_params, f"Cali_{i + 1}_Image", "") for i in range(num_cams)
            ]

            experiment.pm.parameters["ptv"].update(
                {
                    "img_name": img_name,
                    "img_cal": img_cal,
                    "hp_flag": main_params.HighPass,
                    "allcam_flag": main_params.Accept_OnlyAllCameras,
                    "tiff_flag": main_params.tiff_flag,
                    "imx": main_params.imx,
                    "imy": main_params.imy,
                    "pix_x": main_params.pix_x,
                    "pix_y": main_params.pix_y,
                    "chfield": main_params.chfield,
                    "mmp_n1": main_params.Refr_Air,
                    "mmp_n2": main_params.Refr_Glass,
                    "mmp_n3": main_params.Refr_Water,
                    "mmp_d": main_params.Thick_Glass,
                    "splitter": main_params.Splitter,
                    "negative": main_params.Negative,
                }
            )

            gvthres = [
                getattr(main_params, f"Gray_Tresh_{i + 1}", 0) for i in range(num_cams)
            ]
            experiment.pm.parameters["targ_rec"].update(
                {
                    "gvthres": gvthres,
                    "disco": main_params.Tol_Disc,
                    "nnmin": main_params.Min_Npix,
                    "nnmax": main_params.Max_Npix,
                    "nxmin": main_params.Min_Npix_x,
                    "nxmax": main_params.Max_Npix_x,
                    "nymin": main_params.Min_Npix_y,
                    "nymax": main_params.Max_Npix_y,
                    "sumg_min": main_params.Sum_Grey,
                    "cr_sz": main_params.Size_Cross,
                }
            )

            experiment.pm.parameters["pft_version"] = {
                "Existing_Target": int(main_params.Existing_Target)
            }

            base_name = [
                getattr(main_params, f"Basename_{i + 1}_Seq", "")
                for i in range(num_cams)
            ]
            experiment.pm.parameters["sequence"].update(
                {
                    "base_name": base_name,
                    "first": main_params.Seq_First,
                    "last": main_params.Seq_Last,
                }
            )

            experiment.pm.parameters["criteria"].update(
                {
                    "X_lay": [main_params.Xmin, main_params.Xmax],
                    "Zmin_lay": [main_params.Zmin1, main_params.Zmin2],
                    "Zmax_lay": [main_params.Zmax1, main_params.Zmax2],
                    "cnx": main_params.Min_Corr_nx,
                    "cny": main_params.Min_Corr_ny,
                    "cn": main_params.Min_Corr_npix,
                    "csumg": main_params.Sum_gv,
                    "corrmin": main_params.Min_Weight_corr,
                    "eps0": main_params.Tol_Band,
                }
            )

            experiment.pm.parameters["masking"].update(
                {
                    "mask_flag": main_params.Subtr_Mask,
                    "mask_base_name": main_params.Base_Name_Mask,
                }
            )

            experiment.save_parameters()
            print("Parameters saved successfully!")
            if main_params.Negative:
                print(
                    "[WARNING] You must reload images for 'Negative images?' to take effect."
                )


class CalHandler(Handler):
    def closed(self, info, is_ok):
        if is_ok:
            calib_params = info.object
            experiment = calib_params.experiment
            num_cams = experiment.pm.parameters["num_cams"]

            experiment.pm.parameters["ptv"].update(
                {
                    "imx": calib_params.h_image_size,
                    "imy": calib_params.v_image_size,
                    "pix_x": calib_params.h_pixel_size,
                    "pix_y": calib_params.v_pixel_size,
                }
            )

            img_cal_name = [
                getattr(calib_params, f"cam_{i + 1}", "") for i in range(num_cams)
            ]
            img_ori = [
                getattr(calib_params, f"ori_cam_{i + 1}", "") for i in range(num_cams)
            ]

            experiment.pm.parameters["cal_ori"].update(
                {
                    "fixp_name": calib_params.fixp_name,
                    "img_cal_name": img_cal_name,
                    "img_ori": img_ori,
                    "cal_splitter": calib_params._cal_splitter,
                }
            )

            experiment.pm.parameters["detect_plate"] = {
                "gvth_1": calib_params.grey_value_treshold_1,
                "gvth_2": calib_params.grey_value_treshold_2,
                "gvth_3": calib_params.grey_value_treshold_3,
                "gvth_4": calib_params.grey_value_treshold_4,
                "tol_dis": calib_params.tolerable_discontinuity,
                "min_npix": calib_params.min_npix,
                "max_npix": calib_params.max_npix,
                "min_npix_x": calib_params.min_npix_x,
                "max_npix_x": calib_params.max_npix_x,
                "min_npix_y": calib_params.min_npix_y,
                "max_npix_y": calib_params.max_npix_y,
                "sum_grey": calib_params.sum_of_grey,
                "size_cross": calib_params.size_of_crosses,
            }

            nr = []
            for i in range(num_cams):
                for j in range(4):
                    nr.append(getattr(calib_params, f"img_{i + 1}_p{j + 1}", 0))

            experiment.pm.parameters["man_ori"] = {"nr": nr}
            experiment.pm.parameters["examine"] = {
                "Examine_Flag": calib_params.Examine_Flag,
                "Combine_Flag": calib_params.Combine_Flag,
            }
            experiment.pm.parameters["orient"] = {
                "pnfo": calib_params.point_number_of_orientation,
                "cc": int(calib_params.cc),
                "xh": int(calib_params.xh),
                "yh": int(calib_params.yh),
                "k1": int(calib_params.k1),
                "k2": int(calib_params.k2),
                "k3": int(calib_params.k3),
                "p1": int(calib_params.p1),
                "p2": int(calib_params.p2),
                "scale": int(calib_params.scale),
                "shear": int(calib_params.shear),
                "interf": int(calib_params.interf),
            }
            experiment.pm.parameters["shaking"] = {
                "shaking_first_frame": calib_params.shaking_first_frame,
                "shaking_last_frame": calib_params.shaking_last_frame,
                "shaking_max_num_points": calib_params.shaking_max_num_points,
                "shaking_max_num_frames": calib_params.shaking_max_num_frames,
            }
            experiment.pm.parameters["dumbbell"] = {
                "dumbbell_eps": calib_params.dumbbell_eps,
                "dumbbell_scale": calib_params.dumbbell_scale,
                "dumbbell_gradient_descent": calib_params.dumbbell_gradient_descent,
                "dumbbell_penalty_weight": calib_params.dumbbell_penalty_weight,
                "dumbbell_step": calib_params.dumbbell_step,
                "dumbbell_niter": calib_params.dumbbell_niter,
                "dumbbell_fixed_camera": calib_params.dumbbell_fixed_camera,
            }

            experiment.save_parameters()
            print("Calibration parameters saved successfully!")


class TrackHandler(Handler):
    def closed(self, info, is_ok):
        if is_ok:
            track_params = info.object
            experiment = track_params.experiment

            experiment.pm.parameters["track"] = {
                "dvxmin": track_params.dvxmin,
                "dvxmax": track_params.dvxmax,
                "dvymin": track_params.dvymin,
                "dvymax": track_params.dvymax,
                "dvzmin": track_params.dvzmin,
                "dvzmax": track_params.dvzmax,
                "angle": track_params.angle,
                "dacc": track_params.dacc,
                "flagNewParticles": track_params.flagNewParticles,
            }

            experiment.save_parameters()
            print("Tracking parameters saved successfully!")


class Tracking_Params(HasTraits):
    dvxmin = Float()
    dvxmax = Float()
    dvymin = Float()
    dvymax = Float()
    dvzmin = Float()
    dvzmax = Float()
    angle = Float()
    dacc = Float()
    flagNewParticles = Bool(True)

    def __init__(self, experiment: Experiment):
        super().__init__()
        self.experiment = experiment
        track_params = experiment.pm.parameters.get("track", {})

        self.dvxmin = track_params.get("dvxmin", 0.0)
        self.dvxmax = track_params.get("dvxmax", 0.0)
        self.dvymin = track_params.get("dvymin", 0.0)
        self.dvymax = track_params.get("dvymax", 0.0)
        self.dvzmin = track_params.get("dvzmin", 0.0)
        self.dvzmax = track_params.get("dvzmax", 0.0)
        self.angle = track_params.get("angle", 0.0)
        self.dacc = track_params.get("dacc", 0.0)
        self.flagNewParticles = bool(track_params.get("flagNewParticles", True))

    Tracking_Params_View = View(
        HGroup(
            Item(name="dvxmin", label="dvxmin:"),
            Item(name="dvxmax", label="dvxmax:"),
        ),
        HGroup(
            Item(name="dvymin", label="dvymin:"),
            Item(name="dvymax", label="dvymax:"),
        ),
        HGroup(
            Item(name="dvzmin", label="dvzmin:"),
            Item(name="dvzmax", label="dvzmax:"),
        ),
        VGroup(
            Item(name="angle", label="angle [gon]:"),
            Item(name="dacc", label="dacc:"),
        ),
        Item(name="flagNewParticles", label="Add new particles?"),
        buttons=["Undo", "OK", "Cancel"],
        handler=TrackHandler(),
        title="Tracking Parameters",
    )


class Main_Params(HasTraits):
    experiment = Any

    Num_Cam = Int(label="Number of cameras: ")
    Accept_OnlyAllCameras = Bool(label="Accept only points seen from all cameras?")
    pair_Flag = Bool(label="Include pairs")
    pair_enable_flag = True
    all_enable_flag = False
    Splitter = Bool(label="Split images into 4?")

    tiff_flag = Bool()
    imx = Int()
    imy = Int()
    pix_x = Float()
    pix_y = Float()
    chfield = Int()

    Name_1_Image = Str(label="Name of 1. image")
    Name_2_Image = Str(label="Name of 2. image")
    Name_3_Image = Str(label="Name of 3. image")
    Name_4_Image = Str(label="Name of 4. image")
    Cali_1_Image = Str(label="Calibration data for 1. image")
    Cali_2_Image = Str(label="Calibration data for 2. image")
    Cali_3_Image = Str(label="Calibration data for 3. image")
    Cali_4_Image = Str(label="Calibration data for 4. image")

    Refr_Air = Float(label="Air:")
    Refr_Glass = Float(label="Glass:")
    Refr_Water = Float(label="Water:")
    Thick_Glass = Float(label="Thickness of glass:")

    HighPass = Bool(label="High pass filter")
    Gray_Tresh_1 = Int(label="1st image")
    Gray_Tresh_2 = Int(label="2nd image")
    Gray_Tresh_3 = Int(label="3rd image")
    Gray_Tresh_4 = Int(label="4th image")
    Min_Npix = Int(label="min npix")
    Max_Npix = Int(label="max npix")
    Min_Npix_x = Int(label="min npix x")
    Max_Npix_x = Int(label="max npix x")
    Min_Npix_y = Int(label="min npix y")
    Max_Npix_y = Int(label="max npix y")
    Sum_Grey = Int(label="Sum of grey value")
    Tol_Disc = Int(label="Tolerable discontinuity")
    Size_Cross = Int(label="Size of crosses")
    Subtr_Mask = Bool(label="Subtract mask")
    Base_Name_Mask = Str(label="Base name for the mask")
    Existing_Target = Bool(label="Use existing_target files?")
    Negative = Bool(label="Negative images?")

    Seq_First = Int(label="First sequence image:")
    Seq_Last = Int(label="Last sequence image:")
    Basename_1_Seq = Str(label="Basename for 1. sequence")
    Basename_2_Seq = Str(label="Basename for 2. sequence")
    Basename_3_Seq = Str(label="Basename for 3. sequence")
    Basename_4_Seq = Str(label="Basename for 4. sequence")

    Xmin = Int(label="Xmin")
    Xmax = Int(label="Xmax")
    Zmin1 = Int(label="Zmin")
    Zmin2 = Int(label="Zmin")
    Zmax1 = Int(label="Zmax")
    Zmax2 = Int(label="Zmax")

    Min_Corr_nx = Float(label="min corr for ratio nx")
    Min_Corr_ny = Float(label="min corr for ratio ny")
    Min_Corr_npix = Float(label="min corr for ratio npix")
    Sum_gv = Float(label="sum of gv")
    Min_Weight_corr = Float(label="min for weighted correlation")
    Tol_Band = Float(label="Tolerance of epipolar band [mm]")

    Group1 = Group(
        Group(
            Item(name="Num_Cam", width=30),
            Item(name="Splitter"),
            Item(name="Accept_OnlyAllCameras", enabled_when="all_enable_flag"),
            Item(name="pair_Flag", enabled_when="pair_enable_flag"),
            orientation="horizontal",
        ),
        Group(
            Group(
                Item(name="Name_1_Image", width=150),
                Item(name="Name_2_Image"),
                Item(name="Name_3_Image"),
                Item(name="Name_4_Image"),
                orientation="vertical",
            ),
            Group(
                Item(name="Cali_1_Image", width=150),
                Item(name="Cali_2_Image"),
                Item(name="Cali_3_Image"),
                Item(name="Cali_4_Image"),
                orientation="vertical",
            ),
            orientation="horizontal",
        ),
        orientation="vertical",
        label="General",
    )

    Group2 = Group(
        Group(
            Item(name="Refr_Air"),
            Item(name="Refr_Glass"),
            Item(name="Refr_Water"),
            Item(name="Thick_Glass"),
            orientation="horizontal",
        ),
        label="Refractive Indices",
        show_border=True,
        orientation="vertical",
    )

    Group3 = Group(
        Group(
            Item(name="Gray_Tresh_1"),
            Item(name="Gray_Tresh_2"),
            Item(name="Gray_Tresh_3"),
            Item(name="Gray_Tresh_4"),
            label="Gray value treshold: ",
            show_border=True,
            orientation="horizontal",
        ),
        Group(
            Group(
                Item(name="Min_Npix"),
                Item(name="Max_Npix"),
                Item(name="Sum_Grey"),
                orientation="vertical",
            ),
            Group(
                Item(name="Min_Npix_x"),
                Item(name="Max_Npix_x"),
                Item(name="Tol_Disc"),
                orientation="vertical",
            ),
            Group(
                Item(name="Min_Npix_y"),
                Item(name="Max_Npix_y"),
                Item(name="Size_Cross"),
                orientation="vertical",
            ),
            orientation="horizontal",
        ),
        Group(
            Item(name="Subtr_Mask"),
            Item(name="Base_Name_Mask"),
            Item(name="Existing_Target"),
            Item(name="HighPass"),
            Item(name="Negative"),
            orientation="horizontal",
        ),
        orientation="vertical",
        show_border=True,
        label="Particle recognition",
    )

    Group4 = Group(
        Group(
            Item(name="Seq_First"),
            Item(name="Seq_Last"),
            orientation="horizontal",
        ),
        Group(
            Item(name="Basename_1_Seq"),
            Item(name="Basename_2_Seq"),
            Item(name="Basename_3_Seq"),
            Item(name="Basename_4_Seq"),
            orientation="vertical",
        ),
        label="Parameters for sequence processing",
        orientation="vertical",
        show_border=True,
    )

    Group5 = Group(
        Group(Item(name="Xmin"), Item(name="Xmax"), orientation="vertical"),
        Group(Item(name="Zmin1"), Item(name="Zmin2"), orientation="vertical"),
        Group(Item(name="Zmax1"), Item(name="Zmax2"), orientation="vertical"),
        orientation="horizontal",
        label="Observation Volume",
        show_border=True,
    )

    Group6 = Group(
        Group(
            Item(name="Min_Corr_nx"),
            Item(name="Min_Corr_npix"),
            Item(name="Min_Weight_corr"),
            orientation="vertical",
        ),
        Group(
            Item(name="Min_Corr_ny"),
            Item(name="Sum_gv"),
            Item(name="Tol_Band"),
            orientation="vertical",
        ),
        orientation="horizontal",
        label="Criteria for correspondences",
        show_border=True,
    )

    Main_Params_View = View(
        Tabbed(Group1, Group2, Group3, Group4, Group5, Group6),
        resizable=True,
        width=0.5,
        height=0.3,
        dock="horizontal",
        buttons=["Undo", "OK", "Cancel"],
        handler=ParamHandler(),
        title="Main Parameters",
    )

    def _pair_Flag_fired(self):
        if self.pair_Flag:
            self.all_enable_flag = False
        else:
            self.all_enable_flag = True

    def _Accept_OnlyAllCameras_fired(self):
        if self.Accept_OnlyAllCameras:
            self.pair_enable_flag = False
        else:
            self.pair_enable_flag = True

    def _reload(self, num_cams: int, params: dict):
        ptv_params = params.get("ptv", {})

        for i, name in enumerate(ptv_params.get("img_name", [])[:num_cams]):
            setattr(self, f"Name_{i + 1}_Image", name or "")

        for i, cal in enumerate(ptv_params.get("img_cal", [])[:num_cams]):
            setattr(self, f"Cali_{i + 1}_Image", cal or "")

        self.Refr_Air = ptv_params.get("mmp_n1", 0.0)
        self.Refr_Glass = ptv_params.get("mmp_n2", 0.0)
        self.Refr_Water = ptv_params.get("mmp_n3", 0.0)
        self.Thick_Glass = ptv_params.get("mmp_d", 0.0)
        self.Accept_OnlyAllCameras = bool(ptv_params.get("allcam_flag", False))
        self.Num_Cam = num_cams
        self.HighPass = bool(ptv_params.get("hp_flag", False))
        self.tiff_flag = bool(ptv_params.get("tiff_flag", False))
        self.imx = ptv_params.get("imx", 0)
        self.imy = ptv_params.get("imy", 0)
        self.pix_x = ptv_params.get("pix_x", 0.0)
        self.pix_y = ptv_params.get("pix_y", 0.0)
        self.chfield = ptv_params.get("chfield", 0)
        self.Negative = bool(ptv_params.get("negative", False))

        targ_rec_params = params.get("targ_rec", {})
        gvthres = targ_rec_params.get("gvthres", [])
        for i in range(num_cams):
            setattr(self, f"Gray_Tresh_{i + 1}", gvthres[i] if i < len(gvthres) else 0)

        self.Min_Npix = targ_rec_params.get("nnmin", 0)
        self.Max_Npix = targ_rec_params.get("nnmax", 0)
        self.Min_Npix_x = targ_rec_params.get("nxmin", 0)
        self.Max_Npix_x = targ_rec_params.get("nxmax", 0)
        self.Min_Npix_y = targ_rec_params.get("nymin", 0)
        self.Max_Npix_y = targ_rec_params.get("nymax", 0)
        self.Sum_Grey = targ_rec_params.get("sumg_min", 0)
        self.Tol_Disc = targ_rec_params.get("disco", 0)
        self.Size_Cross = targ_rec_params.get("cr_sz", 0)

        pft_version_params = params.get("pft_version", {})
        self.Existing_Target = bool(pft_version_params.get("Existing_Target", 0))

        sequence_params = params.get("sequence", {})
        base_names = sequence_params.get("base_name", [])
        for i in range(num_cams):
            setattr(
                self,
                f"Basename_{i + 1}_Seq",
                base_names[i] if i < len(base_names) else "",
            )

        self.Seq_First = sequence_params.get("first", 0)
        self.Seq_Last = sequence_params.get("last", 0)

        criteria_params = params.get("criteria", {})
        X_lay = criteria_params.get("X_lay", [0, 0])
        self.Xmin, self.Xmax = X_lay[0], X_lay[1]
        Zmin_lay = criteria_params.get("Zmin_lay", [0, 0])
        self.Zmin1, self.Zmin2 = Zmin_lay[0], Zmin_lay[1]
        Zmax_lay = criteria_params.get("Zmax_lay", [0, 0])
        self.Zmax1, self.Zmax2 = Zmax_lay[0], Zmax_lay[1]
        self.Min_Corr_nx = criteria_params.get("cnx", 0.0)
        self.Min_Corr_ny = criteria_params.get("cny", 0.0)
        self.Min_Corr_npix = criteria_params.get("cn", 0.0)
        self.Sum_gv = criteria_params.get("csumg", 0.0)
        self.Min_Weight_corr = criteria_params.get("corrmin", 0.0)
        self.Tol_Band = criteria_params.get("eps0", 0.0)

        masking_params = params.get("masking", {})
        self.Subtr_Mask = masking_params.get("mask_flag", False)
        self.Base_Name_Mask = masking_params.get("mask_base_name", "")

    def __init__(self, experiment: Experiment):
        super().__init__()
        self.experiment = experiment
        self._reload(experiment.get_n_cam(), experiment.pm.parameters)


class Calib_Params(HasTraits):
    experiment = Any
    num_cams = Int
    _cal_splitter = Bool(label="Split calibration image into 4?")

    cam_1 = Str(label="Calibration picture camera 1")
    cam_2 = Str(label="Calibration picture camera 2")
    cam_3 = Str(label="Calibration picture camera 3")
    cam_4 = Str(label="Calibration picture camera 4")
    ori_cam_1 = Str(label="Orientation data picture camera 1")
    ori_cam_2 = Str(label="Orientation data picture camera 2")
    ori_cam_3 = Str(label="Orientation data picture camera 3")
    ori_cam_4 = Str(label="Orientation data picture camera 4")

    fixp_name = Str(label="File of Coordinates on plate")

    h_image_size = Int(label="Image size horizontal")
    v_image_size = Int(label="Image size vertical")
    h_pixel_size = Float(label="Pixel size horizontal")
    v_pixel_size = Float(label="Pixel size vertical")

    grey_value_treshold_1 = Int(label="First Image")
    grey_value_treshold_2 = Int(label="Second Image")
    grey_value_treshold_3 = Int(label="Third Image")
    grey_value_treshold_4 = Int(label="Forth Image")
    tolerable_discontinuity = Int(label="Tolerable discontinuity")
    min_npix = Int(label="min npix")
    min_npix_x = Int(label="min npix in x")
    min_npix_y = Int(label="min npix in y")
    max_npix = Int(label="max npix")
    max_npix_x = Int(label="max npix in x")
    max_npix_y = Int(label="max npix in y")
    sum_of_grey = Int(label="Sum of greyvalue")
    size_of_crosses = Int(label="Size of crosses")

    img_1_p1 = Int(label="P1")
    img_1_p2 = Int(label="P2")
    img_1_p3 = Int(label="P3")
    img_1_p4 = Int(label="P4")
    img_2_p1 = Int(label="P1")
    img_2_p2 = Int(label="P2")
    img_2_p3 = Int(label="P3")
    img_2_p4 = Int(label="P4")
    img_3_p1 = Int(label="P1")
    img_3_p2 = Int(label="P2")
    img_3_p3 = Int(label="P3")
    img_3_p4 = Int(label="P4")
    img_4_p1 = Int(label="P1")
    img_4_p2 = Int(label="P2")
    img_4_p3 = Int(label="P3")
    img_4_p4 = Int(label="P4")

    Examine_Flag = Bool(False, label="Calibrate with different Z")
    Combine_Flag = Bool(False, label="Combine preprocessed planes")

    point_number_of_orientation = Int(label="Point number of orientation")
    cc = Bool(False, label="cc")
    xh = Bool(False, label="xh")
    yh = Bool(False, label="yh")
    k1 = Bool(False, label="k1")
    k2 = Bool(False, label="k2")
    k3 = Bool(False, label="k3")
    p1 = Bool(False, label="p1")
    p2 = Bool(False, label="p2")
    scale = Bool(False, label="scale")
    shear = Bool(False, label="shear")
    interf = Bool(False, label="interfaces check box are available")

    dumbbell_eps = Float(label="dumbbell epsilon")
    dumbbell_scale = Float(label="dumbbell scale")
    dumbbell_gradient_descent = Float(label="dumbbell gradient descent factor")
    dumbbell_penalty_weight = Float(label="weight for dumbbell penalty")
    dumbbell_step = Int(label="step size through sequence")
    dumbbell_niter = Int(label="number of iterations per click")
    dumbbell_fixed_camera = Int(label="fixed camera (0=auto)")

    shaking_first_frame = Int(label="shaking first frame")
    shaking_last_frame = Int(label="shaking last frame")
    shaking_max_num_points = Int(label="shaking max num points")
    shaking_max_num_frames = Int(label="shaking max num frames")

    Group1_1 = Group(
        Item(name="cam_1"),
        Item(name="cam_2"),
        Item(name="cam_3"),
        Item(name="cam_4"),
        label="Calibration images",
        show_border=True,
    )
    Group1_2 = Group(
        Item(name="ori_cam_1"),
        Item(name="ori_cam_2"),
        Item(name="ori_cam_3"),
        Item(name="ori_cam_4"),
        label="Orientation data",
        show_border=True,
    )
    Group1_3 = Group(Item(name="fixp_name"), orientation="vertical")
    Group1 = Group(
        Group1_1, Group1_2, Group1_3, orientation="vertical", label="Images Data"
    )

    Group2_1 = Group(
        Item(name="h_image_size"),
        Item(name="v_image_size"),
        Item(name="h_pixel_size"),
        Item(name="v_pixel_size"),
        label="Image properties",
        show_border=True,
        orientation="horizontal",
    )
    Group2_2 = Group(
        Item(name="grey_value_treshold_1"),
        Item(name="grey_value_treshold_2"),
        Item(name="grey_value_treshold_3"),
        Item(name="grey_value_treshold_4"),
        orientation="horizontal",
        label="Grayvalue threshold",
        show_border=True,
    )
    Group2_3 = Group(
        Group(
            Item(name="min_npix"),
            Item(name="min_npix_x"),
            Item(name="min_npix_y"),
            orientation="vertical",
        ),
        Group(
            Item(name="max_npix"),
            Item(name="max_npix_x"),
            Item(name="max_npix_y"),
            orientation="vertical",
        ),
        Group(
            Item(name="tolerable_discontinuity"),
            Item(name="sum_of_grey"),
            Item(name="size_of_crosses"),
            orientation="vertical",
        ),
        orientation="horizontal",
    )
    Group2 = Group(
        Group2_1,
        Group2_2,
        Group2_3,
        orientation="vertical",
        label="Calibration Data Detection",
    )

    Group3_1 = Group(
        Item(name="img_1_p1"),
        Item(name="img_1_p2"),
        Item(name="img_1_p3"),
        Item(name="img_1_p4"),
        orientation="horizontal",
        label="Image 1",
        show_border=True,
    )
    Group3_2 = Group(
        Item(name="img_2_p1"),
        Item(name="img_2_p2"),
        Item(name="img_2_p3"),
        Item(name="img_2_p4"),
        orientation="horizontal",
        label="Image 2",
        show_border=True,
    )
    Group3_3 = Group(
        Item(name="img_3_p1"),
        Item(name="img_3_p2"),
        Item(name="img_3_p3"),
        Item(name="img_3_p4"),
        orientation="horizontal",
        label="Image 3",
        show_border=True,
    )
    Group3_4 = Group(
        Item(name="img_4_p1"),
        Item(name="img_4_p2"),
        Item(name="img_4_p3"),
        Item(name="img_4_p4"),
        orientation="horizontal",
        label="Image 4",
        show_border=True,
    )
    Group3 = Group(
        Group3_1,
        Group3_2,
        Group3_3,
        Group3_4,
        show_border=True,
        label="Manual pre-orientation",
    )

    Group4_0 = Group(
        Item(name="Examine_Flag"), Item(name="Combine_Flag"), show_border=True
    )
    Group4_1 = Group(
        Item(name="cc"),
        Item(name="xh"),
        Item(name="yh"),
        orientation="vertical",
        columns=3,
    )
    Group4_2 = Group(
        Item(name="k1"),
        Item(name="k2"),
        Item(name="k3"),
        Item(name="p1"),
        Item(name="p2"),
        orientation="vertical",
        columns=5,
        label="Lens distortion(Brown)",
        show_border=True,
    )
    Group4_3 = Group(
        Item(name="scale"),
        Item(name="shear"),
        orientation="vertical",
        columns=2,
        label="Affin transformation",
        show_border=True,
    )
    Group4_4 = Group(Item(name="interf"))
    Group4 = Group(
        Group(
            Group4_0,
            Item(name="point_number_of_orientation"),
            Group4_1,
            Group4_2,
            Group4_3,
            Group4_4,
            label=" Orientation Parameters ",
            show_border=True,
        ),
        orientation="horizontal",
        show_border=True,
        label="Calibration Orientation Param.",
    )

    Group5 = HGroup(
        VGroup(
            Item(name="dumbbell_eps"),
            Item(name="dumbbell_scale"),
            Item(name="dumbbell_gradient_descent"),
            Item(name="dumbbell_penalty_weight"),
            Item(name="dumbbell_step"),
            Item(name="dumbbell_niter"),
            Item(name="dumbbell_fixed_camera"),
        ),
        spring,
        label="Dumbbell calibration parameters",
        show_border=True,
    )

    Group6 = HGroup(
        VGroup(
            Item(name="shaking_first_frame"),
            Item(name="shaking_last_frame"),
            Item(name="shaking_max_num_points"),
            Item(name="shaking_max_num_frames"),
        ),
        spring,
        label="Shaking calibration parameters",
        show_border=True,
    )

    Calib_Params_View = View(
        Tabbed(Group1, Group2, Group3, Group4, Group5, Group6),
        buttons=["Undo", "OK", "Cancel"],
        handler=CalHandler(),
        title="Calibration Parameters",
    )

    def _reload(self, num_cams, params):
        ptv_params = params.get("ptv", {})
        self.h_image_size = ptv_params.get("imx", 0)
        self.v_image_size = ptv_params.get("imy", 0)
        self.h_pixel_size = ptv_params.get("pix_x", 0.0)
        self.v_pixel_size = ptv_params.get("pix_y", 0.0)
        self.hp_flag = bool(ptv_params.get("hp_flag", False))

        cal_ori_params = params.get("cal_ori", {})
        cal_names = cal_ori_params.get("img_cal_name", [])
        for i in range(num_cams):
            setattr(self, f"cam_{i + 1}", cal_names[i] if i < len(cal_names) else "")

        ori_names = cal_ori_params.get("img_ori", [])
        for i in range(num_cams):
            setattr(
                self, f"ori_cam_{i + 1}", ori_names[i] if i < len(ori_names) else ""
            )

        self.fixp_name = cal_ori_params.get("fixp_name", "")
        self._cal_splitter = bool(cal_ori_params.get("cal_splitter", False))

        detect_plate_params = params.get("detect_plate", {})
        self.grey_value_treshold_1 = detect_plate_params.get("gvth_1", 0)
        self.grey_value_treshold_2 = detect_plate_params.get("gvth_2", 0)
        self.grey_value_treshold_3 = detect_plate_params.get("gvth_3", 0)
        self.grey_value_treshold_4 = detect_plate_params.get("gvth_4", 0)
        self.tolerable_discontinuity = detect_plate_params.get("tol_dis", 0)
        self.min_npix = detect_plate_params.get("min_npix", 0)
        self.max_npix = detect_plate_params.get("max_npix", 0)
        self.min_npix_x = detect_plate_params.get("min_npix_x", 0)
        self.max_npix_x = detect_plate_params.get("max_npix_x", 0)
        self.min_npix_y = detect_plate_params.get("min_npix_y", 0)
        self.max_npix_y = detect_plate_params.get("max_npix_y", 0)
        self.sum_of_grey = detect_plate_params.get("sum_grey", 0)
        self.size_of_crosses = detect_plate_params.get("size_cross", 0)

        man_ori_params = params.get("man_ori", {})
        nr = man_ori_params.get("nr", [])
        for i in range(num_cams):
            for j in range(4):
                val = nr[i * 4 + j] if i * 4 + j < len(nr) else 0
                setattr(self, f"img_{i + 1}_p{j + 1}", val)

        examine_params = params.get("examine", {})
        self.Examine_Flag = examine_params.get("Examine_Flag", False)
        self.Combine_Flag = examine_params.get("Combine_Flag", False)

        orient_params = params.get("orient", {})
        self.point_number_of_orientation = orient_params.get("pnfo", 0)
        self.cc = bool(orient_params.get("cc", 0))
        self.xh = bool(orient_params.get("xh", 0))
        self.yh = bool(orient_params.get("yh", 0))
        self.k1 = bool(orient_params.get("k1", 0))
        self.k2 = bool(orient_params.get("k2", 0))
        self.k3 = bool(orient_params.get("k3", 0))
        self.p1 = bool(orient_params.get("p1", 0))
        self.p2 = bool(orient_params.get("p2", 0))
        self.scale = bool(orient_params.get("scale", 0))
        self.shear = bool(orient_params.get("shear", 0))
        self.interf = bool(orient_params.get("interf", 0))

        dumbbell_params = params.get("dumbbell", {})
        self.dumbbell_eps = dumbbell_params.get("dumbbell_eps", 0.0)
        self.dumbbell_scale = dumbbell_params.get("dumbbell_scale", 0.0)
        self.dumbbell_gradient_descent = dumbbell_params.get(
            "dumbbell_gradient_descent", 0.0
        )
        self.dumbbell_penalty_weight = dumbbell_params.get(
            "dumbbell_penalty_weight", 0.0
        )
        self.dumbbell_step = dumbbell_params.get("dumbbell_step", 0)
        self.dumbbell_niter = dumbbell_params.get("dumbbell_niter", 0)
        self.dumbbell_fixed_camera = dumbbell_params.get("dumbbell_fixed_camera", 0)

        shaking_params = params.get("shaking", {})
        self.shaking_first_frame = shaking_params.get("shaking_first_frame", 0)
        self.shaking_last_frame = shaking_params.get("shaking_last_frame", 0)
        self.shaking_max_num_points = shaking_params.get("shaking_max_num_points", 0)
        self.shaking_max_num_frames = shaking_params.get("shaking_max_num_frames", 0)

    def __init__(self, experiment: Experiment):
        super().__init__()
        self.experiment = experiment
        self._reload(experiment.get_n_cam(), experiment.pm.parameters)


from pyptv.experiment import Experiment
