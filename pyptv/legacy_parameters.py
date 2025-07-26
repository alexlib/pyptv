from __future__ import print_function
from __future__ import absolute_import


from pathlib import Path
import shutil
from tqdm import tqdm
import collections.abc
from typing import Optional

# import yaml

# Temporary path for parameters (active run will be copied here)
par_dir_prefix = str("parameters")
max_cam = int(4)


def g(f):
    """Reads the next line from a file object and returns it stripped of leading and trailing whitespace."""
    line = f.readline()
    if line == "":
        # End of file reached
        return ""
    return line.strip()


# Base class for all parameters classes

class Parameters:
    # default path of the directory of the param files
    default_path = Path(par_dir_prefix)
    filename = 'tmp.par'

    def __init__(self, path=None):
        if path is None:
            path = self.default_path
        if isinstance(path, str):
            path = Path(path)
        self.path = path.resolve()
        self.exp_path = self.path.parent




    # returns the path to the specific params file
    def filepath(self):
        if not hasattr(self, 'filename'):
            raise NotImplementedError("Subclasses must define a class attribute 'filename'.")
        return self.path.joinpath(self.filename)

    # sets all variables of the param file (no actual writing to disk)
    def set(self, *vars):
        raise NotImplementedError()

    # reads a param file and stores it in the object
    def read(self):
        raise NotImplementedError()

    # writes values from the object to a file
    def write(self):
        raise NotImplementedError()

    # def to_yaml(self):
    #     """Creates YAML file"""
    #     yaml_file = self.filepath().replace(".par", ".yaml")
    #     with open(yaml_file, "w") as outfile:
    #         yaml.dump(self.__dict__, outfile, default_flow_style=False)

    # def from_yaml(self):
    #     yaml_file = self.filepath().replace(".par", ".yaml")
    #     with open(yaml_file) as f:
    #         yaml_args = yaml.load(f)

    #     for k, v in yaml_args.items():
    #         if isinstance(v, list) and len(v) > 1:  # multi line
    #             setattr(self, k, [])
    #             tmp = [item for item in v]
    #             setattr(self, k, tmp)

    #         setattr(self, k, v)

    def istherefile(self, filename):
        """checks if the filename exists in the experimental path"""
        if not self.exp_path.joinpath(filename).is_file():
            warning(f"{filename} not found")


# Print detailed error to the console and show the user a friendly error window
def error(owner, msg):
    print(f"Exception caught, message: {msg}")


def warning(msg):
    print(f"Warning message: {msg}")


def readParamsDir(par_path):
    """Reads a parameters directory and returns a dictionary with all parameter objects"""

    ptvParams = PtvParams(path=par_path)
    ptvParams.read()
    n_img = ptvParams.n_img

    # n_pts = Int(4)

    ret = {
        PtvParams: ptvParams,
        CalOriParams: CalOriParams(n_img, path=par_path),
        SequenceParams: SequenceParams(n_img, path=par_path),
        CriteriaParams: CriteriaParams(path=par_path),
        TargRecParams: TargRecParams(n_img, path=par_path),
        ManOriParams: ManOriParams(n_img, [], path=par_path),
        DetectPlateParams: DetectPlateParams(path=par_path),
        OrientParams: OrientParams(path=par_path),
        TrackingParams: TrackingParams(path=par_path),
        PftVersionParams: PftVersionParams(path=par_path),
        ExamineParams: ExamineParams(path=par_path),
        DumbbellParams: DumbbellParams(path=par_path),
        ShakingParams: ShakingParams(path=par_path),
        MultiPlaneParams: MultiPlaneParams(n_img=n_img, path=par_path),
        SortGridParams: SortGridParams(n_img=n_img, path=par_path),
    }

    for parType in list(ret.keys()):
        if parType == PtvParams:
            continue
        parObj = ret[parType]
        parObj.read()

    return ret


def copy_params_dir(src: Path, dest: Path):
    """Copying all parameter files from /src folder to /dest
    including .dat, .par and .yaml files
    """
    ext_set = ("*.dat", "*.par", "*.yaml")
    files = []
    for ext in ext_set:
        files.extend(src.glob(ext))

    if not dest.is_dir():
        print("Destination folder does not exist, creating it")
        dest.mkdir(parents=True, exist_ok=True)

    print(f"Copying now file by file from {src} to {dest}: \n")

    for f in tqdm(files):
        shutil.copyfile(
            f,
            dest / f.name,
        )

    print("Successfully \n")



