from __future__ import print_function
from __future__ import absolute_import

from pathlib import Path
import shutil
from tqdm import tqdm
from traits.api import HasTraits, Str, Float, Int, List, Bool

import yaml

# Temporary path for parameters (active run will be copied here)
par_dir_prefix = str("parameters")
max_cam = int(4)


def g(f):
    """ Returns a line without white spaces """
    return f.readline().strip()


# Base class for all parameters classes


class Parameters(HasTraits):
    # default path of the directory of the param files
    default_path = Path(par_dir_prefix)

    def __init__(self, path: Path=default_path):
        HasTraits.__init__(self)
        if isinstance(path, str):
            path = Path(path)
            
        self.path = path.resolve()
        self.exp_path = self.path.parent 

    # returns the name of the specific params file
    def filename(self):
        raise NotImplementedError()

    # returns the path to the specific params file
    def filepath(self):
        return self.path.joinpath(self.filename())

    # sets all variables of the param file (no actual writing to disk)
    def set(self, *vars):
        raise NotImplementedError()

    # reads a param file and stores it in the object
    def read(self):
        raise NotImplementedError()

    # writes values from the object to a file
    def write(self):
        raise NotImplementedError()

    def to_yaml(self):
        """Creates YAML file"""
        yaml_file = self.filepath().replace(".par", ".yaml")
        with open(yaml_file, "w") as outfile:
            yaml.dump(self.__dict__, outfile, default_flow_style=False)

    def from_yaml(self):
        yaml_file = self.filepath().replace(".par", ".yaml")
        with open(yaml_file) as f:
            yaml_args = yaml.load(f)

        for k, v in yaml_args.items():
            if isinstance(v, list) and len(v) > 1:  # multi line
                setattr(self, k, [])
                tmp = [item for item in v]
                setattr(self, k, tmp)

            setattr(self, k, v)

    def istherefile(self, filename):
        """checks if the filename exists in the experimental path"""
        if not self.exp_path.joinpath(filename).is_file():
            warning(f"{filename} not found")


# Print detailed error to the console and show the user a friendly error window
def error(owner, msg):
    print(f"Exception caught, message: {msg}")


def warning(msg):
    print(f"Warning message: {msg}")


# Reads a parameters directory and returns a dictionary with all parameter
# objects
def readParamsDir(par_path):
    # get n_img from ptv.par
    ptvParams = PtvParams(path=par_path)
    ptvParams.read()
    n_img = ptvParams.n_img
    n_pts = Int(4)

    ret = {
        CalOriParams: CalOriParams(n_img, path=par_path),
        SequenceParams: SequenceParams(n_img, path=par_path),
        CriteriaParams: CriteriaParams(path=par_path),
        TargRecParams: TargRecParams(n_img, path=par_path),
        ManOriParams: ManOriParams(n_img, n_pts, path=par_path),
        DetectPlateParams: DetectPlateParams(path=par_path),
        OrientParams: OrientParams(path=par_path),
        TrackingParams: TrackingParams(path=par_path),
        PftVersionParams: PftVersionParams(path=par_path),
        ExamineParams: ExamineParams(path=par_path),
        DumbbellParams: DumbbellParams(path=par_path),
        ShakingParams: ShakingParams(path=par_path),
    }

    for parType in list(ret.keys()):
        if parType == PtvParams:
            continue
        parObj = ret[parType]
        parObj.read()

    return ret


def copy_params_dir(src: Path, dest: Path):
    """ Copying all parameter files from /src folder to /dest 
        including .dat, .par and .yaml files
    """
    ext_set = ("*.dat", "*.par", "*.yaml")
    files = []
    for ext in ext_set:
        files.extend(src.glob(ext))
        
    # print(f'List of parameter files in {src} is \n {files} \n')    
    # print(f'Destination folder is {dest.resolve()}')
    # files = [f for f in src.iterdir() if str(f.parts[-1]).endswith(ext_set)]    

    if not dest.is_dir():
        print(f"Destination folder does not exist, creating it")
        dest.mkdir(parents=True, exist_ok=True)

    print(f"Copying now file by file from {src} to {dest}: \n")

    for f in tqdm(files):
        # print(f"From {f} to {dest / f.name} ")
        shutil.copyfile(
            f,
            dest / f.name,
        )

    print(f"Successfully \n")


# Specific parameter classes #######


