# PyPTV Windows Installation Guide

This guide provides instructions for installing PyPTV on Windows.

## Prerequisites

Before running the installation script, make sure you have the following prerequisites installed:

1. **Miniconda or Anaconda**
   - Download and install from: https://docs.conda.io/en/latest/miniconda.html

2. **Git for Windows**
   - Download and install from: https://git-scm.com/download/win

3. **Visual Studio Build Tools with C++ development components**
   - Download and install from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
   - Make sure to select "Desktop development with C++" during installation

4. **CMake**
   - Download and install from: https://cmake.org/download/
   - Make sure to add CMake to your PATH during installation

## Installation

### Option 1: Automated Installation Script

The installation script has been tested with Wine on Linux to ensure compatibility with Windows systems.

1. Clone the repository:
   ```
   git clone https://github.com/openptv/pyptv
   cd pyptv
   ```

2. Run the installation script:
   ```
   install_pyptv.bat
   ```

3. The script will:
   - Check for required dependencies
   - Create a conda environment named "pyptv" with Python 3.11
   - Install required Python dependencies
   - Build and install OpenPTV (Python bindings)
   - Install PyPTV from the local repository
   - Set up test data
   - Verify the installation
   - Create a run_pyptv.bat script for easy launching

### Option 2: Manual Installation

If the automated script fails, you can follow these manual steps:

1. Create and activate a conda environment:
   ```
   conda create -n pyptv python=3.11
   conda activate pyptv
   ```

2. Install Python dependencies:
   ```
   pip install setuptools numpy==1.26.4 matplotlib pytest flake8 tqdm cython pyyaml build
   pip install traitsui==7.4.3 pyface==7.4.2 PySide6==6.4.0.1
   ```

3. Clone and build OpenPTV:
   ```
   git clone https://github.com/openptv/openptv
   cd openptv\py_bind
   python setup.py prepare
   python -m build --wheel --outdir dist\
   pip install dist\*.whl --force-reinstall
   cd ..\..
   ```

4. Install PyPTV from the local repository:
   ```
   pip install -e .
   ```

5. Set up test data:
   ```
   git clone https://github.com/openptv/test_cavity
   ```

## Running PyPTV

After installation, you can run PyPTV in two ways:

1. Using the provided run script:
   ```
   run_pyptv.bat
   ```

2. Manually:
   ```
   conda activate pyptv
   pyptv test_cavity
   ```

## Troubleshooting

### OpenGL Issues

If you encounter OpenGL errors, try setting these environment variables before running PyPTV:

```
set LIBGL_ALWAYS_SOFTWARE=1
set QT_QPA_PLATFORM=windows
```

### Build Errors

If you encounter build errors:

1. Make sure you have the correct version of Visual Studio Build Tools installed
2. Make sure CMake is in your PATH
3. Try running the Visual Studio Developer Command Prompt and then run the installation from there

### PySide6 and TraitsUI Compatibility Issues

If you encounter errors like:

```
TypeError: 'PySide6.QtWidgets.QBoxLayout.addWidget' called with wrong argument types:
  PySide6.QtWidgets.QBoxLayout.addWidget(QMainWindow)
```

Try reinstalling with specific compatible versions:

```
conda activate pyptv
pip uninstall -y PySide6 traitsui pyface
pip install traitsui==7.4.3 pyface==7.4.2 PySide6==6.4.0.1
```

## Testing the Installation

To verify that the installation was successful:

```
conda activate pyptv
python -c "import pyptv; print(f'PyPTV version: {pyptv.__version__}'); import optv; print(f'OpenPTV version: {optv.__version__}')"
```

You should see output indicating PyPTV version 0.3.5 and OpenPTV version 0.3.0.