class PtvParams(Parameters):
    def __init__(
        self,
        n_img: int = 0,
        img_name: list[str] = [""],
        img_cal: list[str] = [""],
        hp_flag: bool = False,
        allcam_flag: bool = False,
        tiff_flag: bool = False,
        imx: int = 0,
        imy: int = 0,
        pix_x: float = 0.0,
        pix_y: float = 0.0,
        chfield: int = 0,
        mmp_n1: float = 0.0,
        mmp_n2: float = 0.0,
        mmp_n3: float = 0.0,
        mmp_d: float = 0.0,
        path: Optional[Path] = None,
    ):
        Parameters.__init__(self, path)
        self.n_img = n_img
        self.img_name = img_name if img_name is not None else ["" for _ in range(max_cam)]
        self.img_cal = img_cal if img_cal is not None else ["" for _ in range(max_cam)]
        self.hp_flag = hp_flag
        self.allcam_flag = allcam_flag
        self.tiff_flag = tiff_flag
        self.imx = imx
        self.imy = imy
        self.pix_x = pix_x
        self.pix_y = pix_y
        self.chfield = chfield
        self.mmp_n1 = mmp_n1
        self.mmp_n2 = mmp_n2
        self.mmp_n3 = mmp_n3
        self.mmp_d = mmp_d

    filename = "ptv.par"

    def read(self):
        if not self.filepath().exists():
            warning(f"{self.filepath()} does not exist ")
        try:
            with open(self.filepath(), "r", encoding="utf8") as f:
                self.n_img = int(g(f))

                lines = [g(f) for _ in range(2 * self.n_img)]
                self.img_name = lines[::2]
                self.img_cal = lines[1::2]

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

        for i in range(self.n_img):
            self.istherefile(self.img_name[i])
            self.istherefile(self.img_cal[i])

    def write(self):
        try:
            with open(self.filepath(), "w") as f:
                f.write("%d\n" % self.n_img)
                for i in range(self.n_img):
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
    def __init__(self, 
                    n_img:int = 0,
                    fixp_name: str = "",
                    img_cal_name: list[str] = [""], 
                    img_ori: list[str] = [""],
                    tiff_flag: bool = False,
                    pair_flag: bool = False,
                    chfield: int = 0,
                    path: Path=Parameters.default_path
                 ):
        Parameters.__init__(self, path)
        self.n_img = n_img
        self.fixp_name = fixp_name
        self.img_cal_name = img_cal_name
        self.img_ori = img_ori 
        self.tiff_flag = tiff_flag
        self.pair_flag = pair_flag
        self.chfield = chfield

    filename = "cal_ori.par"

    def read(self):
        try:
            with open(self.filepath(), "r") as f:
                self.fixp_name = g(f)
                self.istherefile(self.fixp_name)

                lines = [g(f) for _ in range(2 * self.n_img)]
                self.img_cal_name = lines[::2]
                self.img_ori = lines[1::2]

                self.tiff_flag = int(g(f)) != 0
                self.pair_flag = int(g(f)) != 0
                self.chfield = int(g(f))

        except BaseException:
            error(None, "%s not found" % self.filepath())

        for i in range(self.n_img):
            self.istherefile(self.img_cal_name[i])
            self.istherefile(self.img_ori[i])

    def write(self):
        try:
            with open(self.filepath(), "w") as f:
                f.write("%s\n" % self.fixp_name)
                for i in range(self.n_img):
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
    def __init__(
        self,
        n_img: int = 0,
        base_name: list[str] = [""],
        first: int = 0,
        last: int = 0,
        path: Optional[Path] = None,
    ):
        Parameters.__init__(self, path)
        self.n_img = n_img
        self.base_name = base_name if base_name is not None else ["" for _ in range(n_img)]
        self.first = first
        self.last = last

    filename = "sequence.par"

    def read(self):
        try:
            with open(self.filepath(), "r") as f:
                self.base_name = []
                for i in range(self.n_img):
                    self.base_name.append(g(f))

                self.first = int(g(f))
                self.last = int(g(f))
        except BaseException:
            error(None, "error reading %s" % self.filepath())

    def write(self):
        try:
            with open(self.filepath(), "w") as f:
                for i in range(self.n_img):
                    f.write("%s\n" % self.base_name[i])

                f.write("%d\n" % self.first)
                f.write("%d\n" % self.last)

            return True
        except BaseException:
            error(None, "Error writing %s." % self.filepath())
            return False


