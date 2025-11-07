# Security Audit Report for Flask Application

## Overview
This repository contains a comprehensive security audit of a Python Flask application, including vulnerability identification, fixes, and automated testing infrastructure.

## Files Structure

### Core Files
- `input.py` - Original vulnerable Flask application
- `input_secure.py` - Secured version with all vulnerabilities fixed
- `report.json` - Detailed security audit report in JSON format

### Testing Infrastructure
- `test_security.py` - Comprehensive security test suite
- `auto_test.py` - Automatic test execution with environment detection

### Environment Setup
- `requirements.txt` - Python package dependencies
- `Dockerfile` - Docker container configuration
- `setup.sh` - Linux/macOS environment setup script
- `setup.bat` - Windows environment setup script

### Test Execution Scripts
- `run_test.sh` - Linux/macOS test runner
- `run_test.bat` - Windows test runner

## Identified Vulnerabilities

### Critical Vulnerabilities (3)
1. **SQL Injection** (Lines 15-16) - CWE-89
2. **Insecure Deserialization** (Lines 23-24) - CWE-502
3. **Command Injection** (Lines 30-31) - CWE-78

### High Vulnerabilities (2)
4. **Hardcoded API Key** (Line 8) - CWE-798
5. **Template Injection** (Lines 37-38) - CWE-94

### Medium Vulnerabilities (2)
6. **Weak Authentication** (Lines 41-52) - CWE-521
7. **Debug Mode Enabled** (Line 55) - CWE-489

## Quick Start

### Windows
```powershell
# Setup environment
.\setup.bat

# Run tests
.\run_test.bat

# Or use automatic testing
python auto_test.py
```

### Linux/macOS
```bash
# Setup environment
chmod +x setup.sh
./setup.sh

# Run tests  
chmod +x run_test.sh
./run_test.sh

# Or use automatic testing
python3 auto_test.py
```

### Docker
```bash
# Build container
docker build -t security-audit .

# Run vulnerable version tests
docker run --rm security-audit python test_security.py input.py true

# Run secure version tests
docker run --rm security-audit python test_security.py input_secure.py false

# Run automatic testing
docker run --rm security-audit python auto_test.py
```

## Test Strategy

The testing framework validates that:

### For Original Code (Should FAIL)
- SQL injection attacks succeed
- Pickle deserialization executes arbitrary code
- Command injection succeeds
- Template injection executes

### For Secure Code (Should PASS)
- SQL injection is blocked by parameterized queries
- Only JSON data is accepted (pickle rejected)
- Command execution is whitelisted
- Template injection is prevented by escaping

## Security Fixes Applied

### 1. SQL Injection → Parameterized Queries
```python
# Before (Vulnerable)
sql = "SELECT id, username FROM users WHERE username LIKE '%{}%'".format(name)

# After (Secure)
sql = "SELECT id, username FROM users WHERE username LIKE ?"
cur.execute(sql, (f'%{name}%',))
```

### 2. Pickle Deserialization → JSON with Validation
```python
# Before (Vulnerable)
profile = pickle.loads(data)

# After (Secure)
profile = request.get_json()
# + Input validation and type checking
```

### 3. Command Injection → Command Whitelisting
```python
# Before (Vulnerable)
os.system("echo Running: " + cmd)

# After (Secure)
allowed_commands = ['help', 'status', 'version']
if cmd not in allowed_commands:
    return jsonify({"error": "Command not allowed"}), 400
```

### 4. Hardcoded Secrets → Environment Variables
```python
# Before (Vulnerable)
API_KEY = "AKIA_EXAMPLE_HARDCODED_KEY_123456"

# After (Secure)
API_KEY = os.environ.get('API_KEY', '')
```

### 5. Template Injection → Input Escaping
```python
# Before (Vulnerable)
template = "<h1>Hello %s</h1>" % name

# After (Secure)
safe_name = escape(name)
template = "<h1>Hello {{ name }}</h1>"
```

### 6. Weak Authentication → Password Hashing
```python
# Before (Vulnerable)
"password": "password123"

# After (Secure)
password_hash = generate_password_hash('securepassword123')
check_password_hash(result[0], password)
```

### 7. Debug Mode → Environment Configuration
```python
# Before (Vulnerable)
app.run(debug=True)

# After (Secure)
debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
app.run(debug=debug_mode)
```

## Logging and Monitoring

All test executions are logged to `logs/test_run.log` with timestamps and detailed results. The automatic test runner provides:

- Environment detection (Windows/Linux/macOS/Docker)
- Dependency verification
- Automated setup
- Comprehensive test execution
- Detailed logging and reporting

## Additional Security Improvements

- Database initialization with proper schema
- Error handlers to prevent information leakage
- Input validation and sanitization
- Security-focused logging
- Configurable deployment options
- Session management improvements

## Recommendations

1. Implement regular security code reviews
2. Use automated security scanning in CI/CD
3. Conduct penetration testing
4. Add security headers (CSRF, XSS protection)
5. Implement rate limiting
6. Use HTTPS in production
7. Regular security training for developers

## Support

For questions or issues, refer to the detailed `report.json` file which contains comprehensive vulnerability analysis and remediation details.