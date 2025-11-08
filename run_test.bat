@echo off
REM Flask Security Test Script for Windows
REM Tests both vulnerable and secure versions of the application

setlocal enabledelayedexpansion

set LOG_FILE=logs\test_run.log
if not exist logs mkdir logs

echo === Flask Security Test Suite === > %LOG_FILE%
echo Test started at: %date% %time% >> %LOG_FILE%

REM Test result counters
set VULNERABLE_TESTS_FAILED=0
set SECURE_TESTS_PASSED=0
set TOTAL_TESTS=0
set FAILED_TESTS=0

REM Function to run test (simplified for Windows batch)
:run_test
set test_name=%1
set test_description=%2
set expected_result=%3
echo.
echo Running: %test_name%
echo Description: %test_description%
echo.
echo Running: %test_name% >> %LOG_FILE%
echo Description: %test_description% >> %LOG_FILE%
set /a TOTAL_TESTS+=1
goto :eof

REM Activate virtual environment if it exists
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
) else if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Set environment variables
set API_KEY=test_api_key_for_demo
set FLASK_ENV=development

REM Create test database
python -c "import sqlite3; conn = sqlite3.connect('users.db'); cur = conn.cursor(); cur.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT)'); cur.execute('DELETE FROM users'); cur.execute('INSERT INTO users (id, username) VALUES (1, \"admin\")'); cur.execute('INSERT INTO users (id, username) VALUES (2, \"testuser\")'); cur.execute('INSERT INTO users (id, username) VALUES (3, \"alice\")'); conn.commit(); conn.close(); print('Test database created')"

echo.
echo === Testing Vulnerable Code (input.py) ===
echo === Testing Vulnerable Code (input.py) === >> %LOG_FILE%

REM Start vulnerable app in background
start /b python input.py
timeout /t 3 /nobreak >nul

REM Test 1: Command to check if vulnerable app responds
curl -s http://localhost:5000/greet?name=test >nul 2>&1
if !errorlevel! equ 0 (
    echo [PASS] Vulnerable app is running
    set /a VULNERABLE_TESTS_FAILED+=1
) else (
    echo [FAIL] Could not start vulnerable app
    set /a FAILED_TESTS+=1
)

REM Test 2: Template injection test
curl -s "http://localhost:5000/greet?name={{7*7}}" | findstr "49" >nul 2>&1
if !errorlevel! equ 0 (
    echo [EXPECTED] Template injection succeeded in vulnerable code
    set /a VULNERABLE_TESTS_FAILED+=1
) else (
    echo [UNEXPECTED] Template injection should have succeeded in vulnerable code
    set /a FAILED_TESTS+=1
)

REM Stop any running Python processes (simplified)
taskkill /f /im python.exe >nul 2>&1
timeout /t 2 /nobreak >nul

echo.
echo === Testing Secure Code (input_secure.py) ===
echo === Testing Secure Code (input_secure.py) === >> %LOG_FILE%

REM Run local tests using the Flask test client
set MODE=%1
if "%MODE%"=="" set MODE=both
set TARGET=%2
if "%TARGET%"=="" set TARGET=repaired
python local_tests.py %MODE% %TARGET%
exit /b %errorlevel%

REM Calculate totals
set /a TOTAL_TESTS=%VULNERABLE_TESTS_FAILED%+%SECURE_TESTS_PASSED%+%FAILED_TESTS%

echo.
echo === Test Summary ===
echo === Test Summary === >> %LOG_FILE%
echo Total tests run: %TOTAL_TESTS%
echo Vulnerable tests that failed (good): %VULNERABLE_TESTS_FAILED%
echo Secure tests that passed: %SECURE_TESTS_PASSED%
echo Failed tests: %FAILED_TESTS%
echo Total tests run: %TOTAL_TESTS% >> %LOG_FILE%
echo Vulnerable tests that failed (good): %VULNERABLE_TESTS_FAILED% >> %LOG_FILE%
echo Secure tests that passed: %SECURE_TESTS_PASSED% >> %LOG_FILE%
echo Failed tests: %FAILED_TESTS% >> %LOG_FILE%

echo.
if %FAILED_TESTS% equ 0 (
    echo [SUCCESS] All security tests passed!
    echo Test completed at: %date% %time%
    echo [SUCCESS] All security tests passed! >> %LOG_FILE%
    echo Test completed at: %date% %time% >> %LOG_FILE%
    exit /b 0
) else (
    echo [FAILURE] Some tests failed - please review security implementation
    echo Test completed at: %date% %time%
    echo [FAILURE] Some tests failed - please review security implementation >> %LOG_FILE%
    echo Test completed at: %date% %time% >> %LOG_FILE%
    exit /b 1
)