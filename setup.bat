@echo off
REM Setup script for GRA External Integration API (Windows)

echo === GRA External Integration API Setup ===
echo.

REM Check Python version
echo Checking Python version...
python --version

REM Create virtual environment
echo.
echo Creating virtual environment...
python -m venv venv

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo.
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo.
echo Installing dependencies...
pip install -r requirements.txt

REM Copy environment file
echo.
echo Setting up environment configuration...
if not exist .env (
    copy .env.example .env
    echo .env file created. Please update it with your configuration.
) else (
    echo .env file already exists.
)

echo.
echo === Setup Complete ===
echo.
echo To activate the virtual environment, run:
echo   venv\Scripts\activate.bat
echo.
echo To run the application:
echo   uvicorn app.main:app --reload
echo.
echo To run tests:
echo   pytest
