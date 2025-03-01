"""Dialog modules for the PyPTV UI."""

from pyptv.ui.dialogs.calibration_dialog import CalibrationDialog
from pyptv.ui.dialogs.detection_dialog import DetectionDialog
from pyptv.ui.dialogs.tracking_dialog import TrackingDialog
from pyptv.ui.dialogs.plugin_dialog import PluginManagerDialog
from pyptv.ui.dialogs.visualization_dialog import VisualizationDialog

__all__ = [
    'CalibrationDialog',
    'DetectionDialog',
    'TrackingDialog',
    'PluginManagerDialog',
    'VisualizationDialog',
]