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
        mainPar = info.object
        par_path = mainPar.par_path
        Handler.closed(self, info, is_ok)
        if is_ok:
            img_name = [
                mainPar.Name_1_Image,
                mainPar.Name_2_Image,
                mainPar.Name_3_Image,
                mainPar.Name_4_Image,
            ]
            img_cal_name = [
                mainPar.Cali_1_Image,
                mainPar.Cali_2_Image,
                mainPar.Cali_3_Image,
                mainPar.Cali_4_Image,
            ]

            gvthres = [
                mainPar.Gray_Tresh_1,
                mainPar.Gray_Tresh_2,
                mainPar.Gray_Tresh_3,
                mainPar.Gray_Tresh_4,
            ]
            base_name = [
                mainPar.Basename_1_Seq,
                mainPar.Basename_2_Seq,
                mainPar.Basename_3_Seq,
                mainPar.Basename_4_Seq,
            ]
            X_lay = [mainPar.Xmin, mainPar.Xmax]
            Zmin_lay = [mainPar.Zmin1, mainPar.Zmin2]
            Zmax_lay = [mainPar.Zmax1, mainPar.Zmax2]

            # write ptv_par
            par.PtvPar(
                mainPar.Num_Cam,
                img_name,
                img_cal_name,
                mainPar.HighPass,
                mainPar.Accept_OnlyAllCameras,
                mainPar.tiff_flag,
                mainPar.imx,
                mainPar.imy,
                mainPar.pix_x,
                mainPar.pix_y,
                mainPar.chfield,
                mainPar.Refr_Air,
                mainPar.Refr_Glass,
                mainPar.Refr_Water,
                mainPar.Thick_Glass,
                path=par_path,
            ).write()
            # write calibration parameters
            par.CalOriPar(
                mainPar.Num_Cam,
                mainPar.fixp_name,
                mainPar.img_cal_name,
                mainPar.img_ori,
                mainPar.tiff_flag,
                mainPar.pair_Flag,
                mainPar.chfield,
                path=par_path,
            ).write()

            # write targ_rec_par
            par.TargRecPar(
                mainPar.Num_Cam,
                gvthres,
                mainPar.Tol_Disc,
                mainPar.Min_Npix,
                mainPar.Max_Npix,
                mainPar.Min_Npix_x,
                mainPar.Max_Npix_x,
                mainPar.Min_Npix_y,
                mainPar.Max_Npix_y,
                mainPar.Sum_Grey,
                mainPar.Size_Cross,
                path=par_path,
            ).write()
            # write pft_version_par
            par.PftVersionPar(
                mainPar.Existing_Target, path=par_path
            ).write()
            # write sequence_par
            par.SequencePar(
                mainPar.Num_Cam,
                base_name,
                mainPar.Seq_First,
                mainPar.Seq_Last,
                path=par_path,
            ).write()
            # write criteria_par
            par.CriteriaPar(
                X_lay,
                Zmin_lay,
                Zmax_lay,
                mainPar.Min_Corr_nx,
                mainPar.Min_Corr_ny,
                mainPar.Min_Corr_npix,
                mainPar.Sum_gv,
                mainPar.Min_Weight_corr,
                mainPar.Tol_Band,
                path=par_path,
            ).write()
            
            # write masking parameters
            masking_dict = {
                "mask_flag":mainPar.Subtr_Mask,
                "mask_base_name":mainPar.Base_Name_Mask,
            }
            with (Path(par_path) / 'masking.json').open('w') as json_file:
                json.dump(masking_dict, json_file)


