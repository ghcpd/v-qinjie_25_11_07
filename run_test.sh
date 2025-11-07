#!/bin/bash

# Flask Security Test Script for Linux/macOS
# Tests both vulnerable and secure versions of the application

set -e

LOG_FILE="logs/test_run.log"
mkdir -p logs

echo "=== Flask Security Test Suite ===" | tee -a "$LOG_FILE"
echo "Test started at: $(date)" | tee -a "$LOG_FILE"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test result counters
VULNERABLE_TESTS_FAILED=0
SECURE_TESTS_PASSED=0
TOTAL_TESTS=0

# Function to run test and capture result
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_result="$3"  # "fail" or "pass"
    local description="$4"
    
    echo "" | tee -a "$LOG_FILE"
    echo "Running: $test_name" | tee -a "$LOG_FILE"
    echo "Description: $description" | tee -a "$LOG_FILE"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    # Run the test command and capture output
    if eval "$test_command" &>/dev/null; then
        if [ "$expected_result" = "pass" ]; then
            echo -e "${GREEN}✓ PASS${NC} - Test succeeded as expected" | tee -a "$LOG_FILE"
            SECURE_TESTS_PASSED=$((SECURE_TESTS_PASSED + 1))
        else
            echo -e "${RED}✗ FAIL${NC} - Vulnerable code should have failed this test" | tee -a "$LOG_FILE"
        fi
    else
        if [ "$expected_result" = "fail" ]; then
            echo -e "${GREEN}✓ PASS${NC} - Vulnerable code failed as expected" | tee -a "$LOG_FILE"
            VULNERABLE_TESTS_FAILED=$((VULNERABLE_TESTS_FAILED + 1))
        else
            echo -e "${RED}✗ FAIL${NC} - Secure code should have passed this test" | tee -a "$LOG_FILE"
        fi
    fi
}

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Set environment variables
export API_KEY="test_api_key_for_demo"
export FLASK_ENV="development"

# Create test database
python3 -c "
import sqlite3
conn = sqlite3.connect('users.db')
cur = conn.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT)')
cur.execute('DELETE FROM users')
cur.execute('INSERT INTO users (id, username) VALUES (1, \"admin\")')
cur.execute('INSERT INTO users (id, username) VALUES (2, \"testuser\")')
cur.execute('INSERT INTO users (id, username) VALUES (3, \"alice\")')
conn.commit()
conn.close()
"

echo "" | tee -a "$LOG_FILE"
echo "=== Testing Vulnerable Code (input.py) ===" | tee -a "$LOG_FILE"

# Use local tests (Flask test client) for reliable cross-platform testing
MODE=${1:-both}
TARGET=${2:-repaired}
python3 local_tests.py "$MODE" "$TARGET"
exit $?

# Stop secure app
kill $APP_PID 2>/dev/null || true

# Generate test summary
echo "" | tee -a "$LOG_FILE"
echo "=== Test Summary ===" | tee -a "$LOG_FILE"
echo "Total tests run: $TOTAL_TESTS" | tee -a "$LOG_FILE"
echo "Vulnerable tests that failed (good): $VULNERABLE_TESTS_FAILED" | tee -a "$LOG_FILE"
echo "Secure tests that passed: $SECURE_TESTS_PASSED" | tee -a "$LOG_FILE"

EXPECTED_RESULTS=$((TOTAL_TESTS))
ACTUAL_RESULTS=$((VULNERABLE_TESTS_FAILED + SECURE_TESTS_PASSED))

echo "" | tee -a "$LOG_FILE"
if [ "$ACTUAL_RESULTS" -eq "$EXPECTED_RESULTS" ]; then
    echo -e "${GREEN}✓ ALL TESTS PASSED${NC} - Security fixes are working correctly!" | tee -a "$LOG_FILE"
    echo "Test completed at: $(date)" | tee -a "$LOG_FILE"
    exit 0
else
    echo -e "${RED}✗ SOME TESTS FAILED${NC} - Please review the security implementation" | tee -a "$LOG_FILE"
    echo "Test completed at: $(date)" | tee -a "$LOG_FILE"
    exit 1
fi