class PtvParams(Parameters):
    """ptv.par
    ptv.par:        main parameter file
    4       number of cameras
    cam3.100        image of first camera
    kal1    calibration data of first camera
    cam0.100        image of second camera
    kal3    calibration data of second camera
    cam1.100        image of third camera
    kal4    calibration data of third camera
    cam2.100        image of fourth camera
    kal5    calibration data of fourth camera
    1       flag for highpass filtering, use (1) or not use (0)
    0               flag for using particles identified ONLY in
        all cameras (e.g. only quadruplets for 4 cameras)
    1       flag for TIFF header (1) or raw data (0)
    720     image width in pixel
    576     image height in pixel
    0.009   pixel size horizontal [mm]
    0.0084  pixel size vertical [mm]
    0       flag for frame, odd or even fields
    1.0     refractive index air [no unit]
    1.5     refractive index glass [no unit]
    1.0     refractive index water [no unit]
    9.4     thickness of glass [mm]
    """

    #     n_img = Int
    #     img_name = List
    #     img_cal = List
    #     hp_flag = Bool
    #     allcam_flag = Bool
    #     tiff_flag = Bool
    #     imx = Int
    #     imy = Int
    #     pix_x = Float
    #     pix_y = Float
    #     chfield = Int
    #     mmp_n1 = Float
    #     mmp_n2 = Float
    #     mmp_n3 = Float
    #     mmp_d = Float

    def __init__(
        self,
        n_img=Int,
        img_name=List,
        img_cal=List,
        hp_flag=Bool,
        allcam_flag=Bool,
        tiff_flag=Bool,
        imx=Int,
        imy=Int,
        pix_x=Float,
        pix_y=Float,
        chfield=Int,
        mmp_n1=Float,
        mmp_n2=Float,
        mmp_n3=Float,
        mmp_d=Float,
        path=Parameters.default_path,
    ):
        Parameters.__init__(self, path)
        (
            self.n_img,
            self.img_name,
            self.img_cal,
            self.hp_flag,
            self.allcam_flag,
            self.tiff_flag,
            self.imx,
            self.imy,
            self.pix_x,
            self.pix_y,
            self.chfield,
            self.mmp_n1,
            self.mmp_n2,
            self.mmp_n3,
            self.mmp_d,
        ) = (
            n_img,
            img_name,
            img_cal,
            hp_flag,
            allcam_flag,
            tiff_flag,
            imx,
            imy,
            pix_x,
            pix_y,
            chfield,
            mmp_n1,
            mmp_n2,
            mmp_n3,
            mmp_d,
        )

    def filename(self):
        return "ptv.par"

    def read(self):
        if not self.filepath().exists():
            warning(f"{self.filepath()} does not exist ")
        try:
            with open(self.filepath(), "r", encoding="utf8") as f:
                self.n_img = int(g(f))

                self.img_name = [None] * max_cam
                self.img_cal = [None] * max_cam
                for i in range(self.n_img):
                    # for i in range(max_cam):
                    self.img_name[i] = g(f)
                    self.img_cal[i] = g(f)

                self.hp_flag = int(g(f)) != 0
                self.allcam_flag = int(g(f)) != 0
                self.tiff_flag = int(g(f)) != 0
                self.imx = int(g(f))
                self.imy = int(g(f))
                self.pix_x = float(g(f))
                self.pix_y = float(g(f))
                self.chfield = int(g(f))
                self.mmp_n1 = float(g(f))
                self.mmp_n2 = float(g(f))
                self.mmp_n3 = float(g(f))
                self.mmp_d = float(g(f))

        except IOError:
            error(None, "%s not found" % self.filepath())

        # test existence and issue warnings
        for i in range(self.n_img):
            self.istherefile(self.img_name[i])
            self.istherefile(self.img_cal[i])

    def write(self):
        try:
            with open(self.filepath(), "w") as f:
                f.write("%d\n" % self.n_img)
                for i in range(self.n_img):
                    # for i in range(max_cam):
                    f.write("%s\n" % self.img_name[i])
                    f.write("%s\n" % self.img_cal[i])

                f.write("%d\n" % self.hp_flag)
                f.write("%d\n" % self.allcam_flag)
                f.write("%d\n" % self.tiff_flag)
                f.write("%d\n" % self.imx)
                f.write("%d\n" % self.imy)
                f.write("%g\n" % self.pix_x)
                f.write("%g\n" % self.pix_y)
                f.write("%d\n" % self.chfield)
                f.write("%g\n" % self.mmp_n1)
                f.write("%g\n" % self.mmp_n2)
                f.write("%g\n" % self.mmp_n3)
                f.write("%g\n" % self.mmp_d)
                return True
        except IOError:
            error(None, f"Error writing {self.filepath()}.")
            return False