# define handler function for calibration parameters
class CalHandler(Handler):
    def closed(self, info, is_ok):
        calibPar = info.object
        par_path = calibPar.par_path
        print("inside CalHandler ", par_path)
        Handler.closed(self, info, is_ok)
        if is_ok:
            img_cal_name = [
                calibPar.cam_1,
                calibPar.cam_2,
                calibPar.cam_3,
                calibPar.cam_4,
            ]
            img_ori = [
                calibPar.ori_cam_1,
                calibPar.ori_cam_2,
                calibPar.ori_cam_3,
                calibPar.ori_cam_4,
            ]
            nr1 = [
                calibPar.img_1_p1,
                calibPar.img_1_p2,
                calibPar.img_1_p3,
                calibPar.img_1_p4,
            ]
            nr2 = [
                calibPar.img_2_p1,
                calibPar.img_2_p2,
                calibPar.img_2_p3,
                calibPar.img_2_p4,
            ]
            nr3 = [
                calibPar.img_3_p1,
                calibPar.img_3_p2,
                calibPar.img_3_p3,
                calibPar.img_3_p4,
            ]
            nr4 = [
                calibPar.img_4_p1,
                calibPar.img_4_p2,
                calibPar.img_4_p3,
                calibPar.img_4_p4,
            ]

            nr = [nr1, nr2, nr3, nr4]

            if calibPar.chfield == "Frame":
                chfield = 0
            elif calibPar.chfield == "Field odd":
                chfield = 1
            else:
                chfield = 2
            par.PtvPar(
                calibPar.n_img,
                calibPar.img_name,
                calibPar.img_cal,
                calibPar.hp_flag,
                calibPar.allcam_flag,
                calibPar.tiff_head,
                calibPar.h_image_size,
                calibPar.v_image_size,
                calibPar.h_pixel_size,
                calibPar.v_pixel_size,
                chfield,
                calibPar.mmp_n1,
                calibPar.mmp_n2,
                calibPar.mmp_n3,
                calibPar.mmp_d,
                path=par_path,
            ).write()

            par.CalOriPar(
                calibPar.n_img,
                calibPar.fixp_name,
                img_cal_name,
                img_ori,
                calibPar.tiff_head,
                calibPar.pair_head,
                chfield,
                path=par_path,
            ).write()

            par.DetectPlatePar(
                calibPar.grey_value_treshold_1,
                calibPar.grey_value_treshold_2,
                calibPar.grey_value_treshold_3,
                calibPar.grey_value_treshold_4,
                calibPar.tolerable_discontinuity,
                calibPar.min_npix,
                calibPar.max_npix,
                calibPar.min_npix_x,
                calibPar.max_npix_x,
                calibPar.min_npix_y,
                calibPar.max_npix_y,
                calibPar.sum_of_grey,
                calibPar.size_of_crosses,
                path=par_path,
            ).write()

            par.ManOriPar(calibPar.n_img, nr, path=par_path).write()
            par.ExaminePar(
                calibPar.Examine_Flag,
                calibPar.Combine_Flag,
                path=par_path,
            ).write()
            par.OrientPar(
                calibPar.point_number_of_orientation,
                calibPar.cc,
                calibPar.xh,
                calibPar.yh,
                calibPar.k1,
                calibPar.k2,
                calibPar.k3,
                calibPar.p1,
                calibPar.p2,
                calibPar.scale,
                calibPar.shear,
                calibPar.interf,
                path=par_path,
            ).write()
            par.ShakingPar(
                calibPar.shaking_first_frame,
                calibPar.shaking_last_frame,
                calibPar.shaking_max_num_points,
                calibPar.shaking_max_num_frames,
                path=par_path,
            ).write()

            par.DumbbellPar(
                calibPar.dumbbell_eps,
                calibPar.dumbbell_scale,
                calibPar.dumbbell_gradient_descent,
                calibPar.dumbbell_penalty_weight,
                calibPar.dumbbell_step,
                calibPar.dumbbell_niter,
                path=par_path,
            ).write()


class TrackHandler(Handler):
    def closed(self, info, is_ok):
        trackPar = info.object
        par_path = trackPar.par_path
        Handler.closed(self, info, is_ok)
        if is_ok:
            par.TrackPar(
                trackPar.dvxmin,
                trackPar.dvxmax,
                trackPar.dvymin,
                trackPar.dvymax,
                trackPar.dvzmin,
                trackPar.dvzmax,
                trackPar.angle,
                trackPar.dacc,
                trackPar.flagNewParticles,
                path=par_path,
            ).write()


#             print "Michael:", info.object.dvxmin, type(info.object.dvxmin)
#             info.object.write()


