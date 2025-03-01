#!/bin/bash
# Run the legacy PyPTV pipeline on a dataset
#
# Usage: ./run_legacy_pipeline.sh [experiment_path] [start_frame] [end_frame]
#
# Example: ./run_legacy_pipeline.sh tests/test_cavity 10001 10004
#

set -e  # Exit on error

# Set default experiment path
EXPERIMENT_PATH="tests/test_cavity"
START_FRAME="10001"
END_FRAME="10004"

# Override if arguments provided
if [ "$1" != "" ]; then
    EXPERIMENT_PATH="$1"
fi

if [ "$2" != "" ]; then
    START_FRAME="$2"
fi

if [ "$3" != "" ]; then
    END_FRAME="$3"
fi

# Check if experiment path exists
if [ ! -d "$EXPERIMENT_PATH" ]; then
    echo "Error: Experiment path '$EXPERIMENT_PATH' does not exist"
    exit 1
fi

# Check if parameters directory exists
if [ ! -d "$EXPERIMENT_PATH/parameters" ]; then
    echo "Error: Parameters directory '$EXPERIMENT_PATH/parameters' does not exist"
    exit 1
fi

# Create results directory if it doesn't exist
mkdir -p "$EXPERIMENT_PATH/res"

echo "Running legacy PyPTV pipeline on experiment: $EXPERIMENT_PATH"
echo "Frames: $START_FRAME to $END_FRAME"

# First, make sure optv module is fixed if needed
if [ ! -d "$HOME/Documents/repos/openptv" ]; then
    echo "OpenPTV repository not found at $HOME/Documents/repos/openptv"
    echo "Using alternative approach with PYTHONPATH"
    export PYTHONPATH="$PYTHONPATH:$HOME/miniconda3/lib/python3.12/site-packages"
fi

# Run the Python script with modified PYTHONPATH
cd "$EXPERIMENT_PATH"
python -m pyptv.pyptv_batch . "$START_FRAME" "$END_FRAME" || {
    echo "Legacy pipeline failed to run. This is expected if optv module is not properly installed."
    echo "The unified pipeline is designed to work even with incomplete optv installation."
    exit 1
}

echo "Pipeline completed successfully!"
echo "Results are available in: $EXPERIMENT_PATH/res"

# Show some results
echo ""
echo "Generated files:"
ls -la "$EXPERIMENT_PATH/res"