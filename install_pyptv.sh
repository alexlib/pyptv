#!/bin/bash
# Script to install pyptv locally based on Dockerfile.test

set -e  # Exit on error

echo "=== Setting up pyptv local environment ==="

# Check if conda is installed
if ! command -v conda &> /dev/null; then
    echo "Conda is required but not found. Please install Miniconda or Anaconda first."
    exit 1
fi

# Create and activate conda environment
ENV_NAME="pyptv"
PYTHON_VERSION="3.11"

echo "=== Creating conda environment '$ENV_NAME' with Python $PYTHON_VERSION ==="
conda create -n $ENV_NAME python=$PYTHON_VERSION -y

# Define a function to run commands in the conda environment
run_in_conda() {
    # This is a workaround since 'conda activate' doesn't work in scripts
    bash -c "source $(conda info --base)/etc/profile.d/conda.sh && conda activate $ENV_NAME && $1"
}

# Install system dependencies
# echo "=== Installing system dependencies ==="
# sudo apt-get update
# sudo apt-get install -y cmake check libsubunit-dev pkg-config libxcb-cursor0

# Install Python dependencies
echo "=== Installing Python dependencies ==="
run_in_conda "pip install setuptools numpy==1.26.4 matplotlib pytest flake8 tqdm cython pyyaml build"

# Install specific versions of traitsui and PySide6 that work together
echo "=== Installing compatible UI dependencies ==="
run_in_conda "pip install traitsui==7.4.3 pyface==7.4.2 PySide6==6.4.0.1"

# Clone and build OpenPTV
echo "=== Building OpenPTV ==="
cd "$(dirname "$0")"  # Change to script directory
REPO_DIR="$(pwd)"

# Clone OpenPTV if not already present
if [ ! -d "openptv" ]; then
    run_in_conda "git clone https://github.com/openptv/openptv"
fi

# Build and install liboptv
# run_in_conda "cd $REPO_DIR/openptv/liboptv && mkdir -p build && cd build && cmake ../ && make && sudo make install"

# Build and install Python bindings
run_in_conda "cd $REPO_DIR/openptv/py_bind && python setup.py prepare && python -m build --wheel --outdir dist/ && pip install dist/*.whl --force-reinstall"

# Install pyptv from local repository
echo "=== Installing pyptv from local repository ==="
run_in_conda "pip install -e $REPO_DIR"

# Set up test data
echo "=== Setting up test data ==="
if [ ! -d "test_cavity" ]; then
    run_in_conda "git clone https://github.com/openptv/test_cavity"
fi

# Create test directories if they don't exist
# mkdir -p tests/test_cavity/parameters
# cp -r test_cavity/parameters/* tests/test_cavity/parameters/

# Verify installation
echo "=== Verifying installation ==="
run_in_conda "python -c \"import pyptv; print(f'PyPTV version: {pyptv.__version__}'); import optv; print(f'OpenPTV version: {optv.__version__}')\""

# Check if the installed version matches the expected version
echo "=== Checking version ==="
run_in_conda "python $REPO_DIR/check_version.py"

echo ""
echo "=== Installation complete! ==="
echo "To activate the environment, run: conda activate $ENV_NAME"
echo "To run pyptv with test_cavity data, run: pyptv $REPO_DIR/test_cavity"
echo ""
echo "Note: If you're in a headless environment, you'll need X11 forwarding or a display server to run the GUI."