# This is the view class of the Tracking Parameters window
class Tracking_Par(HasTraits):
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
        super(Tracking_Par, self).__init__()
        self.par_path = par_path
        TrackPar = par.TrackPar(path=self.par_path)
        TrackPar.read()
        self.dvxmin = TrackPar.dvxmin
        self.dvxmax = TrackPar.dvxmax
        self.dvymin = TrackPar.dvymin
        self.dvymax = TrackPar.dvymax
        self.dvzmin = TrackPar.dvzmin
        self.dvzmax = TrackPar.dvzmax
        self.angle = TrackPar.angle
        self.dacc = TrackPar.dacc
        self.flagNewParticles = np.bool8(TrackPar.flagNewParticles)

    Tracking_Par_View = View(
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


class Main_Par(HasTraits):
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
    Xmin = Float(DEFAULT_FLOAT, label="Xmin")
    Xmax = Float(DEFAULT_FLOAT, label="Xmax")
    Zmin1 = Float(DEFAULT_FLOAT, label="Zmin")
    Zmin2 = Float(DEFAULT_FLOAT, label="Zmin")
    Zmax1 = Float(DEFAULT_FLOAT, label="Zmax")
    Zmax2 = Float(DEFAULT_FLOAT, label="Zmax")

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

    Main_Par_View = View(
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
        ptvPar = par.PtvPar(path=self.par_path)
        ptvPar.read()

        for i in range(ptvPar.n_img):
            exec("self.Name_%d_Image = ptvPar.img_name[%d]" % (i + 1, i))
            exec("self.Cali_%d_Image = ptvPar.img_cal[%d]" % (i + 1, i))

        self.Refr_Air = ptvPar.mmp_n1
        self.Refr_Glass = ptvPar.mmp_n2
        self.Refr_Water = ptvPar.mmp_n3
        self.Thick_Glass = ptvPar.mmp_d
        self.Accept_OnlyAllCameras = np.bool8(ptvPar.allcam_flag)
        self.Num_Cam = ptvPar.n_img
        self.HighPass = np.bool8(ptvPar.hp_flag)
        # load unused
        self.tiff_flag = np.bool8(ptvPar.tiff_flag)
        self.imx = ptvPar.imx
        self.imy = ptvPar.imy
        self.pix_x = ptvPar.pix_x
        self.pix_y = ptvPar.pix_y
        self.chfield = ptvPar.chfield

        # read_calibration parameters
        calOriPar = par.CalOriPar(ptvPar.n_img, path=self.par_path)
        calOriPar.read()

        self.pair_Flag = np.bool8(calOriPar.pair_flag)
        self.img_cal_name = calOriPar.img_cal_name
        self.img_ori = calOriPar.img_ori
        self.fixp_name = calOriPar.fixp_name

        # load read_targ_rec
        targRecPar = par.TargRecPar(ptvPar.n_img, path=self.par_path)
        targRecPar.read()

        for i in range(ptvPar.n_img):
            exec(
                "self.Gray_Tresh_{0} = targRecPar.gvthres[{1}]".format(
                    i + 1, i
                )
            )

        self.Min_Npix = targRecPar.nnmin
        self.Max_Npix = targRecPar.nnmax
        self.Min_Npix_x = targRecPar.nxmin
        self.Max_Npix_x = targRecPar.nxmax
        self.Min_Npix_y = targRecPar.nymin
        self.Max_Npix_y = targRecPar.nymax
        self.Sum_Grey = targRecPar.sumg_min
        self.Tol_Disc = targRecPar.disco
        self.Size_Cross = targRecPar.cr_sz

        # load pft_version
        pftVersionPar = par.PftVersionPar(path=self.par_path)
        pftVersionPar.read()
        self.Existing_Target = np.bool8(pftVersionPar.Existing_Target)

        # load sequence_par
        sequencePar = par.SequencePar(
            ptvPar.n_img, path=self.par_path
        )
        sequencePar.read()

        for i in range(ptvPar.n_img):
            exec(
                "self.Basename_{0}_Seq = sequencePar.base_name[{1}]".format(
                    i + 1, i
                )
            )

        self.Seq_First = sequencePar.first
        self.Seq_Last = sequencePar.last

        # load criteria_par
        criteriaPar = par.CriteriaPar(path=self.par_path)
        criteriaPar.read()
        self.Xmin = criteriaPar.X_lay[0]
        self.Xmax = criteriaPar.X_lay[1]
        self.Zmin1 = criteriaPar.Zmin_lay[0]
        self.Zmin2 = criteriaPar.Zmin_lay[1]
        self.Zmax1 = criteriaPar.Zmax_lay[0]
        self.Zmax2 = criteriaPar.Zmax_lay[1]
        self.Min_Corr_nx = criteriaPar.cnx
        self.Min_Corr_ny = criteriaPar.cny
        self.Min_Corr_npix = criteriaPar.cn
        self.Sum_gv = criteriaPar.csumg
        self.Min_Weight_corr = criteriaPar.corrmin
        self.Tol_Band = criteriaPar.eps0
        
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
class Calib_Par(HasTraits):

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

    Calib_Par_View = View(
        Tabbed(Group1, Group2, Group3, Group4, Group5, Group6),
        buttons=["Undo", "OK", "Cancel"],
        handler=CalHandler(),
        title="Calibration Parameters",
    )

    def _reload(self):
        # print("reloading")
        # self.__init__(self)
        # load ptv_par
        ptvPar = par.PtvPar(path=self.par_path)
        ptvPar.read()

        # read picture size parameters
        self.h_image_size = ptvPar.imx
        self.v_image_size = ptvPar.imy
        self.h_pixel_size = ptvPar.pix_x
        self.v_pixel_size = ptvPar.pix_y
        self.img_cal = ptvPar.img_cal
        if ptvPar.allcam_flag:
            self.pair_enable_flag = False
        else:
            self.pair_enable_flag = True

        # unesed parameters

        self.n_img = ptvPar.n_img
        self.img_name = ptvPar.img_name
        self.hp_flag = np.bool8(ptvPar.hp_flag)
        self.allcam_flag = np.bool8(ptvPar.allcam_flag)
        self.mmp_n1 = ptvPar.mmp_n1
        self.mmp_n2 = ptvPar.mmp_n2
        self.mmp_n3 = ptvPar.mmp_n3
        self.mmp_d = ptvPar.mmp_d

        # read_calibration parameters
        calOriPar = par.CalOriPar(self.n_img, path=self.par_path)
        calOriPar.read()
        (fixp_name, img_cal_name, img_ori, tiff_flag, pair_flag, chfield) = (
            calOriPar.fixp_name,
            calOriPar.img_cal_name,
            calOriPar.img_ori,
            calOriPar.tiff_flag,
            calOriPar.pair_flag,
            calOriPar.chfield,
        )

        for i in range(self.n_img):
            exec(
                "self.cam_{0} = calOriPar.img_cal_name[{1}]".format(
                    i + 1, i
                )
            )
            exec(
                "self.ori_cam_{0} = calOriPar.img_ori[{1}]".format(i + 1, i)
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
        detectPlatePar = par.DetectPlatePar(path=self.par_path)
        detectPlatePar.read()

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
            detectPlatePar.gvth_1,
            detectPlatePar.gvth_2,
            detectPlatePar.gvth_3,
            detectPlatePar.gvth_4,
            detectPlatePar.tol_dis,
            detectPlatePar.min_npix,
            detectPlatePar.max_npix,
            detectPlatePar.min_npix_x,
            detectPlatePar.max_npix_x,
            detectPlatePar.min_npix_y,
            detectPlatePar.max_npix_y,
            detectPlatePar.sum_grey,
            detectPlatePar.size_cross,
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
        manOriPar = par.ManOriPar(self.n_img, [], path=self.par_path)
        manOriPar.read()

        for i in range(self.n_img):
            for j in range(4):  # 4 points per image
                exec(f"self.img_{i+1}_p{j+1} = manOriPar.nr[{i*4+j}]")

        # examine arameters
        examinePar = par.ExaminePar(path=self.par_path)
        examinePar.read()
        (self.Examine_Flag, self.Combine_Flag) = (
            examinePar.Examine_Flag,
            examinePar.Combine_Flag,
        )

        # orientation parameters
        orientPar = par.OrientPar(path=self.par_path)
        orientPar.read()
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
            orientPar.pnfo,
            orientPar.cc,
            orientPar.xh,
            orientPar.yh,
            orientPar.k1,
            orientPar.k2,
            orientPar.k3,
            orientPar.p1,
            orientPar.p2,
            orientPar.scale,
            orientPar.shear,
            orientPar.interf,
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

        dumbbellPar = par.DumbbellPar(path=self.par_path)
        dumbbellPar.read()
        (
            self.dumbbell_eps,
            self.dumbbell_scale,
            self.dumbbell_gradient_descent,
            self.dumbbell_penalty_weight,
            self.dumbbell_step,
            self.dumbbell_niter,
        ) = (
            dumbbellPar.dumbbell_eps,
            dumbbellPar.dumbbell_scale,
            dumbbellPar.dumbbell_gradient_descent,
            dumbbellPar.dumbbell_penalty_weight,
            dumbbellPar.dumbbell_step,
            dumbbellPar.dumbbell_niter,
        )

        shakingPar = par.ShakingPar(path=self.par_path)
        shakingPar.read()
        (
            self.shaking_first_frame,
            self.shaking_last_frame,
            self.shaking_max_num_points,
            self.shaking_max_num_frames,
        ) = (
            shakingPar.shaking_first_frame,
            shakingPar.shaking_last_frame,
            shakingPar.shaking_max_num_points,
            shakingPar.shaking_max_num_frames,
        )

    def __init__(self, par_path):
        HasTraits.__init__(self)
        self.par_path = par_path
        self._reload()

    # ---------------------------------------------------------------------------


class Paret(HasTraits):
    name = Str
    par_path = Path
    m_Par = Instance(Main_Par)
    c_Par = Instance(Calib_Par)
    t_Par = Instance(Tracking_Par)


class Experiment(HasTraits):
    active_Par = Instance(Paret)
    Parets = List(Paret)

    def __init__(self):
        HasTraits.__init__(self)
        self.changed_active_Par = False

    def getParetIdx(self, Paret):
        if isinstance(
                Paret,
                type(1)):  # integer value (index of the Paret)
            return Paret
        else:  # Value is instance of Pramset
            return self.Parets.index(Paret)

    def addParet(self, name: str, par_path: Path):
        self.Parets.append(
            Paret(
                name=name,
                par_path=par_path,
                m_Par=Main_Par(par_path=par_path),
                c_Par=Calib_Par(par_path=par_path),
                t_Par=Tracking_Par(par_path=par_path),
            )
        )

    def removeParet(self, Paret):
        Paret_idx = self.getParetIdx(Paret)
        self.Parets.remove(self.Parets[Paret_idx])

    def nParets(self):
        return len(self.Parets)

    def setActive(self, Paret):
        Paret_idx = self.getParetIdx(Paret)
        self.active_Par = self.Parets[Paret_idx]
        self.Parets.pop(Paret_idx)
        self.Parets.insert(0, self.active_Par)
        self.syncActiveDir()

    def syncActiveDir(self):
        default_parameters_path = Path(par.par_dir_prefix).resolve()
        print(" Syncing parameters between two folders: \n")
        print(f"{self.active_Par.par_path}, {default_parameters_path}")
        par.copy_Par_dir(self.active_Par.par_path, default_parameters_path)

    def populate_runs(self, exp_path: Path):
        # Read all parameters directories from an experiment directory
        self.Parets = []
        
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
            par.copy_Par_dir(dir_contents[0], new_path)
            dir_contents.append(new_path)

        # take each path in the dir_contents and create a tree entity with the short name
        for dir_item in dir_contents:
            # par_path = exp_path / dir_item
            if str(dir_item.stem) != par.par_dir_prefix:
                # This should be a Par dir, add a tree entry for it.
                exp_name = str(dir_item.stem).rsplit('parameters',maxsplit=1)[-1]

                print(f"Experiment name is: {exp_name}")
                print(" adding Parameter set\n")
                self.addParet(exp_name, dir_item)

        if not self.changed_active_Par:
            if self.nParets() > 0:
                self.setActive(0)
