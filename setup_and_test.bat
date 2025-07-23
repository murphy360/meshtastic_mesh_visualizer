@echo off
REM Fresh Setup and Test Automation for Meshtastic Mesh Visualizer
REM Simple batch file wrapper

echo.
echo ============================================================
echo   MESHTASTIC MESH VISUALIZER - FRESH SETUP
echo ============================================================
echo.

REM Try different Python commands to find a working one
set PYTHON_CMD=

REM First try python3
python3 --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=python3
    goto :found_python
)

REM Then try python
python --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=python
    goto :found_python
)

REM Try common Python installation paths
if exist "C:\Python311\python.exe" (
    set PYTHON_CMD=C:\Python311\python.exe
    goto :found_python
)

if exist "C:\Python310\python.exe" (
    set PYTHON_CMD=C:\Python310\python.exe
    goto :found_python
)

if exist "C:\Python39\python.exe" (
    set PYTHON_CMD=C:\Python39\python.exe
    goto :found_python
)

if exist "C:\Python38\python.exe" (
    set PYTHON_CMD=C:\Python38\python.exe
    goto :found_python
)

REM If we get here, no Python was found
echo ❌ Python not found. Please install Python 3.8+ from https://python.org
echo    and ensure it's in your PATH or installed in a standard location.
pause
exit /b 1

:found_python
echo ✅ Using Python: %PYTHON_CMD%
echo.

REM Run the main Python setup script
"%PYTHON_CMD%" setup_and_test.py %*

if errorlevel 1 (
    echo.
    echo ❌ Setup failed! Check the output above for errors.
    pause
    exit /b 1
)

echo.
echo ✅ Setup complete! Press any key to continue...
pause >nul
