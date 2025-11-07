#!/usr/bin/env python3
"""
Automatic Test Detection and Execution Script
Detects the current environment and runs appropriate tests
Saves logs to logs/test_run.log
"""

import os
import sys
import platform
import subprocess
import json
from datetime import datetime
from pathlib import Path


class EnvironmentDetector:
    """Detects the current environment and available test runners."""
    
    @staticmethod
    def is_docker():
        """Check if running in Docker."""
        return os.path.exists('/.dockerenv')
    
    @staticmethod
    def is_wsl():
        """Check if running in WSL (Windows Subsystem for Linux)."""
        try:
            with open('/proc/version', 'r') as f:
                return 'microsoft' in f.read().lower()
        except:
            return False
    
    @staticmethod
    def get_platform():
        """Get the current platform."""
        return platform.system()
    
    @staticmethod
    def detect_environment():
        """Detect the current environment."""
        env_info = {
            'is_docker': EnvironmentDetector.is_docker(),
            'is_wsl': EnvironmentDetector.is_wsl(),
            'platform': EnvironmentDetector.get_platform(),
            'python_version': platform.python_version(),
            'python_executable': sys.executable,
            'timestamp': datetime.now().isoformat()
        }
        return env_info


class TestRunner:
    """Runs tests based on the detected environment."""
    
    def __init__(self, log_file='logs/test_run.log'):
        self.log_file = log_file
        self.logs = []
        self.ensure_log_directory()
    
    def ensure_log_directory(self):
        """Ensure logs directory exists."""
        log_dir = os.path.dirname(self.log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
    
    def log(self, message, level='INFO'):
        """Log a message."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {level}: {message}"
        self.logs.append(log_entry)
        print(log_entry)
    
    def save_logs(self):
        """Save logs to file."""
        with open(self.log_file, 'w') as f:
            f.write('\n'.join(self.logs))
        self.log(f"Logs saved to {self.log_file}")
    
    def run_shell_tests(self, script_path):
        """Run shell-based tests."""
        try:
            self.log(f"Running shell tests from {script_path}")
            result = subprocess.run(['bash', script_path], capture_output=True, text=True)
            self.log(f"Shell test output:\n{result.stdout}")
            if result.returncode != 0:
                self.log(f"Shell test stderr:\n{result.stderr}", 'ERROR')
            return result.returncode == 0
        except Exception as e:
            self.log(f"Error running shell tests: {e}", 'ERROR')
            return False
    
    def run_python_tests(self):
        """Run Python-based tests."""
        try:
            self.log("Running Python-based tests")
            
            # Test 1: Hardcoded API Key
            self.log("Test 1: Checking for hardcoded API key in input.py")
            with open('input.py', 'r') as f:
                if 'AKIA_EXAMPLE_HARDCODED_KEY' in f.read():
                    self.log("FAIL: Hardcoded API key found", 'WARN')
                    return False
                else:
                    self.log("PASS: No hardcoded API key in vulnerable code", 'INFO')
            
            # Test 2: Pickle vulnerability
            self.log("Test 2: Checking for pickle.loads in input.py")
            with open('input.py', 'r') as f:
                if 'pickle.loads' in f.read():
                    self.log("FAIL: pickle.loads found in vulnerable code", 'WARN')
                    return False
                else:
                    self.log("PASS: No pickle.loads in vulnerable code", 'INFO')
            
            # Test 3: os.system vulnerability
            self.log("Test 3: Checking for os.system in input.py")
            with open('input.py', 'r') as f:
                if 'os.system' in f.read():
                    self.log("FAIL: os.system found in vulnerable code", 'WARN')
                    return False
                else:
                    self.log("PASS: No os.system in vulnerable code", 'INFO')
            
            # Test 4: Fixed version checks
            self.log("Test 4: Verifying fixes in input_fixed.py")
            with open('input_fixed.py', 'r') as f:
                fixed_content = f.read()
                
            checks = [
                ('subprocess', 'subprocess module used'),
                ('os.environ.get', 'Environment variables used'),
                ('request.get_json', 'JSON deserialization used'),
                ('generate_password_hash', 'Password hashing used'),
                ('check_password_hash', 'Password verification used'),
                ('render_template_string(template, name=name)', 'Safe template rendering used')
            ]
            
            all_passed = True
            for check_string, description in checks:
                if check_string in fixed_content:
                    self.log(f"PASS: {description}", 'INFO')
                else:
                    self.log(f"FAIL: {description} not found", 'ERROR')
                    all_passed = False
            
            return all_passed
            
        except Exception as e:
            self.log(f"Error running Python tests: {e}", 'ERROR')
            return False
    
    def run_tests(self, env_info):
        """Run tests based on environment."""
        self.log("=" * 50)
        self.log("Flask Security Audit - Test Execution")
        self.log("=" * 50)
        self.log(f"Environment Info: {json.dumps(env_info, indent=2)}")
        self.log("")
        
        results = {
            'environment': env_info,
            'test_results': {},
            'overall_status': 'FAILED'
        }
        
        # Run Python tests (platform-independent)
        python_test_result = self.run_python_tests()
        results['test_results']['python_tests'] = python_test_result
        
        # Run platform-specific shell tests
        if env_info['platform'] == 'Windows':
            if os.path.exists('run_test.bat'):
                self.log("\nRunning Windows batch tests...")
                try:
                    result = subprocess.run(['cmd', '/c', 'run_test.bat'], 
                                          capture_output=True, text=True)
                    self.log(f"Batch test output:\n{result.stdout}")
                    if result.stderr:
                        self.log(f"Batch test stderr:\n{result.stderr}", 'WARN')
                    results['test_results']['batch_tests'] = result.returncode == 0
                except Exception as e:
                    self.log(f"Error running batch tests: {e}", 'ERROR')
                    results['test_results']['batch_tests'] = False
        else:
            if os.path.exists('run_test.sh'):
                self.log("\nRunning shell tests...")
                shell_test_result = self.run_shell_tests('run_test.sh')
                results['test_results']['shell_tests'] = shell_test_result
        
        # Determine overall status
        if all(results['test_results'].values()):
            results['overall_status'] = 'PASSED'
            self.log("\n" + "=" * 50)
            self.log("ALL TESTS PASSED!", 'INFO')
            self.log("=" * 50)
        else:
            self.log("\n" + "=" * 50)
            self.log("SOME TESTS FAILED", 'ERROR')
            self.log("=" * 50)
        
        return results


def main():
    """Main entry point."""
    try:
        # Detect environment
        detector = EnvironmentDetector()
        env_info = detector.detect_environment()
        
        # Create test runner
        runner = TestRunner()
        
        # Run tests
        results = runner.run_tests(env_info)
        
        # Save logs
        runner.save_logs()
        
        # Save results as JSON
        results_file = 'logs/test_results.json'
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        runner.log(f"Results saved to {results_file}")
        
        # Exit with appropriate code
        sys.exit(0 if results['overall_status'] == 'PASSED' else 1)
        
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(2)


if __name__ == '__main__':
    main()
