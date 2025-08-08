#!/usr/bin/env python3
"""
Demo script showing PyPTV TTK GUI capabilities
Run this to see how the TTK version achieves feature parity with Traits
"""

import sys
import os
sys.path.insert(0, 'pyptv')

import numpy as np
from pyptv.pyptv_gui_ttk import EnhancedMainApp
import tkinter as tk

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
    
    # Camera 5: Diagonal stripes
    img5 = np.zeros((240, 320), dtype=np.uint8)
    for i in range(240):
        for j in range(320):
            if (i + j) % 40 < 20:
                img5[i, j] = 200
    images.append(img5)
    
    # Camera 6: Concentric circles
    img6 = np.zeros((240, 320), dtype=np.uint8)
    y, x = np.ogrid[:240, :320]
    center_y, center_x = 120, 160
    for radius in [20, 40, 60, 80]:
        mask = np.abs(np.sqrt((x - center_x)**2 + (y - center_y)**2) - radius) < 2
        img6[mask] = 255
    images.append(img6)
    
    return images

def demo_dynamic_cameras():
    """Demonstrate dynamic camera management"""
    print("=== PyPTV TTK GUI Feature Demonstration ===\n")
    
    print("✓ DYNAMIC CAMERA PANELS:")
    print("  - Can create 1-16 cameras dynamically")
    print("  - Automatic grid layout optimization")
    print("  - Runtime camera count changes")
    print("  - Each camera has independent zoom/pan")
    
    print("\n✓ LAYOUT MODES:")
    print("  - Tabs: Each camera in separate tab")
    print("  - Grid: All cameras in optimized grid")
    print("  - Single: One camera with navigation")
    
    print("\n✓ SCIENTIFIC IMAGE DISPLAY:")
    print("  - Matplotlib backend (like Chaco)")
    print("  - Zoom/pan with mouse wheel and buttons")
    print("  - Pixel coordinate and value display")
    print("  - Overlay drawing capabilities")
    
    print("\n✓ INTERACTIVE FEATURES:")
    print("  - Left/right click event handling")
    print("  - Context menus on tree items")
    print("  - Parameter editing dialogs")
    print("  - Keyboard shortcuts (Ctrl+1-9 for cameras)")
    
    print("\n✓ EXPERIMENT MANAGEMENT:")
    print("  - Tree view with experiments/parameters")
    print("  - YAML file loading/saving")
    print("  - Parameter set management")
    print("  - Context-sensitive menus")
    
    print("\n✓ ADVANTAGES OVER TRAITS VERSION:")
    print("  - No heavy dependencies (just tkinter + matplotlib)")
    print("  - Faster startup and operation")
    print("  - Better cross-platform compatibility")
    print("  - Modern themes with ttkbootstrap")
    print("  - More granular control over UI behavior")
    print("  - Easier deployment (fewer dependencies)")
    
    # Create the app with 6 cameras
    app = EnhancedMainApp(num_cameras=6)
    
    # Load demo images after a short delay
    def load_demo_images():
        images = create_demo_images()
        for i, img in enumerate(images):
            if i < len(app.cameras):
                app.update_camera_image(i, img)
        app.status_var.set(f"Loaded demo images into {len(images)} cameras")
    
    # Schedule image loading
    app.after(1000, load_demo_images)
    
    print(f"\nStarting GUI with {app.num_cameras} cameras...")
    print("Try these features:")
    print("- Right-click on tree items for context menus")
    print("- Use View menu to change layouts and camera counts")
    print("- Click on images to see coordinates")
    print("- Use zoom controls and mouse wheel")
    print("- Press Ctrl+1, Ctrl+2, etc. to focus cameras")
    
    app.mainloop()

if __name__ == '__main__':
    demo_dynamic_cameras()
