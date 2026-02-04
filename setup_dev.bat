@echo off
REM Development setup script for Windows

echo ========================================
echo Photo Tool - Development Setup
echo ========================================
echo.

REM Check Python version
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.10 or higher.
    pause
    exit /b 1
)

echo [1/5] Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

echo [2/5] Activating virtual environment...
call venv\Scripts\activate.bat

echo [3/5] Upgrading pip...
python -m pip install --upgrade pip setuptools wheel

echo [4/5] Installing Photo Tool in development mode...
pip install -e ".[dev]"
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo [5/5] Verifying installation...
photo-tool --version
if errorlevel 1 (
    echo WARNING: Command 'photo-tool' not found in PATH
    echo You may need to restart your terminal
)

echo.
echo ========================================
echo Setup complete!
echo ========================================
echo.
echo To activate the virtual environment:
echo   venv\Scripts\activate
echo.
echo To run tests:
echo   pytest
echo.
echo To format code:
echo   black photo_tool tests
echo.
echo To start development:
echo   photo-tool --help
echo.
echo See DEVELOPMENT.md for more information.
echo.

pause
