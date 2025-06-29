import json
from pathlib import Path
import shutil

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

import numpy as np
from pyptv.parameter_manager import ParameterManager


DEFAULT_STRING = "---"
DEFAULT_INT = -999
DEFAULT_FLOAT = -999.0


# define handler function for main parameters
class ParamHandler(Handler):
    def closed(self, info, is_ok):
        if is_ok:
            main_params = info.object
            pm = main_params.param_manager

            # Update ptv.par
            img_name = [main_params.Name_1_Image, main_params.Name_2_Image, main_params.Name_3_Image, main_params.Name_4_Image]
            img_cal_name = [main_params.Cali_1_Image, main_params.Cali_2_Image, main_params.Cali_3_Image, main_params.Cali_4_Image]
            pm.parameters['ptv'].update({
                'n_img': main_params.Num_Cam, 'img_name': img_name, 'img_cal': img_cal_name,
                'hp_flag': main_params.HighPass, 'allcam_flag': main_params.Accept_OnlyAllCameras,
                'tiff_flag': main_params.tiff_flag, 'imx': main_params.imx, 'imy': main_params.imy,
                'pix_x': main_params.pix_x, 'pix_y': main_params.pix_y, 'chfield': main_params.chfield,
                'mmp_n1': main_params.Refr_Air, 'mmp_n2': main_params.Refr_Glass,
                'mmp_n3': main_params.Refr_Water, 'mmp_d': main_params.Thick_Glass,
                'splitter': main_params.Splitter
            })

            # Update cal_ori.par
            pm.parameters['cal_ori'].update({
                'n_img': main_params.Num_Cam, 'fixp_name': main_params.fixp_name,
                'img_cal_name': main_params.img_cal_name, 'img_ori': main_params.img_ori,
                'tiff_flag': main_params.tiff_flag, 'pair_flag': main_params.pair_Flag,
                'chfield': main_params.chfield
            })

            # Update targ_rec.par
            gvthres = [main_params.Gray_Tresh_1, main_params.Gray_Tresh_2, main_params.Gray_Tresh_3, main_params.Gray_Tresh_4]
            pm.parameters['targ_rec'].update({
                'n_img': main_params.Num_Cam, 'gvthres': gvthres, 'disco': main_params.Tol_Disc,
                'nnmin': main_params.Min_Npix, 'nnmax': main_params.Max_Npix,
                'nxmin': main_params.Min_Npix_x, 'nxmax': main_params.Max_Npix_x,
                'nymin': main_params.Min_Npix_y, 'nymax': main_params.Max_Npix_y,
                'sumg_min': main_params.Sum_Grey, 'cr_sz': main_params.Size_Cross
            })

            # Update pft_version.par
            pm.parameters['pft_version']['Existing_Target'] = main_params.Existing_Target

            # Update sequence.par
            base_name = [main_params.Basename_1_Seq, main_params.Basename_2_Seq, main_params.Basename_3_Seq, main_params.Basename_4_Seq]
            pm.parameters['sequence'].update({
                'n_img': main_params.Num_Cam, 'base_name': base_name,
                'first': main_params.Seq_First, 'last': main_params.Seq_Last
            })

            # Update criteria.par
            X_lay = [main_params.Xmin, main_params.Xmax]
            Zmin_lay = [main_params.Zmin1, main_params.Zmin2]
            Zmax_lay = [main_params.Zmax1, main_params.Zmax2]
            pm.parameters['criteria'].update({
                'X_lay': X_lay, 'Zmin_lay': Zmin_lay, 'Zmax_lay': Zmax_lay,
                'cnx': main_params.Min_Corr_nx, 'cny': main_params.Min_Corr_ny,
                'cn': main_params.Min_Corr_npix, 'csumg': main_params.Sum_gv,
                'corrmin': main_params.Min_Weight_corr, 'eps0': main_params.Tol_Band
            })

            # Update masking parameters
            pm.parameters['masking'] = {
                'mask_flag': main_params.Subtr_Mask,
                'mask_base_name': main_params.Base_Name_Mask
            }

            # Save all changes to the YAML file
            pm.to_yaml(pm.path / 'parameters.yaml')


