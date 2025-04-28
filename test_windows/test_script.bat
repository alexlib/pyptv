@echo off
REM Simplified test script for Wine testing

echo === Testing Windows batch script with Wine ===

REM Test basic commands
echo Current directory: %CD%
echo Script location: %~dp0

REM Test environment variables
set TEST_VAR=Hello from Windows batch script
echo %TEST_VAR%

REM Test conditional statements
if exist "%~dp0test_script.bat" (
    echo The script file exists
) else (
    echo The script file does not exist
)

REM Test for loops
echo Counting from 1 to 5:
for /L %%i in (1,1,5) do (
    echo Number: %%i
)

REM Test function-like behavior with labels
call :print_message "This is a test message"
goto :end

:print_message
echo Message: %~1
exit /b

:end
echo === Test completed successfully ===