class CalOriParams(Parameters):
    """ calibration parameters:
    cal_ori.par:    calibration plate, images, orientation files
    ptv/ssc_cal.c3d control point file (point number, X, Y, Z in [mm], ASCII
    kal1    calibration
    kal1.ori    orientation
    kal3    calibration
    kal3.ori    orientation
    kal4    calibration
    kal4.ori    orientation
    kal5    calibration
    kal5.ori    orientation
    1   flag for TIFF header (1) or raw data (0)
    0   flag for pairs?
    0   flag for frame (0), odd (1) or even fields (2)
    """

    #     fixp_name = Str
    #     img_cal_name = List
    #     img_ori = List
    #     tiff_flag = Bool
    #     pair_flag = Bool
    #     chfield = Int

    def __init__(
        self,
        n_img=Int,
        fixp_name=Str,
        img_cal_name=List,
        img_ori=List,
        tiff_flag=Bool,
        pair_flag=Bool,
        chfield=Int,
        path=Parameters.default_path,
    ):
        Parameters.__init__(self, path)

        (
            self.n_img,
            self.fixp_name,
            self.img_cal_name,
            self.img_ori,
            self.tiff_flag,
            self.pair_flag,
            self.chfield,
        ) = (
            n_img,
            fixp_name,
            img_cal_name,
            img_ori,
            tiff_flag,
            pair_flag,
            chfield,
        )

    def filename(self):
        return "cal_ori.par"

    def read(self):
        try:
            with open(self.filepath(), "r") as f:

                self.fixp_name = g(f)
                self.istherefile(self.fixp_name)

                self.img_cal_name = []
                self.img_ori = []
                for i in range(self.n_img):
                    # for i in range(max_cam):
                    self.img_cal_name.append(g(f))
                    self.img_ori.append(g(f))

                self.tiff_flag = int(g(f)) != 0  # <-- overwrites the above
                self.pair_flag = int(g(f)) != 0
                self.chfield = int(g(f))

        except BaseException:
            error(None, "%s not found" % self.filepath())

        # test if files are present, issue warnings
        for i in range(self.n_img):
            self.istherefile(self.img_cal_name[i])
            self.istherefile(self.img_ori[i])

    def write(self):
        try:
            with open(self.filepath(), "w") as f:

                f.write("%s\n" % self.fixp_name)
                for i in range(self.n_img):
                    # for i in range(max_cam):
                    f.write("%s\n" % self.img_cal_name[i])
                    f.write("%s\n" % self.img_ori[i])

                f.write("%d\n" % self.tiff_flag)
                f.write("%d\n" % self.pair_flag)
                f.write("%d\n" % self.chfield)

            return True
        except BaseException:
            error(None, "Error writing %s." % self.filepath())
            return False


class SequenceParams(Parameters):
    """
    sequence.par: sequence parameters
    cam0. basename for 1.sequence
    cam1. basename for 2. sequence
    cam2. basename for 3. sequence
    cam3. basename for 4. sequence
    100  first image of sequence
    119  last image of sequence
    """

    #     base_name = List
    #     first = Int
    #     last = Int

    def __init__(
        self,
        n_img=Int,
        base_name=List,
        first=Int,
        last=Int,
        path=Parameters.default_path,
    ):
        Parameters.__init__(self, path)
        (self.n_img, self.base_name, self.first, self.last) = (
            n_img,
            base_name,
            first,
            last,
        )

    def filename(self):
        return "sequence.par"

    def read(self):
        try:
            with open(self.filepath(), "r") as f:
                self.base_name = []
                for i in range(self.n_img):
                    # for i in range(max_cam):
                    self.base_name.append(g(f))

                self.first = int(g(f))
                self.last = int(g(f))
        except BaseException:
            error(None, "error reading %s" % self.filepath())

    def write(self):
        try:
            with open(self.filepath(), "w") as f:
                for i in range(self.n_img):
                    # for i in range(max_cam):
                    f.write("%s\n" % self.base_name[i])

                f.write("%d\n" % self.first)
                f.write("%d\n" % self.last)

            return True
        except BaseException:
            error(None, "Error writing %s." % self.filepath())
            return False


class CriteriaParams(Parameters):
    """
    criteria.par:   object volume and correspondence parameters
    0.0     illuminated layer data, xmin [mm]
    -10.0   illuminated layer data, zmin [mm]
    0.0     illuminated layer data, zmax [mm]
    10.0    illuminated layer data, xmax [mm]
    -10.0   illuminated layer data, zmin [mm]
    0.0     illuminated layer data, zmax [mm]
    0.02    min corr for ratio nx
    0.02    min corr for ratio ny
    0.02    min corr for ratio npix
    0.02    sum of gv
    33      min for weighted correlation
    0.02    tolerance to epipolar line [mm]
    """

    #     X_lay = List
    #     Zmin_lay = List
    #     Zmax_lay = List
    #     cnx = Float
    #     cny = Float
    #     cn = Float
    #     csumg = Float
    #     corrmin = Float
    #     eps0 = Float

    def __init__(
        self,
        X_lay=List,
        Zmin_lay=List,
        Zmax_lay=List,
        cnx=Float,
        cny=Float,
        cn=Float,
        csumg=Float,
        corrmin=Float,
        eps0=Float,
        path=Parameters.default_path,
    ):
        Parameters.__init__(self, path)
        self.set(X_lay, Zmin_lay, Zmax_lay, cnx, cny, cn, csumg, corrmin, eps0)

    def set(
        self,
        X_lay=List,
        Zmin_lay=List,
        Zmax_lay=List,
        cnx=Float,
        cny=Float,
        cn=Float,
        csumg=Float,
        corrmin=Float,
        eps0=Float,
    ):
        (
            self.X_lay,
            self.Zmin_lay,
            self.Zmax_lay,
            self.cnx,
            self.cny,
            self.cn,
            self.csumg,
            self.corrmin,
            self.eps0,
        ) = (X_lay, Zmin_lay, Zmax_lay, cnx, cny, cn, csumg, corrmin, eps0)

    def filename(self):
        return "criteria.par"

    def read(self):
        try:
            f = open(self.filepath(), "r")

            self.X_lay = []
            self.Zmin_lay = []
            self.Zmax_lay = []
            self.X_lay.append(int(g(f)))
            self.Zmin_lay.append(int(g(f)))
            self.Zmax_lay.append(int(g(f)))
            self.X_lay.append(int(g(f)))
            self.Zmin_lay.append(int(g(f)))
            self.Zmax_lay.append(int(g(f)))
            self.cnx = float(g(f))
            self.cny = float(g(f))
            self.cn = float(g(f))
            self.csumg = float(g(f))
            self.corrmin = float(g(f))
            self.eps0 = float(g(f))

            f.close()
        except BaseException:
            error(None, "%s not found" % self.filepath())

    def write(self):
        try:
            f = open(self.filepath(), "w")

            f.write("%d\n" % self.X_lay[0])
            f.write("%d\n" % self.Zmin_lay[0])
            f.write("%d\n" % self.Zmax_lay[0])
            f.write("%d\n" % self.X_lay[1])
            f.write("%d\n" % self.Zmin_lay[1])
            f.write("%d\n" % self.Zmax_lay[1])
            f.write("%g\n" % self.cnx)
            f.write("%g\n" % self.cny)
            f.write("%g\n" % self.cn)
            f.write("%g\n" % self.csumg)
            f.write("%g\n" % self.corrmin)
            f.write("%g\n" % self.eps0)

            f.close()
            return True
        except BaseException:
            error(None, "Error writing %s." % self.filepath())
            return False


