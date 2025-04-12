@echo off
REM Script to install pyptv locally on Windows
REM Tested with Wine on Linux to ensure compatibility

setlocal enabledelayedexpansion

REM Create a log file
set LOG_FILE=%~dp0install_pyptv.log
echo PyPTV Installation Log > %LOG_FILE%
echo Started at: %date% %time% >> %LOG_FILE%
echo. >> %LOG_FILE%

echo === Setting up pyptv local environment ===
echo === Setting up pyptv local environment === >> %LOG_FILE%

REM Check if conda is installed
where conda >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Conda is required but not found. Please install Miniconda or Anaconda first.
    exit /b 1
)

REM Check if git is installed
where git >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Git is required but not found. Please install Git for Windows first.
    exit /b 1
)

REM Check if Visual Studio Build Tools are installed (needed for compiling C extensions)
where cl >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Visual Studio Build Tools are required but not found.
    echo Please install Visual Studio Build Tools with C++ development components.
    echo You can download it from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
    exit /b 1
)

REM Check if CMake is installed
where cmake >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo CMake is required but not found. Please install CMake first.
    echo You can download it from: https://cmake.org/download/
    exit /b 1
)

REM Create and activate conda environment
set ENV_NAME=pyptv
set PYTHON_VERSION=3.11

echo === Creating conda environment '%ENV_NAME%' with Python %PYTHON_VERSION% ===
call conda create -n %ENV_NAME% python=%PYTHON_VERSION% -y
if %ERRORLEVEL% NEQ 0 (
    echo Failed to create conda environment.
    exit /b 1
)

REM Install Python dependencies
echo === Installing Python dependencies ===
call conda activate %ENV_NAME% && ^
pip install setuptools numpy==1.26.4 matplotlib pytest flake8 tqdm cython pyyaml build
if %ERRORLEVEL% NEQ 0 (
    echo Failed to install Python dependencies.
    exit /b 1
)

REM Install specific versions of traitsui and PySide6 that work together
echo === Installing compatible UI dependencies ===
call conda activate %ENV_NAME% && ^
pip install traitsui==7.4.3 pyface==7.4.2 PySide6==6.4.0.1
if %ERRORLEVEL% NEQ 0 (
    echo Failed to install UI dependencies.
    exit /b 1
)

REM Get the current directory
set REPO_DIR=%CD%

REM Clone and build OpenPTV
echo === Building OpenPTV ===

REM Clone OpenPTV if not already present
if not exist "openptv" (
    call conda activate %ENV_NAME% && ^
    git clone https://github.com/openptv/openptv
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to clone OpenPTV repository.
        exit /b 1
    )
)

REM Build and install Python bindings
echo === Building and installing OpenPTV Python bindings ===
call conda activate %ENV_NAME% && ^
cd %REPO_DIR%\openptv\py_bind && ^
python setup.py prepare && ^
python -m build --wheel --outdir dist\ && ^
pip install dist\*.whl --force-reinstall
if %ERRORLEVEL% NEQ 0 (
    echo Failed to build and install OpenPTV Python bindings.
    exit /b 1
)

REM Return to the repository directory
cd %REPO_DIR%

REM Install pyptv from local repository
echo === Installing pyptv from local repository ===
call conda activate %ENV_NAME% && ^
pip install -e .
if %ERRORLEVEL% NEQ 0 (
    echo Failed to install pyptv from local repository.
    exit /b 1
)

REM Set up test data
echo === Setting up test data ===
if not exist "test_cavity" (
    call conda activate %ENV_NAME% && ^
    git clone https://github.com/openptv/test_cavity
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to clone test_cavity repository.
        exit /b 1
    )
)

REM Verify installation
echo === Verifying installation ===
call conda activate %ENV_NAME% && ^
python -c "import pyptv; print(f'PyPTV version: {pyptv.__version__}'); import optv; print(f'OpenPTV version: {optv.__version__}')"
if %ERRORLEVEL% NEQ 0 (
    echo Failed to verify installation.
    exit /b 1
)