class CriteriaParams(Parameters):
    def __init__(
        self,
        X_lay: list[int] = [0, 0],
        Zmin_lay: list[int] = [0, 0],
        Zmax_lay: list[int] = [0, 0],
        cnx: float = 0.0,
        cny: float = 0.0,
        cn: float = 0.0,
        csumg: float = 0.0,
        corrmin: float = 0.0,
        eps0: float = 0.0,
        path: Optional[Path] = None,
    ):
        Parameters.__init__(self, path)
        self.X_lay = X_lay if X_lay is not None else [0, 0]
        self.Zmin_lay = Zmin_lay if Zmin_lay is not None else [0, 0]
        self.Zmax_lay = Zmax_lay if Zmax_lay is not None else [0, 0]
        self.cnx = cnx
        self.cny = cny
        self.cn = cn
        self.csumg = csumg
        self.corrmin = corrmin
        self.eps0 = eps0

    filename = "criteria.par"

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
    def __init__(
        self,
        n_img: int = 0,
        gvthres: list[int] = [0,0,0,0],
        disco: int = 0,
        nnmin: int = 0,
        nnmax: int = 0,
        nxmin: int = 0,
        nxmax: int = 0,
        nymin: int = 0,
        nymax: int = 0,
        sumg_min: int = 0,
        cr_sz: int = 0,
        path: Path = Parameters.default_path,
    ):
        Parameters.__init__(self, path)
        self.n_img = n_img
        self.gvthres = gvthres if gvthres is not None else [0 for _ in range(max_cam)]
        self.disco = disco
        self.nnmin = nnmin
        self.nnmax = nnmax
        self.nxmin = nxmin
        self.nxmax = nxmax
        self.nymin = nymin
        self.nymax = nymax
        self.sumg_min = sumg_min
        self.cr_sz = cr_sz

    filename = "targ_rec.par"

    def read(self):
        try:
            with open(self.filepath(), "r") as f:
                self.gvthres = [0] * max_cam
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
    def __init__(self, 
                 n_img: int = 0, 
                 nr: list[int] = [0, 0, 0, 0],
                 path: Path = Parameters.default_path
                 ):
        Parameters.__init__(self, path)
        self.n_img = int(n_img) if n_img is not None else 0
        self.nr = nr if nr is not None else []
        self.path = path

    filename = "man_ori.par"

    def read(self):
        try:
            with open(self.filepath(), "r") as f:
                for i in range(self.n_img):
                    for _ in range(4):
                        self.nr.append(int(g(f)))
        except BaseException:
            error(None, "Error reading from %s" % self.filepath())

    def write(self):
        try:
            with open(self.filepath(), "w") as f:
                for i in range(self.n_img):
                    for j in range(4):
                        f.write("%d\n" % self.nr[i * 4 + j])

            return True
        except BaseException:
            error(None, "Error writing %s." % self.filepath())
            return False

