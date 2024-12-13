import sys
import numpy as np
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from PySide6.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class QuiverPlotWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.canvas = FigureCanvas(Figure())
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        self.ax = self.canvas.figure.subplots()

    def plot_quiver(self, x, y, u, v, color='blue'):
        self.ax.clear()
        self.ax.quiver(x, y, u, v, color=color)
        self.canvas.draw()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Quiver Plot Example')
        self.setGeometry(100, 100, 800, 600)

        self.quiver_plot_widget = QuiverPlotWidget()
        self.setCentralWidget(self.quiver_plot_widget)

        # Example data
        x = np.array([0, 1, 2, 3])
        y = np.array([0, 1, 2, 3])
        u = np.array([1, 0, -1, 0])
        v = np.array([0, 1, 0, -1])

        self.quiver_plot_widget.plot_quiver(x, y, u, v)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())