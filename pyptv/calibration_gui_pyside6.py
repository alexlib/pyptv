import sys
import numpy as np
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTabWidget, QStatusBar, QDialog
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QPainter, QColor
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from pyptv import ptv
import pyptv.parameters as par

class CalibrationParametersDialog(QDialog):
    def __init__(self, par_path, parent=None):
        super().__init__(parent)
        self.par_path = par_path
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Edit Calibration Parameters')
        layout = QVBoxLayout()

        self.label = QLabel(f'Editing parameters in: {self.par_path}')
        layout.addWidget(self.label)

        self.save_button = QPushButton('Save')
        self.save_button.clicked.connect(self.accept)
        layout.addWidget(self.save_button)

        self.setLayout(layout)

class PlotWindow(QWidget):
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.canvas = FigureCanvas(Figure())
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        self.ax = self.canvas.figure.subplots()
        self.canvas.mpl_connect('button_press_event', self.on_click)
        self.canvas.mpl_connect('scroll_event', self.on_scroll)

    def on_click(self, event):
        if event.inaxes:
            x, y = event.xdata, event.ydata
            print(f"Clicked at: ({x}, {y})")
            self.ax.plot(x, y, 'ro')
            self.canvas.draw()

    def on_scroll(self, event):
        if event.inaxes:
            scale_factor = 1.1 if event.button == 'up' else 0.9
            self.ax.set_xlim([event.xdata - (event.xdata - self.ax.get_xlim()[0]) * scale_factor,
                              event.xdata + (self.ax.get_xlim()[1] - event.xdata) * scale_factor])
            self.ax.set_ylim([event.ydata - (event.ydata - self.ax.get_ylim()[0]) * scale_factor,
                              event.ydata + (self.ax.get_ylim()[1] - event.ydata) * scale_factor])
            self.canvas.draw()

    def draw_image(self, image, is_float):
        self.ax.clear()
        if is_float:
            self.ax.imshow(image, cmap='gray', origin='upper')
        else:
            self.ax.imshow(image.astype(np.uint8), cmap='gray', origin='upper')
        self.canvas.draw()

