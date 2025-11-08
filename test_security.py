#!/usr/bin/env python3
"""
Security test suite that demonstrates vulnerabilities in original code
and validates security in the repaired version.
"""

import requests
import json
import time
import sys
import subprocess
import threading
import pickle
import os
from urllib.parse import quote

class SecurityTester:
    def __init__(self, base_url="http://127.0.0.1:5000", script_path=None):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = []
        self.script_path = script_path
        self.expect_vulnerable = True
        
    def log_result(self, test_name, expected_vulnerable, actual_vulnerable, details=""):
        """Log test results"""
        status = "PASS" if expected_vulnerable == actual_vulnerable else "FAIL"
        result = {
            "test": test_name,
            "expected_vulnerable": expected_vulnerable,
            "actual_vulnerable": actual_vulnerable,
            "status": status,
            "details": details
        }
        self.results.append(result)
        print(f"[{status}] {test_name}: {'Vulnerable' if actual_vulnerable else 'Secure'}")
        if details:
            print(f"    Details: {details}")
    
    def test_sql_injection(self):
        """Test SQL injection vulnerability"""
        # SQL injection payload
        payload = "admin' OR '1'='1' --"
        
        try:
            # If we have access to the source code, do a static check for insecure patterns
            if self.script_path and os.path.exists(self.script_path):
                with open(self.script_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                insecure_pattern = ('format(name)' in code and 'SELECT' in code) or "' + name + '" in code
                if insecure_pattern:
                    self.log_result("SQL Injection", True, True, "Static analysis: vulnerable string formatting found")
                    return
            
            # Fallback: attempt server-based detection via error messages
            response = self.session.get(f"{self.base_url}/greet?name={quote(payload)}")
            
            # Check if SQL-like errors are revealed
            vulnerable = any(keyword in response.text.lower() for keyword in 
                           ['sql', 'sqlite', 'database', 'syntax error'])
            
            self.log_result("SQL Injection", self.expect_vulnerable, vulnerable, 
                          f"Response: {response.text[:100]}...")
            
        except Exception as e:
            self.log_result("SQL Injection", True, False, f"Error: {str(e)}")
    
    def test_template_injection(self):
        """Test Server-Side Template Injection"""
        # Template injection payload
        payload = "{{7*7}}"
        
        try:
            response = self.session.get(f"{self.base_url}/greet?name={quote(payload)}")
            
            # Check if template was evaluated (49 would appear)
            vulnerable = "49" in response.text and "{{" not in response.text
            
            self.log_result("Template Injection", self.expect_vulnerable, vulnerable,
                          f"Payload executed: {'49' in response.text}")
            
        except Exception as e:
            self.log_result("Template Injection", True, False, f"Error: {str(e)}")
    
    def test_command_injection(self):
        """Test Command Injection"""
        # Command injection payload: attempt to create a file as evidence
        injected_file = os.path.join(os.getcwd(), 'injected_cmd.txt')
        if os.path.exists(injected_file):
            try:
                os.remove(injected_file)
            except:
                pass
        
        # Try different separators for Windows/Linux
        payloads = ["; echo INJECTED > %s" % injected_file.replace('\\', '\\\\'),
                    " & echo INJECTED > %s" % injected_file.replace('\\', '\\\\')]
        
        try:
            for payload in payloads:
                response = self.session.post(f"{self.base_url}/run", data={'cmd': payload})
                time.sleep(0.5)
                if os.path.exists(injected_file):
                    vulnerable = True
                    break
            else:
                vulnerable = False
            
            self.log_result("Command Injection", self.expect_vulnerable, vulnerable,
                          f"Command created file: {vulnerable}")
            
        except Exception as e:
            self.log_result("Command Injection", True, False, f"Error: {str(e)}")
    
    def test_pickle_deserialization(self):
        """Test Insecure Pickle Deserialization"""
        # Create a malicious pickle payload that attempts to create a file
        injected_file = os.path.join(os.getcwd(), 'injected_pickle.txt')
        if os.path.exists(injected_file):
            try:
                os.remove(injected_file)
            except:
                pass
        
        class MaliciousPayload:
            def __reduce__(self):
                # Attempt to execute a shell command to create a file
                return (os.system, ("echo PICKLE_INJECTED > %s" % injected_file.replace('\\', '\\\\'),))
        
        try:
            malicious_data = pickle.dumps(MaliciousPayload())
            
            response = self.session.post(f"{self.base_url}/upload_profile",
                                       data=malicious_data,
                                       headers={'Content-Type': 'application/octet-stream'})
            time.sleep(0.5)
            
            # Check if file was created by injected code
            vulnerable = os.path.exists(injected_file)
            
            self.log_result("Pickle Deserialization", self.expect_vulnerable, vulnerable,
                          f"Pickle created file: {vulnerable}")
            
        except Exception as e:
            self.log_result("Pickle Deserialization", True, False, f"Error: {str(e)}")
    
    def test_json_safety(self):
        """Test that JSON endpoint is safe"""
        try:
            safe_data = {"name": "TestUser"}
            response = self.session.post(f"{self.base_url}/upload_profile",
                                       json=safe_data,
                                       headers={'Content-Type': 'application/json'})
            
            # This should work safely
            secure = response.status_code == 200 and "TestUser" in response.text
            
            self.log_result("JSON Safety", False, not secure,
                          f"JSON processed safely: {secure}")
            
        except Exception as e:
            self.log_result("JSON Safety", False, True, f"Error: {str(e)}")
    
    def test_command_whitelist(self):
        """Test command whitelisting"""
        try:
            # Test allowed command
            response = self.session.post(f"{self.base_url}/run", 
                                       data={'cmd': 'help'})
            allowed_works = response.status_code == 200
            
            # Test disallowed command
            response = self.session.post(f"{self.base_url}/run", 
                                       data={'cmd': 'rm -rf /'})
            disallowed_blocked = response.status_code == 400
            
            secure = allowed_works and disallowed_blocked
            
            self.log_result("Command Whitelist", False, not secure,
                          f"Whitelist working: {secure}")
            
        except Exception as e:
            self.log_result("Command Whitelist", False, True, f"Error: {str(e)}")
    
    def wait_for_server(self, max_attempts=30):
        """Wait for server to be ready"""
        for i in range(max_attempts):
            try:
                response = self.session.get(self.base_url, timeout=2)
                return True
            except:
                time.sleep(1)
        return False
    
    def run_all_tests(self, expect_vulnerable=True):
        """Run all security tests"""
        self.expect_vulnerable = expect_vulnerable
        print(f"\n=== Running Security Tests (Expecting {'Vulnerable' if expect_vulnerable else 'Secure'}) ===")
        
        if not self.wait_for_server():
            print("ERROR: Server not responding")
            return False
        
        # Run tests
        self.test_sql_injection()
        self.test_template_injection() 
        self.test_command_injection()
        self.test_pickle_deserialization()
        
        if not expect_vulnerable:
            # Additional tests for secure version
            self.test_json_safety()
            self.test_command_whitelist()
        
        # Summary
        passed = sum(1 for r in self.results if r['status'] == 'PASS')
        total = len(self.results)
        
        print(f"\n=== Test Summary ===")
        print(f"Passed: {passed}/{total}")
        print(f"Expected behavior: {'Vulnerable' if expect_vulnerable else 'Secure'}")
        
        return passed == total

def start_server(script_name, port=5000):
    """Start the Flask server"""
    env = os.environ.copy()
    env.update({
        'FLASK_HOST': '127.0.0.1',
        'FLASK_PORT': str(port),
        'API_KEY': 'test_api_key',
        'SECRET_KEY': 'test_secret_key'
    })
    
    cmd = [sys.executable, script_name]
    return subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, 
                          stderr=subprocess.PIPE)

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_security.py <script_name> [expect_vulnerable]")
        print("Example: python test_security.py input.py true")
        print("Example: python test_security.py input_secure.py false")
        sys.exit(1)
    
    script_name = sys.argv[1]
    expect_vulnerable = len(sys.argv) > 2 and sys.argv[2].lower() == 'true'
    
    print(f"Testing {script_name}")
    
    # Start server
    server_process = start_server(script_name)
    
    try:
        # Run tests
        tester = SecurityTester(script_path=script_name)
        success = tester.run_all_tests(expect_vulnerable)
        
        # Return appropriate exit code
        sys.exit(0 if success else 1)
        
    finally:
        # Cleanup
        server_process.terminate()
        server_process.wait()

if __name__ == "__main__":
    main()