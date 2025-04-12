#!/bin/bash
# Script to fix OpenGL driver issues for pyptv

set -e  # Exit on error

echo "=== Installing Mesa OpenGL libraries and drivers ==="

# Install Mesa OpenGL libraries and drivers
sudo apt-get update
sudo apt-get install -y \
    libgl1-mesa-glx \
    libgl1-mesa-dri \
    mesa-utils \
    mesa-utils-extra \
    libglx-mesa0 \
    libegl-mesa0 \
    libglu1-mesa

echo ""
echo "=== Installation complete! ==="
echo "Try running pyptv again. If you still encounter OpenGL errors, you may need to:"
echo "1. Update your graphics drivers"
echo "2. Set the QT_XCB_GL_INTEGRATION environment variable: export QT_XCB_GL_INTEGRATION=none"
echo "3. Or try running with software rendering: export LIBGL_ALWAYS_SOFTWARE=1"
