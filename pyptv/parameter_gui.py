import os
import json
from pathlib import Path

from traits.api import HasTraits, Str, Float, Int, List, Bool, Enum, Instance
from traitsui.api import (
    View,
    Item,
    HGroup,
    VGroup,
    Handler,
    Group,
    Tabbed,
    spring,
)

# from traits.etsconfig.api import ETSConfig

from pyptv import parameters as par
import numpy as np


DEFAULT_STRING = "---"
DEFAULT_INT = -999
DEFAULT_FLOAT = -999.0


# define handler function for main parameters
class ParamHandler(Handler):
    def closed(self, info, is_ok):
        mainParams = info.object
        par_path = mainParams.par_path
        Handler.closed(self, info, is_ok)
        if is_ok:
            img_name = [
                mainParams.Name_1_Image,
                mainParams.Name_2_Image,
                mainParams.Name_3_Image,
                mainParams.Name_4_Image,
            ]
            img_cal_name = [
                mainParams.Cali_1_Image,
                mainParams.Cali_2_Image,
                mainParams.Cali_3_Image,
                mainParams.Cali_4_Image,
            ]

            gvthres = [
                mainParams.Gray_Tresh_1,
                mainParams.Gray_Tresh_2,
                mainParams.Gray_Tresh_3,
                mainParams.Gray_Tresh_4,
            ]
            base_name = [
                mainParams.Basename_1_Seq,
                mainParams.Basename_2_Seq,
                mainParams.Basename_3_Seq,
                mainParams.Basename_4_Seq,
            ]
            X_lay = [mainParams.Xmin, mainParams.Xmax]
            Zmin_lay = [mainParams.Zmin1, mainParams.Zmin2]
            Zmax_lay = [mainParams.Zmax1, mainParams.Zmax2]

            # write ptv_par
            par.PtvParams(
                mainParams.Num_Cam,
                img_name,
                img_cal_name,
                mainParams.HighPass,
                mainParams.Accept_OnlyAllCameras,
                mainParams.tiff_flag,
                mainParams.imx,
                mainParams.imy,
                mainParams.pix_x,
                mainParams.pix_y,
                mainParams.chfield,
                mainParams.Refr_Air,
                mainParams.Refr_Glass,
                mainParams.Refr_Water,
                mainParams.Thick_Glass,
                path=par_path,
            ).write()
            # write calibration parameters
            par.CalOriParams(
                mainParams.Num_Cam,
                mainParams.fixp_name,
                mainParams.img_cal_name,
                mainParams.img_ori,
                mainParams.tiff_flag,
                mainParams.pair_Flag,
                mainParams.chfield,
                path=par_path,
            ).write()

            # write targ_rec_par
            par.TargRecParams(
                mainParams.Num_Cam,
                gvthres,
                mainParams.Tol_Disc,
                mainParams.Min_Npix,
                mainParams.Max_Npix,
                mainParams.Min_Npix_x,
                mainParams.Max_Npix_x,
                mainParams.Min_Npix_y,
                mainParams.Max_Npix_y,
                mainParams.Sum_Grey,
                mainParams.Size_Cross,
                path=par_path,
            ).write()
            # write pft_version_par
            par.PftVersionParams(
                mainParams.Existing_Target, path=par_path
            ).write()
            # write sequence_par
            par.SequenceParams(
                mainParams.Num_Cam,
                base_name,
                mainParams.Seq_First,
                mainParams.Seq_Last,
                path=par_path,
            ).write()
            # write criteria_par
            par.CriteriaParams(
                X_lay,
                Zmin_lay,
                Zmax_lay,
                mainParams.Min_Corr_nx,
                mainParams.Min_Corr_ny,
                mainParams.Min_Corr_npix,
                mainParams.Sum_gv,
                mainParams.Min_Weight_corr,
                mainParams.Tol_Band,
                path=par_path,
            ).write()
            
            # write masking parameters
            masking_dict = {
                "mask_flag":mainParams.Subtr_Mask,
                "mask_base_name":mainParams.Base_Name_Mask,
            }
            with (Path(par_path) / 'masking.json').open('w') as json_file:
                json.dump(masking_dict, json_file)


