#!/bin/bash

# Make the script exit on error
set -e

echo "Applying fixes to PTVCore implementation..."

# Apply the main window fix
git apply pyptv/ui/ptv_core_fix.patch

# Apply the bridge fix
git apply pyptv/ui/ptv_core_bridge_fix.patch

echo "Fixes applied successfully!"
echo ""
echo "These fixes address the infinite loop issue by:"
echo "1. Ensuring proper loading of the PTVCore implementation"
echo "2. Avoiding conflicts between the bridge and full implementations"
echo "3. Adding more debug output to identify initialization issues"
echo ""
echo "To commit these changes, run:"
echo "git commit -am \"Fix initialization infinite loop when opening experiment directory\""