#!/bin/bash
set -e

echo "========================================="
echo "Flask Security Audit - Test Suite"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to test for SQL injection vulnerability
test_sql_injection_vulnerable() {
    echo "Testing SQL Injection (vulnerable code)..."
    python3 << 'EOF'
import sys
sys.path.insert(0, '.')

# Import vulnerable version
exec(open('input.py').read())

# Try SQL injection payload
try:
    payload = "' OR '1'='1"
    result = query_users_by_name(payload)
    # If we get here without error, vulnerable code executed
    print("VULNERABLE: SQL injection payload executed")
    sys.exit(0)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
EOF
    
    if [ $? -eq 0 ]; then
        echo -e "${RED}FAIL: Vulnerable code should trigger SQL injection${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    else
        echo -e "${GREEN}PASS: Vulnerable code triggers error as expected${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    fi
}

# Function to test for pickle vulnerability
test_pickle_vulnerable() {
    echo "Testing Insecure Deserialization (vulnerable code)..."
    python3 << 'EOF'
import sys
import pickle
sys.path.insert(0, '.')

# Test if pickle vulnerability exists in input.py
with open('input.py', 'r') as f:
    content = f.read()
    if 'pickle.loads' in content:
        print("VULNERABLE: pickle.loads found")
        sys.exit(0)
    else:
        print("NOT VULNERABLE: pickle.loads not found")
        sys.exit(1)
EOF
    
    if [ $? -eq 0 ]; then
        echo -e "${RED}FAIL: Vulnerable pickle.loads should be removed${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    else
        echo -e "${GREEN}PASS: pickle.loads not found in fixed code${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    fi
}

# Function to test for command injection vulnerability
test_command_injection_vulnerable() {
    echo "Testing Command Injection (vulnerable code)..."
    if grep -q "os.system" input.py; then
        echo -e "${RED}FAIL: os.system() should be replaced with subprocess${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    else
        echo -e "${GREEN}PASS: os.system() not found in fixed code${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    fi
}

# Function to test for hardcoded API key
test_hardcoded_api_key() {
    echo "Testing Hardcoded API Key..."
    if grep -q "AKIA_EXAMPLE_HARDCODED_KEY" input.py; then
        echo -e "${RED}FAIL: Hardcoded API key should be removed${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    else
        echo -e "${GREEN}PASS: Hardcoded API key not found${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    fi
}

# Function to test fixed version
test_fixed_version() {
    echo ""
    echo "Testing Fixed Version..."
    echo ""
    
    if ! grep -q "os.system" input_fixed.py && \
       ! grep -q "pickle.loads" input_fixed.py && \
       ! grep -q "AKIA_EXAMPLE_HARDCODED_KEY" input_fixed.py && \
       grep -q "os.environ.get" input_fixed.py && \
       grep -q "subprocess" input_fixed.py && \
       grep -q "request.get_json" input_fixed.py && \
       grep -q "generate_password_hash" input_fixed.py; then
        echo -e "${GREEN}PASS: All vulnerabilities fixed${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}FAIL: Some fixes are missing${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# Run vulnerable code tests
echo "Running Vulnerable Code Tests..."
echo "=================================="
test_sql_injection_vulnerable
test_pickle_vulnerable
test_command_injection_vulnerable
test_hardcoded_api_key

# Run fixed code tests
test_fixed_version

# Print summary
echo ""
echo "========================================="
echo "Test Summary"
echo "========================================="
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed!${NC}"
    exit 1
fi
