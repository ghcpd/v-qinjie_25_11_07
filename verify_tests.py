#!/usr/bin/env python3
"""
Test verification script to ensure all components work correctly
"""

import os
import sys
import subprocess
import time
import requests
import json
import sqlite3
from threading import Thread

def create_test_db():
    """Create test database with sample data"""
    conn = sqlite3.connect('users.db')
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT)')
    cur.execute('DELETE FROM users')
    cur.execute('INSERT INTO users (id, username) VALUES (1, "admin")')
    cur.execute('INSERT INTO users (id, username) VALUES (2, "testuser")')
    cur.execute('INSERT INTO users (id, username) VALUES (3, "alice")')
    conn.commit()
    conn.close()
    print("Test database created")

def test_vulnerable_app():
    """Test the vulnerable version"""
    print("\n=== Testing Vulnerable App ===")
    
    # Start app in background
    process = subprocess.Popen([sys.executable, 'input.py'], 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE)
    time.sleep(3)
    
    results = {}
    
    try:
        # Test 1: Basic functionality
        response = requests.get('http://localhost:5000/greet?name=test', timeout=5)
        results['basic'] = response.status_code == 200
        
        # Test 2: SQL Injection vulnerability
        response = requests.get("http://localhost:5000/search?name=test' OR '1'='1", timeout=5)
        results['sql_injection'] = 'admin' in response.text
        
        # Test 3: Template injection vulnerability  
        response = requests.get('http://localhost:5000/greet?name={{7*7}}', timeout=5)
        results['template_injection'] = '49' in response.text
        
        # Test 4: Command injection vulnerability
        response = requests.post('http://localhost:5000/run', 
                               data={'cmd': 'echo test123'}, timeout=5)
        results['command_injection'] = response.status_code == 200
        
    except Exception as e:
        print(f"Error testing vulnerable app: {e}")
    finally:
        process.terminate()
        time.sleep(1)
    
    print(f"Basic functionality: {'OK' if results.get('basic') else 'FAIL'}")
    print(f"SQL injection vulnerable: {'OK' if results.get('sql_injection') else 'FAIL'}")
    print(f"Template injection vulnerable: {'OK' if results.get('template_injection') else 'FAIL'}")
    print(f"Command injection accessible: {'OK' if results.get('command_injection') else 'FAIL'}")
    
    return results

def test_secure_app():
    """Test the secure version"""
    print("\n=== Testing Secure App ===")
    
    # Set environment variables
    os.environ['API_KEY'] = 'test_api_key_for_demo'
    
    # Start app in background
    process = subprocess.Popen([sys.executable, 'input_secure.py'], 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE)
    time.sleep(3)
    
    results = {}
    
    try:
        # Test 1: Basic functionality
        response = requests.get('http://localhost:5000/greet?name=test', timeout=5)
        results['basic'] = response.status_code == 200
        
        # Test 2: SQL Injection protection
        response = requests.get("http://localhost:5000/search?name=test' OR '1'='1", timeout=5)
        results['sql_protection'] = 'admin' not in response.text
        
        # Test 3: Template injection protection
        response = requests.get('http://localhost:5000/greet?name={{7*7}}', timeout=5)
        results['template_protection'] = '{{7*7}}' in response.text and '49' not in response.text
        
        # Test 4: API authentication required
        response = requests.post('http://localhost:5000/run', 
                               data={'cmd': 'echo test'}, timeout=5)
        results['auth_required'] = response.status_code == 401
        
        # Test 5: Valid API request works
        headers = {'X-API-Key': 'test_api_key_for_demo'}
        response = requests.post('http://localhost:5000/run', 
                               headers=headers,
                               data={'cmd': 'echo test'}, timeout=5)
        print('DEBUG: Valid auth status:', response.status_code)
        print('DEBUG: Valid auth body:', response.text)
        results['valid_auth'] = response.status_code == 200
        
        # Test 6: Command injection protection
        headers = {'X-API-Key': 'test_api_key_for_demo'}
        response = requests.post('http://localhost:5000/run', 
                               headers=headers,
                               data={'cmd': 'rm -rf /'}, timeout=5)
        print('DEBUG: Command protection status:', response.status_code)
        print('DEBUG: Command protection body:', response.text)
        results['command_protection'] = 'not allowed' in response.text
        
    except Exception as e:
        print(f"Error testing secure app: {e}")
    finally:
        process.terminate()
        time.sleep(1)
    
    print(f"Basic functionality: {'OK' if results.get('basic') else 'FAIL'}")
    print(f"SQL injection blocked: {'OK' if results.get('sql_protection') else 'FAIL'}")
    print(f"Template injection blocked: {'OK' if results.get('template_protection') else 'FAIL'}")
    print(f"Authentication required: {'OK' if results.get('auth_required') else 'FAIL'}")
    print(f"Valid authentication works: {'OK' if results.get('valid_auth') else 'FAIL'}")
    print(f"Command injection blocked: {'OK' if results.get('command_protection') else 'FAIL'}")
    
    return results

def main():
    """Main test verification function"""
    print("Flask Security Audit - Test Verification")
    print("=" * 50)
    
    # Create test database
    create_test_db()
    
    # Test vulnerable app
    vuln_results = test_vulnerable_app()
    
    # Test secure app  
    secure_results = test_secure_app()
    
    # Summary
    print("\n=== Test Summary ===")
    
    vuln_expected = {
        'basic': True,
        'sql_injection': True,
        'template_injection': True,
        'command_injection': True
    }
    
    secure_expected = {
        'basic': True,
        'sql_protection': True,
        'template_protection': True,
        'auth_required': True,
        'valid_auth': True,
        'command_protection': True
    }
    
    vuln_score = sum(1 for k, v in vuln_expected.items() if vuln_results.get(k) == v)
    secure_score = sum(1 for k, v in secure_expected.items() if secure_results.get(k) == v)
    
    print(f"Vulnerable app tests: {vuln_score}/{len(vuln_expected)} passed")
    print(f"Secure app tests: {secure_score}/{len(secure_expected)} passed")
    
    total_score = vuln_score + secure_score
    total_possible = len(vuln_expected) + len(secure_expected)
    
    print(f"\nOverall: {total_score}/{total_possible} tests passed")
    
    if total_score == total_possible:
        print("ALL TESTS PASSED - Security audit implementation is working correctly!")
        return 0
    else:
        print("Some tests failed - please review the implementation")
        return 1

if __name__ == '__main__':
    sys.exit(main())