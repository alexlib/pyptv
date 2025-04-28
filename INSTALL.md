# PyPTV Installation Guide

This guide provides instructions for installing PyPTV locally on your system.

## Prerequisites

- Linux operating system (Ubuntu/Debian recommended)
- Conda (Miniconda or Anaconda)
- Git
- sudo privileges for installing system dependencies

## Installation Options

### Option 1: Automated Installation Script

1. Clone the repository:
   ```bash
   git clone https://github.com/openptv/pyptv
   cd pyptv
   ```

2. Run the installation script:
   ```bash
   ./install_pyptv.sh
   ```

3. The script will:
   - Create a conda environment named "pyptv" with Python 3.11
   - Install required system dependencies
   - Build and install OpenPTV (liboptv and Python bindings)
   - Install PyPTV from PyPI
   - Set up test data
   - Verify the installation

### Option 2: Manual Installation

1. Create and activate a conda environment:
   ```bash
   conda create -n pyptv python=3.11
   conda activate pyptv
   ```

2. Install system dependencies:
   ```bash
   sudo apt-get update
   sudo apt-get install -y cmake check libsubunit-dev pkg-config libxcb-cursor0
   ```

3. Install Python dependencies:
   ```bash
   conda install -y numpy==1.26.4 matplotlib pytest flake8 tqdm cython pyyaml build
   pip install traitsui==7.4.3 pyface==7.4.2 PySide6==6.4.0.1
   ```

4. Build and install OpenPTV:
   ```bash
   git clone https://github.com/openptv/openptv
   cd openptv/liboptv
   mkdir -p build && cd build
   cmake ../
   make
   sudo make install
   cd ../../py_bind
   python setup.py prepare
   python -m build --wheel --outdir dist/
   pip install dist/*.whl --force-reinstall
   cd ../..
   ```

5. Install PyPTV:

   **Option A**: Install from PyPI (stable version 0.3.4):
   ```bash
   pip install pyptv --index-url https://pypi.fury.io/pyptv --extra-index-url https://pypi.org/simple
   ```

   **Option B**: Install from local repository (development version 0.3.5):
   ```bash
   # Assuming you're in the pyptv repository directory
   pip install -e .
   ```

6. Set up test data:
   ```bash
   git clone https://github.com/openptv/test_cavity
   ```

## Testing the Installation

1. Verify that PyPTV and OpenPTV are installed correctly:
   ```bash
   conda activate pyptv
   python -c "import pyptv; print(f'PyPTV version: {pyptv.__version__}'); import optv; print(f'OpenPTV version: {optv.__version__}')"
   ```

2. Run the test script:
   ```bash
   conda activate pyptv
   python test_installation.py
   ```

3. Run PyPTV with the test_cavity data:
   ```bash
   conda activate pyptv
   pyptv /path/to/pyptv/test_cavity
   ```

## Troubleshooting

### GUI Issues

If you're running in a headless environment or through SSH, you'll need X11 forwarding or a display server to run the GUI:

1. For SSH connections, use the `-X` flag:
   ```bash
   ssh -X user@host
   ```

2. Or use a VNC server/client setup.

### Qt Platform Plugin Issues

If you encounter Qt platform plugin errors, try:

1. Installing additional X11 dependencies:
   ```bash
   sudo apt-get install -y libxcb-xinerama0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-render-util0 libxcb-xkb1 libxkbcommon-x11-0 libxcb-cursor0
   ```

2. Running with a specific platform:
   ```bash
   QT_QPA_PLATFORM=xcb pyptv /path/to/test_cavity
   ```

### PySide6 and TraitsUI Compatibility Issues

If you encounter errors like:

```
TypeError: 'PySide6.QtWidgets.QBoxLayout.addWidget' called with wrong argument types:
  PySide6.QtWidgets.QBoxLayout.addWidget(QMainWindow)
```

This is a compatibility issue between PySide6 and TraitsUI. Fix it by installing specific compatible versions:

```bash
conda activate pyptv
pip uninstall -y PySide6 traitsui pyface
pip install traitsui==7.4.3 pyface==7.4.2 PySide6==6.4.0.1
```

### OpenPTV Build Issues

If you encounter issues building OpenPTV:

1. Make sure all dependencies are installed:
   ```bash
   sudo apt-get install -y cmake check libsubunit-dev pkg-config
   ```

2. Check the CMake output for specific errors.

## Running Batch Processing

For batch processing without the GUI:

```bash
conda activate pyptv
cd /path/to/test_cavity
python -m pyptv.pyptv_batch . /path/to/pyptv
```
