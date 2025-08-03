#!/bin/bash
# Script to fix PySide6 and TraitsUI compatibility issues by trying multiple versions

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

# Install traitsui and pyface
echo "=== Installing traitsui and pyface ==="
run_in_conda "pip install traitsui==7.4.3 pyface==7.4.2"

# Try different versions of PySide6 until one works
echo "=== Trying different versions of PySide6 ==="
VERSIONS=("6.4.0.1" "6.4.1" "6.4.2" "6.4.3" "6.5.0" "6.5.1")
SUCCESS=false

for VERSION in "${VERSIONS[@]}"; do
    echo "Trying PySide6 version $VERSION..."
    if run_in_conda "pip install PySide6==$VERSION" > /dev/null 2>&1; then
        echo "Successfully installed PySide6 version $VERSION"
        SUCCESS=true
        break
    else
        echo "Failed to install PySide6 version $VERSION, trying next version..."
    fi
done

if [ "$SUCCESS" = true ]; then
    echo ""
    echo "=== Fix completed! ==="
    echo "The compatibility issues between PySide6 and TraitsUI should now be resolved."
    echo "Try running pyptv again."
else
    echo ""
    echo "=== Fix failed! ==="
    echo "Could not find a compatible version of PySide6."
    echo "Please try manually installing a different version of PySide6."
fi
