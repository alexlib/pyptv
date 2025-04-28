#!/bin/bash
# Script to fix PySide6 and TraitsUI compatibility issues

set -e  # Exit on error

echo "=== Fixing PySide6 and TraitsUI compatibility issues ==="

# Check if conda is installed
if ! command -v conda &> /dev/null; then
    echo "Conda is required but not found. Please install Miniconda or Anaconda first."
    exit 1
fi

# Define a function to run commands in the conda environment
run_in_conda() {
    # This is a workaround since 'conda activate' doesn't work in scripts
    bash -c "source $(conda info --base)/etc/profile.d/conda.sh && conda activate pyptv && $1"
}

# Uninstall problematic packages
echo "=== Uninstalling problematic packages ==="
run_in_conda "pip uninstall -y PySide6 traitsui pyface"

# Install compatible versions
echo "=== Installing compatible versions ==="
run_in_conda "pip install traitsui==7.4.3 pyface==7.4.2 PySide6==6.4.0.1"

echo ""
echo "=== Fix completed! ==="
echo "The compatibility issues between PySide6 and TraitsUI should now be resolved."
echo "Try running pyptv again."