class CalibrationGUI(QMainWindow):
    def __init__(self, active_path: Path):
        super().__init__()
        self.active_path = active_path
        self.par_path = self.active_path / "parameters"
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Calibration GUI')
        self.setGeometry(100, 100, 1200, 800)

        # Main layout
        main_layout = QHBoxLayout()

        # Sidebar layout
        sidebar_layout = QVBoxLayout()

        # Add buttons to the sidebar
        self.button_showimg = QPushButton('Load/Show Images')
        self.button_detection = QPushButton('Detection')
        self.button_manual = QPushButton('Manual orient.')
        self.button_file_orient = QPushButton('Orient. with file')
        self.button_init_guess = QPushButton('Show initial guess')
        self.button_sort_grid = QPushButton('Sortgrid')
        self.button_raw_orient = QPushButton('Raw orientation')
        self.button_fine_orient = QPushButton('Fine tuning')
        self.button_orient_part = QPushButton('Orientation with particles')
        self.button_orient_dumbbell = QPushButton('Orientation from dumbbell')
        self.button_restore_orient = QPushButton('Restore ori files')
        self.button_checkpoint = QPushButton('Checkpoints')
        self.button_ap_figures = QPushButton('Ap figures')
        self.button_edit_cal_parameters = QPushButton('Edit calibration parameters')
        self.button_edit_ori_files = QPushButton('Edit ori files')
        self.button_edit_addpar_files = QPushButton('Edit addpar files')

        # Connect buttons to functions
        self.button_showimg.clicked.connect(self._button_showimg_fired)
        self.button_detection.clicked.connect(self._button_detection_fired)
        self.button_manual.clicked.connect(self._button_manual_fired)
        self.button_file_orient.clicked.connect(self._button_file_orient_fired)
        self.button_init_guess.clicked.connect(self._button_init_guess_fired)
        self.button_sort_grid.clicked.connect(self._button_sort_grid_fired)
        self.button_raw_orient.clicked.connect(self._button_raw_orient_fired)
        self.button_fine_orient.clicked.connect(self._button_fine_orient_fired)
        self.button_orient_part.clicked.connect(self._button_orient_part_fired)
        self.button_orient_dumbbell.clicked.connect(self._button_orient_dumbbell_fired)
        self.button_restore_orient.clicked.connect(self._button_restore_orient_fired)
        self.button_checkpoint.clicked.connect(self._button_checkpoint_fired)
        self.button_ap_figures.clicked.connect(self._button_ap_figures_fired)
        self.button_edit_cal_parameters.clicked.connect(self._button_edit_cal_parameters_fired)
        self.button_edit_ori_files.clicked.connect(self._button_edit_ori_files_fired)
        self.button_edit_addpar_files.clicked.connect(self._button_edit_addpar_files_fired)

        # Add buttons to the sidebar layout
        sidebar_layout.addWidget(self.button_showimg)
        sidebar_layout.addWidget(self.button_detection)
        sidebar_layout.addWidget(self.button_manual)
        sidebar_layout.addWidget(self.button_file_orient)
        sidebar_layout.addWidget(self.button_init_guess)
        sidebar_layout.addWidget(self.button_sort_grid)
        sidebar_layout.addWidget(self.button_raw_orient)
        sidebar_layout.addWidget(self.button_fine_orient)
        sidebar_layout.addWidget(self.button_orient_part)
        sidebar_layout.addWidget(self.button_orient_dumbbell)
        sidebar_layout.addWidget(self.button_restore_orient)
        sidebar_layout.addWidget(self.button_checkpoint)
        sidebar_layout.addWidget(self.button_ap_figures)
        sidebar_layout.addWidget(self.button_edit_cal_parameters)
        sidebar_layout.addWidget(self.button_edit_ori_files)
        sidebar_layout.addWidget(self.button_edit_addpar_files)

        # Add stretch to push buttons to the top
        sidebar_layout.addStretch()

        # Create a tab widget for the camera views
        self.tab_widget = QTabWidget()
        self.camera = [PlotWindow(f"Camera {i + 1}") for i in range(4)]  # Example with 4 cameras
        for cam in self.camera:
            self.tab_widget.addTab(cam, cam.name)

        # Add sidebar and tab widget to the main layout
        main_layout.addLayout(sidebar_layout)
        main_layout.addWidget(self.tab_widget)

        # Create a central widget and set the main layout
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

    def _button_edit_cal_parameters_fired(self):
        dialog = CalibrationParametersDialog(self.par_path, self)
        if dialog.exec():
            # At the end of a modification, copy the parameters
            par.copy_params_dir(self.par_path, self.active_path)
            (
                self.cpar,
                self.spar,
                self.vpar,
                self.track_par,
                self.tpar,
                self.cals,
                self.epar,
            ) = ptv.py_start_proc_c(self.n_cams)

    def _button_showimg_fired(self):
        print("Loading images/parameters \n")
        # Initialize what is needed, copy necessary things
        print("\n Copying man_ori.dat \n")

    def _button_detection_fired(self):
        print("Detection button clicked")

    def _button_manual_fired(self):
        print("Manual orient. button clicked")

    def _button_file_orient_fired(self):
        print("Orient. with file button clicked")

    def _button_init_guess_fired(self):
        print("Show initial guess button clicked")

    def _button_sort_grid_fired(self):
        print("Sortgrid button clicked")

    def _button_raw_orient_fired(self):
        print("Raw orientation button clicked")

    def _button_fine_orient_fired(self):
        print("Fine tuning button clicked")

    def _button_orient_part_fired(self):
        print("Orientation with particles button clicked")

    def _button_orient_dumbbell_fired(self):
        print("Orientation from dumbbell button clicked")

    def _button_restore_orient_fired(self):
        print("Restore ori files button clicked")

    def _button_checkpoint_fired(self):
        print("Checkpoints button clicked")

    def _button_ap_figures_fired(self):
        print("Ap figures button clicked")

    def _button_edit_ori_files_fired(self):
        print("Edit ori files button clicked")

    def _button_edit_addpar_files_fired(self):
        print("Edit addpar files button clicked")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    active_path = Path('/path/to/active')  # Update with the actual path
    main_window = CalibrationGUI(active_path)
    main_window.show()
    sys.exit(app.exec())