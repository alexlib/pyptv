#!/bin/bash

# Make the script exit on error
set -e

echo "Applying debug patch to PTVCore..."
git apply debug_ptv_core.patch

echo "Debug patch applied successfully!"
echo "You can now run the debug script with:"
echo "python debug_init.py /path/to/experiment [--step]"
echo ""
echo "To remove the debug patch, run:"
echo "git checkout -- pyptv/ui/ptv_core.py"