#!/bin/bash

# Usage: ./dev-setup.sh /path/to/openptv/dist/optv-0.3.0-cp310-cp310-linux_x86_64.whl

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 /path/to/openptv/wheel.whl"
    exit 1
fi

OPTV_WHEEL=$1

# Verify the wheel exists
if [ ! -f "$OPTV_WHEEL" ]; then
    echo "OpenPTV wheel not found at: $OPTV_WHEEL"
    exit 1
fi

# Create and activate environment
conda env create -f environment-dev.yml
conda activate pyptv-dev

# Install the local OpenPTV wheel
pip install "$OPTV_WHEEL"

# Install PyPTV in development mode
pip install -e .

echo "Development environment ready!"
echo "OpenPTV wheel installed from: $OPTV_WHEEL"
echo "PyPTV installed in development mode"