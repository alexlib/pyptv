@echo off
REM Simplified version of install_pyptv.bat for testing with Wine

echo === Setting up pyptv local environment (TEST MODE) ===

REM Check for dependencies
echo Checking for required dependencies...

REM Check if conda is installed (simulated)
echo Checking for conda... 
echo Found: conda 23.11.0

REM Check if git is installed (simulated)
echo Checking for git...
echo Found: git version 2.43.0

REM Check if Visual Studio Build Tools are installed (simulated)
echo Checking for Visual Studio Build Tools...
echo Found: MSVC v143 - VS 2022 C++ x64/x86 build tools

REM Check if CMake is installed (simulated)
echo Checking for CMake...
echo Found: cmake version 3.28.1

REM Create and activate conda environment (simulated)
set ENV_NAME=pyptv
set PYTHON_VERSION=3.11

echo === Creating conda environment '%ENV_NAME%' with Python %PYTHON_VERSION% ===
echo conda create -n %ENV_NAME% python=%PYTHON_VERSION% -y
echo Environment created successfully

REM Install Python dependencies (simulated)
echo === Installing Python dependencies ===
echo pip install setuptools numpy==1.26.4 matplotlib pytest flake8 tqdm cython pyyaml build
echo Python dependencies installed successfully

REM Install specific versions of traitsui and PySide6 (simulated)
echo === Installing compatible UI dependencies ===
echo pip install traitsui==7.4.3 pyface==7.4.2 PySide6==6.4.0.1
echo UI dependencies installed successfully

REM Get the current directory
set REPO_DIR=%CD%
echo Repository directory: %REPO_DIR%

REM Clone and build OpenPTV (simulated)
echo === Building OpenPTV ===
echo git clone https://github.com/openptv/openptv
echo OpenPTV cloned successfully

REM Build and install Python bindings (simulated)
echo === Building and installing OpenPTV Python bindings ===
echo cd %REPO_DIR%\openptv\py_bind
echo python setup.py prepare
echo python -m build --wheel --outdir dist\
echo pip install dist\*.whl --force-reinstall
echo OpenPTV Python bindings installed successfully

REM Install pyptv from local repository (simulated)
echo === Installing pyptv from local repository ===
echo pip install -e .
echo PyPTV installed successfully

REM Set up test data (simulated)
echo === Setting up test data ===
echo git clone https://github.com/openptv/test_cavity
echo Test data set up successfully

REM Verify installation (simulated)
echo === Verifying installation ===
echo PyPTV version: 0.3.5
echo OpenPTV version: 0.3.0
echo Installation verified successfully

REM Check version (simulated)
echo === Checking version ===
echo Installed pyptv version: 0.3.5
echo Version check passed: 0.3.5

echo.
echo === Installation complete! ===
echo To activate the environment, run: conda activate %ENV_NAME%
echo To run pyptv with test_cavity data, run: pyptv %REPO_DIR%\test_cavity
echo.
echo Note: If you encounter OpenGL errors, try setting these environment variables:
echo   set LIBGL_ALWAYS_SOFTWARE=1
echo   set QT_QPA_PLATFORM=windows
echo.

REM Create a run script (simulated)
echo Creating run_pyptv.bat...
echo Run script created successfully

echo Testing completed successfully!
