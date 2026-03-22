"""
Parameter Schema Definitions for PyPTV

This module defines all parameter schemas in one place, eliminating duplication
between parameter definitions, GUI traits, and YAML serialization.
"""

from typing import Any, Type

PARAM_TYPES = {
    "int": int,
    "float": float,
    "bool": bool,
    "str": str,
    "List[int]": list[int],
    "List[float]": list[float],
    "List[str]": list[str],
}

DEFAULT_VALUES = {
    "int": 0,
    "float": 0.0,
    "bool": False,
    "str": "",
    "List[int]": [0, 0],
    "List[float]": [0.0, 0.0],
    "List[str]": [""],
}


class ParamField:
    def __init__(
        self,
        param_type: str,
        default: Any = None,
        label: str = "",
        per_camera: bool = False,
        gui_only: bool = False,
    ):
        self.param_type = param_type
        self.default = (
            default if default is not None else DEFAULT_VALUES.get(param_type, None)
        )
        self.label = label
        self.per_camera = per_camera
        self.gui_only = gui_only

    def get_default(self):
        if callable(self.default):
            return self.default()
        return self.default


PTV_SCHEMA = {
    "name": "ptv",
    "filename": "ptv.par",
    "n_img_dependent": True,
    "fields": {
        "img_name": ParamField("List[str]", label="Image name"),
        "img_cal": ParamField("List[str]", label="Calibration image"),
        "hp_flag": ParamField("bool", label="High pass filter"),
        "allcam_flag": ParamField("bool", label="Accept only all cameras"),
        "tiff_flag": ParamField("bool", label="TIFF format"),
        "imx": ParamField("int", label="Image width"),
        "imy": ParamField("int", label="Image height"),
        "pix_x": ParamField("float", label="Pixel size X"),
        "pix_y": ParamField("float", label="Pixel size Y"),
        "chfield": ParamField("int", label="Chroma field"),
        "mmp_n1": ParamField("float", label="Refractive index air"),
        "mmp_n2": ParamField("float", label="Refractive index glass"),
        "mmp_n3": ParamField("float", label="Refractive index water"),
        "mmp_d": ParamField("float", label="Glass thickness"),
        "splitter": ParamField("bool", label="Split images into 4", gui_only=True),
        "negative": ParamField("bool", label="Negative images"),
    },
}

CAL_ORI_SCHEMA = {
    "name": "cal_ori",
    "filename": "cal_ori.par",
    "n_img_dependent": True,
    "fields": {
        "fixp_name": ParamField("str", label="Target coordinates file"),
        "img_cal_name": ParamField(
            "List[str]", label="Calibration image", per_camera=True
        ),
        "img_ori": ParamField("List[str]", label="Orientation data", per_camera=True),
        "tiff_flag": ParamField("bool"),
        "pair_flag": ParamField("bool"),
        "chfield": ParamField("int"),
        "cal_splitter": ParamField(
            "bool", label="Split calibration image", gui_only=True
        ),
    },
}

SEQUENCE_SCHEMA = {
    "name": "sequence",
    "filename": "sequence.par",
    "n_img_dependent": True,
    "fields": {
        "base_name": ParamField(
            "List[str]", label="Base name for sequence", per_camera=True
        ),
        "first": ParamField("int", label="First frame"),
        "last": ParamField("int", label="Last frame"),
    },
}

CRITERIA_SCHEMA = {
    "name": "criteria",
    "filename": "criteria.par",
    "n_img_dependent": False,
    "fields": {
        "X_lay": ParamField("List[int]", label="X range [min, max]"),
        "Zmin_lay": ParamField("List[int]", label="Zmin [layer1, layer2]"),
        "Zmax_lay": ParamField("List[int]", label="Zmax [layer1, layer2]"),
        "cnx": ParamField("float", label="Min correlation nx"),
        "cny": ParamField("float", label="Min correlation ny"),
        "cn": ParamField("float", label="Min correlation npix"),
        "csumg": ParamField("float", label="Min sum grey"),
        "corrmin": ParamField("float", label="Min weight correlation"),
        "eps0": ParamField("float", label="Epipolar band tolerance"),
    },
}

