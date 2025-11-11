# Security Audit Report and Fixes

This repository contains a security audit of a Flask application (`input.py`) with identified vulnerabilities, fixes, and automated testing scripts.

## Overview

The original `input.py` file contained **7 critical security vulnerabilities**:
- SQL Injection
- Remote Code Execution (Pickle deserialization)
- Command Injection
- Template Injection (XSS)
- Hardcoded API Key
- Weak Authentication (plain text passwords)
- Debug Mode Enabled

All vulnerabilities have been fixed in `input_secured.py`.

## Files

- **input.py** - Original vulnerable code
- **input_secured.py** - Secured version with all fixes applied
- **report.json** - Detailed vulnerability report with explanations
- **requirements.txt** - Python dependencies
- **Dockerfile** - Docker container configuration
- **setup.sh** - Environment setup script for Linux/macOS
- **run_test.sh** - Test script for Linux/macOS
- **run_test.bat** - Test script for Windows
- **auto_test.py** - Automatic test execution (detects environment)
- **init_secured_db.py** - Database initialization helper

## Quick Start

### Linux/macOS

1. **Setup environment:**
   ```bash
   chmod +x setup.sh run_test.sh
   ./setup.sh
   source venv/bin/activate
   ```

2. **Run tests automatically:**
   ```bash
   python3 auto_test.py
   ```

   Or manually:
   ```bash
   ./run_test.sh
   ```

### Windows

1. **Setup environment:**
   ```cmd
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Run tests:**
   ```cmd
   python auto_test.py
   ```

   Or manually:
   ```cmd
   run_test.bat
   ```

### Docker

```bash
docker build -t security-audit .
docker run security-audit
```

## Test Results

Tests verify that:
- Original code (`input.py`) contains vulnerabilities (tests detect them)
- Secured code (`input_secured.py`) fixes all vulnerabilities (tests pass)

Test logs are saved to `logs/test_run.log` and `logs/test_results.txt`.

## Vulnerability Details

See `report.json` for complete details on each vulnerability, including:
- Severity level
- Affected file and line numbers
- Vulnerable code snippets
- Fixed code snippets
- Detailed explanations of fixes
- CWE references

## Security Fixes Summary

1. **SQL Injection** → Parameterized queries
2. **Pickle RCE** → JSON serialization
3. **Command Injection** → subprocess.run() with proper arguments
4. **Template Injection** → Input escaping and safe template rendering
5. **Hardcoded Secrets** → Environment variables
6. **Weak Authentication** → Password hashing (bcrypt)
7. **Debug Mode** → Disabled in production

## Environment Variables

Set the following environment variable for the secured application:
```bash
export API_KEY="your_api_key_here"
```

## Notes

- The test scripts start Flask servers temporarily for testing
- Original code tests are expected to show vulnerabilities
- Secured code tests verify all vulnerabilities are fixed
- All logs are saved to the `logs/` directory

