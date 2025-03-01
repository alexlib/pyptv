#!/bin/bash

# Make the script exit on error
set -e

echo "Applying fixes to PyPTV initialization..."

# Apply the main PTVCore fix
git apply patches/ptv_core_fix.patch

# Apply the PTVCore bridge fix
git apply patches/ptv_core_bridge_fix.patch

echo "Fixes applied successfully!"
echo ""
echo "These fixes address the following issues:"
echo "1. Fixed infinite loop during experiment initialization by properly handling PTVCore imports"
echo "2. Added intelligent bridge/implementation selection to prevent conflicts"
echo "3. Added more logging to debug parameter loading issues"
echo ""
echo "To commit these changes, run:"
echo "git commit -am \"Fix initialization infinite loop when opening experiment directory\""