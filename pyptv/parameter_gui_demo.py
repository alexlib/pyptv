import sys
import os
import json
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFormLayout, QDialog, QDialogButtonBox
)
from PySide6.QtCore import Qt

class ParameterDialog(QDialog):
    def __init__(self, par_path, parent=None):
        super().__init__(parent)
        self.par_path = par_path
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Edit Calibration Parameters')
        layout = QVBoxLayout()

        form_layout = QFormLayout()

        self.focal_length = QLineEdit()
        self.sensor_width = QLineEdit()
        self.sensor_height = QLineEdit()
        self.iso = QLineEdit()
        self.exposure_time = QLineEdit()

        form_layout.addRow('Focal Length (mm):', self.focal_length)
        form_layout.addRow('Sensor Width (mm):', self.sensor_width)
        form_layout.addRow('Sensor Height (mm):', self.sensor_height)
        form_layout.addRow('ISO:', self.iso)
        form_layout.addRow('Exposure Time (s):', self.exposure_time)

        layout.addLayout(form_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def load_parameters(self):
        # Load parameters from file
        with open(self.par_path / 'parameters.yaml', 'r') as f:
            params = json.load(f)
            self.focal_length.setText(str(params.get('focal_length', '')))
            self.sensor_width.setText(str(params.get('sensor_width', '')))
            self.sensor_height.setText(str(params.get('sensor_height', '')))
            self.iso.setText(str(params.get('iso', '')))
            self.exposure_time.setText(str(params.get('exposure_time', '')))

    def save_parameters(self):
        # Save parameters to file
        params = {
            'focal_length': float(self.focal_length.text()),
            'sensor_width': float(self.sensor_width.text()),
            'sensor_height': float(self.sensor_height.text()),
            'iso': int(self.iso.text()),
            'exposure_time': float(self.exposure_time.text())
        }
        with open(self.par_path / 'parameters.yaml', 'w') as f:
            json.dump(params, f, indent=4)

class MainWindow(QMainWindow):
    def __init__(self, par_path):
        super().__init__()
        self.par_path = par_path
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Parameter GUI')
        self.setGeometry(100, 100, 400, 300)

        self.parameter_dialog = ParameterDialog(self.par_path, self)
        self.parameter_dialog.load_parameters()

        main_layout = QVBoxLayout()

        edit_button = QPushButton('Edit Parameters')
        edit_button.clicked.connect(self.edit_parameters)
        main_layout.addWidget(edit_button)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def edit_parameters(self):
        if self.parameter_dialog.exec():
            self.parameter_dialog.save_parameters()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    par_path = Path('.')  # Update with the actual path
    main_window = MainWindow(par_path)
    main_window.show()
    sys.exit(app.exec())