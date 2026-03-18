"""Backend compatibility layer for PyPTV.

This module exposes the local openptv_python implementation behind the
legacy names expected by the GUI layer.
"""

from __future__ import annotations

from typing import Any

import openptv_python

BACKEND: str = "openptv_python"
BACKEND_MODULE: Any = openptv_python


# =============================================================================
# Helper functions for converting between naming conventions
# =============================================================================


def _to_camel_case(snake_str: str) -> str:
    """Convert snake_case to CamelCase."""
    return "".join(word.capitalize() for word in snake_str.split("_"))


def _to_optv_params_name(name: str) -> str:
    """Convert openptv_python naming (ControlPar) to legacy naming."""
    if name.endswith("Par"):
        return name[:-3] + "Params"
    return name


def _to_openptv_name(name: str) -> str:
    """Convert legacy naming to openptv_python naming."""
    if name.endswith("Params"):
        return name[:-6] + "Par"
    return name


# =============================================================================
# Module imports with compatibility wrapping
# =============================================================================

from openptv_python.calibration import Calibration
from openptv_python.parameters import ControlPar as ControlParams
from openptv_python.parameters import MultimediaPar
from openptv_python.parameters import SequencePar as SequenceParams
from openptv_python.parameters import TargetPar as TargetParams
from openptv_python.parameters import TrackPar as TrackingParams
from openptv_python.parameters import VolumePar as VolumeParams
from openptv_python.image_processing import preprocess_image
from openptv_python.segmentation import target_recognition
from openptv_python.correspondences import correspondences, MatchedCoords
from openptv_python.orientation import (
    point_positions,
    multi_cam_point_positions,
    external_calibration,
    full_calibration,
    match_detection_to_ref,
)
from openptv_python.tracking_frame_buf import TargetArray, Target, Frame
from openptv_python.track import Tracker, default_naming
from openptv_python.trafo import arr_pixel_to_metric as convert_arr_pixel_to_metric
from openptv_python.trafo import arr_metric_to_pixel as convert_arr_metric_to_pixel
from openptv_python.imgcoord import image_coordinates, img_coord
from openptv_python.epi import epipolar_curve


# =============================================================================
# Backend info
# =============================================================================


def get_backend() -> str:
    """Return the name of the currently active backend."""
    return BACKEND or "unknown"


def get_backend_module() -> Any:
    """Return the backend module being used."""
    return BACKEND_MODULE


# =============================================================================
# Parameter compatibility helpers
# =============================================================================


def create_control_params(num_cams: int, **kwargs) -> ControlParams:
    """Create ControlParams with backend-appropriate initialization."""
    cpar = ControlParams(
        num_cams=num_cams,
        img_base_name=["" for _ in range(num_cams)],
        cal_img_base_name=["" for _ in range(num_cams)],
        mm=MultimediaPar(),
    )
    for key, value in kwargs.items():
        if hasattr(cpar, key):
            setattr(cpar, key, value)
    return cpar


def create_sequence_params(num_cams: int, **kwargs) -> SequenceParams:
    """Create SequenceParams with backend-appropriate initialization."""
    spar = SequenceParams(img_base_name=["" for _ in range(num_cams)])

    for key, value in kwargs.items():
        if hasattr(spar, key):
            setattr(spar, key, value)
    return spar


def create_tracking_params(**kwargs) -> TrackingParams:
    """Create TrackingParams with backend-appropriate initialization."""
    tpar = TrackingParams()

    for key, value in kwargs.items():
        if hasattr(tpar, key):
            setattr(tpar, key, value)
    return tpar


def create_volume_params(**kwargs) -> VolumeParams:
    """Create VolumeParams with backend-appropriate initialization."""
    vpar = VolumeParams()

    for key, value in kwargs.items():
        if hasattr(vpar, key):
            setattr(vpar, key, value)
    return vpar


def create_target_params(**kwargs) -> TargetParams:
    """Create TargetParams with backend-appropriate initialization."""
    if BACKEND == "openptv_python":
        tpar = TargetParams()
    else:
        tpar = TargetParams()

    for key, value in kwargs.items():
        if hasattr(tpar, key):
            setattr(tpar, key, value)
    return tpar


# =============================================================================
# Export all symbols
# =============================================================================

__all__ = [
    # Backend info
    "get_backend",
    "get_backend_module",
    "BACKEND",
    "BACKEND_MODULE",
    # Classes
    "Calibration",
    "ControlParams",
    "SequenceParams",
    "TrackingParams",
    "TargetParams",
    "VolumeParams",
    "MultimediaPar",
    "TargetArray",
    "Target",
    "Frame",
    "Tracker",
    "MatchedCoords",
    # Functions
    "preprocess_image",
    "target_recognition",
    "correspondences",
    "point_positions",
    "multi_cam_point_positions",
    "default_naming",
    "convert_arr_pixel_to_metric",
    "convert_arr_metric_to_pixel",
    "image_coordinates",
    "img_coord",
    "epipolar_curve",
    # Factory functions
    "create_control_params",
    "create_sequence_params",
    "create_tracking_params",
    "create_volume_params",
    "create_target_params",
]
