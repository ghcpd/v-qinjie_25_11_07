# Security Fix Implementation Guide

## Overview
This document provides detailed explanations for each vulnerability fix applied to the Flask application.

---

## VUL-001: Hardcoded API Key

### ❌ Vulnerable Code
```python
API_KEY = "AKIA_EXAMPLE_HARDCODED_KEY_123456"
```

### ✅ Secure Code
```python
API_KEY = os.environ.get('API_KEY', 'default-dev-key-change-in-production')
```

### Why This Is Dangerous
- **Credential Exposure**: The API key is visible in version control history and source code
- **Attacker Access**: Anyone with repository access can use the key to authenticate as the application
- **Compliance Violation**: Violates PCI-DSS, HIPAA, and other standards
- **Irreversible**: Once exposed, the key must be rotated across all systems

### How to Fix
1. Remove the hardcoded key immediately
2. Load from environment variables using `os.environ.get()`
3. Provide a sensible default only for development
4. Rotate the exposed AWS key in your AWS console
5. Use a secrets management service in production (AWS Secrets Manager, HashiCorp Vault, etc.)

### Testing
```bash
# Before: Key visible in source
grep "AKIA_" input.py

# After: Key in environment only
echo $API_KEY  # On Linux/macOS
$env:API_KEY  # On Windows PowerShell
```

---

## VUL-002: SQL Injection

### ❌ Vulnerable Code
```python
sql = "SELECT id, username FROM users WHERE username LIKE '%{}%'".format(name)
cur.execute(sql)
```

### ✅ Secure Code
```python
sql = "SELECT id, username FROM users WHERE username LIKE ?"
cur.execute(sql, (f'%{name}%',))
```

### Why This Is Dangerous
**Attack Example:**
```
Input: ' OR '1'='1
Result: SELECT * FROM users WHERE username LIKE '%' OR '1'='1%'
Effect: Returns all users, authentication bypass
```

- **Complete Database Compromise**: Attackers can read, modify, or delete data
- **Data Exfiltration**: Extract sensitive information like passwords, PII
- **Privilege Escalation**: Modify user roles or create admin accounts
- **System Takeover**: Execute commands if database permissions allow

### How to Fix
1. Always use parameterized queries (prepared statements)
2. Never concatenate user input into SQL strings
3. Use the `?` placeholder (SQLite) or `%s` (PostgreSQL)
4. Pass data as separate tuple to execute()

### Testing
```python
# Vulnerable - will execute injection
query_users_by_name("' OR '1'='1")

# Secure - treats as literal string
# SELECT * FROM users WHERE username LIKE '%' OR '1'='1%'
# (searches for that exact string, doesn't execute)
```

---

## VUL-003: Insecure Deserialization

### ❌ Vulnerable Code
```python
data = request.data
profile = pickle.loads(data)
```

### ✅ Secure Code
```python
data = request.get_json()
if not data:
    return jsonify({"error": "Invalid JSON"}), 400
profile = data
```

### Why This Is Dangerous
**Pickle Arbitrary Code Execution Example:**
```python
import pickle
import os

# Malicious pickle that executes code
class Shell(object):
    def __reduce__(self):
        return (os.system, ('rm -rf /',))

# When attacker sends this pickled object and it's unpickled:
# The entire server filesystem is deleted!
```

- **Remote Code Execution (RCE)**: Attackers execute arbitrary Python code on server
- **Complete System Compromise**: With server code execution, attackers get full system access
- **Data Theft**: Access to all application data and secrets
- **Lateral Movement**: Use compromised server to attack internal systems

### How to Fix
1. Never use pickle for untrusted input
2. Replace with JSON deserialization
3. Validate JSON schema if needed
4. Consider using safer serialization like MessagePack or Protocol Buffers if needed
5. Implement input validation and error handling

### Testing
```python
# Vulnerable - accepts any pickled object
pickle.loads(attacker_payload)

# Secure - only accepts JSON
try:
    json.loads(data)
except json.JSONDecodeError:
    return error
```

---

## VUL-004: OS Command Injection

### ❌ Vulnerable Code
```python
cmd = request.form.get('cmd', '')
os.system("echo Running: " + cmd)
```

### ✅ Secure Code
```python
cmd = request.form.get('cmd', '')
try:
    result = subprocess.run(
        ['echo', 'Running:', cmd],
        capture_output=True,
        text=True,
        timeout=5
    )
    return jsonify({"status": "done", "output": result.stdout})
except subprocess.TimeoutExpired:
    return jsonify({"error": "Command timeout"}), 500
```

### Why This Is Dangerous
**Attack Example:**
```
Input: test; rm -rf /
Execution: echo Running: test; rm -rf /
Effect: Deletes entire filesystem!
```

- **Server Compromise**: Execute any command on the server
- **Data Destruction**: Delete files, databases, backups
- **Lateral Attacks**: Access internal networks and systems
- **Ransomware**: Encrypt valuable data and demand ransom

### How to Fix
1. Use `subprocess.run()` with argument list instead of shell string
2. Never concatenate user input into commands
3. Implement timeout protection
4. Capture and validate output
5. Never use `shell=True` parameter

### Testing
```python
# Vulnerable - command injection succeeds
os.system("echo Running: test; whoami")

# Secure - treats "test; whoami" as literal argument
subprocess.run(['echo', 'Running:', 'test; whoami'])
# Output: echo Running: test; whoami
```

---

## VUL-005: Server-Side Template Injection (SSTI)

### ❌ Vulnerable Code
```python
name = request.args.get('name', 'guest')
template = "<h1>Hello %s</h1>" % name
return render_template_string(template)
```