TARG_REC_SCHEMA = {
    "name": "targ_rec",
    "filename": "targ_rec.par",
    "n_img_dependent": True,
    "fields": {
        "gvthres": ParamField("List[int]", label="Grey threshold", per_camera=True),
        "disco": ParamField("int", label="Tolerable discontinuity"),
        "nnmin": ParamField("int", label="Min particles"),
        "nnmax": ParamField("int", label="Max particles"),
        "nxmin": ParamField("int", label="Min particles x"),
        "nxmax": ParamField("int", label="Max particles x"),
        "nymin": ParamField("int", label="Min particles y"),
        "nymax": ParamField("int", label="Max particles y"),
        "sumg_min": ParamField("int", label="Min sum grey"),
        "cr_sz": ParamField("int", label="Cross size"),
    },
}

DETECT_PLATE_SCHEMA = {
    "name": "detect_plate",
    "filename": "detect_plate.par",
    "n_img_dependent": False,
    "fields": {
        "gvth_1": ParamField("int", label="Grey threshold 1"),
        "gvth_2": ParamField("int", label="Grey threshold 2"),
        "gvth_3": ParamField("int", label="Grey threshold 3"),
        "gvth_4": ParamField("int", label="Grey threshold 4"),
        "tol_dis": ParamField("int", label="Tolerable discontinuity"),
        "min_npix": ParamField("int", label="Min particles"),
        "max_npix": ParamField("int", label="Max particles"),
        "min_npix_x": ParamField("int", label="Min particles x"),
        "max_npix_x": ParamField("int", label="Max particles x"),
        "min_npix_y": ParamField("int", label="Min particles y"),
        "max_npix_y": ParamField("int", label="Max particles y"),
        "sum_grey": ParamField("int", label="Sum of grey"),
        "size_cross": ParamField("int", label="Size of crosses"),
    },
}

MAN_ORI_SCHEMA = {
    "name": "man_ori",
    "filename": "man_ori.par",
    "n_img_dependent": True,
    "fields": {
        "nr": ParamField("List[int]", label="Image points (4 per camera)"),
    },
}

ORIENT_SCHEMA = {
    "name": "orient",
    "filename": "orient.par",
    "n_img_dependent": False,
    "fields": {
        "pnfo": ParamField("int", label="Points for orientation"),
        "cc": ParamField("bool", label="Principal distance"),
        "xh": ParamField("bool", label="Center shift X"),
        "yh": ParamField("bool", label="Center shift Y"),
        "k1": ParamField("bool", label="Radial distortion k1"),
        "k2": ParamField("bool", label="Radial distortion k2"),
        "k3": ParamField("bool", label="Radial distortion k3"),
        "p1": ParamField("bool", label="Tangential distortion p1"),
        "p2": ParamField("bool", label="Tangential distortion p2"),
        "scale": ParamField("bool", label="Scale factor"),
        "shear": ParamField("bool", label="Shear factor"),
        "interf": ParamField("bool", label="Interference term"),
    },
}

TRACK_SCHEMA = {
    "name": "track",
    "filename": "track.par",
    "n_img_dependent": False,
    "fields": {
        "dvxmin": ParamField("float", label="Min dVx"),
        "dvxmax": ParamField("float", label="Max dVx"),
        "dvymin": ParamField("float", label="Min dVy"),
        "dvymax": ParamField("float", label="Max dVy"),
        "dvzmin": ParamField("float", label="Min dVz"),
        "dvzmax": ParamField("float", label="Max dVz"),
        "angle": ParamField("float", label="Max angle [gon]"),
        "dacc": ParamField("float", label="Max acceleration"),
        "flagNewParticles": ParamField("bool", label="Add new particles"),
    },
}

