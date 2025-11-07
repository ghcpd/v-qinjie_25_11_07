@echo off
mkdir logs 2>nul
python test_runner.py > logs\test_run.log 2>&1
if %errorlevel% neq 0 exit /b %errorlevel%
