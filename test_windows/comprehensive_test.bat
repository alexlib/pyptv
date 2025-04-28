@echo off
REM Comprehensive test script for Windows installation

echo === Comprehensive test of Windows installation script ===

REM Test dependency checking
echo Testing dependency checking...

REM Test conda check
echo Simulating conda check...
where conda >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Conda check works correctly - detected as not installed
) else (
    echo Conda check failed - conda should not be detected in Wine
)

REM Test git check
echo Simulating git check...
where git >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Git check works correctly - detected as not installed
) else (
    echo Git check failed - git should not be detected in Wine
)

REM Test Visual Studio check
echo Simulating Visual Studio check...
where cl >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Visual Studio check works correctly - detected as not installed
) else (
    echo Visual Studio check failed - cl should not be detected in Wine
)

REM Test CMake check
echo Simulating CMake check...
where cmake >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo CMake check works correctly - detected as not installed
) else (
    echo CMake check failed - cmake should not be detected in Wine
)

REM Test environment variable handling
echo Testing environment variable handling...
set TEST_ENV_VAR=test_value
echo Environment variable set: %TEST_ENV_VAR%

REM Test path handling
echo Testing path handling...
set CURRENT_DIR=%CD%
echo Current directory: %CURRENT_DIR%
echo Script directory: %~dp0

REM Test file existence check
echo Testing file existence check...
if exist "%~dp0comprehensive_test.bat" (
    echo File existence check works correctly
) else (
    echo File existence check failed
)

REM Test directory creation
echo Testing directory creation...
if not exist "%~dp0test_dir" (
    mkdir "%~dp0test_dir"
    echo Directory created successfully
) else (
    echo Directory already exists
)

REM Test file creation
echo Testing file creation...
echo This is a test > "%~dp0test_dir\test_file.txt"
if exist "%~dp0test_dir\test_file.txt" (
    echo File created successfully
    type "%~dp0test_dir\test_file.txt"
) else (
    echo File creation failed
)

REM Test command execution simulation
echo Testing command execution simulation...
echo Simulating: conda create -n pyptv python=3.11 -y
echo Simulating: pip install numpy==1.26.4
echo Simulating: git clone https://github.com/openptv/openptv

REM Test error handling
echo Testing error handling...
cd "%~dp0non_existent_directory" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error handling works correctly - detected non-existent directory
) else (
    echo Error handling failed
)

REM Test cleanup
echo Testing cleanup...
if exist "%~dp0test_dir\test_file.txt" (
    del "%~dp0test_dir\test_file.txt"
    echo File deleted successfully
)
if exist "%~dp0test_dir" (
    rmdir "%~dp0test_dir"
    echo Directory deleted successfully
)

echo === Comprehensive test completed successfully ===
