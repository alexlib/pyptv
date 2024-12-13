import sys
import numpy as np
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QCheckBox, QPushButton, QFileDialog
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QPainter, QColor
from PySide6.QtGui import QMouseEvent, QPainter, QColor, QPixmap
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTabWidget, QStatusBar

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure




class ImagePlotWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.image_path = None
        self.points = []
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.label = QLabel(self)
        layout.addWidget(self.label)
        self.setLayout(layout)

    def load_image(self, image_path):
        self.image_path = image_path
        pixmap = QPixmap(image_path)
        self.label.setPixmap(pixmap)
        self.update()

    def set_points(self, points):
        self.points = points
        self.update()

    def paintEvent(self, event):
        if self.image_path:
            painter = QPainter(self)
            painter.drawPixmap(0, 0, QPixmap(self.image_path))
            painter.setPen(QColor(255, 0, 0))
            for point in self.points:
                painter.drawEllipse(point[0], point[1], 5, 5)

class ControlWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.file_button = QPushButton('Select Image')
        self.file_button.clicked.connect(self.select_image)
        layout.addWidget(self.file_button)

        self.start_button = QPushButton('Start')
        self.start_button.clicked.connect(self.start)
        layout.addWidget(self.start_button)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setValue(50)
        self.slider.valueChanged.connect(self.main_window.update_plot)
        layout.addWidget(self.slider)

        self.checkbox = QCheckBox('Show Points')
        self.checkbox.setChecked(True)
        self.checkbox.stateChanged.connect(self.main_window.update_plot)
        layout.addWidget(self.checkbox)

        self.setLayout(layout)

    def select_image(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Select Image", "", "Images (*.png *.xpm *.jpg *.tif)")
        if file_path:
            self.main_window.image_path = file_path

    def start(self):
        if self.main_window.image_path:
            self.main_window.image_plot_widget.load_image(self.main_window.image_path)

# class MainWindow(QMainWindow):
#     def __init__(self):
#         super().__init__()
#         self.image_path = None
#         self.initUI()

#     def initUI(self):
#         self.setWindowTitle('Simple Image Plot GUI')

#         # Main area
#         self.image_plot_widget = ImagePlotWidget()
#         self.setCentralWidget(self.image_plot_widget)

#         # Floating control window
#         self.control_window = ControlWindow(self)
#         self.control_window.show()

#     def update_plot(self):
#         # Update points or other parameters based on slider and checkbox
#         if self.control_window.checkbox.isChecked():
#             self.image_plot_widget.set_points([(50, 50), (100, 100), (150, 150)])  # Example points
#         else:
#             self.image_plot_widget.set_points([])



class ClickerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.x = 0
        self.y = 0
        self.left_changed = 1
        self.right_changed = 1
        self.last_mouse_position = None
        self.initUI()

    def initUI(self):
        self.setFixedSize(800, 600)
        self.label = QLabel(self)
        self.label.setText("Click on the widget")
        self.label.move(10, 10)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.normal_left_down(event)

    def normal_left_down(self, event: QMouseEvent):
        self.x = event.position().x()
        self.y = event.position().y()
        print(self.x)
        print(self.y)
        self.left_changed = 1 - self.left_changed
        self.last_mouse_position = (self.x, self.y)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(QColor(255, 0, 0))
        painter.drawEllipse(self.x - 5, self.y - 5, 10, 10)

# class MainWindow(QMainWindow):
#     def __init__(self):
#         super().__init__()
#         self.initUI()

#     def initUI(self):
#         self.setWindowTitle('Clicker Tool')
#         self.clicker_widget = ClickerWidget()
#         self.setCentralWidget(self.clicker_widget)

class ClickerTool:
    def __init__(self, plot_widget):
        self.plot_widget = plot_widget
        self.left_changed = 1
        self.right_changed = 1
        self.x = 0
        self.y = 0

    def normal_left_down(self, event):
        self.x = event.xdata
        self.y = event.ydata
        print(self.x, self.y)
        self.left_changed = 1 - self.left_changed
        self.plot_widget.left_clicked_event()

    def normal_right_down(self, event):
        self.x = event.xdata
        self.y = event.ydata
        print(self.x, self.y)
        self.right_changed = 1 - self.right_changed
        self.plot_widget.right_clicked_event()

class PlotWindow(QWidget):
    def __init__(self):
        super().__init__()
        self._x, self._y = [], []
        self.man_ori = [1, 2, 3, 4]
        self._right_click_avail = 0
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.canvas = FigureCanvas(Figure())
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        self.ax = self.canvas.figure.subplots()
        self._click_tool = ClickerTool(self)
        self.canvas.mpl_connect('button_press_event', self.on_click)

    def on_click(self, event):
        if event.button == 1:  # Left click
            self._click_tool.normal_left_down(event)
        elif event.button == 3:  # Right click
            self._click_tool.normal_right_down(event)

    def left_clicked_event(self):
        print("left clicked")
        if len(self._x) < 4:
            self._x.append(self._click_tool.x)
            self._y.append(self._click_tool.y)
        print(self._x, self._y)
        self.drawcross(self._x, self._y, "red", 5)
        self.plot_num_overlay(self._x, self._y, self.man_ori)

    def right_clicked_event(self):
        print("right clicked")
        if len(self._x) > 0:
            self._x.pop()
            self._y.pop()
            print(self._x, self._y)
            self.drawcross(self._x, self._y, "red", 5)
            self.plot_num_overlay(self._x, self._y, self.man_ori)
        else:
            if self._right_click_avail:
                print("deleting point")
                # Implement py_rclick_delete and py_get_pix_N if needed
                # self.py_rclick_delete(self._click_tool.x, self._click_tool.y, self.cameraN)
                # x, y = [], []
                # self.py_get_pix_N(x, y, self.cameraN)
                # self.drawcross(x[0], y[0], "blue", 4)

    def drawcross(self, x, y, color, size):
        self.ax.clear()
        self.ax.scatter(x, y, color=color, s=size)
        self.canvas.draw()

    def plot_num_overlay(self, x, y, txt):
        for i in range(len(x)):
            self.ax.text(x[i], y[i], str(txt[i]), color="white", bbox=dict(facecolor='red', alpha=0.5))
        self.canvas.draw()

    def update_image(self, image, is_float):
        self.ax.clear()
        if is_float:
            self.ax.imshow(image, cmap='gray', origin='upper')
        else:
            self.ax.imshow(image.astype(np.uint8), cmap='gray', origin='upper')
        self.canvas.draw()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Calibration GUI')
        self.plot_window = PlotWindow()
        self.setCentralWidget(self.plot_window)

# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     main_window = MainWindow()
#     main_window.show()
#     sys.exit(app.exec())


class PlotWindow(QWidget):
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.label = QLabel(self.name)
        layout.addWidget(self.label)
        self.setLayout(layout)

class CalibrationGUI(QMainWindow):
    def __init__(self, active_path: Path):
        super().__init__()
        self.active_path = active_path
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

if __name__ == '__main__':

    app = QApplication(sys.argv)
    active_path = Path('../test_cavity')  # Update with the actual path
    main_window = CalibrationGUI(active_path)
    main_window.show()
    sys.exit(app.exec())