### ✅ Secure Code
```python
name = request.args.get('name', 'guest')
template = "<h1>Hello {{ name }}</h1>"
return render_template_string(template, name=name)
```

### Why This Is Dangerous
**Attack Example:**
```
Input: {{ request.environ }}
Execution: Template renders environment variables
Effect: Attacker sees sensitive configuration and secrets
```

- **Information Disclosure**: Access environment variables, configuration
- **Code Execution**: Jinja2 templates can call Python methods and properties
- **Authentication Bypass**: Access session data, tokens
- **Privilege Escalation**: Modify application behavior

### How to Fix
1. Use Jinja2 template variables `{{ variable }}`
2. Pass data as context parameters
3. Rely on Jinja2's auto-escaping for HTML
4. Never build template strings dynamically
5. Use static templates from files when possible

### Testing
```python
# Vulnerable - injects template code
render_template_string("<h1>Hello %s</h1>" % "{{ 1+1 }}")
# Output: <h1>Hello 2</h1> - template executed!

# Secure - template code treated as text
render_template_string("<h1>Hello {{ name }}</h1>", name="{{ 1+1 }}")
# Output: <h1>Hello {{ 1+1 }}</h1> - displayed as literal text
```

---

## VUL-006: Weak Password Storage

### ❌ Vulnerable Code
```python
USERS = {
    "alice": {"password": "password123"},
}

if user and user.get("password") == password:
    return "login ok"
```

### ✅ Secure Code
```python
from werkzeug.security import generate_password_hash, check_password_hash

USERS = {
    "alice": {"password": generate_password_hash("secure_password_123")},
}

if user and check_password_hash(user.get("password", ""), password):
    return jsonify({"status": "login ok"})
```

### Why This Is Dangerous
- **Database Breach**: If database is compromised, attacker has all passwords
- **Credential Reuse**: Users often reuse passwords across services
- **Account Takeover**: Direct access to user accounts
- **Compliance Violation**: GDPR, CCPA require password protection
- **Irreversible**: Plaintext passwords cannot be recovered securely

**Hash Comparison Issue:**
```python
# Vulnerable - timing attack possible
if user["password"] == provided_password:  # Fast fail if first char doesn't match

# Secure - constant-time comparison
check_password_hash(user["password"], provided_password)  # Always takes same time
```

### How to Fix
1. Use bcrypt hashing via werkzeug.security
2. Hash passwords before storing (never store plaintext)
3. Use `check_password_hash()` for verification
4. Consider argon2 for even stronger protection
5. Implement password policies (length, complexity)
6. Use constant-time comparison functions

### Testing
```python
from werkzeug.security import generate_password_hash, check_password_hash

# Generate hash
hash_value = generate_password_hash("mypassword123")
print(hash_value)
# Example: pbkdf2:sha256:260000$...

# Verify password
check_password_hash(hash_value, "mypassword123")  # True
check_password_hash(hash_value, "wrongpassword")  # False
```

---

## VUL-007: Debug Mode Enabled

### ❌ Vulnerable Code
```python
if __name__ == '__main__':
    app.run(debug=True)
```

### ✅ Secure Code
```python
if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_DEBUG', 'False') == 'True'
    app.run(debug=debug_mode)
```

### Why This Is Dangerous
**Debug Mode Exposes:**
- Full stack traces with local variables
- Source code paths and structure
- Environment variables and configuration
- Interactive Python console on errors
- Static file access and URLs
- Database queries and performance info

- **Information Disclosure**: Attackers learn system architecture
- **Credential Exposure**: Secrets in stack traces and variables
- **Interactive Console**: If REPL available, remote code execution
- **Attack Surface**: More information for crafting targeted attacks

### How to Fix
1. Disable debug mode in production (`debug=False`)
2. Make it configurable via environment variables
3. Enable detailed logging instead of debug mode
4. Implement proper error pages for production
5. Never expose stack traces to users

### Testing
```python
# Development
export FLASK_DEBUG=True
python app.py

# Production
export FLASK_DEBUG=False
python app.py
```

---

## Summary: Defense in Depth

The fixes demonstrate multiple security principles:

| Principle | Implementation |
|-----------|-----------------|
| **Least Privilege** | API key only where needed (environment) |
| **Input Validation** | Parameterized queries, JSON schema |
| **Output Encoding** | Jinja2 auto-escaping for HTML |
| **Secure Defaults** | Debug off by default, safe methods |
| **Defense in Depth** | Multiple layers (validation + hashing + timeouts) |
| **Secure Libraries** | subprocess, werkzeug.security, JSON |
| **Configuration Management** | Environment-driven, no hardcoding |

---

## Verification Checklist

- [ ] API key moved to .env file
- [ ] All SQL queries use parameterized format
- [ ] pickle completely removed from codebase
- [ ] subprocess.run() used for all command execution
- [ ] All templates use {{ }} variables, not % formatting
- [ ] All passwords hashed with generate_password_hash()
- [ ] Debug mode configurable via environment
- [ ] .env file added to .gitignore
- [ ] Tests pass for all fixes
- [ ] Application tested with fixed code
- [ ] Old hardcoded API key rotated in AWS

---

## Resources

- [OWASP Top 10 2021](https://owasp.org/Top10/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [OWASP Cheat Sheets](https://cheatsheetseries.owasp.org/)
- [Flask Security Documentation](https://flask.palletsprojects.com/security/)
- [Werkzeug Security](https://werkzeug.palletsprojects.com/en/2.3.x/utils/#security)

