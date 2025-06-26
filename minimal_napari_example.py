"""
Minimal napari example with custom widget on the right
"""

import napari
import numpy as np
from qtpy.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QSlider, QMenu, QAction
from qtpy.QtCore import Qt


def create_custom_widget(viewer):
    """Create a custom control widget"""
    widget = QWidget()
    layout = QVBoxLayout(widget)
    
    # Title
    title = QLabel("Custom Controls")
    title.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")
    layout.addWidget(title)
    
    # Load image button
    load_btn = QPushButton("Load Sample Image")
    layout.addWidget(load_btn)
    
    # Contrast slider
    layout.addWidget(QLabel("Contrast:"))
    contrast_slider = QSlider(Qt.Horizontal)
    contrast_slider.setRange(1, 100)
    contrast_slider.setValue(50)
    contrast_label = QLabel("50")
    layout.addWidget(contrast_slider)
    layout.addWidget(contrast_label)
    
    # Brightness slider
    layout.addWidget(QLabel("Brightness:"))
    brightness_slider = QSlider(Qt.Horizontal)
    brightness_slider.setRange(-50, 50)
    brightness_slider.setValue(0)
    brightness_label = QLabel("0")
    layout.addWidget(brightness_slider)
    layout.addWidget(brightness_label)
    
    # Connect functions
    def load_image():
        # Create sample image
        img = np.random.random((512, 512)) * 255
        if len(viewer.layers) > 0:
            viewer.layers.clear()
        viewer.add_image(img, name="Sample")
    
    def update_contrast(value):
        contrast_label.setText(str(value))
        if viewer.layers:
            layer = viewer.layers[0] 
            current_limits = layer.contrast_limits
            layer.contrast_limits = (current_limits[0], value * 5)
    
    def update_brightness(value):
        brightness_label.setText(str(value))
        if viewer.layers:
            layer = viewer.layers[0]
            current_limits = layer.contrast_limits
            layer.contrast_limits = (value, current_limits[1])
    
    load_btn.clicked.connect(load_image)
    contrast_slider.valueChanged.connect(update_contrast)
    brightness_slider.valueChanged.connect(update_brightness)
    
    # Add some spacing
    layout.addStretch()
    
    return widget


def main():
    """Main function"""
    # Create napari viewer
    viewer = napari.Viewer(title="Minimal Napari Example")
    
    # Hide default left-side widgets using proper napari API
    viewer.window.qt_viewer.dockLayerList.setVisible(False)
    viewer.window.qt_viewer.dockLayerControls.setVisible(False)
    
    # Console remains visible at bottom by default
    
    # Create and add custom widget
    custom_widget = create_custom_widget(viewer)
    viewer.window.add_dock_widget(
        custom_widget, 
        area='right', 
        name='Controls'
    )
    
    # Add custom menu to the top menu bar
    menu_bar = viewer.window._qt_window.menuBar()
    custom_menu = QMenu("Custom Tools", parent=viewer.window._qt_window)
    
    # Add some actions to the custom menu
    action1 = QAction("Reset View", parent=viewer.window._qt_window)
    action1.triggered.connect(lambda: viewer.reset_view())
    custom_menu.addAction(action1)
    
    action2 = QAction("Toggle Full Screen", parent=viewer.window._qt_window)
    action2.triggered.connect(lambda: viewer.window._qt_window.setWindowState(
        viewer.window._qt_window.windowState() ^ Qt.WindowFullScreen))
    custom_menu.addAction(action2)
    
    action3 = QAction("About", parent=viewer.window._qt_window)
    action3.triggered.connect(lambda: print("Custom Napari Application"))
    custom_menu.addAction(action3)
    
    # Add the menu to the menu bar
    menu_bar.addMenu(custom_menu)
    
    # Load initial image
    sample_img = np.random.random((256, 256)) * 100
    viewer.add_image(sample_img, name="Initial Image")
    
    # Start napari
    napari.run()


if __name__ == "__main__":
    main()


