# Installation Guide

This guide covers installing PyPTV on Linux and macOS systems.

> 📝 **Windows Users**: See the [Windows Installation Guide](windows-installation.md) for platform-specific instructions.

## Prerequisites

Before installing PyPTV, ensure you have:

- **Operating System**: Linux (Ubuntu 20.04+ or equivalent) or macOS 10.15+
- **Conda**: [Miniconda](https://docs.conda.io/en/latest/miniconda.html) or [Anaconda](https://www.anaconda.com/products/distribution)
- **Git**: For cloning the repository
- **Compiler**: GCC (Linux) or Xcode Command Line Tools (macOS)

### System Dependencies

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install -y build-essential cmake git pkg-config
sudo apt install -y libhdf5-dev libopencv-dev
```

#### Fedora/RHEL/CentOS
```bash
sudo dnf install -y gcc gcc-c++ cmake git pkg-config
sudo dnf install -y hdf5-devel opencv-devel
```

#### macOS
```bash
# Install Xcode Command Line Tools
xcode-select --install

# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install cmake pkg-config hdf5 opencv
```

## Installation Methods

### Method 1: Automated Installation (Recommended)

The easiest way to install PyPTV is using the provided installation script:

```bash
# 1. Clone the repository
git clone https://github.com/openptv/pyptv.git
cd pyptv

# 2. Run the installation script
./install_pyptv.sh

# 3. Activate the environment
conda activate pyptv
```

The script will:
- Create a conda environment named "pyptv" with Python 3.11
- Install all required dependencies
- Build and install OpenPTV (liboptv)
- Install PyPTV in development mode

### Method 2: Manual Installation

If you prefer manual control or need to customize the installation:

```bash
# 1. Clone the repository
git clone https://github.com/openptv/pyptv.git
cd pyptv

# 2. Create conda environment
conda env create -f environment.yml
conda activate pyptv

# 3. Install PyPTV
pip install -e .
```

### Method 3: Development Installation

For developers who want to contribute to PyPTV:

```bash
# 1. Fork and clone your fork
git clone https://github.com/yourusername/pyptv.git
cd pyptv

# 2. Create development environment
conda env create -f environment.yml
conda activate pyptv

# 3. Install in development mode with test dependencies
pip install -e ".[dev,test]"

# 4. Install pre-commit hooks
pre-commit install
```

## Verification

Test your installation by running:

```bash
# Activate the environment
conda activate pyptv

# Test basic import
python -c "import pyptv; print('PyPTV installed successfully!')"

# Launch the GUI (should open without errors)
python -m pyptv.pyptv_gui

# Run the test suite
pytest tests/

## Testing: Headless vs GUI

PyPTV separates tests into two categories:

- **Headless tests** (no GUI): Located in `tests/`. These run in CI (GitHub Actions) and Docker, and do not require a display.
- **GUI-dependent tests**: Located in `tests_gui/`. These require a display and are run locally or with Xvfb.

To run all tests locally:
```bash
bash run_tests.sh
```
To run only headless tests (recommended for CI/Docker):
```bash
bash run_headless_tests.sh
```

## Docker Usage

For headless testing and reproducible builds, you can use Docker:
```bash
docker build -t pyptv-test .
docker run --rm pyptv-test
```
This runs only headless tests in a minimal environment, mimicking CI.
```

## Common Installation Issues

### Issue: "liboptv not found"
**Solution**: The OpenPTV library needs to be built and installed. Try:
```bash
conda activate pyptv
cd pyptv
./install_pyptv.sh
```

### Issue: "Cannot import cv2"
**Solution**: OpenCV installation issue. Try:
```bash
conda activate pyptv
conda install -c conda-forge opencv
```

### Issue: "HDF5 headers not found"
**Solution**: Install HDF5 development packages:
```bash
# Ubuntu/Debian
sudo apt install libhdf5-dev

# macOS
brew install hdf5
```

### Issue: Permission errors during compilation
**Solution**: Ensure you have write permissions and try:
```bash
# Clean previous builds
rm -rf build/ dist/ *.egg-info/
./install_pyptv.sh
```

## Environment Management

### Activating PyPTV
Every time you want to use PyPTV:
```bash
conda activate pyptv
```

### Updating PyPTV
To get the latest changes:
```bash
conda activate pyptv
cd pyptv
git pull origin main
pip install -e .
```

### Removing PyPTV
To completely remove PyPTV:
```bash
conda env remove -n pyptv
rm -rf pyptv/  # Remove the source directory
```

## Next Steps

Once PyPTV is installed:

1. **Test with Example Data**: Follow the [Quick Start Guide](quick-start.md)
2. **Set Up Your Experiment**: Learn about [parameter configuration](parameter-migration.md)
3. **Launch the GUI**: See [Running the GUI](running-gui.md)

## Getting Help

If you encounter installation issues:

- Check the [GitHub Issues](https://github.com/openptv/pyptv/issues) for similar problems
- Create a new issue with your system details and error messages
- Join the [GitHub Discussions](https://github.com/openptv/pyptv/discussions) for community help

---

**Next**: [Quick Start Guide](quick-start.md) or [Windows Installation](windows-installation.md)