class TargRecParams(Parameters):
    """
    targ_rec.par:   parameters for particle detection
    12      grey value threshold 1. image
    12      grey value threshold 2. image
    12      grey value threshold 3. image
    12      grey value threshold 4. image
    50      tolerable discontinuity in grey values
    25      min npix, area covered by particle
    400     max npix, area covered by particle
    5       min npix in x, dimension in pixel
    20      max npix in x, dimension in pixel
    5       min npix in y, dimension in pixel
    20      max npix in y, dimension in pixel
    100     sum of grey value
    1       size of crosses
    """

    #     gvthres = List
    #     disco = Int
    #     nnmin = Int
    #     nnmax = Int
    #     nxmin = Int
    #     nxmax = Int
    #     nymin = Int
    #     nymax = Int
    #     sumg_min = Int
    #     cr_sz = Int

    def __init__(
        self,
        n_img=Int,
        gvthres=List,
        disco=Int,
        nnmin=Int,
        nnmax=Int,
        nxmin=Int,
        nxmax=Int,
        nymin=Int,
        nymax=Int,
        sumg_min=Int,
        cr_sz=Int,
        path=Parameters.default_path,
    ):
        Parameters.__init__(self, path)

        (
            self.n_img,
            self.gvthres,
            self.disco,
            self.nnmin,
            self.nnmax,
            self.nxmin,
            self.nxmax,
            self.nymin,
            self.nymax,
            self.sumg_min,
            self.cr_sz,
        ) = (
            n_img,
            gvthres,
            disco,
            nnmin,
            nnmax,
            nxmin,
            nxmax,
            nymin,
            nymax,
            sumg_min,
            cr_sz,
        )

    def filename(self):
        return "targ_rec.par"

    def read(self):
        try:
            with open(self.filepath(), "r") as f:

                self.gvthres = [0] * max_cam
                # for i in range(self.n_img):
                for i in range(max_cam):
                    self.gvthres[i] = int(g(f))

                self.disco = int(g(f))
                self.nnmin = int(g(f))
                self.nnmax = int(g(f))
                self.nxmin = int(g(f))
                self.nxmax = int(g(f))
                self.nymin = int(g(f))
                self.nymax = int(g(f))
                self.sumg_min = int(g(f))
                self.cr_sz = int(g(f))

        except BaseException:
            error(None, "Error reading from %s" % self.filepath())

    def write(self):
        try:
            f = open(self.filepath(), "w")
            #            for i in range(self.n_img):
            for i in range(max_cam):
                f.write("%d\n" % self.gvthres[i])

            f.write("%d\n" % self.disco)
            f.write("%d\n" % self.nnmin)
            f.write("%d\n" % self.nnmax)
            f.write("%d\n" % self.nxmin)
            f.write("%d\n" % self.nxmax)
            f.write("%d\n" % self.nymin)
            f.write("%d\n" % self.nymax)
            f.write("%d\n" % self.sumg_min)
            f.write("%d\n" % self.cr_sz)

            f.close()
            return True
        except BaseException:
            error(None, "Error writing %s." % self.filepath())
            return False


class ManOriParams(Parameters):
    """
    man_ori.par:    point number for manual pre-orientation
    28      image 1 p1 on target plate (reference body)
    48      image 1 p2
    42      image 1 p3
    22      image 1 p4
    28      image 2 p1
    48      image 2 p2
    42      image 2 p3
    23      image 2 p4
    28      image 3 p1
    48      image 3 p2
    42      image 3 p3
    22      image 3 p4
    28      image 4 p1
    48      image 4 p2
    42      image 4 p3
    22      image 4 p4
    """

    #     nr = List(List(Int))

    def __init__(self, n_img=Int, nr=List, path=Parameters.default_path):
        Parameters.__init__(self, path)
        self.n_img = int(n_img)
        self.nr = nr
        self.path = path

    def filename(self):
        return "man_ori.par"

    def read(self):
        try:
            with open(self.filepath(), "r") as f:
                for i in range(self.n_img):
                    for _ in range(4):  # always 4 points
                        self.nr.append(int(g(f)))
        except BaseException:
            error(None, "Error reading from %s" % self.filepath())

    def write(self):
        try:
            with open(self.filepath(), "w") as f:
                for i in range(self.n_img):
                    for j in range(4):  # always 4 points
                        f.write("%d\n" % self.nr[i][j])

            return True
        except BaseException:
            error(None, "Error writing %s." % self.filepath())
            return False


