#!/bin/bash
# Script to run pyptv with OpenGL workarounds

# Activate conda environment
source $(conda info --base)/etc/profile.d/conda.sh
conda activate pyptv

# Set environment variables to work around OpenGL issues
export LIBGL_ALWAYS_SOFTWARE=1
export QT_XCB_GL_INTEGRATION=none
export QT_QPA_PLATFORM=xcb

# Run pyptv with the test_cavity data
echo "Running pyptv with OpenGL workarounds..."
pyptv tests/test_cavity

# If pyptv exits with an error, try with different settings
if [ $? -ne 0 ]; then
    echo "First attempt failed, trying with different settings..."
    unset QT_XCB_GL_INTEGRATION
    export QT_QPA_PLATFORM=offscreen
    pyptv test_cavity
fi
