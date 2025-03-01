#!/bin/bash
# Run the complete PyPTV pipeline on the test_cavity dataset

set -e  # Exit on error

# Set default experiment path
EXPERIMENT_PATH="tests/test_cavity"

# Override if argument provided
if [ "$1" != "" ]; then
    EXPERIMENT_PATH="$1"
fi

echo "Running PyPTV pipeline on experiment: $EXPERIMENT_PATH"

# Run the Python script
python run_full_pipeline.py "$EXPERIMENT_PATH"

echo "Pipeline completed successfully!"
echo "Results are available in: $EXPERIMENT_PATH/res"