PFT_VERSION_SCHEMA = {
    "name": "pft_version",
    "filename": "pft_version.par",
    "n_img_dependent": False,
    "fields": {
        "Existing_Target": ParamField("int", label="Use existing target files"),
    },
}

EXAMINE_SCHEMA = {
    "name": "examine",
    "filename": "examine.par",
    "n_img_dependent": False,
    "fields": {
        "Examine_Flag": ParamField("bool", label="Calibrate with different Z"),
        "Combine_Flag": ParamField("bool", label="Combine preprocessed planes"),
    },
}

DUMBBELL_SCHEMA = {
    "name": "dumbbell",
    "filename": "dumbbell.par",
    "n_img_dependent": False,
    "fields": {
        "dumbbell_eps": ParamField("float", label="Dumbbell epsilon"),
        "dumbbell_scale": ParamField("float", label="Dumbbell scale"),
        "dumbbell_gradient_descent": ParamField(
            "float", label="Gradient descent factor"
        ),
        "dumbbell_penalty_weight": ParamField("float", label="Penalty weight"),
        "dumbbell_step": ParamField("int", label="Step through sequence"),
        "dumbbell_niter": ParamField("int", label="Iterations per click"),
        "dumbbell_fixed_camera": ParamField("int", label="Fixed camera (0=auto)"),
    },
}

SHAKING_SCHEMA = {
    "name": "shaking",
    "filename": "shaking.par",
    "n_img_dependent": False,
    "fields": {
        "shaking_first_frame": ParamField("int", label="First frame"),
        "shaking_last_frame": ParamField("int", label="Last frame"),
        "shaking_max_num_points": ParamField("int", label="Max num points"),
        "shaking_max_num_frames": ParamField("int", label="Max num frames"),
    },
}

MASKING_SCHEMA = {
    "name": "masking",
    "filename": None,
    "n_img_dependent": False,
    "fields": {
        "mask_flag": ParamField("bool", label="Subtract mask"),
        "mask_base_name": ParamField("str", label="Mask base name"),
    },
}

UNSHARP_MASK_SCHEMA = {
    "name": "unsharp_mask",
    "filename": None,
    "n_img_dependent": False,
    "fields": {
        "flag": ParamField("bool", label="Enable unsharp mask"),
        "size": ParamField("int", label="Kernel size"),
        "strength": ParamField("float", label="Strength"),
    },
}

PLUGINS_SCHEMA = {
    "name": "plugins",
    "filename": None,
    "n_img_dependent": False,
    "fields": {
        "available_tracking": ParamField("List[str]", gui_only=True),
        "available_sequence": ParamField("List[str]", gui_only=True),
        "selected_tracking": ParamField("str", label="Tracking plugin", gui_only=True),
        "selected_sequence": ParamField("str", label="Sequence plugin", gui_only=True),
    },
}

ALL_SCHEMAS = {
    "ptv": PTV_SCHEMA,
    "cal_ori": CAL_ORI_SCHEMA,
    "sequence": SEQUENCE_SCHEMA,
    "criteria": CRITERIA_SCHEMA,
    "targ_rec": TARG_REC_SCHEMA,
    "detect_plate": DETECT_PLATE_SCHEMA,
    "man_ori": MAN_ORI_SCHEMA,
    "orient": ORIENT_SCHEMA,
    "track": TRACK_SCHEMA,
    "pft_version": PFT_VERSION_SCHEMA,
    "examine": EXAMINE_SCHEMA,
    "dumbbell": DUMBBELL_SCHEMA,
    "shaking": SHAKING_SCHEMA,
    "masking": MASKING_SCHEMA,
    "unsharp_mask": UNSHARP_MASK_SCHEMA,
    "plugins": PLUGINS_SCHEMA,
}


def get_schema_defaults():
    defaults = {"num_cams": 0}
    for schema in ALL_SCHEMAS.values():
        section = schema["name"]
        defaults[section] = {}
        for field_name, field_def in schema["fields"].items():
            if not field_def.gui_only:
                defaults[section][field_name] = field_def.get_default()
    return defaults
