#!/bin/bash
# Build binary wheels for pyptv
# pyptv is pure Python, so a single universal wheel works for all Python versions

set -e

echo "=== Building pyptv wheels ==="

# Ensure we're in the right directory
cd "$(dirname "$0")"

# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build the wheel and source distribution
echo "Building wheel and source distribution..."
uv build

# Copy wheels to wheels/ folder
echo "Copying wheel to wheels/ folder..."
mkdir -p wheels/
cp dist/*.whl wheels/

# List built distributions
echo ""
echo "=== Built distributions ==="
ls -lh dist/

echo ""
echo "=== Wheels folder ==="
ls -lh wheels/

echo ""
echo "✓ Build complete!"
echo ""
echo "To install the wheel:"
echo "  uv venv --python 3.11"
echo "  source .venv/bin/activate"
echo "  uv pip install wheels/optv-0.3.2-*.whl"
echo "  uv pip install dist/pyptv-*.whl"
echo ""
echo "Or install in editable mode:"
echo "  uv pip install -e ."