# define handler function for calibration parameters
class CalHandler(Handler):
    def closed(self, info, is_ok):
        calibParams = info.object
        par_path = calibParams.par_path
        print("inside CalHandler ", par_path)
        Handler.closed(self, info, is_ok)
        if is_ok:
            img_cal_name = [
                calibParams.cam_1,
                calibParams.cam_2,
                calibParams.cam_3,
                calibParams.cam_4,
            ]
            img_ori = [
                calibParams.ori_cam_1,
                calibParams.ori_cam_2,
                calibParams.ori_cam_3,
                calibParams.ori_cam_4,
            ]
            nr1 = [
                calibParams.img_1_p1,
                calibParams.img_1_p2,
                calibParams.img_1_p3,
                calibParams.img_1_p4,
            ]
            nr2 = [
                calibParams.img_2_p1,
                calibParams.img_2_p2,
                calibParams.img_2_p3,
                calibParams.img_2_p4,
            ]
            nr3 = [
                calibParams.img_3_p1,
                calibParams.img_3_p2,
                calibParams.img_3_p3,
                calibParams.img_3_p4,
            ]
            nr4 = [
                calibParams.img_4_p1,
                calibParams.img_4_p2,
                calibParams.img_4_p3,
                calibParams.img_4_p4,
            ]

            nr = [nr1, nr2, nr3, nr4]

            if calibParams.chfield == "Frame":
                chfield = 0
            elif calibParams.chfield == "Field odd":
                chfield = 1
            else:
                chfield = 2
            par.PtvParams(
                calibParams.n_img,
                calibParams.img_name,
                calibParams.img_cal,
                calibParams.hp_flag,
                calibParams.allcam_flag,
                calibParams.tiff_head,
                calibParams.h_image_size,
                calibParams.v_image_size,
                calibParams.h_pixel_size,
                calibParams.v_pixel_size,
                chfield,
                calibParams.mmp_n1,
                calibParams.mmp_n2,
                calibParams.mmp_n3,
                calibParams.mmp_d,
                path=par_path,
            ).write()

            par.CalOriParams(
                calibParams.n_img,
                calibParams.fixp_name,
                img_cal_name,
                img_ori,
                calibParams.tiff_head,
                calibParams.pair_head,
                chfield,
                path=par_path,
            ).write()

            par.DetectPlateParams(
                calibParams.grey_value_treshold_1,
                calibParams.grey_value_treshold_2,
                calibParams.grey_value_treshold_3,
                calibParams.grey_value_treshold_4,
                calibParams.tolerable_discontinuity,
                calibParams.min_npix,
                calibParams.max_npix,
                calibParams.min_npix_x,
                calibParams.max_npix_x,
                calibParams.min_npix_y,
                calibParams.max_npix_y,
                calibParams.sum_of_grey,
                calibParams.size_of_crosses,
                path=par_path,
            ).write()

            par.ManOriParams(calibParams.n_img, nr, path=par_path).write()
            par.ExamineParams(
                calibParams.Examine_Flag,
                calibParams.Combine_Flag,
                path=par_path,
            ).write()
            par.OrientParams(
                calibParams.point_number_of_orientation,
                calibParams.cc,
                calibParams.xh,
                calibParams.yh,
                calibParams.k1,
                calibParams.k2,
                calibParams.k3,
                calibParams.p1,
                calibParams.p2,
                calibParams.scale,
                calibParams.shear,
                calibParams.interf,
                path=par_path,
            ).write()
            par.ShakingParams(
                calibParams.shaking_first_frame,
                calibParams.shaking_last_frame,
                calibParams.shaking_max_num_points,
                calibParams.shaking_max_num_frames,
                path=par_path,
            ).write()

            par.DumbbellParams(
                calibParams.dumbbell_eps,
                calibParams.dumbbell_scale,
                calibParams.dumbbell_gradient_descent,
                calibParams.dumbbell_penalty_weight,
                calibParams.dumbbell_step,
                calibParams.dumbbell_niter,
                path=par_path,
            ).write()


class TrackHandler(Handler):
    def closed(self, info, is_ok):
        trackParams = info.object
        par_path = trackParams.par_path
        Handler.closed(self, info, is_ok)
        if is_ok:
            par.TrackingParams(
                trackParams.dvxmin,
                trackParams.dvxmax,
                trackParams.dvymin,
                trackParams.dvymax,
                trackParams.dvzmin,
                trackParams.dvzmax,
                trackParams.angle,
                trackParams.dacc,
                trackParams.flagNewParticles,
                path=par_path,
            ).write()


#             print "Michael:", info.object.dvxmin, type(info.object.dvxmin)
#             info.object.write()


