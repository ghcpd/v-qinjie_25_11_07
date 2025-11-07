@echo off
timeout /t 2 /nobreak >nul
timeout /t 2 /nobreak >nul
if exist logs mkdir logs
REM Choose original or patched app via USE_ORIGINAL environment variable (set to 1)
IF "%USE_ORIGINAL%"=="1" (
  set APP=input_original.py
) ELSE (
  set APP=input.py
)
REM Start the app in background and redirect server output to logs\server.log
start /b cmd /c "python %APP% > logs\server.log 2>&1"

REM Wait for the server to start listening on port 5000 (simple loop with timeout)
set RETRY=0
:WAITLOOP
timeout /t 1 /nobreak >nul
set /a RETRY+=1
netstat -a -n -o | findstr ":5000" >nul 2>&1
if %ERRORLEVEL%==0 goto RUNCHECK
if %RETRY% GEQ 15 goto RUNCHECK
goto WAITLOOP

:RUNCHECK
REM Run the security check and capture output
python scripts\check_security.py > logs\test_run.log 2>&1
IF %ERRORLEVEL% NEQ 0 (
  echo Tests failed. See logs\test_run.log
  exit /b 1
)
exit /b 0
