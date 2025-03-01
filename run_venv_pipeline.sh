#!/bin/bash
# Run the PyPTV pipeline using the virtual environment
#
# This script:
# 1. Activates the virtual environment
# 2. Runs the full pipeline with unified YAML parameters
# 3. Deactivates the virtual environment
#
# Usage: ./run_venv_pipeline.sh [experiment_path] [venv_path]
#
# Example: ./run_venv_pipeline.sh tests/test_cavity venv
#

set -e  # Exit on error

# Default values
EXPERIMENT_PATH="tests/test_cavity"
VENV_PATH="venv"

# Override if arguments provided
if [ "$1" != "" ]; then
    EXPERIMENT_PATH="$1"
fi

if [ "$2" != "" ]; then
    VENV_PATH="$2"
fi

# Check if experiment path exists
if [ ! -d "$EXPERIMENT_PATH" ]; then
    echo "Error: Experiment path '$EXPERIMENT_PATH' does not exist"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo "Error: Virtual environment '$VENV_PATH' does not exist."
    echo "       Create it using ./setup_environment.sh $VENV_PATH"
    exit 1
fi

# Create results directory if it doesn't exist
mkdir -p "$EXPERIMENT_PATH/res"

echo "Running PyPTV pipeline on experiment: $EXPERIMENT_PATH"
echo "Using virtual environment: $VENV_PATH"

# Activate virtual environment
echo "Activating virtual environment..."
source "$VENV_PATH/bin/activate"

# Run the pipeline script
python run_full_pipeline.py "$EXPERIMENT_PATH"

# Check if the pipeline succeeded
if [ $? -eq 0 ]; then
    echo "Pipeline completed successfully!"
    echo "Results are available in: $EXPERIMENT_PATH/res"
    
    # Show some results
    echo ""
    echo "Generated files:"
    ls -la "$EXPERIMENT_PATH/res"
else
    echo "Pipeline failed. Check the error messages above."
fi

# Deactivate virtual environment
echo "Deactivating virtual environment..."
deactivate