@echo off
REM Test script for Windows
REM Tests both vulnerable and secured versions of the application

setlocal enabledelayedexpansion

set LOG_DIR=logs
set LOG_FILE=%LOG_DIR%\test_run.log
set TEST_RESULTS=%LOG_DIR%\test_results.txt

REM Create logs directory if it doesn't exist
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

REM Function to log messages
:log
echo [%date% %time%] %~1 >> "%LOG_FILE%"
echo [%date% %time%] %~1
goto :eof

REM Function to test endpoint
:test_endpoint
set url=%~1
set method=%~2
set data=%~3
set expected_status=%~4
set description=%~5

call :log "Testing: %description%"

if "%method%"=="GET" (
    curl -s -w "\n%%{http_code}" "%url%" > "%TEMP%\curl_response.txt" 2>nul
) else (
    curl -s -w "\n%%{http_code}" -X "%method%" "%url%" -d "%data%" -H "Content-Type: application/x-www-form-urlencoded" > "%TEMP%\curl_response.txt" 2>nul
)

for /f "tokens=*" %%a in ('type "%TEMP%\curl_response.txt"') do set response=%%a
for /f "tokens=*" %%a in ('powershell -Command "(Get-Content '%TEMP%\curl_response.txt')[-1]"') do set http_code=%%a

if "%http_code%"=="%expected_status%" (
    call :log "  ✓ PASS: HTTP %http_code%"
    exit /b 0
) else (
    call :log "  ✗ FAIL: Expected HTTP %expected_status%, got %http_code%"
    exit /b 1
)

REM Function to run tests on a Flask app
:run_tests
set app_file=%~1
set app_name=%~2
set should_fail=%~3

call :log ""
call :log "=========================================="
call :log "Testing %app_name% (%app_file%)"
call :log "=========================================="

REM Start Flask app in background
set FLASK_APP=%app_file%
set API_KEY=test_key_12345
start /B python "%app_file%" > "%LOG_DIR%\%app_name%_server.log" 2>&1

REM Wait for server to start
timeout /t 3 /nobreak >nul

set BASE_URL=http://localhost:5000
set FAILED_TESTS=0
set TOTAL_TESTS=0

REM Test 1: Basic endpoint availability
set /a TOTAL_TESTS+=1
call :test_endpoint "%BASE_URL%/greet?name=test" "GET" "" "200" "Greet endpoint availability"
if errorlevel 1 set /a FAILED_TESTS+=1

REM Test 2: Template Injection/XSS test
set /a TOTAL_TESTS+=1
call :log "Testing Template Injection/XSS protection..."
curl -s "%BASE_URL%/greet?name=<script>alert('xss')</script>" > "%TEMP%\xss_test.txt" 2>nul
findstr /C:"<script>" "%TEMP%\xss_test.txt" >nul 2>&1
if errorlevel 1 (
    REM Script tag not found - XSS is escaped
    if "%should_fail%"=="true" (
        call :log "  ⚠ WARNING: XSS was escaped (unexpected for original code)"
        set /a FAILED_TESTS+=1
    ) else (
        call :log "  ✓ PASS: XSS properly escaped"
    )
) else (
    REM Script tag found - XSS not escaped
    if "%should_fail%"=="true" (
        call :log "  ⚠ VULNERABILITY DETECTED: XSS script tag not escaped (expected for original code)"
    ) else (
        call :log "  ✗ FAIL: XSS script tag not escaped in secured code"
        set /a FAILED_TESTS+=1
    )
)

REM Test 3: Command Injection attempt
set /a TOTAL_TESTS+=1
call :test_endpoint "%BASE_URL%/run" "POST" "cmd=test123" "200" "Command execution endpoint"
if errorlevel 1 set /a FAILED_TESTS+=1

REM Test 4: Login endpoint - test authentication
set /a TOTAL_TESTS+=1
call :test_endpoint "%BASE_URL%/login" "POST" "username=alice&password=password123" "200" "Login endpoint (correct credentials)"
if errorlevel 1 set /a FAILED_TESTS+=1

REM Test 5: Login endpoint - test wrong password
set /a TOTAL_TESTS+=1
if "%should_fail%"=="true" (
    REM Original code returns 200 with "login failed" message
    call :test_endpoint "%BASE_URL%/login" "POST" "username=alice&password=wrong" "200" "Login endpoint (wrong credentials - original)"
) else (
    REM Secured code returns 401
    call :test_endpoint "%BASE_URL%/login" "POST" "username=alice&password=wrong" "401" "Login endpoint (wrong credentials - secured)"
)
if errorlevel 1 set /a FAILED_TESTS+=1