class DetectPlateParams(Parameters):
    """
    detect_plate.par: parameters for control point detection
    30 grey value threshold 1. calibration image
    30 grey value threshold 2. calibration image
    30 grey value threshold 3. calibration image
    30 grey value threshold 4. calibration image
    40 tolerable discontinuity in grey values
    25 min npix, area covered by particle
    400 max npix, area covered by particle
    5 min npix in x, dimension in pixel
    20 max npix in x, dimension in pixel
    5 min npix in y, dimension in pixel
    20 max npix in y, dimension in pixel
    100 sum of grey value
    3 size of crosses
    """

    #     gvth_1 = Int
    #     gvth_2 = Int
    #     gvth_3 = Int
    #     gvth_4 = Int
    #     tol_dis = Int
    #     min_npix = Int
    #     max_npix = Int
    #     min_npix_x = Int
    #     max_npix_x = Int
    #     min_npix_y = Int
    #     max_npix_y = Int
    #     sum_grey = Int
    #     size_cross = Int

    def __init__(
        self,
        gvth_1=Int,
        gvth_2=Int,
        gvth_3=Int,
        gvth_4=Int,
        tol_dis=Int,
        min_npix=Int,
        max_npix=Int,
        min_npix_x=Int,
        max_npix_x=Int,
        min_npix_y=Int,
        max_npix_y=Int,
        sum_grey=Int,
        size_cross=Int,
        path=Parameters.default_path,
    ):
        Parameters.__init__(self, path)
        self.set(
            gvth_1,
            gvth_2,
            gvth_3,
            gvth_4,
            tol_dis,
            min_npix,
            max_npix,
            min_npix_x,
            max_npix_x,
            min_npix_y,
            max_npix_y,
            sum_grey,
            size_cross,
        )

    def set(
        self,
        gvth_1=Int,
        gvth_2=Int,
        gvth_3=Int,
        gvth_4=Int,
        tol_dis=Int,
        min_npix=Int,
        max_npix=Int,
        min_npix_x=Int,
        max_npix_x=Int,
        min_npix_y=Int,
        max_npix_y=Int,
        sum_grey=Int,
        size_cross=Int,
    ):
        (
            self.gvth_1,
            self.gvth_2,
            self.gvth_3,
            self.gvth_4,
            self.tol_dis,
            self.min_npix,
            self.max_npix,
            self.min_npix_x,
            self.max_npix_x,
            self.min_npix_y,
            self.max_npix_y,
            self.sum_grey,
            self.size_cross,
        ) = (
            gvth_1,
            gvth_2,
            gvth_3,
            gvth_4,
            tol_dis,
            min_npix,
            max_npix,
            min_npix_x,
            max_npix_x,
            min_npix_y,
            max_npix_y,
            sum_grey,
            size_cross,
        )

    def filename(self):
        return "detect_plate.par"

    def read(self):
        try:
            f = open(self.filepath(), "r")

            self.gvth_1 = int(g(f))
            self.gvth_2 = int(g(f))
            self.gvth_3 = int(g(f))
            self.gvth_4 = int(g(f))
            self.tol_dis = int(g(f))
            self.min_npix = int(g(f))
            self.max_npix = int(g(f))
            self.min_npix_x = int(g(f))
            self.max_npix_x = int(g(f))
            self.min_npix_y = int(g(f))
            self.max_npix_y = int(g(f))
            self.sum_grey = int(g(f))
            self.size_cross = int(g(f))

            f.close()
        except BaseException:
            error(None, "Error reading from %s" % self.filepath())

    def write(self):
        try:
            f = open(self.filepath(), "w")

            f.write("%d\n" % int(self.gvth_1))
            f.write("%d\n" % int(self.gvth_2))
            f.write("%d\n" % int(self.gvth_3))
            f.write("%d\n" % int(self.gvth_4))
            f.write("%d\n" % int(self.tol_dis))
            f.write("%d\n" % int(self.min_npix))
            f.write("%d\n" % int(self.max_npix))
            f.write("%d\n" % int(self.min_npix_x))
            f.write("%d\n" % int(self.max_npix_x))
            f.write("%d\n" % int(self.min_npix_y))
            f.write("%d\n" % int(self.max_npix_y))
            f.write("%d\n" % int(self.sum_grey))
            f.write("%d\n" % int(self.size_cross))

            f.close()
            return True
        except BaseException:
            error(None, "Error writing %s." % self.filepath())
            return False


