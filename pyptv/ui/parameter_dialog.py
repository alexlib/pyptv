"""Parameter dialog for editing YAML parameters."""

from pathlib import Path
import os
from typing import Any, Dict, List, Optional, Type, Union

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QPushButton,
    QFileDialog,
    QTabWidget,
    QWidget,
    QMessageBox,
    QGroupBox,
    QComboBox
)

from pyptv.yaml_parameters import (
    ParameterBase,
    PtvParams,
    TrackingParams,
    SequenceParams,
    CriteriaParams,
    ParameterManager
)


class ParameterDialog(QDialog):
    """Base parameter dialog for editing YAML parameters."""
    
    def __init__(self, parameter: ParameterBase, parent=None):
        """Initialize the parameter dialog.
        
        Args:
            parameter: Parameter object to edit
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.parameter = parameter
        self.param_widgets = {}
        
        # Set window properties
        self.setWindowTitle(f"Edit {type(parameter).__name__}")
        self.resize(600, 500)
        
        # Create the main layout
        self.main_layout = QVBoxLayout(self)
        
        # Create form for parameters
        self.form_widget = QWidget()
        self.form_layout = QFormLayout(self.form_widget)
        self.main_layout.addWidget(self.form_widget)
        
        # Create the parameter widgets
        self.create_parameter_widgets()
        
        # Create buttons
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_parameters)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        
        self.main_layout.addLayout(button_layout)
    
    def create_parameter_widgets(self):
        """Create widgets for each parameter (to be implemented by subclasses)."""
        raise NotImplementedError("Subclasses must implement create_parameter_widgets")
    
    def add_section_header(self, title: str):
        """Add a section header to the form.
        
        Args:
            title: Section title
        """
        label = QLabel(f"<b>{title}</b>")
        self.form_layout.addRow("", label)
    
    def add_parameter_widget(self, name: str, widget: QWidget, tooltip: Optional[str] = None):
        """Add a parameter widget to the form.
        
        Args:
            name: Parameter name
            widget: Parameter widget
            tooltip: Optional tooltip
        """
        if tooltip:
            widget.setToolTip(tooltip)
        self.param_widgets[name] = widget
        self.form_layout.addRow(name.replace('_', ' ').title() + ":", widget)
    
    def create_int_spinner(self, value: int, min_val: int = 0, max_val: int = 9999):
        """Create an integer spinner widget.
        
        Args:
            value: Current value
            min_val: Minimum value
            max_val: Maximum value
            
        Returns:
            Spinner widget
        """
        spinner = QSpinBox()
        spinner.setRange(min_val, max_val)
        spinner.setValue(value)
        return spinner
    
    def create_float_spinner(self, value: float, min_val: float = -9999.0, max_val: float = 9999.0, 
                            decimals: int = 2):
        """Create a float spinner widget.
        
        Args:
            value: Current value
            min_val: Minimum value
            max_val: Maximum value
            decimals: Number of decimal places
            
        Returns:
            Spinner widget
        """
        spinner = QDoubleSpinBox()
        spinner.setRange(min_val, max_val)
        spinner.setDecimals(decimals)
        spinner.setValue(value)
        return spinner
    
    def create_checkbox(self, value: bool):
        """Create a checkbox widget.
        
        Args:
            value: Current value
            
        Returns:
            Checkbox widget
        """
        checkbox = QCheckBox()
        checkbox.setChecked(value)
        return checkbox
    
    def create_path_selector(self, value: str, filter_str: str = "All Files (*)"):
        """Create a path selector widget.
        
        Args:
            value: Current value
            filter_str: Filter string for file dialog
            
        Returns:
            Path selector widget
        """
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        line_edit = QLineEdit(value)
        browse_button = QPushButton("Browse...")
        
        layout.addWidget(line_edit)
        layout.addWidget(browse_button)
        
        container = QWidget()
        container.setLayout(layout)
        
        def browse():
            path, _ = QFileDialog.getOpenFileName(
                self, "Select File", line_edit.text(), filter_str
            )
            if path:
                line_edit.setText(path)
        
        browse_button.clicked.connect(browse)
        
        # Attach the line edit to the container for retrieval
        container.line_edit = line_edit
        
        return container
    
    def get_widget_value(self, widget: QWidget) -> Any:
        """Get the value from a widget.
        
        Args:
            widget: Widget to get value from
            
        Returns:
            Widget value
        """
        if isinstance(widget, QSpinBox):
            return widget.value()
        elif isinstance(widget, QDoubleSpinBox):
            return widget.value()
        elif isinstance(widget, QCheckBox):
            return widget.isChecked()
        elif isinstance(widget, QLineEdit):
            return widget.text()
        elif hasattr(widget, 'line_edit'):
            return widget.line_edit.text()
        else:
            return None
    
    def save_parameters(self):
        """Save parameter values from widgets to the parameter object."""
        # Update parameter values from widgets
        for name, widget in self.param_widgets.items():
            if hasattr(self.parameter, name):
                value = self.get_widget_value(widget)
                setattr(self.parameter, name, value)
        
        # Save to file
        self.parameter.save()
        
        # Also save legacy version
        try:
            self.parameter.save_legacy()
        except Exception as e:
            print(f"Warning: Failed to save legacy parameters: {e}")
        
        # Accept the dialog
        self.accept()


class PtvParamsDialog(ParameterDialog):
    """Dialog for editing PTV parameters."""
    
    def create_parameter_widgets(self):
        """Create widgets for PTV parameters."""
        # Main camera parameters
        self.add_section_header("Camera Settings")
        
        # Number of cameras
        n_cam_spinner = self.create_int_spinner(self.parameter.n_img, 1, 8)
        self.add_parameter_widget("n_img", n_cam_spinner, "Number of cameras")
        
        # Image dimensions
        imx_spinner = self.create_int_spinner(self.parameter.imx, 1, 10000)
        self.add_parameter_widget("imx", imx_spinner, "Image width in pixels")
        
        imy_spinner = self.create_int_spinner(self.parameter.imy, 1, 10000)
        self.add_parameter_widget("imy", imy_spinner, "Image height in pixels")
        
        # Pixel size
        pix_x_spinner = self.create_float_spinner(self.parameter.pix_x, 0.001, 1.0, 4)
        self.add_parameter_widget("pix_x", pix_x_spinner, "Pixel size horizontal [mm]")
        
        pix_y_spinner = self.create_float_spinner(self.parameter.pix_y, 0.001, 1.0, 4)
        self.add_parameter_widget("pix_y", pix_y_spinner, "Pixel size vertical [mm]")
        
        # Processing flags
        self.add_section_header("Processing Flags")
        
        hp_flag_checkbox = self.create_checkbox(self.parameter.hp_flag)
        self.add_parameter_widget("hp_flag", hp_flag_checkbox, "Apply highpass filter")
        
        allcam_flag_checkbox = self.create_checkbox(self.parameter.allcam_flag)
        self.add_parameter_widget("allcam_flag", allcam_flag_checkbox, 
                                "Use only particles visible in all cameras")
        
        tiff_flag_checkbox = self.create_checkbox(self.parameter.tiff_flag)
        self.add_parameter_widget("tiff_flag", tiff_flag_checkbox, "Images have TIFF headers")
        
        # Field flag
        chfield_spinner = self.create_int_spinner(self.parameter.chfield, 0, 2)
        self.add_parameter_widget("chfield", chfield_spinner, 
                                "Field flag (0=frame, 1=odd, 2=even)")
        
        # Multimedia parameters
        self.add_section_header("Multimedia Parameters")
        
        mmp_n1_spinner = self.create_float_spinner(self.parameter.mmp_n1, 1.0, 2.0, 3)
        self.add_parameter_widget("mmp_n1", mmp_n1_spinner, "Refractive index air")
        
        mmp_n2_spinner = self.create_float_spinner(self.parameter.mmp_n2, 1.0, 2.0, 3)
        self.add_parameter_widget("mmp_n2", mmp_n2_spinner, "Refractive index water")
        
        mmp_n3_spinner = self.create_float_spinner(self.parameter.mmp_n3, 1.0, 2.0, 3)
        self.add_parameter_widget("mmp_n3", mmp_n3_spinner, "Refractive index glass")
        
        mmp_d_spinner = self.create_float_spinner(self.parameter.mmp_d, 0.0, 100.0, 1)
        self.add_parameter_widget("mmp_d", mmp_d_spinner, "Thickness of glass [mm]")


class TrackingParamsDialog(ParameterDialog):
    """Dialog for editing tracking parameters."""
    
    def create_parameter_widgets(self):
        """Create widgets for tracking parameters."""
        # Velocity search range
        self.add_section_header("Velocity Search Range")
        
        dvxmin_spinner = self.create_float_spinner(self.parameter.dvxmin, -100.0, 0.0, 1)
        self.add_parameter_widget("dvxmin", dvxmin_spinner, "Minimum X velocity")
        
        dvxmax_spinner = self.create_float_spinner(self.parameter.dvxmax, 0.0, 100.0, 1)
        self.add_parameter_widget("dvxmax", dvxmax_spinner, "Maximum X velocity")
        
        dvymin_spinner = self.create_float_spinner(self.parameter.dvymin, -100.0, 0.0, 1)
        self.add_parameter_widget("dvymin", dvymin_spinner, "Minimum Y velocity")
        
        dvymax_spinner = self.create_float_spinner(self.parameter.dvymax, 0.0, 100.0, 1)
        self.add_parameter_widget("dvymax", dvymax_spinner, "Maximum Y velocity")
        
        dvzmin_spinner = self.create_float_spinner(self.parameter.dvzmin, -100.0, 0.0, 1)
        self.add_parameter_widget("dvzmin", dvzmin_spinner, "Minimum Z velocity")
        
        dvzmax_spinner = self.create_float_spinner(self.parameter.dvzmax, 0.0, 100.0, 1)
        self.add_parameter_widget("dvzmax", dvzmax_spinner, "Maximum Z velocity")
        
        # Other tracking parameters
        self.add_section_header("Tracking Parameters")
        
        angle_spinner = self.create_float_spinner(self.parameter.angle, 0.0, 180.0, 1)
        self.add_parameter_widget("angle", angle_spinner, "Angle for search cone [degrees]")
        
        dacc_spinner = self.create_float_spinner(self.parameter.dacc, 0.0, 1.0, 2)
        self.add_parameter_widget("dacc", dacc_spinner, "Acceleration limit")
        
        flagNewParticles_checkbox = self.create_checkbox(self.parameter.flagNewParticles)
        self.add_parameter_widget("flagNewParticles", flagNewParticles_checkbox, 
                                "Allow adding new particles")


class SequenceParamsDialog(ParameterDialog):
    """Dialog for editing sequence parameters."""
    
    def create_parameter_widgets(self):
        """Create widgets for sequence parameters."""
        # Frame range
        self.add_section_header("Frame Range")
        
        seq_first_spinner = self.create_int_spinner(self.parameter.Seq_First, 0, 1000000)
        self.add_parameter_widget("Seq_First", seq_first_spinner, "First frame in sequence")
        
        seq_last_spinner = self.create_int_spinner(self.parameter.Seq_Last, 0, 1000000)
        self.add_parameter_widget("Seq_Last", seq_last_spinner, "Last frame in sequence")
        
        # Image paths
        self.add_section_header("Image Paths")
        
        basename_1_edit = QLineEdit(self.parameter.Basename_1_Seq)
        self.add_parameter_widget("Basename_1_Seq", basename_1_edit, 
                                "Base name for camera 1 images")
        
        basename_2_edit = QLineEdit(self.parameter.Basename_2_Seq)
        self.add_parameter_widget("Basename_2_Seq", basename_2_edit, 
                                "Base name for camera 2 images")
        
        basename_3_edit = QLineEdit(self.parameter.Basename_3_Seq)
        self.add_parameter_widget("Basename_3_Seq", basename_3_edit, 
                                "Base name for camera 3 images")
        
        basename_4_edit = QLineEdit(self.parameter.Basename_4_Seq)
        self.add_parameter_widget("Basename_4_Seq", basename_4_edit, 
                                "Base name for camera 4 images")
        
        # Reference images
        self.add_section_header("Reference Images")
        
        name_1_edit = QLineEdit(self.parameter.Name_1_Image)
        self.add_parameter_widget("Name_1_Image", name_1_edit, 
                                "Reference image for camera 1")
        
        name_2_edit = QLineEdit(self.parameter.Name_2_Image)
        self.add_parameter_widget("Name_2_Image", name_2_edit, 
                                "Reference image for camera 2")
        
        name_3_edit = QLineEdit(self.parameter.Name_3_Image)
        self.add_parameter_widget("Name_3_Image", name_3_edit, 
                                "Reference image for camera 3")
        
        name_4_edit = QLineEdit(self.parameter.Name_4_Image)
        self.add_parameter_widget("Name_4_Image", name_4_edit, 
                                "Reference image for camera 4")
        
        # Volume limits
        self.add_section_header("Volume Limits")
        
        xmin_spinner = self.create_float_spinner(self.parameter.Xmin_lay, -1000.0, 1000.0, 1)
        self.add_parameter_widget("Xmin_lay", xmin_spinner, "Minimum X coordinate [mm]")
        
        xmax_spinner = self.create_float_spinner(self.parameter.Xmax_lay, -1000.0, 1000.0, 1)
        self.add_parameter_widget("Xmax_lay", xmax_spinner, "Maximum X coordinate [mm]")
        
        ymin_spinner = self.create_float_spinner(self.parameter.Ymin_lay, -1000.0, 1000.0, 1)
        self.add_parameter_widget("Ymin_lay", ymin_spinner, "Minimum Y coordinate [mm]")
        
        ymax_spinner = self.create_float_spinner(self.parameter.Ymax_lay, -1000.0, 1000.0, 1)
        self.add_parameter_widget("Ymax_lay", ymax_spinner, "Maximum Y coordinate [mm]")
        
        zmin_spinner = self.create_float_spinner(self.parameter.Zmin_lay, -1000.0, 1000.0, 1)
        self.add_parameter_widget("Zmin_lay", zmin_spinner, "Minimum Z coordinate [mm]")
        
        zmax_spinner = self.create_float_spinner(self.parameter.Zmax_lay, -1000.0, 1000.0, 1)
        self.add_parameter_widget("Zmax_lay", zmax_spinner, "Maximum Z coordinate [mm]")
        
        # Image processing options
        self.add_section_header("Image Processing")
        
        inverse_checkbox = self.create_checkbox(self.parameter.Inverse)
        self.add_parameter_widget("Inverse", inverse_checkbox, "Invert images")
        
        subtr_mask_checkbox = self.create_checkbox(self.parameter.Subtr_Mask)
        self.add_parameter_widget("Subtr_Mask", subtr_mask_checkbox, "Subtract mask/background")
        
        base_name_mask_edit = QLineEdit(self.parameter.Base_Name_Mask)
        self.add_parameter_widget("Base_Name_Mask", base_name_mask_edit, 
                                "Base name for mask files")


class CriteriaParamsDialog(ParameterDialog):
    """Dialog for editing criteria parameters."""
    
    def create_parameter_widgets(self):
        """Create widgets for criteria parameters."""
        # Volume parameters
        self.add_section_header("Volume Parameters")
        
        x_lay_spinner = self.create_float_spinner(self.parameter.X_lay, -1000.0, 1000.0, 1)
        self.add_parameter_widget("X_lay", x_lay_spinner, "X center of illuminated volume [mm]")
        
        xmin_spinner = self.create_float_spinner(self.parameter.Xmin_lay, -1000.0, 1000.0, 1)
        self.add_parameter_widget("Xmin_lay", xmin_spinner, "Minimum X coordinate [mm]")
        
        xmax_spinner = self.create_float_spinner(self.parameter.Xmax_lay, -1000.0, 1000.0, 1)
        self.add_parameter_widget("Xmax_lay", xmax_spinner, "Maximum X coordinate [mm]")
        
        ymin_spinner = self.create_float_spinner(self.parameter.Ymin_lay, -1000.0, 1000.0, 1)
        self.add_parameter_widget("Ymin_lay", ymin_spinner, "Minimum Y coordinate [mm]")
        
        ymax_spinner = self.create_float_spinner(self.parameter.Ymax_lay, -1000.0, 1000.0, 1)
        self.add_parameter_widget("Ymax_lay", ymax_spinner, "Maximum Y coordinate [mm]")
        
        zmin_spinner = self.create_float_spinner(self.parameter.Zmin_lay, -1000.0, 1000.0, 1)
        self.add_parameter_widget("Zmin_lay", zmin_spinner, "Minimum Z coordinate [mm]")
        
        zmax_spinner = self.create_float_spinner(self.parameter.Zmax_lay, -1000.0, 1000.0, 1)
        self.add_parameter_widget("Zmax_lay", zmax_spinner, "Maximum Z coordinate [mm]")
        
        # Convergence parameters
        self.add_section_header("Convergence Parameters")
        
        cn_spinner = self.create_float_spinner(self.parameter.cn, 0.0, 10.0, 3)
        self.add_parameter_widget("cn", cn_spinner, "Convergence limit")
        
        eps0_spinner = self.create_float_spinner(self.parameter.eps0, 0.0, 1.0, 3)
        self.add_parameter_widget("eps0", eps0_spinner, "Convergence criteria slope")


class ParameterTabDialog(QDialog):
    """Dialog with tabs for different parameter sets."""
    
    def __init__(self, param_manager: ParameterManager, parent=None):
        """Initialize parameter tab dialog.
        
        Args:
            param_manager: Parameter manager
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.param_manager = param_manager
        self.parameters = param_manager.load_all()
        
        # Set window properties
        self.setWindowTitle("Edit Parameters")
        self.resize(700, 600)
        
        # Create main layout
        self.main_layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)
        
        # Create tabs for each parameter type
        self.create_parameter_tabs()
        
        # Create buttons
        button_layout = QHBoxLayout()
        
        self.save_all_button = QPushButton("Save All")
        self.save_all_button.clicked.connect(self.save_all_parameters)
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        
        button_layout.addStretch()
        button_layout.addWidget(self.save_all_button)
        button_layout.addWidget(self.close_button)
        
        self.main_layout.addLayout(button_layout)
    
    def create_parameter_tabs(self):
        """Create tabs for each parameter type."""
        # Main PTV parameters
        ptv_params = self.parameters.get("PtvParams")
        if ptv_params:
            ptv_tab = QWidget()
            ptv_layout = QVBoxLayout(ptv_tab)
            ptv_dialog = PtvParamsDialog(ptv_params)
            ptv_layout.addWidget(ptv_dialog.form_widget)
            self.tab_widget.addTab(ptv_tab, "PTV")
            ptv_dialog.form_widget.setParent(ptv_tab)
        
        # Tracking parameters
        tracking_params = self.parameters.get("TrackingParams")
        if tracking_params:
            tracking_tab = QWidget()
            tracking_layout = QVBoxLayout(tracking_tab)
            tracking_dialog = TrackingParamsDialog(tracking_params)
            tracking_layout.addWidget(tracking_dialog.form_widget)
            self.tab_widget.addTab(tracking_tab, "Tracking")
            tracking_dialog.form_widget.setParent(tracking_tab)
        
        # Sequence parameters
        seq_params = self.parameters.get("SequenceParams")
        if seq_params:
            seq_tab = QWidget()
            seq_layout = QVBoxLayout(seq_tab)
            seq_dialog = SequenceParamsDialog(seq_params)
            seq_layout.addWidget(seq_dialog.form_widget)
            self.tab_widget.addTab(seq_tab, "Sequence")
            seq_dialog.form_widget.setParent(seq_tab)
        
        # Criteria parameters
        criteria_params = self.parameters.get("CriteriaParams")
        if criteria_params:
            criteria_tab = QWidget()
            criteria_layout = QVBoxLayout(criteria_tab)
            criteria_dialog = CriteriaParamsDialog(criteria_params)
            criteria_layout.addWidget(criteria_dialog.form_widget)
            self.tab_widget.addTab(criteria_tab, "Criteria")
            criteria_dialog.form_widget.setParent(criteria_tab)
    
    def save_all_parameters(self):
        """Save all parameters."""
        try:
            self.param_manager.save_all(self.parameters)
            self.param_manager.save_all_legacy(self.parameters)
            QMessageBox.information(self, "Parameters Saved", 
                                  "All parameters have been saved successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error Saving Parameters", 
                               f"An error occurred while saving parameters: {e}")


def show_parameter_dialog(path: Union[str, Path] = "parameters", parent=None) -> None:
    """Show the parameter dialog.
    
    Args:
        path: Path to parameters directory
        parent: Parent widget
    """
    param_manager = ParameterManager(path)
    dialog = ParameterTabDialog(param_manager, parent)
    dialog.exec_()