REM Test 6: JSON upload endpoint
set /a TOTAL_TESTS+=1
if "%should_fail%"=="true" (
    call :log "Testing upload_profile endpoint (expects pickle in original)..."
    curl -s -w "\n%%{http_code}" -X POST "%BASE_URL%/upload_profile" -d "{\"name\": \"test\"}" -H "Content-Type: application/json" > "%TEMP%\upload_test.txt" 2>nul
    for /f "tokens=*" %%a in ('powershell -Command "(Get-Content '%TEMP%\upload_test.txt')[-1]"') do set http_code=%%a
    if "!http_code!"=="200" (
        call :log "  ⚠ Endpoint responded (may accept pickle)"
    ) else (
        call :log "  ✓ Endpoint rejected invalid format (expected)"
    )
) else (
    REM Secured code accepts JSON
    curl -s -w "\n%%{http_code}" -X POST "%BASE_URL%/upload_profile" -d "{\"name\": \"test\"}" -H "Content-Type: application/json" > "%TEMP%\json_test.txt" 2>nul
    for /f "tokens=*" %%a in ('powershell -Command "(Get-Content '%TEMP%\json_test.txt')[-1]"') do set http_code=%%a
    if "!http_code!"=="200" (
        call :log "  ✓ PASS: JSON upload accepted"
    ) else (
        call :log "  ✗ FAIL: JSON upload rejected"
        set /a FAILED_TESTS+=1
    )
)

REM Stop Flask server (find and kill Python process running the app)
for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq python.exe" /FO LIST ^| findstr /I "PID"') do (
    taskkill /PID %%a /F >nul 2>&1
)

call :log ""
call :log "Test Summary for %app_name%:"
call :log "  Total Tests: %TOTAL_TESTS%"
call :log "  Failed Tests: %FAILED_TESTS%"
set /a PASSED_TESTS=%TOTAL_TESTS% - %FAILED_TESTS%
call :log "  Passed Tests: !PASSED_TESTS!"

echo %app_name%: !PASSED_TESTS!/%TOTAL_TESTS% tests passed >> "%TEST_RESULTS%"

if "%should_fail%"=="true" (
    if !FAILED_TESTS! equ 0 (
        call :log "  ⚠ WARNING: All tests passed, but vulnerabilities should exist"
        exit /b 1
    ) else (
        call :log "  ✓ Vulnerabilities detected as expected"
        exit /b 0
    )
) else (
    if !FAILED_TESTS! equ 0 (
        call :log "  ✓ All security tests passed"
        exit /b 0
    ) else (
        call :log "  ✗ Some security tests failed"
        exit /b 1
    )
)

REM Main execution
call :log "Starting security audit tests..."
call :log "Timestamp: %date% %time%"
call :log ""

REM Initialize test results file
echo Security Audit Test Results > "%TEST_RESULTS%"
echo Generated: %date% %time% >> "%TEST_RESULTS%"
echo. >> "%TEST_RESULTS%"

REM Test original vulnerable code
call :log "Phase 1: Testing original vulnerable code (input.py)"
call :run_tests "input.py" "Original (Vulnerable)" "true"
if errorlevel 1 (
    set ORIGINAL_RESULT=VULNERABILITIES_DETECTED
) else (
    set ORIGINAL_RESULT=TESTS_FAILED
)

REM Wait a bit between tests
timeout /t 2 /nobreak >nul

REM Test secured code
call :log ""
call :log "Phase 2: Testing secured code (input_secured.py)"
call :run_tests "input_secured.py" "Secured" "false"
if errorlevel 1 (
    set SECURED_RESULT=ALL_TESTS_PASSED
) else (
    set SECURED_RESULT=SOME_TESTS_FAILED
)

REM Final summary
call :log ""
call :log "=========================================="
call :log "Final Test Summary"
call :log "=========================================="
call :log "Original Code: %ORIGINAL_RESULT%"
call :log "Secured Code: %SECURED_RESULT%"
call :log ""
call :log "Detailed results saved to: %TEST_RESULTS%"
call :log "Full log saved to: %LOG_FILE%"

if "%SECURED_RESULT%"=="ALL_TESTS_PASSED" (
    exit /b 0
) else (
    exit /b 1
)