class OrientParams(Parameters):
    """
    orient.par: flags for camera parameter usage 1=use, 0=unused
    2 point number for orientation, in this case
    every second point on the reference body is
    used, 0 for using all points
    1 principle distance
    1 xp
    9. Conclusion and perspectives
    114
    1 yp
    1 k1
    1 k2
    1 k3
    0 p1
    0 p2
    1 scx
    1 she
    0 interf
    """

    #     pnfo = Int
    #     prin_dis = Int
    #     xp = Int
    #     yp = Int
    #     k1 = Int
    #     k2 = Int
    #     k3 = Int
    #     p1 = Int
    #     p2 = Int
    #     scx = Int
    #     she = Int
    #     interf = Int

    def __init__(
        self,
        pnfo=Int,
        cc=Int,
        xh=Int,
        yh=Int,
        k1=Int,
        k2=Int,
        k3=Int,
        p1=Int,
        p2=Int,
        scale=Int,
        shear=Int,
        interf=Int,
        path=Parameters.default_path,
    ):
        Parameters.__init__(self, path)
        self.set(pnfo, cc, xh, yh, k1, k2, k3, p1, p2, scale, shear, interf)

    def set(
        self,
        pnfo=Int,
        cc=Int,
        xh=Int,
        yh=Int,
        k1=Int,
        k2=Int,
        k3=Int,
        p1=Int,
        p2=Int,
        scale=Int,
        shear=Int,
        interf=Int,
    ):
        (
            self.pnfo,
            self.cc,
            self.xh,
            self.yh,
            self.k1,
            self.k2,
            self.k3,
            self.p1,
            self.p2,
            self.scale,
            self.shear,
            self.interf,
        ) = (pnfo, cc, xh, yh, k1, k2, k3, p1, p2, scale, shear, interf)

    def filename(self):
        return "orient.par"

    def read(self):
        try:
            with open(self.filepath(), "r") as f:

                self.pnfo = int(g(f))
                self.cc = int(g(f))
                self.xh = int(g(f))
                self.yh = int(g(f))
                self.k1 = int(g(f))
                self.k2 = int(g(f))
                self.k3 = int(g(f))
                self.p1 = int(g(f))
                self.p2 = int(g(f))
                self.scale = int(g(f))
                self.shear = int(g(f))
                self.interf = int(g(f))

        except BaseException:
            error(None, "Error reading %s" % self.filepath())

    def write(self):
        try:
            with open(self.filepath(), "w") as f:

                f.write("%d\n" % int(self.pnfo))
                f.write("%d\n" % int(self.cc))
                f.write("%d\n" % int(self.xh))
                f.write("%d\n" % int(self.yh))
                f.write("%d\n" % int(self.k1))
                f.write("%d\n" % int(self.k2))
                f.write("%d\n" % int(self.k3))
                f.write("%d\n" % int(self.p1))
                f.write("%d\n" % int(self.p2))
                f.write("%d\n" % int(self.scale))
                f.write("%d\n" % int(self.shear))
                f.write("%d\n" % int(self.interf))

            return True
        except BaseException:
            error(None, "Error writing %s." % self.filepath())
            return False


class TrackingParams(Parameters):
    #     dvxmin = Float
    #     dvxmax = Float
    #     dvymin = Float
    #     dvymax = Float
    #     dvzmin = Float
    #     dvzmax = Float
    #     angle = Float
    #     dacc = Float
    #     flagNewParticles = Bool

    def __init__(
        self,
        dvxmin=Float,
        dvxmax=Float,
        dvymin=Float,
        dvymax=Float,
        dvzmin=Float,
        dvzmax=Float,
        angle=Float,
        dacc=Float,
        flagNewParticles=Bool,
        path=Parameters.default_path,
    ):
        Parameters.__init__(self, path)
        self.set(
            dvxmin,
            dvxmax,
            dvymin,
            dvymax,
            dvzmin,
            dvzmax,
            angle,
            dacc,
            flagNewParticles,
        )

    def set(
        self,
        dvxmin=Float,
        dvxmax=Float,
        dvymin=Float,
        dvymax=Float,
        dvzmin=Float,
        dvzmax=Float,
        angle=Float,
        dacc=Float,
        flagNewParticles=Bool,
    ):
        (
            self.dvxmin,
            self.dvxmax,
            self.dvymin,
            self.dvymax,
            self.dvzmin,
            self.dvzmax,
            self.angle,
            self.dacc,
            self.flagNewParticles,
        ) = (
            dvxmin,
            dvxmax,
            dvymin,
            dvymax,
            dvzmin,
            dvzmax,
            angle,
            dacc,
            flagNewParticles,
        )

    def filename(self):
        return "track.par"

    def read(self):
        try:
            f = open(self.filepath(), "r")
            self.dvxmin = float(g(f))
            self.dvxmax = float(g(f))
            self.dvymin = float(g(f))
            self.dvymax = float(g(f))
            self.dvzmin = float(g(f))
            self.dvzmax = float(g(f))
            self.angle = float(g(f))
            self.dacc = float(g(f))
            self.flagNewParticles = int(g(f)) != 0
            f.close()
        except BaseException:
            error(None, "%s not found" % self.filepath())

    def write(self):
        try:
            f = open(self.filepath(), "w")
            f.write("%g\n" % self.dvxmin)
            f.write("%g\n" % self.dvxmax)
            f.write("%g\n" % self.dvymin)
            f.write("%g\n" % self.dvymax)
            f.write("%g\n" % self.dvzmin)
            f.write("%g\n" % self.dvzmax)
            f.write("%g\n" % self.angle)
            f.write("%g\n" % self.dacc)
            f.write("%d\n" % self.flagNewParticles)
            f.close()
            return True
        except BaseException:
            error(None, "Error writing %s." % self.filepath())
            return False


