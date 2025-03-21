#!/bin/bash

# Usage: ./update-optv.sh /path/to/openptv/dist/optv-0.3.0-cp310-cp310-linux_x86_64.whl

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

# Make sure we're in the right environment
if [[ $CONDA_DEFAULT_ENV != "pyptv-dev" ]]; then
    echo "Please activate the pyptv-dev environment first:"
    echo "conda activate pyptv-dev"
    exit 1
fi

# Uninstall current optv
pip uninstall -y optv

# Install the new wheel
pip install "$OPTV_WHEEL"

echo "OpenPTV updated successfully!"