# define handler function for calibration parameters
class CalHandler(Handler):
    def closed(self, info, is_ok):
        if is_ok:
            calib_params = info.object
            pm = calib_params.param_manager

            # Update ptv.par
            pm.parameters['ptv'].update({
                'n_img': calib_params.n_img, 'img_name': calib_params.img_name, 'img_cal': calib_params.img_cal,
                'hp_flag': calib_params.hp_flag, 'allcam_flag': calib_params.allcam_flag,
                'tiff_flag': calib_params.tiff_head, 'imx': calib_params.h_image_size,
                'imy': calib_params.v_image_size, 'pix_x': calib_params.h_pixel_size,
                'pix_y': calib_params.v_pixel_size, 'chfield': calib_params.chfield,
                'mmp_n1': calib_params.mmp_n1, 'mmp_n2': calib_params.mmp_n2,
                'mmp_n3': calib_params.mmp_n3, 'mmp_d': calib_params.mmp_d
            })

            # Update cal_ori.par
            img_cal_name = [calib_params.cam_1, calib_params.cam_2, calib_params.cam_3, calib_params.cam_4]
            img_ori = [calib_params.ori_cam_1, calib_params.ori_cam_2, calib_params.ori_cam_3, calib_params.ori_cam_4]
            pm.parameters['cal_ori'].update({
                'n_img': calib_params.n_img, 'fixp_name': calib_params.fixp_name,
                'img_cal_name': img_cal_name, 'img_ori': img_ori,
                'tiff_flag': calib_params.tiff_head, 'pair_flag': calib_params.pair_head,
                'chfield': calib_params.chfield,
                'cal_splitter': calib_params._cal_splitter
            })

            # Update detect_plate.par
            pm.parameters['detect_plate'].update({
                'gvth_1': calib_params.grey_value_treshold_1, 'gvth_2': calib_params.grey_value_treshold_2,
                'gvth_3': calib_params.grey_value_treshold_3, 'gvth_4': calib_params.grey_value_treshold_4,
                'tol_dis': calib_params.tolerable_discontinuity, 'min_npix': calib_params.min_npix,
                'max_npix': calib_params.max_npix, 'min_npix_x': calib_params.min_npix_x,
                'max_npix_x': calib_params.max_npix_x, 'min_npix_y': calib_params.min_npix_y,
                'max_npix_y': calib_params.max_npix_y, 'sum_grey': calib_params.sum_of_grey,
                'size_cross': calib_params.size_of_crosses
            })

            # Update man_ori.par
            nr1 = [calib_params.img_1_p1, calib_params.img_1_p2, calib_params.img_1_p3, calib_params.img_1_p4]
            nr2 = [calib_params.img_2_p1, calib_params.img_2_p2, calib_params.img_2_p3, calib_params.img_2_p4]
            nr3 = [calib_params.img_3_p1, calib_params.img_3_p2, calib_params.img_3_p3, calib_params.img_3_p4]
            nr4 = [calib_params.img_4_p1, calib_params.img_4_p2, calib_params.img_4_p3, calib_params.img_4_p4]
            nr = [nr1, nr2, nr3, nr4]
            pm.parameters['man_ori']['nr'] = nr

            # Update examine.par
            pm.parameters['examine']['Examine_Flag'] = calib_params.Examine_Flag
            pm.parameters['examine']['Combine_Flag'] = calib_params.Combine_Flag

            # Update orient.par
            pm.parameters['orient'].update({
                'pnfo': calib_params.point_number_of_orientation, 'cc': calib_params.cc,
                'xh': calib_params.xh, 'yh': calib_params.yh, 'k1': calib_params.k1,
                'k2': calib_params.k2, 'k3': calib_params.k3, 'p1': calib_params.p1,
                'p2': calib_params.p2, 'scale': calib_params.scale, 'shear': calib_params.shear,
                'interf': calib_params.interf
            })

            # Update shaking.par
            pm.parameters['shaking'].update({
                'shaking_first_frame': calib_params.shaking_first_frame,
                'shaking_last_frame': calib_params.shaking_last_frame,
                'shaking_max_num_points': calib_params.shaking_max_num_points,
                'shaking_max_num_frames': calib_params.shaking_max_num_frames
            })

            # Update dumbbell.par
            pm.parameters['dumbbell'].update({
                'dumbbell_eps': calib_params.dumbbell_eps,
                'dumbbell_scale': calib_params.dumbbell_scale,
                'dumbbell_gradient_descent': calib_params.dumbbell_gradient_descent,
                'dumbbell_penalty_weight': calib_params.dumbbell_penalty_weight,
                'dumbbell_step': calib_params.dumbbell_step,
                'dumbbell_niter': calib_params.dumbbell_niter
            })

            # Save all changes to the YAML file
            pm.to_yaml(pm.path / 'parameters.yaml')