class PftVersionParams(Parameters):
    #     Existing_Target = Int

    def __init__(self, Existing_Target=Int, path=Parameters.default_path):
        Parameters.__init__(self, path)
        self.set(Existing_Target)

    def set(self, Existing_Target=Int):
        self.Existing_Target = Existing_Target

    def filename(self):
        return "pft_version.par"

    def read(self):
        try:
            f = open(self.filepath(), "r")

            self.Existing_Target = int(g(f))

            f.close()
        except BaseException:
            error(None, "%s not found" % self.filepath())

    def write(self):
        try:
            f = open(self.filepath(), "w")

            f.write("%d\n" % self.Existing_Target)

            f.close()
            return True
        except BaseException:
            error(None, "Error writing %s." % self.filepath())
            return False


class ExamineParams(Parameters):
    #     Examine_Flag = Bool
    #     Combine_Flag = Bool

    def __init__(
        self,
        Examine_Flag=Bool,
        Combine_Flag=Bool,
        path=Parameters.default_path,
    ):
        Parameters.__init__(self, path)
        self.set(Examine_Flag, Combine_Flag)

    def set(self, Examine_Flag=Bool, Combine_Flag=Bool):
        (self.Examine_Flag, self.Combine_Flag) = (Examine_Flag, Combine_Flag)

    def filename(self):
        return "examine.par"

    def read(self):
        if not self.filepath().exists():
            f = open(self.filepath(), "w")
            f.write("%d\n" % 0)
            f.write("%d\n" % 0)
            f.close()

        try:
            f = open(self.filepath(), "r")

            self.Examine_Flag = int(g(f)) != 0
            self.Combine_Flag = int(g(f)) != 0

            f.close()
        except BaseException:
            error(None, "%s not found" % self.filepath())

    def write(self):
        try:
            f = open(self.filepath(), "w")

            f.write("%d\n" % self.Examine_Flag)
            f.write("%d\n" % self.Combine_Flag)

            f.close()
            return True
        except BaseException:
            error(None, "Error writing %s." % self.filepath())
            return False


class DumbbellParams(Parameters):
    """
    dumbbell parameters
    5  eps (mm)
    46.5 dumbbell scale
    0.005 gradient descent factor
    1 weight for dumbbell penalty
    2 step size through sequence
    500 num iterations per click
    """

    #     dumbbell_eps = Float
    #     dumbbell_scale = Float
    #     dumbbell_gradient_descent = Float
    #     dumbbell_penalty_weight = Float
    #     dumbbell_step = Int
    #     dumbbell_niter = Int

    def __init__(
        self,
        dumbbell_eps=Float,
        dumbbell_scale=Float,
        dumbbell_gradient_descent=Float,
        dumbbell_penalty_weight=Float,
        dumbbell_step=Int,
        dumbbell_niter=Int,
        path=Parameters.default_path,
    ):
        Parameters.__init__(self, path)
        self.set(
            dumbbell_eps,
            dumbbell_scale,
            dumbbell_gradient_descent,
            dumbbell_penalty_weight,
            dumbbell_step,
            dumbbell_niter,
        )

    def set(
        self,
        dumbbell_eps=Float,
        dumbbell_scale=Float,
        dumbbell_gradient_descent=Float,
        dumbbell_penalty_weight=Float,
        dumbbell_step=Int,
        dumbbell_niter=Int,
    ):
        (
            self.dumbbell_eps,
            self.dumbbell_scale,
            self.dumbbell_gradient_descent,
            self.dumbbell_penalty_weight,
            self.dumbbell_step,
            self.dumbbell_niter,
        ) = (
            dumbbell_eps,
            dumbbell_scale,
            dumbbell_gradient_descent,
            dumbbell_penalty_weight,
            dumbbell_step,
            dumbbell_niter,
        )

    def filename(self):
        return "dumbbell.par"

    def read(self):
        if not self.filepath().exists():
            f = open(self.filepath(), "w")
            f.write("%f\n" % 0.0)
            f.write("%f\n" % 0.0)
            f.write("%f\n" % 0.0)
            f.write("%f\n" % 0.0)
            f.write("%d\n" % 0.0)
            f.write("%d\n" % 0.0)
            f.close()

        try:
            f = open(self.filepath(), "r")

            self.dumbbell_eps = float(g(f))
            self.dumbbell_scale = float(g(f))
            self.dumbbell_gradient_descent = float(g(f))
            self.dumbbell_penalty_weight = float(g(f))
            self.dumbbell_step = int(g(f))
            self.dumbbell_niter = int(g(f))

            f.close()
        except BaseException:
            error(None, "%s not found" % self.filepath())

    def write(self):
        try:
            f = open(self.filepath(), "w")

            f.write("%f\n" % self.dumbbell_eps)
            f.write("%f\n" % self.dumbbell_scale)
            f.write("%f\n" % self.dumbbell_gradient_descent)
            f.write("%f\n" % self.dumbbell_penalty_weight)
            f.write("%d\n" % self.dumbbell_step)
            f.write("%d\n" % self.dumbbell_niter)

            f.close()
            return True
        except BaseException:
            error(None, "Error writing %s." % self.filepath())
            return False


