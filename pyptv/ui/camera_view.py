"""Camera view component for the PyPTV UI."""

import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.patches import Circle
import matplotlib.pyplot as plt

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QHBoxLayout,
    QToolBar,
    QSizePolicy
)


class MatplotlibCanvas(FigureCanvasQTAgg):
    """Canvas for displaying images and overlays using matplotlib."""
    
    # Signals for mouse events
    clicked = Signal(float, float, int)  # x, y, button
    
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        """Initialize the canvas.
        
        Args:
            parent: Parent widget
            width: Figure width in inches
            height: Figure height in inches
            dpi: Dots per inch
        """
        self.figure = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.figure.add_subplot(111)
        
        # Configure the axes for image display
        self.axes.set_aspect('equal')
        self.axes.set_axis_off()
        
        super(MatplotlibCanvas, self).__init__(self.figure)
        self.setParent(parent)
        
        # Enable mouse click handling
        self.mpl_connect('button_press_event', self._on_click)
        
        # For storing image and overlay elements
        self.image = None
        self.overlay_elements = []
        
        # Set size policy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.updateGeometry()
        
    def _on_click(self, event):
        """Handle mouse click events.
        
        Args:
            event: Matplotlib event object
        """
        if event.xdata is not None and event.ydata is not None:
            # Emit signal with coordinates and button
            self.clicked.emit(event.xdata, event.ydata, event.button)
    
    def display_image(self, image_data):
        """Display an image on the canvas.
        
        Args:
            image_data: Numpy array containing image data
        """
        self.axes.clear()
        self.image = self.axes.imshow(image_data, cmap='gray', interpolation='nearest')
        self.figure.tight_layout()
        self.draw()
    
    def add_points(self, x, y, color='r', size=5, marker='o'):
        """Add points to the overlay.
        
        Args:
            x: X coordinates (array or single value)
            y: Y coordinates (array or single value)
            color: Point color
            size: Point size
            marker: Point marker style
        """
        if not hasattr(x, '__iter__'):
            x = [x]
            y = [y]
            
        scatter = self.axes.scatter(x, y, c=color, s=size, marker=marker, zorder=10)
        self.overlay_elements.append(scatter)
        self.draw()
        
        return scatter
    
    def add_line(self, x0, y0, x1, y1, color='g', linewidth=1):
        """Add a line to the overlay.
        
        Args:
            x0: Starting x coordinate
            y0: Starting y coordinate
            x1: Ending x coordinate
            y1: Ending y coordinate
            color: Line color
            linewidth: Line width
        """
        line = self.axes.plot([x0, x1], [y0, y1], color=color, linewidth=linewidth, zorder=5)[0]
        self.overlay_elements.append(line)
        self.draw()
        
        return line
    
    def add_epipolar_line(self, points, color='cyan', linewidth=1):
        """Add an epipolar line to the overlay.
        
        Args:
            points: Array of (x,y) coordinates defining the epipolar curve
            color: Line color
            linewidth: Line width
        """
        x = [p[0] for p in points]
        y = [p[1] for p in points]
        
        line = self.axes.plot(x, y, color=color, linewidth=linewidth, zorder=5)[0]
        self.overlay_elements.append(line)
        self.draw()
        
        return line
    
    def clear_overlays(self):
        """Clear all overlay elements."""
        for element in self.overlay_elements:
            element.remove()
        
        self.overlay_elements = []
        self.draw()


