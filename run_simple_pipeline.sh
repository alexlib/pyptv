#!/bin/bash
# Run the simplified PyPTV pipeline on a dataset
#
# Usage: ./run_simple_pipeline.sh [experiment_path]
#
# Example: ./run_simple_pipeline.sh tests/test_cavity
#

set -e  # Exit on error

# Set default experiment path
EXPERIMENT_PATH="tests/test_cavity"

# Override if argument provided
if [ "$1" != "" ]; then
    EXPERIMENT_PATH="$1"
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

echo "Running simplified PyPTV pipeline on experiment: $EXPERIMENT_PATH"

# Run the Python script
python run_full_pipeline_simple.py "$EXPERIMENT_PATH"

echo "Pipeline completed successfully!"
echo "Results are available in: $EXPERIMENT_PATH/res"

# Show some results
echo ""
echo "Generated files:"
ls -la "$EXPERIMENT_PATH/res"