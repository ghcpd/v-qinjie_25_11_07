#!/bin/bash

# run_test.sh - Security testing script for Linux/macOS

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

LOG_DIR="logs"
LOG_FILE="$LOG_DIR/test_run.log"

# Create logs directory
mkdir -p "$LOG_DIR"

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Function to test a specific file
test_file() {
    local file=$1
    local expect_vulnerable=$2
    local description=$3
    
    echo -e "${YELLOW}Testing $description...${NC}" | tee -a "$LOG_FILE"
    log_message "Starting test for $file (expect vulnerable: $expect_vulnerable)"
    
    if [[ ! -f "$file" ]]; then
        echo -e "${RED}ERROR: File $file not found${NC}" | tee -a "$LOG_FILE"
        return 1
    fi
    
    # Run security tests
    if python3 test_security.py "$file" "$expect_vulnerable" 2>&1 | tee -a "$LOG_FILE"; then
        echo -e "${GREEN}✓ $description tests passed${NC}" | tee -a "$LOG_FILE"
        return 0
    else
        echo -e "${RED}✗ $description tests failed${NC}" | tee -a "$LOG_FILE"
        return 1
    fi
}

main() {
    echo -e "${YELLOW}=== Security Testing Suite ===${NC}"
    log_message "Starting security test suite"
    
    # Check if virtual environment is activated
    if [[ -z "$VIRTUAL_ENV" ]]; then
        echo -e "${YELLOW}Activating virtual environment...${NC}"
        if [[ -f "venv/bin/activate" ]]; then
            source venv/bin/activate
        else
            echo -e "${RED}ERROR: Virtual environment not found. Run setup.sh first.${NC}"
            exit 1
        fi
    fi
    
    # Load environment variables
    if [[ -f ".env" ]]; then
        source .env
    fi
    
    # Test results
    declare -a results
    
    echo -e "${YELLOW}\n=== Testing Original Vulnerable Code ===${NC}"
    if test_file "input.py" "true" "Original (Vulnerable) Code"; then
        results+=("PASS: Original code correctly identified as vulnerable")
    else
        results+=("FAIL: Original code test failed")
    fi
    
    echo -e "${YELLOW}\n=== Testing Secure Code ===${NC}"
    if test_file "input_secure.py" "false" "Secure Code"; then
        results+=("PASS: Secure code correctly identified as secure")
    else
        results+=("FAIL: Secure code test failed")
    fi
    
    # Summary
    echo -e "${YELLOW}\n=== Test Summary ===${NC}"
    log_message "Test Summary:"
    
    passed=0
    total=${#results[@]}
    
    for result in "${results[@]}"; do
        if [[ $result == PASS* ]]; then
            echo -e "${GREEN}✓ $result${NC}" | tee -a "$LOG_FILE"
            ((passed++))
        else
            echo -e "${RED}✗ $result${NC}" | tee -a "$LOG_FILE"
        fi
    done
    
    echo -e "\nOverall: $passed/$total tests passed" | tee -a "$LOG_FILE"
    log_message "Test suite completed. Overall: $passed/$total tests passed"
    
    if [[ $passed -eq $total ]]; then
        echo -e "${GREEN}🎉 All tests passed!${NC}"
        log_message "SUCCESS: All tests passed"
        exit 0
    else
        echo -e "${RED}❌ Some tests failed${NC}"
        log_message "FAILURE: Some tests failed"
        exit 1
    fi
}

# Handle script interruption
trap 'echo -e "\n${RED}Test interrupted${NC}"; log_message "Test suite interrupted"; exit 130' INT

# Run main function
main "$@"