REM Create a version check script if it doesn't exist
if not exist "check_version.py" (
    echo Creating version check script...
    echo #!/usr/bin/env python > check_version.py
    echo """>> check_version.py
    echo Script to check the installed version of pyptv and warn if it's not the expected version.>> check_version.py
    echo """>> check_version.py
    echo import sys>> check_version.py
    echo import importlib.metadata>> check_version.py
    echo.>> check_version.py
    echo EXPECTED_VERSION = "0.3.5"  # The version in the local repository>> check_version.py
    echo.>> check_version.py
    echo def check_version():>> check_version.py
    echo     """Check if the installed version matches the expected version.""">> check_version.py
    echo     try:>> check_version.py
    echo         installed_version = importlib.metadata.version("pyptv")>> check_version.py
    echo         print(f"Installed pyptv version: {installed_version}")>> check_version.py
    echo.>> check_version.py
    echo         if installed_version != EXPECTED_VERSION:>> check_version.py
    echo             print(f"\nWARNING: The installed version ({installed_version}) does not match ">> check_version.py
    echo                   f"the expected version ({EXPECTED_VERSION}).")>> check_version.py
    echo             print("\nPossible reasons:")>> check_version.py
    echo.>> check_version.py
    echo             if installed_version == "0.3.4":>> check_version.py
    echo                 print("- You installed from PyPI, which has version 0.3.4")>> check_version.py
    echo                 print("- To install the development version (0.3.5), run:")>> check_version.py
    echo                 print("  pip install -e /path/to/pyptv/repository")>> check_version.py
    echo             else:>> check_version.py
    echo                 print("- You might have a different version installed")>> check_version.py
    echo                 print("- Check your installation source")>> check_version.py
    echo.>> check_version.py
    echo             return False>> check_version.py
    echo         else:>> check_version.py
    echo             print(f"Version check passed: {installed_version}")>> check_version.py
    echo             return True>> check_version.py
    echo     except importlib.metadata.PackageNotFoundError:>> check_version.py
    echo         print("ERROR: pyptv is not installed.")>> check_version.py
    echo         return False>> check_version.py
    echo.>> check_version.py
    echo if __name__ == "__main__":>> check_version.py
    echo     success = check_version()>> check_version.py
    echo     sys.exit(0 if success else 1)>> check_version.py
)

REM Check if the installed version matches the expected version
echo === Checking version ===
call conda activate %ENV_NAME% && ^
python %REPO_DIR%\check_version.py
if %ERRORLEVEL% NEQ 0 (
    echo Version check failed.
    exit /b 1
)

echo.
echo === Installation complete! ===
echo To activate the environment, run: conda activate %ENV_NAME%
echo To run pyptv with test_cavity data, run: pyptv %REPO_DIR%\test_cavity
echo.
echo Note: If you encounter OpenGL errors, try setting these environment variables:
echo   set LIBGL_ALWAYS_SOFTWARE=1
echo   set QT_QPA_PLATFORM=windows
echo.

REM Create a run script for convenience
echo @echo off > run_pyptv.bat
echo REM Script to run pyptv with OpenGL workarounds >> run_pyptv.bat
echo. >> run_pyptv.bat
echo REM Set environment variables to work around OpenGL issues >> run_pyptv.bat
echo set LIBGL_ALWAYS_SOFTWARE=1 >> run_pyptv.bat
echo set QT_QPA_PLATFORM=windows >> run_pyptv.bat
echo. >> run_pyptv.bat
echo REM Activate conda environment and run pyptv >> run_pyptv.bat
echo call conda activate %ENV_NAME% ^&^& pyptv test_cavity >> run_pyptv.bat
echo. >> run_pyptv.bat
echo pause >> run_pyptv.bat

echo Created run_pyptv.bat for easy launching of pyptv.

REM Log completion
echo. >> %LOG_FILE%
echo Installation completed successfully at: %date% %time% >> %LOG_FILE%
echo Log file created at: %LOG_FILE%

REM Return to original directory
cd %REPO_DIR%

endlocal
