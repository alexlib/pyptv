#!/bin/bash
# Setup script for PyPTV development environment
#
# This script:
# 1. Creates a Python 3.11 virtual environment
# 2. Installs pip and necessary dependencies
# 3. Installs pyptv locally in development mode
# 4. Installs optv from PyPI
#
# Usage: ./setup_environment.sh [venv_path]
#
# Example: ./setup_environment.sh ~/venvs/pyptv_env
#

set -e  # Exit on error

# Default virtual environment path
VENV_PATH="venv"

# Override if argument provided
if [ "$1" != "" ]; then
    VENV_PATH="$1"
fi

echo "Setting up PyPTV development environment..."
echo "Virtual environment will be created at: $VENV_PATH"

# Check if Python 3.11 is available
if command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
elif command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    if [[ "$PYTHON_VERSION" == "3.11" ]]; then
        PYTHON_CMD="python3"
    else
        echo "Warning: Python 3.11 is recommended but not found. Using Python $PYTHON_VERSION instead."
        PYTHON_CMD="python3"
    fi
else
    echo "Error: Python 3.11 or Python 3.x not found. Please install Python 3.11."
    exit 1
fi

echo "Using Python: $($PYTHON_CMD --version)"

# Create virtual environment
echo "Creating virtual environment..."
$PYTHON_CMD -m venv "$VENV_PATH"

# Activate virtual environment
echo "Activating virtual environment..."
source "$VENV_PATH/bin/activate"

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install build dependencies
echo "Installing build dependencies..."
pip install setuptools wheel numpy cython

# Install pyptv in development mode
echo "Installing pyptv in development mode..."
pip install -e .

# Install optv from PyPI
echo "Installing optv from PyPI..."
pip install optv

# Verify installations
echo "Verifying installations..."
echo "Installed packages:"
pip list | grep -E 'pyptv|optv|numpy|cython'

echo ""
echo "PyPTV development environment setup complete!"
echo ""
echo "To activate the environment, run:"
echo "  source $VENV_PATH/bin/activate"
echo ""
echo "To run the full pipeline with the unified YAML parameters, run:"
echo "  ./run_pipeline.sh tests/test_cavity"
echo ""
echo "To deactivate the environment when done, run:"
echo "  deactivate"