"""Backend compatibility layer for PyPTV.

This module provides a unified API that works with either:
- optv (native C bindings)
- openptv-python (pure Python/Numba with optional optv delegation)

The API exposed matches optv naming conventions for backward compatibility.
"""

from __future__ import annotations

import warnings
from typing import Any

# Try to import backends in order of preference
# openptv-python is preferred as it can delegate to optv when available

BACKEND: str | None = None
BACKEND_MODULE: Any = None

# Try openptv-python first
try:
    import openptv_python

    BACKEND = "openptv_python"
    BACKEND_MODULE = openptv_python
except ImportError:
    openptv_python = None  # type: ignore

# Fall back to optv
try:
    import optv

    if BACKEND is None:
        BACKEND = "optv"
        BACKEND_MODULE = optv
except ImportError:
    optv = None  # type: ignore

if BACKEND is None:
    raise ImportError(
        "No PTV backend available. Please install either 'openptv-python' or 'optv'."
    )

# Warn about which backend is being used
if BACKEND == "optv":
    warnings.warn(
        "Using optv backend. Consider installing openptv-python for better performance and compatibility.",
        UserWarning,
        stacklevel=2,
    )


# =============================================================================
# Helper functions for converting between naming conventions
# =============================================================================


def _to_camel_case(snake_str: str) -> str:
    """Convert snake_case to CamelCase."""
    return "".join(word.capitalize() for word in snake_str.split("_"))


def _to_optv_params_name(name: str) -> str:
    """Convert openptv_python naming (ControlPar) to optv naming (ControlParams)."""
    if name.endswith("Par"):
        return name[:-3] + "Params"
    return name


def _to_openptv_name(name: str) -> str:
    """Convert optv naming (ControlParams) to openptv_python naming (ControlPar)."""
    if name.endswith("Params"):
        return name[:-6] + "Par"
    return name


# =============================================================================
# Module imports with compatibility wrapping
# =============================================================================

# --- calibration ---
if BACKEND == "openptv_python":
    from openptv_python.calibration import Calibration
else:
    from optv.calibration import Calibration

# --- parameters ---
if BACKEND == "openptv_python":
    from openptv_python.parameters import ControlPar as ControlParams
    from openptv_python.parameters import SequencePar as SequenceParams
    from openptv_python.parameters import TrackPar as TrackingParams
    from openptv_python.parameters import TargetPar as TargetParams
    from openptv_python.parameters import VolumePar as VolumeParams
    from openptv_python.parameters import MultimediaPar
else:
    from optv.parameters import ControlParams
    from optv.parameters import SequenceParams
    from optv.parameters import TrackingParams
    from optv.parameters import TargetParams
    from optv.parameters import VolumeParams
    from optv.parameters import MultimediaParams as MultimediaPar

# --- image_processing ---
if BACKEND == "openptv_python":
    from openptv_python.image_processing import preprocess_image
else:
    from optv.image_processing import preprocess_image

# --- segmentation ---
if BACKEND == "openptv_python":
    from openptv_python.segmentation import target_recognition
else:
    from optv.segmentation import target_recognition

# --- correspondences ---
if BACKEND == "openptv_python":
    from openptv_python.correspondences import correspondences, MatchedCoords
else:
    from optv.correspondences import correspondences, MatchedCoords

# --- orientation ---
if BACKEND == "openptv_python":
    from openptv_python.orientation import (
        point_positions,
        multi_cam_point_positions,
        external_calibration,
        full_calibration,
        match_detection_to_ref,
    )
else:
    from optv.orientation import (
        point_positions,
        multi_cam_point_positions,
        external_calibration,
        full_calibration,
        match_detection_to_ref,
    )

# --- tracking_framebuf ---
if BACKEND == "openptv_python":
    from openptv_python.tracking_frame_buf import TargetArray, Target, Frame
else:
    from optv.tracking_framebuf import TargetArray, Target, Frame

# --- tracker ---
if BACKEND == "openptv_python":
    try:
        from openptv_python.track import Tracker, default_naming
    except ImportError:
        from optv.tracker import Tracker, default_naming
else:
    from optv.tracker import Tracker, default_naming

# --- transforms ---
if BACKEND == "openptv_python":
    from openptv_python.trafo import arr_pixel_to_metric as convert_arr_pixel_to_metric
    from openptv_python.trafo import arr_metric_to_pixel as convert_arr_metric_to_pixel
else:
    from optv.transforms import convert_arr_pixel_to_metric, convert_arr_metric_to_pixel

# --- imgcoord ---
if BACKEND == "openptv_python":
    from openptv_python.imgcoord import image_coordinates, img_coord
else:
    from optv.imgcoord import image_coordinates

    # optv doesn't have img_coord, create alias
    img_coord = image_coordinates

# --- epipolar ---
if BACKEND == "openptv_python":
    from openptv_python.epi import epipolar_curve
else:
    from optv.epipolar import epipolar_curve


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
    if BACKEND == "openptv_python":
        # openptv_python uses ControlPar with different initialization
        from openptv_python.parameters import MultimediaPar

        cpar = ControlParams(
            num_cams=num_cams,
            img_base_name=["" for _ in range(num_cams)],
            cal_img_base_name=["" for _ in range(num_cams)],
            mm=MultimediaPar(),
        )
        # Set additional attributes from kwargs
        for key, value in kwargs.items():
            if hasattr(cpar, key):
                setattr(cpar, key, value)
        return cpar
    else:
        # optv uses ControlParams with num_cams constructor
        cpar = ControlParams(num_cams)
        for key, value in kwargs.items():
            if hasattr(cpar, key):
                setattr(cpar, key, value)
        return cpar


def create_sequence_params(num_cams: int, **kwargs) -> SequenceParams:
    """Create SequenceParams with backend-appropriate initialization."""
    if BACKEND == "openptv_python":
        spar = SequenceParams(img_base_name=["" for _ in range(num_cams)])
    else:
        spar = SequenceParams(num_cams)

    for key, value in kwargs.items():
        if hasattr(spar, key):
            setattr(spar, key, value)
    return spar


def create_tracking_params(**kwargs) -> TrackingParams:
    """Create TrackingParams with backend-appropriate initialization."""
    if BACKEND == "openptv_python":
        tpar = TrackingParams()
    else:
        tpar = TrackingParams()

    for key, value in kwargs.items():
        if hasattr(tpar, key):
            setattr(tpar, key, value)
    return tpar


def create_volume_params(**kwargs) -> VolumeParams:
    """Create VolumeParams with backend-appropriate initialization."""
    if BACKEND == "openptv_python":
        vpar = VolumeParams()
    else:
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
