#!/bin/bash

# Test script for Linux/macOS
# Tests both vulnerable and secured versions of the application

set -e

LOG_DIR="logs"
LOG_FILE="$LOG_DIR/test_run.log"
TEST_RESULTS="$LOG_DIR/test_results.txt"

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to test endpoint
test_endpoint() {
    local url=$1
    local method=$2
    local data=$3
    local expected_status=$4
    local description=$5
    
    log "Testing: $description"
    
    if [ "$method" == "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$url" || echo -e "\n000")
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$url" -d "$data" -H "Content-Type: application/x-www-form-urlencoded" || echo -e "\n000")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" == "$expected_status" ] || [ "$expected_status" == "any" ]; then
        log "  ✓ PASS: HTTP $http_code"
        return 0
    else
        log "  ✗ FAIL: Expected HTTP $expected_status, got $http_code"
        return 1
    fi
}

# Function to test JSON endpoint
test_json_endpoint() {
    local url=$1
    local data=$2
    local expected_status=$3
    local description=$4
    
    log "Testing: $description"
    
    response=$(curl -s -w "\n%{http_code}" -X POST "$url" -d "$data" -H "Content-Type: application/json" || echo -e "\n000")
    http_code=$(echo "$response" | tail -n1)
    
    if [ "$http_code" == "$expected_status" ] || [ "$expected_status" == "any" ]; then
        log "  ✓ PASS: HTTP $http_code"
        return 0
    else
        log "  ✗ FAIL: Expected HTTP $expected_status, got $http_code"
        return 1
    fi
}

