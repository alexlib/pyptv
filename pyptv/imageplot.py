import sys
import numpy as np
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class ImagePlotWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.canvas = FigureCanvas(Figure())
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        self.ax = self.canvas.figure.subplots()
        self.canvas.mpl_connect('button_press_event', self.on_click)
        self.canvas.mpl_connect('scroll_event', self.on_scroll)

    def plot_image(self, data, colormap='gray'):
        self.ax.clear()
        self.ax.imshow(data, cmap=colormap, origin='upper')
        self.canvas.draw()

    def on_click(self, event):
        if event.inaxes:
            x, y = event.xdata, event.ydata
            if event.button == 1:  # Left click
                print(f"Left click at: ({x}, {y})")
                self.ax.plot(x, y, 'ro')  # Draw a red circle
            elif event.button == 3:  # Right click
                print(f"Right click at: ({x}, {y})")
                self.ax.plot(x, y, 'bx')  # Draw a blue "X"
            self.canvas.draw()

    def on_scroll(self, event):
        if event.inaxes:
            scale_factor = 1.1 if event.button == 'up' else 0.9
            self.ax.set_xlim([event.xdata - (event.xdata - self.ax.get_xlim()[0]) * scale_factor,
                              event.xdata + (self.ax.get_xlim()[1] - event.xdata) * scale_factor])
            self.ax.set_ylim([event.ydata - (event.ydata - self.ax.get_ylim()[0]) * scale_factor,
                              event.ydata + (self.ax.get_ylim()[1] - event.ydata) * scale_factor])
            self.canvas.draw()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Image Plot Example')
        self.setGeometry(100, 100, 600, 600)

        self.image_plot_widget = ImagePlotWidget()
        self.setCentralWidget(self.image_plot_widget)

        # Example data
        x = np.linspace(-2, 2, 100)
        y = np.linspace(-2, 2, 100)
        X, Y = np.meshgrid(x, y)
        Z = np.exp(-X**2 - Y**2)

        self.image_plot_widget.plot_image(Z, colormap='viridis')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())