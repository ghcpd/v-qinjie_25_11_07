@echo off
REM Flask Security Audit - Test Suite for Windows

setlocal enabledelayedexpansion

echo =========================================
echo Flask Security Audit - Test Suite
echo =========================================
echo.

set TESTS_PASSED=0
set TESTS_FAILED=0

REM Test for hardcoded API key
echo Testing Hardcoded API Key...
findstr /M "AKIA_EXAMPLE_HARDCODED_KEY" input.py >nul
if !ERRORLEVEL! equ 0 (
    echo [FAIL] Hardcoded API key should be removed
    set /a TESTS_FAILED+=1
) else (
    echo [PASS] Hardcoded API key not found
    set /a TESTS_PASSED+=1
)

REM Test for pickle.loads
echo Testing Insecure Deserialization...
findstr /M "pickle.loads" input.py >nul
if !ERRORLEVEL! equ 0 (
    echo [FAIL] pickle.loads should be removed
    set /a TESTS_FAILED+=1
) else (
    echo [PASS] pickle.loads not found
    set /a TESTS_PASSED+=1
)

REM Test for os.system
echo Testing Command Injection...
findstr /M "os.system" input.py >nul
if !ERRORLEVEL! equ 0 (
    echo [FAIL] os.system should be replaced with subprocess
    set /a TESTS_FAILED+=1
) else (
    echo [PASS] os.system not found
    set /a TESTS_PASSED+=1
)

REM Test parameterized queries
echo Testing SQL Injection Fix...
findstr /M "SELECT.*LIKE ?" input.py >nul
if !ERRORLEVEL! equ 0 (
    echo [FAIL] Parameterized queries not properly implemented in vulnerable code
    set /a TESTS_FAILED+=1
) else (
    echo [PASS] Vulnerable code still uses string formatting
    set /a TESTS_PASSED+=1
)

REM Test fixed version
echo.
echo Testing Fixed Version...
echo ================================

findstr /M "os.environ.get" input_fixed.py >nul
if !ERRORLEVEL! equ 0 (
    echo [PASS] Environment variables used in fixed version
    set /a TESTS_PASSED+=1
) else (
    echo [FAIL] Environment variables not used in fixed version
    set /a TESTS_FAILED+=1
)

findstr /M "subprocess" input_fixed.py >nul
if !ERRORLEVEL! equ 0 (
    echo [PASS] subprocess module used in fixed version
    set /a TESTS_PASSED+=1
) else (
    echo [FAIL] subprocess module not used in fixed version
    set /a TESTS_FAILED+=1
)

findstr /M "request.get_json" input_fixed.py >nul
if !ERRORLEVEL! equ 0 (
    echo [PASS] JSON deserialization used in fixed version
    set /a TESTS_PASSED+=1
) else (
    echo [FAIL] JSON deserialization not used in fixed version
    set /a TESTS_FAILED+=1
)

findstr /M "generate_password_hash" input_fixed.py >nul
if !ERRORLEVEL! equ 0 (
    echo [PASS] Password hashing used in fixed version
    set /a TESTS_PASSED+=1
) else (
    echo [FAIL] Password hashing not used in fixed version
    set /a TESTS_FAILED+=1
)

REM Print summary
echo.
echo =========================================
echo Test Summary
echo =========================================
echo Tests Passed: %TESTS_PASSED%
echo Tests Failed: %TESTS_FAILED%
echo.

if %TESTS_FAILED% equ 0 (
    echo All tests passed!
    exit /b 0
) else (
    echo Some tests failed!
    exit /b 1
)