class ShakingParams(Parameters):
    """
    shaking parameters
    10000 - first frame
    10004 - last frame
    10 - max num points used per frame
    5 - max number of frames to track
    """

    #     shaking_first_frame = Int
    #     shaking_last_frame = Int
    #     shaking_max_num_points = Int
    #     shaking_max_num_frames = Int

    def __init__(
        self,
        shaking_first_frame=Int,
        shaking_last_frame=Int,
        shaking_max_num_points=Int,
        shaking_max_num_frames=Int,
        path=Parameters.default_path,
    ):
        Parameters.__init__(self, path)
        self.set(
            shaking_first_frame,
            shaking_last_frame,
            shaking_max_num_points,
            shaking_max_num_frames,
        )

    def set(
        self,
        shaking_first_frame=Int,
        shaking_last_frame=Int,
        shaking_max_num_points=Int,
        shaking_max_num_frames=Int,
    ):
        (
            self.shaking_first_frame,
            self.shaking_last_frame,
            self.shaking_max_num_points,
            self.shaking_max_num_frames,
        ) = (
            shaking_first_frame,
            shaking_last_frame,
            shaking_max_num_points,
            shaking_max_num_frames,
        )

    def filename(self):
        return "shaking.par"

    def read(self):
        if not self.filepath().exists():
            f = open(self.filepath(), "w")
            f.write("%f\n" % 0)
            f.write("%f\n" % 0)
            f.write("%f\n" % 0)
            f.write("%f\n" % 0)
            f.close()

        try:
            f = open(self.filepath(), "r")

            self.shaking_first_frame = int(g(f))
            self.shaking_last_frame = int(g(f))
            self.shaking_max_num_points = int(g(f))
            self.shaking_max_num_frames = int(g(f))

            f.close()
        except BaseException:
            error(None, "%s not found" % self.filepath())

    def write(self):
        try:
            f = open(self.filepath(), "w")

            f.write("%d\n" % self.shaking_first_frame)
            f.write("%d\n" % self.shaking_last_frame)
            f.write("%d\n" % self.shaking_max_num_points)
            f.write("%d\n" % self.shaking_max_num_frames)

            f.close()
            return True
        except BaseException:
            error(None, "Error writing %s." % self.filepath())
            return False


class MultiPlaneParams(Parameters):
    # m parameters
    """
    3 :    number of planes
    img/calib_a_cam  : name of the plane
    img/calib_b_cam  : name of the plane
    img/calib_c_cam  : name of the plane

    """

    def __init__(
        self,
        n_img=Int,
        n_planes=Int,
        plane_name=[],
        path=Parameters.default_path,
    ):
        Parameters.__init__(self, path)
        self.set(n_img, n_planes, plane_name)

    def set(self, n_img=Int, n_planes=Int, plane_name=[]):
        self.n_img = n_img
        (self.n_planes, self.plane_name) = (n_planes, plane_name)

    def filename(self):
        return "multi_planes.par"

    def read(self):
        try:
            with open(self.filepath(), "r") as f:
                self.n_planes = int(g(f))
                for i in range(self.n_planes):
                    self.plane_name.append(g(f))
                    # if not self.plane_name[i].is_file():
                    #     print(f"Plane {self.plane_name[i]} is missing.")

        except BaseException:
            error(None, "%s not found" % self.filepath())

    def write(self):
        try:
            with open(self.filepath(), "w") as f:

                f.write("%d\n" % self.n_planes)
                #            for i in range(self.n_img):
                for i in range(self.n_planes):
                    f.write("%s\n" % self.plane_name[i])

                return True
        except BaseException:
            error(None, "Error writing %s." % self.filepath())
            return False


class SortGridParams(Parameters):
    # m parameters
    """
    20 :    pixels, radius of search for a target point

    """

    def __init__(self, n_img=Int, radius=Int, path=Parameters.default_path):
        Parameters.__init__(self, path)
        self.set(n_img, radius)

    def set(self, n_img=Int, radius=Int):
        self.n_img = n_img
        self.radius = radius

    def filename(self):
        return "sortgrid.par"

    def read(self):
        try:
            with open(self.filepath(), "r") as f:
                self.radius = int(g(f))

        except BaseException:
            error(None, "%s not found" % self.filepath())

    def write(self):
        try:
            with open(self.filepath(), "w") as f:
                f.write("%d\n" % self.radius)

            return True
        except BaseException:
            error(None, "Error writing %s." % self.filepath())
            return False