# This is the view class of the Tracking Parameters window
class Tracking_Params(HasTraits):
    dvxmin = Float(DEFAULT_FLOAT)
    dvxmax = Float(DEFAULT_FLOAT)
    dvymin = Float(DEFAULT_FLOAT)
    dvymax = Float(DEFAULT_FLOAT)
    dvzmin = Float(DEFAULT_FLOAT)
    dvzmax = Float(DEFAULT_FLOAT)
    angle = Float(DEFAULT_FLOAT)
    dacc = Float(DEFAULT_FLOAT)
    flagNewParticles = Bool(True)

    def __init__(self, par_path):
        super(Tracking_Params, self).__init__()
        self.par_path = par_path
        TrackingParams = par.TrackingParams(path=self.par_path)
        TrackingParams.read()
        self.dvxmin = TrackingParams.dvxmin
        self.dvxmax = TrackingParams.dvxmax
        self.dvymin = TrackingParams.dvymin
        self.dvymax = TrackingParams.dvymax
        self.dvzmin = TrackingParams.dvzmin
        self.dvzmax = TrackingParams.dvzmax
        self.angle = TrackingParams.angle
        self.dacc = TrackingParams.dacc
        self.flagNewParticles = np.bool8(TrackingParams.flagNewParticles)

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
    # loading parameters files:
    # read main parameters

    # Panel 1: General
    Num_Cam = Int(4, label="Number of cameras: ")
    Accept_OnlyAllCameras = Bool(
        False, label="Accept only points seen from all cameras?"
    )
    pair_Flag = Bool(False, label="Include pairs")
    pair_enable_flag = Bool(True)
    all_enable_flag = Bool(True)
    hp_enable_flag = Bool(True)
    inverse_image_flag = Bool(False)

    # add here also size of the images, e.g. 1280 x 1024 pix and
    # the size of the pixels.
    # future option: name of the camera from the list with these
    # parameters saved once somewhere, e.g.
    # Mikrotron EoSense (1280 x 1024, 12 micron pixels)

    # Future - this should be kind of more flexible, e.g.
    # select only some name structure: CamX.YYYYY is clear that the
    # X should be 1-Num_Cam and YYYY should be
    # the running counter of the images. or Cam.X_00YYY.TIFF is also kind
    # of clear that we have 5 digits with
    # same could be for calibration, we have no point to create different
    # names for 4 cameras:
    # calX_run3 will be fine as a base name and X is 1 - Num_Cam
    # not clear yet how to use the variable name later. probably we need to
    # build it as a structure
    # and use it as: for cam in range(Num_Cam):
    # Name_Pre_Image[cam] = ''.join(BaseName,eval(cam),'.',eval(counter))
    #

    # unused parameters
    # TODO: then why are they here?
    # Answer: historical reasons, back compatibility

    tiff_flag = Bool()
    imx = Int(DEFAULT_INT)
    imy = Int(DEFAULT_INT)
    pix_x = Float(DEFAULT_FLOAT)
    pix_y = Float(DEFAULT_FLOAT)
    chfield = Int(DEFAULT_INT)
    img_cal_name = []

    # unsed for calibration
    fixp_name = Str()
    img_ori = []

    Name_1_Image = Str(DEFAULT_STRING, label="Name of 1. image")
    Name_2_Image = Str(DEFAULT_STRING, label="Name of 2. image")
    Name_3_Image = Str(DEFAULT_STRING, label="Name of 3. image")
    Name_4_Image = Str(DEFAULT_STRING, label="Name of 4. image")
    Cali_1_Image = Str(DEFAULT_STRING, label="Calibration data for 1. image")
    Cali_2_Image = Str(DEFAULT_STRING, label="Calibration data for 2. image")
    Cali_3_Image = Str(DEFAULT_STRING, label="Calibration data for 3. image")
    Cali_4_Image = Str(DEFAULT_STRING, label="Calibration data for 4. image")

    # TiffHeader=Bool(True,label='Tiff header') -> probably obsolete for
    # the Python imread () function
    # FrameType=Enum('Frame','Field-odd','Field-even') -> obsolete
    # future option:  List -> Select Media 1 (for each one):
    # {'Air','Glass','Water','Custom'}, etc.
    Refr_Air = Float(1.0, label="Air:")
    Refr_Glass = Float(1.33, label="Glass:")
    Refr_Water = Float(1.46, label="Water:")
    Thick_Glass = Float(1.0, label="Thickness of glass:")

    # New panel 2: ImageProcessing
    HighPass = Bool(True, label="High pass filter")
    # future option: Slider between 0 and 1 for each one
    Gray_Tresh_1 = Int(DEFAULT_INT, label="1st image")
    Gray_Tresh_2 = Int(DEFAULT_INT, label="2nd image")
    Gray_Tresh_3 = Int(DEFAULT_INT, label="3rd image")
    Gray_Tresh_4 = Int(DEFAULT_INT, label="4th image")
    Min_Npix = Int(DEFAULT_INT, label="min npix")
    Max_Npix = Int(DEFAULT_INT, label="max npix")
    Min_Npix_x = Int(DEFAULT_INT, label="min npix x")
    Max_Npix_x = Int(DEFAULT_INT, label="max npix x")
    Min_Npix_y = Int(DEFAULT_INT, label="min npix y")
    Max_Npix_y = Int(DEFAULT_INT, label="max npix y")
    Sum_Grey = Int(DEFAULT_INT, label="Sum of grey value")
    Tol_Disc = Int(DEFAULT_INT, label="Tolerable discontinuity")
    Size_Cross = Int(DEFAULT_INT, label="Size of crosses")
    Subtr_Mask = Bool(False, label="Subtract mask")
    Base_Name_Mask = Str(DEFAULT_STRING, label="Base name for the mask")
    Existing_Target = Bool(False, label="Use existing_target files?")
    Inverse = Bool(False, label="Negative images?")

    # New panel 3: Sequence
    Seq_First = Int(DEFAULT_INT, label="First sequence image:")
    Seq_Last = Int(DEFAULT_INT, label="Last sequence image:")
    Basename_1_Seq = Str(DEFAULT_STRING, label="Basename for 1. sequence")
    Basename_2_Seq = Str(DEFAULT_STRING, label="Basename for 2. sequence")
    Basename_3_Seq = Str(DEFAULT_STRING, label="Basename for 3. sequence")
    Basename_4_Seq = Str(DEFAULT_STRING, label="Basename for 4. sequence")

    # Panel 4: ObservationVolume
    Xmin = Int(DEFAULT_FLOAT, label="Xmin")
    Xmax = Int(DEFAULT_FLOAT, label="Xmax")
    Zmin1 = Int(DEFAULT_FLOAT, label="Zmin")
    Zmin2 = Int(DEFAULT_FLOAT, label="Zmin")
    Zmax1 = Int(DEFAULT_FLOAT, label="Zmax")
    Zmax2 = Int(DEFAULT_FLOAT, label="Zmax")

    # Panel 5: ParticleDetection
    Min_Corr_nx = Float(DEFAULT_FLOAT, label="min corr for ratio nx")
    Min_Corr_ny = Float(DEFAULT_FLOAT, label="min corr for ratio ny")
    Min_Corr_npix = Float(DEFAULT_FLOAT, label="min corr for ratio npix")
    Sum_gv = Float(DEFAULT_FLOAT, label="sum of gv")
    Min_Weight_corr = Float(
        DEFAULT_FLOAT, label="min for weighted correlation"
    )
    Tol_Band = Float(DEFAULT_FLOAT, lable="Tolerance of epipolar band [mm]")

    # Group 1 is the group of General parameters
    # number of cameras, use only quadruplets or also triplets/pairs?
    # names of the test images, calibration files
    Group1 = Group(
        Group(
            Item(name="Num_Cam", width=30),
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
            Item(name="HighPass", enabled_when="hp_enable_flag"),
            Item(name="Inverse"),
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
        # print("test")
        if self.pair_Flag:

            self.all_enable_flag = False

        else:

            self.all_enable_flag = True

    def _Accept_OnlyAllCameras_fired(self):

        if self.Accept_OnlyAllCameras:

            self.pair_enable_flag = False

        else:

            self.pair_enable_flag = True

    # TODO: underscore in Python signifies a private method (i.e. it shouldn't be accessed from outside this module).
    # Answer: change it to the proper names. here it probably means just
    # 'reload'
    def _reload(self):
        # load ptv_par
        ptvParams = par.PtvParams(path=self.par_path)
        ptvParams.read()

        for i in range(ptvParams.n_img):
            exec("self.Name_%d_Image = ptvParams.img_name[%d]" % (i + 1, i))
            exec("self.Cali_%d_Image = ptvParams.img_cal[%d]" % (i + 1, i))

        self.Refr_Air = ptvParams.mmp_n1
        self.Refr_Glass = ptvParams.mmp_n2
        self.Refr_Water = ptvParams.mmp_n3
        self.Thick_Glass = ptvParams.mmp_d
        self.Accept_OnlyAllCameras = np.bool8(ptvParams.allcam_flag)
        self.Num_Cam = ptvParams.n_img
        self.HighPass = np.bool8(ptvParams.hp_flag)
        # load unused
        self.tiff_flag = np.bool8(ptvParams.tiff_flag)
        self.imx = ptvParams.imx
        self.imy = ptvParams.imy
        self.pix_x = ptvParams.pix_x
        self.pix_y = ptvParams.pix_y
        self.chfield = ptvParams.chfield

        # read_calibration parameters
        calOriParams = par.CalOriParams(ptvParams.n_img, path=self.par_path)
        calOriParams.read()

        self.pair_Flag = np.bool8(calOriParams.pair_flag)
        self.img_cal_name = calOriParams.img_cal_name
        self.img_ori = calOriParams.img_ori
        self.fixp_name = calOriParams.fixp_name

        # load read_targ_rec
        targRecParams = par.TargRecParams(ptvParams.n_img, path=self.par_path)
        targRecParams.read()

        for i in range(ptvParams.n_img):
            exec(
                "self.Gray_Tresh_{0} = targRecParams.gvthres[{1}]".format(
                    i + 1, i
                )
            )

        self.Min_Npix = targRecParams.nnmin
        self.Max_Npix = targRecParams.nnmax
        self.Min_Npix_x = targRecParams.nxmin
        self.Max_Npix_x = targRecParams.nxmax
        self.Min_Npix_y = targRecParams.nymin
        self.Max_Npix_y = targRecParams.nymax
        self.Sum_Grey = targRecParams.sumg_min
        self.Tol_Disc = targRecParams.disco
        self.Size_Cross = targRecParams.cr_sz

        # load pft_version
        pftVersionParams = par.PftVersionParams(path=self.par_path)
        pftVersionParams.read()
        self.Existing_Target = np.bool8(pftVersionParams.Existing_Target)

        # load sequence_par
        sequenceParams = par.SequenceParams(
            ptvParams.n_img, path=self.par_path
        )
        sequenceParams.read()

        for i in range(ptvParams.n_img):
            exec(
                "self.Basename_{0}_Seq = sequenceParams.base_name[{1}]".format(
                    i + 1, i
                )
            )

        self.Seq_First = sequenceParams.first
        self.Seq_Last = sequenceParams.last

        # load criteria_par
        criteriaParams = par.CriteriaParams(path=self.par_path)
        criteriaParams.read()
        self.Xmin = criteriaParams.X_lay[0]
        self.Xmax = criteriaParams.X_lay[1]
        self.Zmin1 = criteriaParams.Zmin_lay[0]
        self.Zmin2 = criteriaParams.Zmin_lay[1]
        self.Zmax1 = criteriaParams.Zmax_lay[0]
        self.Zmax2 = criteriaParams.Zmax_lay[1]
        self.Min_Corr_nx = criteriaParams.cnx
        self.Min_Corr_ny = criteriaParams.cny
        self.Min_Corr_npix = criteriaParams.cn
        self.Sum_gv = criteriaParams.csumg
        self.Min_Weight_corr = criteriaParams.corrmin
        self.Tol_Band = criteriaParams.eps0
        
        # write masking parameters
        masking_filename = Path(self.par_path) / 'masking.json'
        if masking_filename.exists():
                masking_dict = json.load(masking_filename.open('r'))
                # json.dump(masking_dict, json_file)
                self.Subtr_Mask = masking_dict['mask_flag']
                self.Base_Name_Mask = masking_dict['mask_base_name']

    # create initfunc
    def __init__(self, par_path):
        HasTraits.__init__(self)
        self.par_path = par_path
        self._reload()


# -----------------------------------------------------------------------------
class Calib_Params(HasTraits):

    # general and unsed variables
    pair_enable_flag = Bool(True)
    n_img = Int(DEFAULT_INT)
    img_name = List
    img_cal = List
    hp_flag = Bool(False, label="highpass")
    allcam_flag = Bool(False, label="all camera targets")
    mmp_n1 = Float(DEFAULT_FLOAT)
    mmp_n2 = Float(DEFAULT_FLOAT)
    mmp_n3 = Float(DEFAULT_FLOAT)
    mmp_d = Float(DEFAULT_FLOAT)

    # images data
    cam_1 = Str(DEFAULT_STRING, label="Calibration picture camera 1")
    cam_2 = Str(DEFAULT_STRING, label="Calibration picture camera 2")
    cam_3 = Str(DEFAULT_STRING, label="Calibration picture camera 3")
    cam_4 = Str(DEFAULT_STRING, label="Calibration picture camera 4")
    ori_cam_1 = Str(DEFAULT_STRING, label="Orientation data picture camera 1")
    ori_cam_2 = Str(DEFAULT_STRING, label="Orientation data picture camera 2")
    ori_cam_3 = Str(DEFAULT_STRING, label="Orientation data picture camera 3")
    ori_cam_4 = Str(DEFAULT_STRING, label="Orientation data picture camera 4")

    fixp_name = Str(DEFAULT_STRING, label="File of Coordinates on plate")
    tiff_head = Bool(True, label="TIFF-Header")
    pair_head = Bool(True, label="Include pairs")
    chfield = Enum("Frame", "Field odd", "Field even")

    Group1_1 = Group(
        Item(name="cam_1"),
        Item(name="cam_2"),
        Item(name="cam_3"),
        Item(name="cam_4"),
        label="Calibration pictures",
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
    Group1_3 = Group(
        Item(name="fixp_name"),
        Group(
            Item(name="tiff_head"),
            Item(name="pair_head", enabled_when="pair_enable_flag"),
            Item(name="chfield", show_label=False, style="custom"),
            orientation="vertical",
            columns=3,
        ),
        orientation="vertical",
    )

    # Group 1 is the group of General parameters
    # number of cameras, use only quadruplets or also triplets/pairs?
    # names of the test images, calibration files

    Group1 = Group(
        Group1_1,
        Group1_2,
        Group1_3,
        orientation="vertical",
        label="Images Data",
    )

    # calibration data detection

    h_image_size = Int(DEFAULT_INT, label="Image size horizontal")
    v_image_size = Int(DEFAULT_INT, label="Image size vertical")
    h_pixel_size = Float(DEFAULT_FLOAT, label="Pixel size horizontal")
    v_pixel_size = Float(DEFAULT_FLOAT, label="Pixel size vertical")

    grey_value_treshold_1 = Int(DEFAULT_INT, label="First Image")
    grey_value_treshold_2 = Int(DEFAULT_INT, label="Second Image")
    grey_value_treshold_3 = Int(DEFAULT_INT, label="Third Image")
    grey_value_treshold_4 = Int(DEFAULT_INT, label="Forth Image")
    tolerable_discontinuity = Int(DEFAULT_INT, label="Tolerable discontinuity")
    min_npix = Int(DEFAULT_INT, label="min npix")
    min_npix_x = Int(DEFAULT_INT, label="min npix in x")
    min_npix_y = Int(DEFAULT_INT, label="min npix in y")
    max_npix = Int(DEFAULT_INT, label="max npix")
    max_npix_x = Int(DEFAULT_INT, label="max npix in x")
    max_npix_y = Int(DEFAULT_INT, label="max npix in y")
    sum_of_grey = Int(DEFAULT_INT, label="Sum of greyvalue")
    size_of_crosses = Int(DEFAULT_INT, label="Size of crosses")

    Group2_1 = Group(
        Item(name="h_image_size"),
        Item(name="v_image_size"),
        Item(name="h_pixel_size"),
        Item(name="v_pixel_size"),
        label="Image properties",
        show_border=True,
        orientation="horizontal",
    )

    Group2_2 = (
        Group(
            Item(name="grey_value_treshold_1"),
            Item(name="grey_value_treshold_2"),
            Item(name="grey_value_treshold_3"),
            Item(name="grey_value_treshold_4"),
            orientation="horizontal",
            label="Grayvalue threshold",
            show_border=True,
        ),
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

    # manuel pre orientation
    img_1_p1 = Int(DEFAULT_INT, label="P1")
    img_1_p2 = Int(DEFAULT_INT, label="P2")
    img_1_p3 = Int(DEFAULT_INT, label="P3")
    img_1_p4 = Int(DEFAULT_INT, label="P4")
    img_2_p1 = Int(DEFAULT_INT, label="P1")
    img_2_p2 = Int(DEFAULT_INT, label="P2")
    img_2_p3 = Int(DEFAULT_INT, label="P3")
    img_2_p4 = Int(DEFAULT_INT, label="P4")
    img_3_p1 = Int(DEFAULT_INT, label="P1")
    img_3_p2 = Int(DEFAULT_INT, label="P2")
    img_3_p3 = Int(DEFAULT_INT, label="P3")
    img_3_p4 = Int(DEFAULT_INT, label="P4")
    img_4_p1 = Int(DEFAULT_INT, label="P1")
    img_4_p2 = Int(DEFAULT_INT, label="P2")
    img_4_p3 = Int(DEFAULT_INT, label="P3")
    img_4_p4 = Int(DEFAULT_INT, label="P4")

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

    # calibration orientation param.

    Examine_Flag = Bool(False, label="Calibrate with different Z")
    Combine_Flag = Bool(False, label="Combine preprocessed planes")

    point_number_of_orientation = Int(
        DEFAULT_INT, label="Point number of orientation"
    )
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

    # dumbbell parameters
    # 5  eps (mm)
    # 46.5 dumbbell scale
    # 0.005 gradient descent factor
    # 1 weight for dumbbell penalty
    # 2 step size through sequence
    # 500 num iterations per click

    dumbbell_eps = Float(DEFAULT_FLOAT, label="dumbbell epsilon")
    dumbbell_scale = Float(DEFAULT_FLOAT, label="dumbbell scale")
    dumbbell_gradient_descent = Float(
        DEFAULT_FLOAT, label="dumbbell gradient descent factor"
    )
    dumbbell_penalty_weight = Float(
        DEFAULT_FLOAT, label="weight for dumbbell penalty"
    )
    dumbbell_step = Int(DEFAULT_INT, label="step size through sequence")
    dumbbell_niter = Int(DEFAULT_INT, label="number of iterations per click")

    Group5 = HGroup(
        VGroup(
            Item(name="dumbbell_eps"),
            Item(name="dumbbell_scale"),
            Item(name="dumbbell_gradient_descent"),
            Item(name="dumbbell_penalty_weight"),
            Item(name="dumbbell_step"),
            Item(name="dumbbell_niter"),
        ),
        spring,
        label="Dumbbell calibration parameters",
        show_border=True,
    )

    # shaking parameters
    # 10000 - first frame
    # 10004 - last frame
    # 10 - max num points used per frame
    # 5 - max number of frames to track

    shaking_first_frame = Int(DEFAULT_INT, label="shaking first frame")
    shaking_last_frame = Int(DEFAULT_INT, label="shaking last frame")
    shaking_max_num_points = Int(DEFAULT_INT, label="shaking max num points")
    shaking_max_num_frames = Int(DEFAULT_INT, label="shaking max num frames")

    Group6 = HGroup(
        VGroup(
            Item(
                name="shaking_first_frame",
            ),
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

    def _reload(self):
        # print("reloading")
        # self.__init__(self)
        # load ptv_par
        ptvParams = par.PtvParams(path=self.par_path)
        ptvParams.read()

        # read picture size parameters
        self.h_image_size = ptvParams.imx
        self.v_image_size = ptvParams.imy
        self.h_pixel_size = ptvParams.pix_x
        self.v_pixel_size = ptvParams.pix_y
        self.img_cal = ptvParams.img_cal
        if ptvParams.allcam_flag:
            self.pair_enable_flag = False
        else:
            self.pair_enable_flag = True

        # unesed parameters

        self.n_img = ptvParams.n_img
        self.img_name = ptvParams.img_name
        self.hp_flag = np.bool8(ptvParams.hp_flag)
        self.allcam_flag = np.bool8(ptvParams.allcam_flag)
        self.mmp_n1 = ptvParams.mmp_n1
        self.mmp_n2 = ptvParams.mmp_n2
        self.mmp_n3 = ptvParams.mmp_n3
        self.mmp_d = ptvParams.mmp_d

        # read_calibration parameters
        calOriParams = par.CalOriParams(self.n_img, path=self.par_path)
        calOriParams.read()
        (fixp_name, img_cal_name, img_ori, tiff_flag, pair_flag, chfield) = (
            calOriParams.fixp_name,
            calOriParams.img_cal_name,
            calOriParams.img_ori,
            calOriParams.tiff_flag,
            calOriParams.pair_flag,
            calOriParams.chfield,
        )

        for i in range(self.n_img):
            exec(
                "self.cam_{0} = calOriParams.img_cal_name[{1}]".format(
                    i + 1, i
                )
            )
            exec(
                "self.ori_cam_{0} = calOriParams.img_ori[{1}]".format(i + 1, i)
            )

        self.tiff_head = np.bool8(tiff_flag)
        self.pair_head = np.bool8(pair_flag)
        self.fixp_name = fixp_name
        if chfield == 0:
            self.chfield = "Frame"
        elif chfield == 1:
            self.chfield = "Field odd"
        else:
            self.chfield = "Field even"

        # read detect plate parameters
        detectPlateParams = par.DetectPlateParams(path=self.par_path)
        detectPlateParams.read()

        (
            gv_th1,
            gv_th2,
            gv_th3,
            gv_th4,
            tolerable_discontinuity,
            min_npix,
            max_npix,
            min_npix_x,
            max_npix_x,
            min_npix_y,
            max_npix_y,
            sum_of_grey,
            size_of_crosses,
        ) = (
            detectPlateParams.gvth_1,
            detectPlateParams.gvth_2,
            detectPlateParams.gvth_3,
            detectPlateParams.gvth_4,
            detectPlateParams.tol_dis,
            detectPlateParams.min_npix,
            detectPlateParams.max_npix,
            detectPlateParams.min_npix_x,
            detectPlateParams.max_npix_x,
            detectPlateParams.min_npix_y,
            detectPlateParams.max_npix_y,
            detectPlateParams.sum_grey,
            detectPlateParams.size_cross,
        )

        for i in range(self.n_img):
            exec("self.grey_value_treshold_{0} = gv_th{0}".format(i + 1))

        self.tolerable_discontinuity = tolerable_discontinuity
        self.min_npix = min_npix
        self.min_npix_x = min_npix_x
        self.min_npix_y = min_npix_y
        self.max_npix = max_npix
        self.max_npix_x = max_npix_x
        self.max_npix_y = max_npix_y
        self.sum_of_grey = sum_of_grey
        self.size_of_crosses = size_of_crosses

        # read manual orientaion parameters
        manOriParams = par.ManOriParams(self.n_img, [], path=self.par_path)
        manOriParams.read()

        for i in range(self.n_img):
            for j in range(4):  # 4 points per image
                exec(f"self.img_{i+1}_p{j+1} = manOriParams.nr[{i*4+j}]")

        # examine arameters
        examineParams = par.ExamineParams(path=self.par_path)
        examineParams.read()
        (self.Examine_Flag, self.Combine_Flag) = (
            examineParams.Examine_Flag,
            examineParams.Combine_Flag,
        )

        # orientation parameters
        orientParams = par.OrientParams(path=self.par_path)
        orientParams.read()
        (
            po_num_of_ori,
            cc,
            xh,
            yh,
            k1,
            k2,
            k3,
            p1,
            p2,
            scale,
            shear,
            interf,
        ) = (
            orientParams.pnfo,
            orientParams.cc,
            orientParams.xh,
            orientParams.yh,
            orientParams.k1,
            orientParams.k2,
            orientParams.k3,
            orientParams.p1,
            orientParams.p2,
            orientParams.scale,
            orientParams.shear,
            orientParams.interf,
        )

        self.point_number_of_orientation = po_num_of_ori
        self.cc = np.bool8(cc)
        self.xh = np.bool8(xh)
        self.yh = np.bool8(yh)
        self.k1 = np.bool8(k1)
        self.k2 = np.bool8(k2)
        self.k3 = np.bool8(k3)
        self.p1 = np.bool8(p1)
        self.p2 = np.bool8(p2)
        self.scale = np.bool8(scale)
        self.shear = np.bool8(shear)
        self.interf = np.bool8(interf)

        dumbbellParams = par.DumbbellParams(path=self.par_path)
        dumbbellParams.read()
        (
            self.dumbbell_eps,
            self.dumbbell_scale,
            self.dumbbell_gradient_descent,
            self.dumbbell_penalty_weight,
            self.dumbbell_step,
            self.dumbbell_niter,
        ) = (
            dumbbellParams.dumbbell_eps,
            dumbbellParams.dumbbell_scale,
            dumbbellParams.dumbbell_gradient_descent,
            dumbbellParams.dumbbell_penalty_weight,
            dumbbellParams.dumbbell_step,
            dumbbellParams.dumbbell_niter,
        )

        shakingParams = par.ShakingParams(path=self.par_path)
        shakingParams.read()
        (
            self.shaking_first_frame,
            self.shaking_last_frame,
            self.shaking_max_num_points,
            self.shaking_max_num_frames,
        ) = (
            shakingParams.shaking_first_frame,
            shakingParams.shaking_last_frame,
            shakingParams.shaking_max_num_points,
            shakingParams.shaking_max_num_frames,
        )

    def __init__(self, par_path):
        HasTraits.__init__(self)
        self.par_path = par_path
        self._reload()

    # ---------------------------------------------------------------------------


class Paramset(HasTraits):
    name = Str
    par_path = Path
    m_params = Instance(Main_Params)
    c_params = Instance(Calib_Params)
    t_params = Instance(Tracking_Params)


class Experiment(HasTraits):
    active_params = Instance(Paramset)
    paramsets = List(Paramset)

    def __init__(self):
        HasTraits.__init__(self)
        self.changed_active_params = False

    def getParamsetIdx(self, paramset):
        if isinstance(
                paramset,
                type(1)):  # integer value (index of the paramset)
            return paramset
        else:  # Value is instance of Pramset
            return self.paramsets.index(paramset)

    def addParamset(self, name: str, par_path: Path):
        self.paramsets.append(
            Paramset(
                name=name,
                par_path=par_path,
                m_params=Main_Params(par_path=par_path),
                c_params=Calib_Params(par_path=par_path),
                t_params=Tracking_Params(par_path=par_path),
            )
        )

    def removeParamset(self, paramset):
        paramset_idx = self.getParamsetIdx(paramset)
        self.paramsets.remove(self.paramsets[paramset_idx])

    def nParamsets(self):
        return len(self.paramsets)

    def setActive(self, paramset):
        paramset_idx = self.getParamsetIdx(paramset)
        self.active_params = self.paramsets[paramset_idx]
        self.paramsets.pop(paramset_idx)
        self.paramsets.insert(0, self.active_params)
        self.syncActiveDir()

    def syncActiveDir(self):
        default_parameters_path = Path(par.par_dir_prefix).resolve()
        print(f" Syncing parameters between two folders: \n")
        print(f"{self.active_params.par_path}, {default_parameters_path}")
        par.copy_params_dir(self.active_params.par_path, default_parameters_path)

    def populate_runs(self, exp_path: Path):
        # Read all parameters directories from an experiment directory
        self.paramsets = []
        
        # list all directories
        dir_contents = [
            f
            for f in exp_path.iterdir()
            if (exp_path / f).is_dir()
        ]
        
        # choose directories that has 'parameters' in their path
        dir_contents = [
            f for f in dir_contents if str(f.stem).startswith(par.par_dir_prefix)
        ]
        # print(f" parameter sets are in {dir_contents}")

        # if only 'parameters' folder, create its copy 'parametersRun1'
        if len(dir_contents) == 1 and str(dir_contents[0].stem) == par.par_dir_prefix:
            # single parameters directory, backward compatibility
            exp_name = "Run1"
            new_name = str(dir_contents[0]) + exp_name
            new_path = Path(new_name).resolve()
            print(f" Copying to the new folder {new_path} \n")
            print("------------------------------------------\n")
            par.copy_params_dir(dir_contents[0], new_path)
            dir_contents.append(new_path)

        # take each path in the dir_contents and create a tree entity with the short name
        for dir_item in dir_contents:
            # par_path = exp_path / dir_item
            if str(dir_item.stem) != par.par_dir_prefix:
                # This should be a params dir, add a tree entry for it.
                exp_name = str(dir_item.stem).rsplit('parameters',maxsplit=1)[-1]

                print(f"Experiment name is: {exp_name}")
                print(f" adding Parameter set\n")
                self.addParamset(exp_name, dir_item)

        if not self.changed_active_params:
            if self.nParamsets() > 0:
                self.setActive(0)