# Function to run tests on a Flask app
run_tests() {
    local app_file=$1
    local app_name=$2
    local should_fail=$3
    
    log ""
    log "=========================================="
    log "Testing $app_name ($app_file)"
    log "=========================================="
    
    # Start Flask app in background
    export FLASK_APP="$app_file"
    export API_KEY="test_key_12345"
    python3 "$app_file" > "$LOG_DIR/${app_name}_server.log" 2>&1 &
    FLASK_PID=$!
    
    # Wait for server to start
    sleep 3
    
    # Check if server is running
    if ! kill -0 $FLASK_PID 2>/dev/null; then
        log "ERROR: Flask server failed to start"
        return 1
    fi
    
    BASE_URL="http://localhost:5000"
    FAILED_TESTS=0
    TOTAL_TESTS=0
    
    # Test 1: Basic endpoint availability
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    test_endpoint "$BASE_URL/greet?name=test" "GET" "" "200" "Greet endpoint availability" || FAILED_TESTS=$((FAILED_TESTS + 1))
    
    # Test 2: Template Injection attempt - check if XSS is escaped
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    log "Testing Template Injection/XSS protection..."
    response=$(curl -s "$BASE_URL/greet?name=<script>alert('xss')</script>")
    if echo "$response" | grep -q "<script>"; then
        if [ "$should_fail" == "true" ]; then
            log "  ⚠ VULNERABILITY DETECTED: XSS script tag not escaped (expected for original code)"
            # This is expected for vulnerable code
        else
            log "  ✗ FAIL: XSS script tag not escaped in secured code"
            FAILED_TESTS=$((FAILED_TESTS + 1))
        fi
    else
        if [ "$should_fail" == "true" ]; then
            log "  ⚠ WARNING: XSS was escaped (unexpected for original code)"
            FAILED_TESTS=$((FAILED_TESTS + 1))
        else
            log "  ✓ PASS: XSS properly escaped"
        fi
    fi
    
    # Test 3: Command Injection attempt
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    test_endpoint "$BASE_URL/run" "POST" "cmd=test123" "200" "Command execution endpoint" || FAILED_TESTS=$((FAILED_TESTS + 1))
    
    # Test 4: Login endpoint - test authentication
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    test_endpoint "$BASE_URL/login" "POST" "username=alice&password=password123" "200" "Login endpoint (correct credentials)" || FAILED_TESTS=$((FAILED_TESTS + 1))
    
    # Test 5: Login endpoint - test wrong password
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    if [ "$should_fail" == "true" ]; then
        # Original code returns 200 with "login failed" message
        test_endpoint "$BASE_URL/login" "POST" "username=alice&password=wrong" "200" "Login endpoint (wrong credentials - original)" || FAILED_TESTS=$((FAILED_TESTS + 1))
    else
        # Secured code returns 401
        test_endpoint "$BASE_URL/login" "POST" "username=alice&password=wrong" "401" "Login endpoint (wrong credentials - secured)" || FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
    
    # Test 6: JSON upload endpoint
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    if [ "$should_fail" == "true" ]; then
        # Original code accepts pickle - test with JSON should fail
        log "Testing upload_profile endpoint (expects pickle in original)..."
        response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/upload_profile" -d '{"name": "test"}' -H "Content-Type: application/json")
        http_code=$(echo "$response" | tail -n1)
        if [ "$http_code" == "200" ]; then
            log "  ⚠ Endpoint responded (may accept pickle)"
        else
            log "  ✓ Endpoint rejected invalid format (expected)"
        fi
    else
        # Secured code accepts JSON
        test_json_endpoint "$BASE_URL/upload_profile" '{"name": "test"}' "200" "JSON upload (secured)" || FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
    
    # Stop Flask server
    kill $FLASK_PID 2>/dev/null || true
    wait $FLASK_PID 2>/dev/null || true
    
    log ""
    log "Test Summary for $app_name:"
    log "  Total Tests: $TOTAL_TESTS"
    log "  Failed Tests: $FAILED_TESTS"
    log "  Passed Tests: $((TOTAL_TESTS - FAILED_TESTS))"
    
    echo "$app_name: $((TOTAL_TESTS - FAILED_TESTS))/$TOTAL_TESTS tests passed" >> "$TEST_RESULTS"
    
    if [ "$should_fail" == "true" ]; then
        # For original code, we expect vulnerabilities to exist
        # So "failure" here means vulnerabilities were detected
        if [ $FAILED_TESTS -eq 0 ]; then
            log "  ⚠ WARNING: All tests passed, but vulnerabilities should exist in original code"
            return 1
        else
            log "  ✓ Vulnerabilities detected as expected"
            return 0
        fi
    else
        # For secured code, we expect all security measures to work
        if [ $FAILED_TESTS -eq 0 ]; then
            log "  ✓ All security tests passed"
            return 0
        else
            log "  ✗ Some security tests failed"
            return 1
        fi
    fi
}

# Main execution
log "Starting security audit tests..."
log "Timestamp: $(date)"
log ""

# Initialize test results file
echo "Security Audit Test Results" > "$TEST_RESULTS"
echo "Generated: $(date)" >> "$TEST_RESULTS"
echo "" >> "$TEST_RESULTS"

# Test original vulnerable code (should fail/detect vulnerabilities)
log "Phase 1: Testing original vulnerable code (input.py)"
if run_tests "input.py" "Original (Vulnerable)" "true"; then
    ORIGINAL_RESULT="VULNERABILITIES_DETECTED"
else
    ORIGINAL_RESULT="TESTS_FAILED"
fi

# Wait a bit between tests
sleep 2

# Test secured code (should pass)
log ""
log "Phase 2: Testing secured code (input_secured.py)"
if run_tests "input_secured.py" "Secured" "false"; then
    SECURED_RESULT="ALL_TESTS_PASSED"
else
    SECURED_RESULT="SOME_TESTS_FAILED"
fi

# Final summary
log ""
log "=========================================="
log "Final Test Summary"
log "=========================================="
log "Original Code: $ORIGINAL_RESULT"
log "Secured Code: $SECURED_RESULT"
log ""
log "Detailed results saved to: $TEST_RESULTS"
log "Full log saved to: $LOG_FILE"

# Determine exit code
if [ "$SECURED_RESULT" == "ALL_TESTS_PASSED" ]; then
    exit 0
else
    exit 1
fi

