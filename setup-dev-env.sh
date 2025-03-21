#!/bin/bash

# Usage: ./setup-dev-env.sh /path/to/openptv/dist/optv-0.3.0-cp310-cp310-linux_x86_64.whl

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

echo "Creating development environment..."

# Create new environment from yml file
conda env create -f environment-dev.yml

# Activate the environment
eval "$(conda shell.bash hook)"
conda activate pyptv-dev

if [ $? -ne 0 ]; then
    echo "Failed to activate conda environment"
    exit 1
fi

echo "Installing OpenPTV wheel..."
pip install "$OPTV_WHEEL"

echo "Installing PyPTV in development mode..."
pip install -e .

# Fix Chaco issues with 'sometrue'
echo "Patching Chaco files..."
SITE_PACKAGES=$(python -c "import site; print(site.getsitepackages()[0])")

# Files to patch
declare -a files_to_patch=(
    "chaco/log_mapper.py"
    "chaco/color_mapper.py"
)

# Patch each file
for file in "${files_to_patch[@]}"; do
    FULL_PATH="$SITE_PACKAGES/$file"
    if [ -f "$FULL_PATH" ]; then
        echo "Patching $file..."
        # Create backup
        cp "$FULL_PATH" "${FULL_PATH}.bak"
        # Replace 'sometrue' with 'any'
        sed -i 's/sometrue/any/g' "$FULL_PATH"
        echo "Successfully patched $file"
    else
        echo "Warning: Could not find $file"
    fi
done

# Verify the installation
echo "Verifying installation..."
python scripts/verify_environment.py

echo "Development environment setup complete!"
echo "To activate the environment, run: conda activate pyptv-dev"
