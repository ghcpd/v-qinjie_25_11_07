#!/usr/bin/env bash
set -e
mkdir -p logs
# Detect Docker by checking /.dockerenv
if [ -f /.dockerenv ]; then
  echo "Running inside Docker"
  python scripts/check_security.py | tee logs/test_run.log
  exit $?
fi
# Choose original or patched app
if [ "$USE_ORIGINAL" = "1" ]; then
  APP_SCRIPT="input_original.py"
else
  APP_SCRIPT="input.py"
fi

# Linux/macOS: run tests against local Flask instance
export FLASK_DEBUG=0
# Redirect flask stdout/stderr to logs/server.log to avoid file locking with the reloader
python "$APP_SCRIPT" > logs/server.log 2>&1 &
APP_PID=$!

# Wait for port 5000 to be ready (timeout after ~15s)
RETRY=0
until nc -z localhost 5000 || [ $RETRY -ge 15 ]; do
  sleep 1
  RETRY=$((RETRY+1))
done

python scripts/check_security.py | tee logs/test_run.log
RESULT=$?
kill $APP_PID || true
exit $RESULT