class TrackHandler(Handler):
    def closed(self, info, is_ok):
        if is_ok:
            track_params = info.object
            pm = track_params.param_manager
            pm.parameters['track'].update({
                'dvxmin': track_params.dvxmin, 'dvxmax': track_params.dvxmax,
                'dvymin': track_params.dvymin, 'dvymax': track_params.dvymax,
                'dvzmin': track_params.dvzmin, 'dvzmax': track_params.dvzmax,
                'angle': track_params.angle, 'dacc': track_params.dacc,
                'flagNewParticles': track_params.flagNewParticles
            })
            pm.to_yaml(pm.path / 'parameters.yaml')


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

    def __init__(self, param_manager: ParameterManager):
        super(Tracking_Params, self).__init__()
        self.param_manager = param_manager
        tracking_params = self.param_manager.parameters.get('track')
        if tracking_params:
            self.dvxmin = tracking_params.get('dvxmin', DEFAULT_FLOAT)
            self.dvxmax = tracking_params.get('dvxmax', DEFAULT_FLOAT)
            self.dvymin = tracking_params.get('dvymin', DEFAULT_FLOAT)
            self.dvymax = tracking_params.get('dvymax', DEFAULT_FLOAT)
            self.dvzmin = tracking_params.get('dvzmin', DEFAULT_FLOAT)
            self.dvzmax = tracking_params.get('dvzmax', DEFAULT_FLOAT)
            self.angle = tracking_params.get('angle', DEFAULT_FLOAT)
            self.dacc = tracking_params.get('dacc', DEFAULT_FLOAT)
            self.flagNewParticles = bool(tracking_params.get('flagNewParticles', True))

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
    Splitter = Bool(False, label="Split images into 4?")

    tiff_flag = Bool()
    imx = Int(DEFAULT_INT)
    imy = Int(DEFAULT_INT)
    pix_x = Float(DEFAULT_FLOAT)
    pix_y = Float(DEFAULT_FLOAT)
    chfield = Int(DEFAULT_INT)
    img_cal_name = []

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

    Refr_Air = Float(1.0, label="Air:")
    Refr_Glass = Float(1.33, label="Glass:")
    Refr_Water = Float(1.46, label="Water:")
    Thick_Glass = Float(1.0, label="Thickness of glass:")

    # New panel 2: ImageProcessing
    HighPass = Bool(True, label="High pass filter")
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
    Min_Weight_corr = Float(DEFAULT_FLOAT, label="min for weighted correlation")
    Tol_Band = Float(DEFAULT_FLOAT, lable="Tolerance of epipolar band [mm]")

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
        if self.pair_Flag:
            self.all_enable_flag = False
        else:
            self.all_enable_flag = True

    def _Accept_OnlyAllCameras_fired(self):
        if self.Accept_OnlyAllCameras:
            self.pair_enable_flag = False
        else:
            self.pair_enable_flag = True

    def _reload(self, params):
        ptv_params = params.get('ptv', {})
        self.Name_1_Image, self.Name_2_Image, self.Name_3_Image, self.Name_4_Image = ptv_params.get('img_name', [''] * 4)
        self.Cali_1_Image, self.Cali_2_Image, self.Cali_3_Image, self.Cali_4_Image = ptv_params.get('img_cal', [''] * 4)
        self.Refr_Air = ptv_params.get('mmp_n1')
        self.Refr_Glass = ptv_params.get('mmp_n2')
        self.Refr_Water = ptv_params.get('mmp_n3')
        self.Thick_Glass = ptv_params.get('mmp_d')
        self.Accept_OnlyAllCameras = bool(ptv_params.get('allcam_flag', False))
        self.Num_Cam = ptv_params.get('n_img')
        self.HighPass = bool(ptv_params.get('hp_flag', False))
        self.tiff_flag = bool(ptv_params.get('tiff_flag', False))
        self.imx = ptv_params.get('imx')
        self.imy = ptv_params.get('imy')
        self.pix_x = ptv_params.get('pix_x')
        self.pix_y = ptv_params.get('pix_y')
        self.chfield = ptv_params.get('chfield')
        self.Splitter = bool(ptv_params.get('splitter', False))

        cal_ori_params = params.get('cal_ori', {})
        self.pair_Flag = bool(cal_ori_params.get('pair_flag', False))
        self.img_cal_name = cal_ori_params.get('img_cal_name')
        self.img_ori = cal_ori_params.get('img_ori')
        self.fixp_name = cal_ori_params.get('fixp_name')

        targ_rec_params = params.get('targ_rec', {})
        self.Gray_Tresh_1, self.Gray_Tresh_2, self.Gray_Tresh_3, self.Gray_Tresh_4 = targ_rec_params.get('gvthres', [0]*4)
        self.Min_Npix = targ_rec_params.get('nnmin')
        self.Max_Npix = targ_rec_params.get('nnmax')
        self.Min_Npix_x = targ_rec_params.get('nxmin')
        self.Max_Npix_x = targ_rec_params.get('nxmax')
        self.Min_Npix_y = targ_rec_params.get('nymin')
        self.Max_Npix_y = targ_rec_params.get('nymax')
        self.Sum_Grey = targ_rec_params.get('sumg_min')
        self.Tol_Disc = targ_rec_params.get('disco')
        self.Size_Cross = targ_rec_params.get('cr_sz')

        pft_version_params = params.get('pft_version', {})
        self.Existing_Target = bool(pft_version_params.get('Existing_Target', False))

        sequence_params = params.get('sequence', {})
        self.Basename_1_Seq, self.Basename_2_Seq, self.Basename_3_Seq, self.Basename_4_Seq = sequence_params.get('base_name', [''] * 4)
        self.Seq_First = sequence_params.get('first')
        self.Seq_Last = sequence_params.get('last')

        criteria_params = params.get('criteria', {})
        self.Xmin, self.Xmax = criteria_params.get('X_lay', [0,0])
        self.Zmin1, self.Zmin2 = criteria_params.get('Zmin_lay', [0,0])
        self.Zmax1, self.Zmax2 = criteria_params.get('Zmax_lay', [0,0])
        self.Min_Corr_nx = criteria_params.get('cnx')
        self.Min_Corr_ny = criteria_params.get('cny')
        self.Min_Corr_npix = criteria_params.get('cn')
        self.Sum_gv = criteria_params.get('csumg')
        self.Min_Weight_corr = criteria_params.get('corrmin')
        self.Tol_Band = criteria_params.get('eps0')

        masking_params = params.get('masking', {})
        self.Subtr_Mask = masking_params.get('mask_flag', False)
        self.Base_Name_Mask = masking_params.get('mask_base_name', '')

    def __init__(self, param_manager: ParameterManager):
        HasTraits.__init__(self)
        self.param_manager = param_manager
        self._reload(self.param_manager.parameters)


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
    _cal_splitter = Bool(False, label="Split calibration image into 4?")

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

    point_number_of_orientation = Int(DEFAULT_INT, label="Point number of orientation")
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

    dumbbell_eps = Float(DEFAULT_FLOAT, label="dumbbell epsilon")
    dumbbell_scale = Float(DEFAULT_FLOAT, label="dumbbell scale")
    dumbbell_gradient_descent = Float(
        DEFAULT_FLOAT, label="dumbbell gradient descent factor"
    )
    dumbbell_penalty_weight = Float(DEFAULT_FLOAT, label="weight for dumbbell penalty")
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

    def _reload(self, params):
        ptv_params = params.get('ptv', {})
        self.h_image_size = ptv_params.get('imx')
        self.v_image_size = ptv_params.get('imy')
        self.h_pixel_size = ptv_params.get('pix_x')
        self.v_pixel_size = ptv_params.get('pix_y')
        self.img_cal = ptv_params.get('img_cal')
        if ptv_params.get('allcam_flag', False):
            self.pair_enable_flag = False
        else:
            self.pair_enable_flag = True

        self.n_img = ptv_params.get('n_img')
        self.img_name = ptv_params.get('img_name')
        self.hp_flag = bool(ptv_params.get('hp_flag', False))
        self.allcam_flag = bool(ptv_params.get('allcam_flag', False))
        self.mmp_n1 = ptv_params.get('mmp_n1')
        self.mmp_n2 = ptv_params.get('mmp_n2')
        self.mmp_n3 = ptv_params.get('mmp_n3')
        self.mmp_d = ptv_params.get('mmp_d')

        cal_ori_params = params.get('cal_ori', {})
        self.cam_1, self.cam_2, self.cam_3, self.cam_4 = cal_ori_params.get('img_cal_name', [''] * 4)
        self.ori_cam_1, self.ori_cam_2, self.ori_cam_3, self.ori_cam_4 = cal_ori_params.get('img_ori', [''] * 4)
        self.tiff_head = bool(cal_ori_params.get('tiff_flag', False))
        self.pair_head = bool(cal_ori_params.get('pair_flag', False))
        self.fixp_name = cal_ori_params.get('fixp_name')
        self._cal_splitter = bool(cal_ori_params.get('cal_splitter', False))
        chfield = cal_ori_params.get('chfield')
        if chfield == 0:
            self.chfield = "Frame"
        elif chfield == 1:
            self.chfield = "Field odd"
        else:
            self.chfield = "Field even"

        detect_plate_params = params.get('detect_plate', {})
        self.grey_value_treshold_1 = detect_plate_params.get('gvth_1')
        self.grey_value_treshold_2 = detect_plate_params.get('gvth_2')
        self.grey_value_treshold_3 = detect_plate_params.get('gvth_3')
        self.grey_value_treshold_4 = detect_plate_params.get('gvth_4')
        self.tolerable_discontinuity = detect_plate_params.get('tol_dis')
        self.min_npix = detect_plate_params.get('min_npix')
        self.max_npix = detect_plate_params.get('max_npix')
        self.min_npix_x = detect_plate_params.get('min_npix_x')
        self.max_npix_x = detect_plate_params.get('max_npix_x')
        self.min_npix_y = detect_plate_params.get('min_npix_y')
        self.max_npix_y = detect_plate_params.get('max_npix_y')
        self.sum_of_grey = detect_plate_params.get('sum_grey')
        self.size_of_crosses = detect_plate_params.get('size_cross')

        man_ori_params = params.get('man_ori', {})
        nr = man_ori_params.get('nr', [])
        for i in range(self.n_img):
            for j in range(4):
                val = nr[i * 4 + j] if i * 4 + j < len(nr) else 0
                setattr(self, f"img_{i + 1}_p{j + 1}", val)

        examine_params = params.get('examine', {})
        self.Examine_Flag = examine_params.get('Examine_Flag', False)
        self.Combine_Flag = examine_params.get('Combine_Flag', False)

        orient_params = params.get('orient', {})
        self.point_number_of_orientation = orient_params.get('pnfo')
        self.cc = bool(orient_params.get('cc', False))
        self.xh = bool(orient_params.get('xh', False))
        self.yh = bool(orient_params.get('yh', False))
        self.k1 = bool(orient_params.get('k1', False))
        self.k2 = bool(orient_params.get('k2', False))
        self.k3 = bool(orient_params.get('k3', False))
        self.p1 = bool(orient_params.get('p1', False))
        self.p2 = bool(orient_params.get('p2', False))
        self.scale = bool(orient_params.get('scale', False))
        self.shear = bool(orient_params.get('shear', False))
        self.interf = bool(orient_params.get('interf', False))

        dumbbell_params = params.get('dumbbell', {})
        self.dumbbell_eps = dumbbell_params.get('dumbbell_eps')
        self.dumbbell_scale = dumbbell_params.get('dumbbell_scale')
        self.dumbbell_gradient_descent = dumbbell_params.get('dumbbell_gradient_descent')
        self.dumbbell_penalty_weight = dumbbell_params.get('dumbbell_penalty_weight')
        self.dumbbell_step = dumbbell_params.get('dumbbell_step')
        self.dumbbell_niter = dumbbell_params.get('dumbbell_niter')

        shaking_params = params.get('shaking', {})
        self.shaking_first_frame = shaking_params.get('shaking_first_frame')
        self.shaking_last_frame = shaking_params.get('shaking_last_frame')
        self.shaking_max_num_points = shaking_params.get('shaking_max_num_points')
        self.shaking_max_num_frames = shaking_params.get('shaking_max_num_frames')

    def __init__(self, param_manager: ParameterManager):
        HasTraits.__init__(self)
        self.param_manager = param_manager
        self._reload(self.param_manager.parameters)


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
        if isinstance(paramset, type(1)):
            return paramset
        else:
            return self.paramsets.index(paramset)

    def addParamset(self, name: str, par_path: Path):
        pm = ParameterManager()
        yaml_path = par_path / 'parameters.yaml'
        if yaml_path.exists():
            pm.from_yaml(yaml_path)
        else:
            pm.from_directory(par_path)
            pm.to_yaml(yaml_path)

        self.paramsets.append(
            Paramset(
                name=name,
                par_path=par_path,
                m_params=Main_Params(param_manager=pm),
                c_params=Calib_Params(param_manager=pm),
                t_params=Tracking_Params(param_manager=pm),
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
        default_parameters_path = Path('parameters').resolve()
        if not default_parameters_path.exists():
            default_parameters_path.mkdir()
        
        src_yaml = self.active_params.par_path / 'parameters.yaml'
        dest_yaml = default_parameters_path / 'parameters.yaml'
        
        if src_yaml.exists():
            shutil.copy(src_yaml, dest_yaml)
            print(f"Copied {src_yaml} to {dest_yaml}")

    def populate_runs(self, exp_path: Path):
        self.paramsets = []

        dir_contents = [f for f in exp_path.iterdir() if (exp_path / f).is_dir()]

        dir_contents = [
            f for f in dir_contents if str(f.stem).startswith('parameters')
        ]

        if len(dir_contents) == 1 and str(dir_contents[0].stem) == 'parameters':
            exp_name = "Run1"
            new_name = str(dir_contents[0]) + exp_name
            new_path = Path(new_name).resolve()
            new_path.mkdir(exist_ok=True)
            
            pm = ParameterManager()
            pm.from_directory(dir_contents[0])
            pm.to_yaml(new_path / 'parameters.yaml')
            
            dir_contents.append(new_path)

        for dir_item in dir_contents:
            if str(dir_item.stem) != 'parameters':
                exp_name = str(dir_item.stem).rsplit("parameters", maxsplit=1)[-1]

                print(f"Experiment name is: {exp_name}")
                print(" adding Parameter set\n")
                self.addParamset(exp_name, dir_item)

        if not self.changed_active_params:
            if self.nParamsets() > 0:
                self.setActive(0)