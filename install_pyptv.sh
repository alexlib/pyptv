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

echo "=== Using conda environment '$ENV_NAME' with Python $PYTHON_VERSION ==="

# Define a function to run commands in the conda environment
run_in_conda() {
    # This is a workaround since 'conda activate' doesn't work in scripts
    bash -c "source $(conda info --base)/etc/profile.d/conda.sh && conda activate $ENV_NAME && $1"
}

# Install Python dependencies
echo "=== Installing Python dependencies ==="
run_in_conda "pip install setuptools numpy==1.26.4 matplotlib pytest tqdm cython pyyaml build"

# Install UI dependencies
echo "=== Installing UI dependencies ==="
run_in_conda "pip install traits traitsui pyface PySide6 enable chaco"

# Install additional dependencies for PyPTV
echo "=== Installing additional dependencies ==="
run_in_conda "pip install scikit-image scipy pandas tables imagecodecs flowtracks pygments pyparsing"

# Clone and build OpenPTV
echo "=== Building OpenPTV ==="
cd "$(dirname "$0")"  # Change to script directory
REPO_DIR="$(pwd)"

# Clone OpenPTV if not already present
if [ ! -d "openptv" ]; then
    run_in_conda "git clone https://github.com/openptv/openptv"
fi

# Build and install Python bindings
run_in_conda "cd $REPO_DIR/openptv/py_bind && python setup.py prepare && python setup.py build_ext --inplace && pip install ."

# Install pyptv from local repository
echo "=== Installing pyptv from local repository ==="
run_in_conda "pip install -e $REPO_DIR"

# Set up test data
echo "=== Setting up test data ==="
if [ ! -d "test_cavity" ]; then
    run_in_conda "git clone https://github.com/openptv/test_cavity"
fi

# Verify installation
echo "=== Verifying installation ==="
run_in_conda "python -c \"import pyptv; print(f'PyPTV version: {pyptv.__version__}'); import optv; print(f'OpenPTV version: {optv.__version__}')\""

echo ""
echo "=== Installation complete! ==="
echo "To activate the environment, run: conda activate $ENV_NAME"
echo "To run pyptv with test_cavity data, run: pyptv $REPO_DIR/test_cavity"
echo ""