class CameraView(QWidget):
    """Widget for displaying and interacting with camera images."""
    
    # Signals
    point_clicked = Signal(str, float, float, int)  # camera_name, x, y, button
    
    def __init__(self, name="Camera"):
        """Initialize the camera view.
        
        Args:
            name: Camera name
        """
        super().__init__()
        
        self.name = name
        self.image_data = None
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Add header with camera name
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(5, 5, 5, 0)
        
        self.name_label = QLabel(name)
        self.name_label.setStyleSheet("font-weight: bold;")
        header_layout.addWidget(self.name_label)
        
        header_layout.addStretch()
        
        self.info_label = QLabel("")
        header_layout.addWidget(self.info_label)
        
        layout.addLayout(header_layout)
        
        # Add toolbar for camera-specific actions
        self.toolbar = QToolBar()
        self.toolbar.setIconSize(Qt.QSize(16, 16))
        layout.addWidget(self.toolbar)
        
        # Add matplotlib canvas
        self.canvas = MatplotlibCanvas(self)
        self.canvas.clicked.connect(self._on_canvas_clicked)
        layout.addWidget(self.canvas)
        
        # Add status bar
        self.status_bar = QLabel("Ready")
        self.status_bar.setStyleSheet("padding: 2px; background-color: #f0f0f0;")
        layout.addWidget(self.status_bar)
        
        # Set placeholder image
        self._create_placeholder_image()
    
    def _create_placeholder_image(self):
        """Create a placeholder image when no image is loaded."""
        # Create a gray placeholder image
        placeholder = np.ones((480, 640), dtype=np.uint8) * 200
        
        # Add text saying "No Image"
        for i in range(150, 350):
            for j in range(250, 450):
                placeholder[i, j] = 150
                
        self.set_image(placeholder)
    
    def set_image(self, image_data):
        """Set the image to display.
        
        Args:
            image_data: Numpy array containing image data
        """
        if image_data is None:
            # Create an empty image if None is provided
            image_data = np.zeros((480, 640), dtype=np.uint8)
            self.status_bar.setText("No image data provided")
            
        try:
            # Ensure image is a proper 2D array
            if not isinstance(image_data, np.ndarray):
                self.status_bar.setText("Invalid image format")
                image_data = np.zeros((480, 640), dtype=np.uint8)
            elif len(image_data.shape) > 2 and image_data.shape[2] > 1:
                # Convert color image to grayscale if needed
                from skimage.color import rgb2gray
                from skimage.util import img_as_ubyte
                image_data = img_as_ubyte(rgb2gray(image_data))
                self.status_bar.setText("Converted color image to grayscale")
            
            self.image_data = image_data
            self.canvas.display_image(image_data)
            
            # Update information
            h, w = image_data.shape[:2]
            self.info_label.setText(f"{w}x{h}")
            
        except Exception as e:
            self.status_bar.setText(f"Error displaying image: {e}")
            # Use placeholder if there's an error
            self.image_data = np.zeros((480, 640), dtype=np.uint8)
            self.canvas.display_image(self.image_data)
            self.info_label.setText("640x480")
    
    def _on_canvas_clicked(self, x, y, button):
        """Handle canvas click events.
        
        Args:
            x: X coordinate
            y: Y coordinate
            button: Mouse button
        """
        if self.image_data is not None:
            # Get image value at click position (if within bounds)
            h, w = self.image_data.shape[:2]
            if 0 <= int(y) < h and 0 <= int(x) < w:
                value = self.image_data[int(y), int(x)]
                self.status_bar.setText(f"Position: ({int(x)}, {int(y)}) Value: {value}")
            
            # Emit signal with camera name and coordinates
            self.point_clicked.emit(self.name, x, y, button)
    
    def add_points(self, x, y, color='r', size=5, marker='o'):
        """Add points to the overlay.
        
        Args:
            x: X coordinates (array or single value)
            y: Y coordinates (array or single value)
            color: Point color
            size: Point size
            marker: Point marker style
        """
        return self.canvas.add_points(x, y, color, size, marker)
    
    def add_line(self, x0, y0, x1, y1, color='g', linewidth=1):
        """Add a line to the overlay.
        
        Args:
            x0: Starting x coordinate
            y0: Starting y coordinate
            x1: Ending x coordinate
            y1: Ending y coordinate
            color: Line color
            linewidth: Line width
        """
        return self.canvas.add_line(x0, y0, x1, y1, color, linewidth)
    
    def add_epipolar_line(self, points, color='cyan', linewidth=1):
        """Add an epipolar line to the overlay.
        
        Args:
            points: Array of (x,y) coordinates defining the epipolar curve
            color: Line color
            linewidth: Line width
        """
        return self.canvas.add_epipolar_line(points, color, linewidth)
    
    def clear_overlays(self):
        """Clear all overlay elements."""
        self.canvas.clear_overlays()