import sys
import numpy as np
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QCheckBox, QDockWidget, QPushButton, QFileDialog
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QPainter, QColor, QImageReader

class ImagePlotWidget(QWidget):
    def __init__(self, image_path=None, points=None, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.points = points if points is not None else []
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.label = QLabel(self)
        if self.image_path:
            self.pixmap = self.load_and_resize_image(self.image_path)
            self.label.setPixmap(self.pixmap)
        layout.addWidget(self.label)
        self.setLayout(layout)

    def load_and_resize_image(self, image_path):
        reader = QImageReader(image_path)
        reader.setAutoTransform(True)
        image = reader.read()
        screen_rect = QApplication.primaryScreen().availableGeometry()
        screen_width, screen_height = screen_rect.width(), screen_rect.height()
        image = image.scaled(screen_width, screen_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        return QPixmap.fromImage(image)

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.image_path:
            painter.drawPixmap(0, 0, self.pixmap)
        painter.setPen(QColor(255, 0, 0))
        for point in self.points:
            painter.drawEllipse(point[0], point[1], 5, 5)

    def update_image(self, image_path):
        self.image_path = image_path
        self.pixmap = self.load_and_resize_image(image_path)
        self.label.setPixmap(self.pixmap)
        self.update()

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
            self.main_window.image_plot_widget.update_image(self.main_window.image_path)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.image_path = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Simple Image Plot GUI')

        # Main area
        self.image_plot_widget = ImagePlotWidget()
        self.setCentralWidget(self.image_plot_widget)

        # Floating control window
        self.control_window = ControlWindow(self)
        self.dock_widget = QDockWidget("Controls", self)
        self.dock_widget.setWidget(self.control_window)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_widget)

    def update_plot(self):
        # Update points or other parameters based on slider and checkbox
        if self.control_window.checkbox.isChecked():
            self.image_plot_widget.points = [(50, 50), (100, 100), (150, 150)]  # Example points
        else:
            self.image_plot_widget.points = []
        self.image_plot_widget.update()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())