class DetectPlateParams(Parameters):
    def __init__(
        self,
        gvth_1: int = 0,
        gvth_2: int = 0,
        gvth_3: int = 0,
        gvth_4: int = 0,
        tol_dis: int = 0,
        min_npix: int = 0,
        max_npix: int = 0,
        min_npix_x: int = 0,
        max_npix_x: int = 0,
        min_npix_y: int = 0,
        max_npix_y: int = 0,
        sum_grey: int = 0,
        size_cross: int = 0,
        path: Path = Parameters.default_path,
    ):
        Parameters.__init__(self, path)
        self.gvth_1 = gvth_1
        self.gvth_2 = gvth_2
        self.gvth_3 = gvth_3
        self.gvth_4 = gvth_4
        self.tol_dis = tol_dis
        self.min_npix = min_npix
        self.max_npix = max_npix
        self.min_npix_x = min_npix_x
        self.max_npix_x = max_npix_x
        self.min_npix_y = min_npix_y
        self.max_npix_y = max_npix_y
        self.sum_grey = sum_grey
        self.size_cross = size_cross

    filename = "detect_plate.par"

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
    1 cc = principle distance
    1 xp - shift of the center
    1 yp - shift of the center
    1 k1 - radial distortion coefficient
    1 k2 - radial distortion coefficient
    1 k3 - radial distortion coefficient
    0 p1 - tangential distortion coefficient
    0 p2 - tangential distortion coefficient
    1 scx - scale factor in x direction
    1 she - shear factor
    0 interf - interference term
    """

    def __init__(
        self,
        pnfo: int = 0,
        cc: float = 0.0,
        xh: float = 0.0,
        yh: float = 0.0,
        k1: float = 0.0,
        k2: float = 0.0,
        k3: float = 0.0,
        p1: float = 0.0,
        p2: float = 0.0,
        scale: float = 0.0,
        shear: float = 0.0,
        interf: float = 0.0,
        path: Optional[Path] = None,
    ):
        Parameters.__init__(self, path)
        self.pnfo = pnfo
        self.cc = cc
        self.xh = xh
        self.yh = yh
        self.k1 = k1
        self.k2 = k2
        self.k3 = k3
        self.p1 = p1
        self.p2 = p2
        self.scale = scale
        self.shear = shear
        self.interf = interf

    filename = "orient.par"

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
    """Parameters for the tracking algorithm""" 
    def __init__(
        self,
        dvxmin: float = 0.0,
        dvxmax: float = 0.0,
        dvymin: float = 0.0,
        dvymax: float = 0.0,
        dvzmin: float = 0.0,
        dvzmax: float = 0.0,
        angle: float = 0.0,
        dacc: float = 0.0,
        flagNewParticles: bool = False,
        path=Parameters.default_path,
    ):
        Parameters.__init__(self, path)
        self.dvxmin = dvxmin
        self.dvxmax = dvxmax
        self.dvymin = dvymin
        self.dvymax = dvymax
        self.dvzmin = dvzmin
        self.dvzmax = dvzmax
        self.angle = angle
        self.dacc = dacc
        self.flagNewParticles = flagNewParticles

    filename = "track.par"

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
    def __init__(self, Existing_Target: int=0, path=None):
        Parameters.__init__(self, path)
        self.Existing_Target = Existing_Target

    filename = "pft_version.par"

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
    def __init__(
        self,
        Examine_Flag: bool = False,
        Combine_Flag: bool = False,
        path: Optional[Path] = None,
    ):
        Parameters.__init__(self, path)
        self.Examine_Flag = Examine_Flag
        self.Combine_Flag = Combine_Flag

    filename = "examine.par"

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
    def __init__(
        self,
        dumbbell_eps: float = 0.0,
        dumbbell_scale: float = 0.0,
        dumbbell_gradient_descent: float = 0.0,
        dumbbell_penalty_weight: float = 0.0,
        dumbbell_step: int = 0,
        dumbbell_niter: int = 0,
        path: Path = Parameters.default_path,
    ):
        Parameters.__init__(self, path)
        self.dumbbell_eps = dumbbell_eps
        self.dumbbell_scale = dumbbell_scale
        self.dumbbell_gradient_descent = dumbbell_gradient_descent
        self.dumbbell_penalty_weight = dumbbell_penalty_weight
        self.dumbbell_step = dumbbell_step
        self.dumbbell_niter = dumbbell_niter

    filename = "dumbbell.par"

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
    def __init__(
        self,
        shaking_first_frame: int = 0,
        shaking_last_frame: int = 0,
        shaking_max_num_points: int = 0,
        shaking_max_num_frames: int = 0,
        path: Optional[Path] = None,
    ):
        Parameters.__init__(self, path)
        self.shaking_first_frame = shaking_first_frame
        self.shaking_last_frame = shaking_last_frame
        self.shaking_max_num_points = shaking_max_num_points
        self.shaking_max_num_frames = shaking_max_num_frames

    filename = "shaking.par"

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
    def __init__(
        self,
        n_img: int = 0,
        n_planes: int = 0,
        plane_name: list[str] = [""],
        path: Path = Parameters.default_path,
    ):
        Parameters.__init__(self, path)
        if plane_name is None:
            plane_name = []
        self.n_img = n_img
        self.n_planes = n_planes
        self.plane_name = plane_name

    filename = "multi_planes.par"

    def read(self):
        try:
            with open(self.filepath(), "r") as f:
                self.n_planes = int(g(f))
                self.plane_name = []
                for i in range(self.n_planes):
                    self.plane_name.append(g(f))

        except BaseException:
            error(None, "%s not found" % self.filepath())

    def write(self):
        try:
            with open(self.filepath(), "w") as f:
                f.write("%d\n" % self.n_planes)
                for i in range(self.n_planes):
                    f.write("%s\n" % self.plane_name[i])

                return True
        except BaseException:
            error(None, "Error writing %s." % self.filepath())
            return False


class SortGridParams(Parameters):
    def __init__(self, 
                 n_img: int = 0, 
                 radius: int = 0, 
                 path: Path = Parameters.default_path
                 ):
        Parameters.__init__(self, path)
        self.n_img = n_img
        self.radius = radius

    filename = "sortgrid.par"

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
