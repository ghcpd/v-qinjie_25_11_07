@echo off
REM run_test.bat - Security testing script for Windows

setlocal enabledelayedexpansion

REM Set colors (limited support in cmd)
set "LOG_DIR=logs"
set "LOG_FILE=%LOG_DIR%\test_run.log"

REM Create logs directory
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

REM Function to log messages (simulated with goto)
call :log_message "Starting security test suite"

echo === Security Testing Suite ===

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH
    exit /b 1
)

REM Check if virtual environment is activated
if not defined VIRTUAL_ENV (
    echo Activating virtual environment...
    if exist ".venv\Scripts\activate.bat" (
        call .venv\Scripts\activate.bat
    ) else (
        echo ERROR: Virtual environment not found. Run setup.bat first.
        exit /b 1
    )
)

REM Load environment variables
if exist ".env" (
    for /f "tokens=1,2 delims==" %%a in (.env) do (
        set "%%a=%%b"
    )
)

REM Test results tracking
set /a total_tests=0
set /a passed_tests=0

echo.
echo === Testing Original Vulnerable Code ===
call :test_file "input.py" "true" "Original (Vulnerable) Code"
if !errorlevel! equ 0 (
    set /a passed_tests+=1
    echo PASS: Original code correctly identified as vulnerable
) else (
    echo FAIL: Original code test failed
)
set /a total_tests+=1

echo.
echo === Testing Secure Code ===
call :test_file "input_secure.py" "false" "Secure Code"
if !errorlevel! equ 0 (
    set /a passed_tests+=1
    echo PASS: Secure code correctly identified as secure
) else (
    echo FAIL: Secure code test failed
)
set /a total_tests+=1

REM Summary
echo.
echo === Test Summary ===
call :log_message "Test Summary:"
echo Overall: !passed_tests!/!total_tests! tests passed

if !passed_tests! equ !total_tests! (
    echo All tests passed!
    call :log_message "SUCCESS: All tests passed"
    exit /b 0
) else (
    echo Some tests failed
    call :log_message "FAILURE: Some tests failed"
    exit /b 1
)

:test_file
set "file=%~1"
set "expect_vulnerable=%~2"
set "description=%~3"

echo Testing %description%...
call :log_message "Starting test for %file% (expect vulnerable: %expect_vulnerable%)"

if not exist "%file%" (
    echo ERROR: File %file% not found
    exit /b 1
)

REM Run security tests
python test_security.py "%file%" "%expect_vulnerable%" >> "%LOG_FILE%" 2>&1
if !errorlevel! equ 0 (
    echo ✓ %description% tests passed
    exit /b 0
) else (
    echo ✗ %description% tests failed
    exit /b 1
)

:log_message
echo %date% %time% - %~1 >> "%LOG_FILE%"
goto :eof