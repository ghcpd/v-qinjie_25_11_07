@echo off
REM setup.bat - Environment setup script for Windows

echo === Security Audit Environment Setup ===

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python 3 is required but not installed
    exit /b 1
)

REM Create virtual environment
echo Creating virtual environment...
python -m venv .venv

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install requirements
echo Installing requirements...
pip install -r requirements.txt

REM Create logs directory
echo Creating logs directory...
if not exist logs mkdir logs

REM Create .env file for persistent environment variables
echo Creating .env file...
(
echo FLASK_ENV=development
echo FLASK_DEBUG=False
echo FLASK_HOST=127.0.0.1
echo FLASK_PORT=5000
echo API_KEY=test_api_key_for_demo
echo SECRET_KEY=your_secret_key_here
) > .env

echo === Setup Complete ===
echo To activate the environment manually, run: .venv\Scripts\activate.bat
echo To run tests, execute: run_test.bat