#!/usr/bin/env python3
"""
Demo script for PyPTV TTK GUI with matplotlib integration
This demonstrates the complete replacement of Chaco/Enable/Traits with Tkinter+matplotlib
"""

import sys
import os
sys.path.insert(0, 'pyptv')

import numpy as np
import tkinter as tk
from pyptv.pyptv_gui_ttk import EnhancedMainApp

def create_demo_images():
    """Create demo images with different patterns for each camera"""
    images = []
    
    # Camera 1: Gradient pattern
    img1 = np.zeros((240, 320), dtype=np.uint8)
    for i in range(240):
        img1[i, :] = int(255 * i / 240)
    images.append(img1)
    
    # Camera 2: Circular pattern  
    img2 = np.zeros((240, 320), dtype=np.uint8)
    y, x = np.ogrid[:240, :320]
    center_y, center_x = 120, 160
    mask = (x - center_x)**2 + (y - center_y)**2 < 80**2
    img2[mask] = 255
    images.append(img2)
    
    # Camera 3: Grid pattern
    img3 = np.zeros((240, 320), dtype=np.uint8)
    img3[::20, :] = 128  # Horizontal lines
    img3[:, ::20] = 128  # Vertical lines
    images.append(img3)
    
    # Camera 4: Random particles
    img4 = np.zeros((240, 320), dtype=np.uint8)
    np.random.seed(42)
    for _ in range(50):
        x = np.random.randint(10, 310)
        y = np.random.randint(10, 230)
        img4[y-2:y+3, x-2:x+3] = 255
    images.append(img4)
    
    return images

def demo_matplotlib_features(app):
    """Demonstrate matplotlib features in the GUI"""
    print("\n=== PyPTV TTK + Matplotlib Demo ===")
    print("Features demonstrated:")
    print("  ✓ Matplotlib-based image display")
    print("  ✓ Interactive zoom and pan")
    print("  ✓ Click event handling")
    print("  ✓ Overlay drawing (crosses, trajectories)")
    print("  ✓ Quiver plots for velocity vectors")
    print("  ✓ Complete replacement of Chaco/Enable/Traits")
    
    # Load test images
    app.load_test_images()
    
    # Add some demo overlays
    if len(app.cameras) > 0:
        cam = app.cameras[0]
        
        # Add some crosses
        x_data = [50, 100, 150, 200]
        y_data = [60, 120, 180, 100]
        cam.drawcross('demo', 'points', x_data, y_data, color='red', size=5)
        
        # Add quiver plot if we have enough cameras
        if len(app.cameras) > 1:
            cam2 = app.cameras[1]
            x_pos = np.array([80, 120, 160, 200])
            y_pos = np.array([80, 120, 160, 200])
            u_vel = np.array([10, -5, 8, -12])
            v_vel = np.array([5, 10, -8, 6])
            cam2.draw_quiver(x_pos, y_pos, u_vel, v_vel, color='blue', scale=50)
    
    print("\nDemo overlays added:")
    print("  ✓ Red crosses on Camera 1")
    print("  ✓ Blue velocity vectors on Camera 2")
    print("\nGUI Features:")
    print("  • Use 'Images' menu to load test images or files")
    print("  • Click on images to add crosshairs")
    print("  • Use zoom controls or mouse wheel")
    print("  • Right-click for context menus")
    print("  • All functionality works without Chaco/Enable/Traits!")

def main():
    """Main demo function"""
    print("PyPTV TTK + Matplotlib GUI Demo")
    print("================================")
    print("This demo shows the complete replacement of:")
    print("  - Chaco plotting → matplotlib")
    print("  - Enable interaction → matplotlib events")
    print("  - Traits GUI → TTK widgets")
    print("  - TraitsUI dialogs → TTK dialogs")
    
    try:
        root = tk.Tk()
        root.title("PyPTV - TTK + Matplotlib GUI")
        
        # Create the enhanced main application
        app = EnhancedMainApp(root)
        
        # Run demo features
        root.after(1000, lambda: demo_matplotlib_features(app))
        
        print("\nStarting GUI...")
        print("Close the window to exit the demo.")
        
        # Start the GUI
        root.mainloop()
        
    except Exception as e:
        print(f"Error running demo: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()